"""
Serviços de Consultas, Autenticação, Triagem e Prontuários.
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Optional

from core.abstracts import IAppointmentService, IAuthService, ITriageService
from core.exceptions import (
    AppointmentNotFoundError, AuthenticationError, PatientNotFoundError,
    DoctorNotFoundError, RecordNotFoundError, ValidationError
)
from core.decorators import log_action, validate_required
from database.models import (
    Appointment, AppointmentStatus, MedicalRecord, Triage,
    TriagePriority, User, Doctor
)
from database.repositories import (
    AppointmentRepository, UserRepository, TriageRepository,
    MedicalRecordRepository, SQLAlchemyRepository
)

logger = logging.getLogger("HospitalSystem.Services")


# ─── Autenticação ────────────────────────────────────────────────────────────

class AuthService(IAuthService):
    """Serviço de autenticação de utilizadores."""

    def __init__(self, session):
        self._repo = UserRepository(session, User)
        self._session = session

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @log_action("AuthService.login")
    def login(self, username: str, password: str) -> Optional[dict]:
        user = self._repo.get_by_username(username)
        if not user or not user.is_active:
            raise AuthenticationError("Utilizador não encontrado ou inactivo.")
        if user.password_hash != self._hash(password):
            raise AuthenticationError("Palavra-passe incorrecta.")
        user.last_login = datetime.utcnow()
        self._session.commit()
        return user.to_dict()

    def logout(self, user_id: int) -> None:
        logger.info(f"Utilizador {user_id} saiu do sistema.")

    def change_password(self, user_id: int, old_pw: str, new_pw: str) -> bool:
        user = self._repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("Utilizador não encontrado.")
        if user.password_hash != self._hash(old_pw):
            raise AuthenticationError("Palavra-passe actual incorrecta.")
        if len(new_pw) < 6:
            raise ValidationError("A nova palavra-passe deve ter pelo menos 6 caracteres.")
        user.password_hash = self._hash(new_pw)
        self._session.commit()
        return True

    def get_all_users(self) -> List[User]:
        return self._repo.get_all()

    def create_user(self, data: dict) -> User:
        new_user = User(
            username=data["username"],
            password_hash=self._hash(data.get("password", "123456")),
            full_name=data["full_name"],
            email=data.get("email"),
            role=data["role"],
            is_active=True,
        )
        return self._repo.create(new_user)

    def get_active_doctors(self) -> List[Doctor]:
        return self._repo.get_active_doctors()


# ─── Consultas ───────────────────────────────────────────────────────────────

class AppointmentService(IAppointmentService):
    """Serviço de gestão de consultas médicas."""

    def __init__(self, session):
        self._repo = AppointmentRepository(session, Appointment)
        self._session = session

    @log_action("AppointmentService.schedule")
    @validate_required("patient_id", "doctor_id", "scheduled_date")
    def schedule_appointment(self, data: dict) -> Appointment:
        scheduled = data["scheduled_date"]
        if isinstance(scheduled, str):
            scheduled = datetime.strptime(scheduled, "%Y-%m-%d %H:%M")

        appt = Appointment(
            patient_id=int(data["patient_id"]),
            doctor_id=int(data["doctor_id"]),
            scheduled_date=scheduled,
            reason=data.get("reason", "").strip() or None,
            notes=data.get("notes", "").strip() or None,
            status=AppointmentStatus.SCHEDULED,
        )
        return self._repo.create(appt)

    @log_action("AppointmentService.cancel")
    def cancel_appointment(self, appointment_id: int) -> bool:
        appt = self._repo.get_by_id(appointment_id)
        if not appt:
            raise AppointmentNotFoundError(appointment_id)
        appt.status = AppointmentStatus.CANCELLED
        self._session.commit()
        return True

    def complete_appointment(self, appointment_id: int) -> bool:
        appt = self._repo.get_by_id(appointment_id)
        if not appt:
            raise AppointmentNotFoundError(appointment_id)
        appt.status = AppointmentStatus.COMPLETED
        self._session.commit()
        return True

    def get_appointments_by_patient(self, patient_id: int) -> List[Appointment]:
        return self._repo.get_by_patient(patient_id)

    def get_appointments_by_doctor(self, doctor_id: int) -> List[Appointment]:
        return self._repo.get_by_doctor(doctor_id)

    def get_all_appointments(self) -> List[Appointment]:
        return self._repo.get_all()

    def count_by_status(self) -> dict:
        return self._repo.count_by_status()

    def get_by_id(self, appt_id: int) -> Appointment:
        appt = self._repo.get_by_id(appt_id)
        if not appt:
            raise AppointmentNotFoundError(appt_id)
        return appt


# ─── Triagem com IA ──────────────────────────────────────────────────────────

class TriageService:
    """Serviço de triagem de pacientes integrado com modelo de IA."""

    def __init__(self, session, ai_model):
        self._repo = TriageRepository(session, Triage)
        self._ai = ai_model
        self._session = session

    @log_action("TriageService.triage_patient")
    def triage_patient(self, patient_id: int, symptoms: dict, user_id: int = None) -> dict:
        """Executa a triagem IA e persiste o resultado."""
        result = self._ai.predict_priority(symptoms)
        recommendation = self._ai.get_recommendation(result["priority"])

        priority_map = {p.value: p for p in TriagePriority}
        priority_enum = priority_map.get(result["priority"], TriagePriority.NORMAL)

        triage = Triage(
            patient_id=patient_id,
            symptoms=json.dumps(symptoms, ensure_ascii=False),
            priority=priority_enum,
            ai_confidence=result["confidence"],
            recommendation=recommendation,
            attended_by=user_id,
        )
        saved = self._repo.create(triage)
        result["triage_id"] = saved.id
        result["recommendation"] = recommendation
        return result

    def get_triages_by_patient(self, patient_id: int) -> List[Triage]:
        return self._repo.get_by_patient(patient_id)

    def get_recent_triages(self, limit: int = 20) -> List[Triage]:
        return self._repo.get_recent(limit)

    def count_by_priority(self) -> dict:
        return self._repo.count_by_priority()

    def get_ai_metrics(self) -> dict:
        return self._ai.get_model_metrics()

    def get_feature_importance(self) -> dict:
        return self._ai.get_feature_importance()


# ─── Prontuários ─────────────────────────────────────────────────────────────

class MedicalRecordService:
    """Serviço de gestão de prontuários médicos."""

    def __init__(self, session):
        self._repo = MedicalRecordRepository(session, MedicalRecord)
        self._session = session

    @log_action("MedicalRecordService.create")
    def create_record(self, data: dict) -> MedicalRecord:
        record = MedicalRecord(
            patient_id=int(data["patient_id"]),
            appointment_id=data.get("appointment_id"),
            diagnosis=data.get("diagnosis", "").strip() or None,
            prescription=data.get("prescription", "").strip() or None,
            observations=data.get("observations", "").strip() or None,
            weight=float(data["weight"]) if data.get("weight") else None,
            height=float(data["height"]) if data.get("height") else None,
            blood_pressure=data.get("blood_pressure", "").strip() or None,
            temperature=float(data["temperature"]) if data.get("temperature") else None,
            heart_rate=int(data["heart_rate"]) if data.get("heart_rate") else None,
        )
        return self._repo.create(record)

    def get_records_by_patient(self, patient_id: int) -> List[MedicalRecord]:
        return self._repo.get_by_patient(patient_id)

    def get_record(self, record_id: int) -> MedicalRecord:
        record = self._repo.get_by_id(record_id)
        if not record:
            raise RecordNotFoundError(record_id)
        return record

    def update_record(self, record_id: int, data: dict) -> MedicalRecord:
        record = self.get_record(record_id)
        for field in ["diagnosis", "prescription", "observations", "blood_pressure"]:
            if field in data:
                setattr(record, field, data[field].strip() or None)
        for field in ["weight", "height", "temperature"]:
            if field in data and data[field]:
                setattr(record, field, float(data[field]))
        if "heart_rate" in data and data["heart_rate"]:
            record.heart_rate = int(data["heart_rate"])
        return self._repo.update(record)
