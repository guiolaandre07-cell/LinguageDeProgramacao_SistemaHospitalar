"""
Serviço de gestão de pacientes.
Implementa a lógica de negócio para operações com pacientes.
"""
import logging
from datetime import date, datetime
from typing import List, Optional

from core.abstracts import IPatientService
from core.exceptions import (
    PatientNotFoundError, DuplicateRecordError, ValidationError
)
from core.decorators import log_action, validate_required
from database.models import Patient, Gender
from database.repositories import PatientRepository

logger = logging.getLogger("HospitalSystem.PatientService")


class PatientService(IPatientService):
    """Implementação do serviço de pacientes."""

    def __init__(self, session):
        self._repo = PatientRepository(session, Patient)

    @log_action("PatientService.register")
    @validate_required("full_name", "birth_date", "gender")
    def register_patient(self, data: dict) -> Patient:
        """Regista um novo paciente no sistema."""
        # Verificar BI duplicado
        if data.get("bi"):
            existing = self._repo.get_by_bi(data["bi"])
            if existing:
                raise DuplicateRecordError(
                    f"Já existe um paciente com o BI '{data['bi']}'."
                )

        birth = data["birth_date"]
        if isinstance(birth, str):
            birth = datetime.strptime(birth, "%Y-%m-%d").date()

        gender_val = data["gender"]
        if isinstance(gender_val, str):
            for g in Gender:
                if g.value == gender_val or g.name == gender_val:
                    gender_val = g
                    break

        patient = Patient(
            full_name=data["full_name"].strip(),
            birth_date=birth,
            gender=gender_val,
            bi=(data.get("bi") or "").strip() or None,
            phone=(data.get("phone") or "").strip() or None,
            email=(data.get("email") or "").strip() or None,
            address=(data.get("address") or "").strip() or None,
            blood_type=(data.get("blood_type") or "").strip() or None,
            allergies=(data.get("allergies") or "").strip() or None,
            emergency_contact=(data.get("emergency_contact") or "").strip() or None,
        )
        return self._repo.create(patient)

    def get_patient(self, patient_id: int) -> Patient:
        patient = self._repo.get_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(patient_id)
        return patient

    def get_all_patients(self) -> List[Patient]:
        return self._repo.get_all()

    def search_patients(self, query: str) -> List[Patient]:
        return self._repo.search(query)

    @log_action("PatientService.update")
    def update_patient(self, patient_id: int, data: dict) -> Patient:
        patient = self.get_patient(patient_id)

        if "full_name" in data and data["full_name"]:
            patient.full_name = data["full_name"].strip()
        if "phone" in data:
            patient.phone = data["phone"].strip() or None
        if "email" in data:
            patient.email = data["email"].strip() or None
        if "address" in data:
            patient.address = data["address"].strip() or None
        if "blood_type" in data:
            patient.blood_type = data["blood_type"].strip() or None
        if "allergies" in data:
            patient.allergies = data["allergies"].strip() or None
        if "emergency_contact" in data:
            patient.emergency_contact = data["emergency_contact"].strip() or None
        if "birth_date" in data and data["birth_date"]:
            bd = data["birth_date"]
            if isinstance(bd, str):
                bd = datetime.strptime(bd, "%Y-%m-%d").date()
            patient.birth_date = bd

        patient.updated_at = datetime.utcnow()
        return self._repo.update(patient)

    @log_action("PatientService.delete")
    def delete_patient(self, patient_id: int) -> bool:
        self.get_patient(patient_id)  # raises if not found
        return self._repo.delete(patient_id)

    def get_patient_count(self) -> int:
        return len(self._repo.get_all())

    def calculate_age(self, birth_date: date) -> int:
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
