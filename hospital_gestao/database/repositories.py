"""
Repositórios DAO genéricos e especializados.
Implementa padrão Repository com SQLAlchemy para todas as entidades.
"""
from typing import List, Optional, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from core.abstracts import IRepository
from core.decorators import log_action
from core.exceptions import DatabaseError
import logging

logger = logging.getLogger("HospitalSystem.Repository")

T = TypeVar("T")


class SQLAlchemyRepository(IRepository, Generic[T]):
    """Repositório genérico com operações CRUD via SQLAlchemy."""

    def __init__(self, session: Session, model: Type[T]):
        self._session = session
        self._model = model

    @log_action("Repository.create")
    def create(self, entity: T) -> T:
        try:
            self._session.add(entity)
            self._session.commit()
            self._session.refresh(entity)
            return entity
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f"Erro ao criar {self._model.__name__}: {e}")

    def get_by_id(self, entity_id: int) -> Optional[T]:
        try:
            return self._session.query(self._model).filter_by(id=entity_id).first()
        except Exception as e:
            raise DatabaseError(f"Erro ao buscar {self._model.__name__} id={entity_id}: {e}")

    def get_all(self) -> List[T]:
        try:
            return self._session.query(self._model).all()
        except Exception as e:
            raise DatabaseError(f"Erro ao listar {self._model.__name__}: {e}")

    @log_action("Repository.update")
    def update(self, entity: T) -> T:
        try:
            self._session.merge(entity)
            self._session.commit()
            return entity
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f"Erro ao actualizar {self._model.__name__}: {e}")

    @log_action("Repository.delete")
    def delete(self, entity_id: int) -> bool:
        try:
            obj = self.get_by_id(entity_id)
            if obj:
                self._session.delete(obj)
                self._session.commit()
                return True
            return False
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f"Erro ao eliminar {self._model.__name__} id={entity_id}: {e}")


# ─── Repositórios Especializados ─────────────────────────────────────────────

class PatientRepository(SQLAlchemyRepository):
    """Repositório especializado para pacientes."""

    def search(self, query: str):
        from database.models import Patient
        q = f"%{query}%"
        try:
            return (
                self._session.query(Patient)
                .filter(
                    Patient.full_name.ilike(q)
                    | Patient.bi.ilike(q)
                    | Patient.phone.ilike(q)
                    | Patient.email.ilike(q)
                )
                .all()
            )
        except Exception as e:
            raise DatabaseError(f"Erro na pesquisa de pacientes: {e}")

    def get_by_bi(self, bi: str):
        from database.models import Patient
        return self._session.query(Patient).filter_by(bi=bi).first()


class AppointmentRepository(SQLAlchemyRepository):
    """Repositório especializado para consultas."""

    def get_by_patient(self, patient_id: int):
        from database.models import Appointment
        return (
            self._session.query(Appointment)
            .filter_by(patient_id=patient_id)
            .order_by(Appointment.scheduled_date.desc())
            .all()
        )

    def get_by_doctor(self, doctor_id: int):
        from database.models import Appointment
        return (
            self._session.query(Appointment)
            .filter_by(doctor_id=doctor_id)
            .order_by(Appointment.scheduled_date.desc())
            .all()
        )

    def get_by_date(self, date_from, date_to=None):
        from database.models import Appointment
        from sqlalchemy import and_
        q = self._session.query(Appointment).filter(
            Appointment.scheduled_date >= date_from
        )
        if date_to:
            q = q.filter(Appointment.scheduled_date <= date_to)
        return q.order_by(Appointment.scheduled_date).all()

    def count_by_status(self):
        """Retorna contagem agrupada por status para o dashboard."""
        from database.models import Appointment, AppointmentStatus
        from sqlalchemy import func
        rows = (
            self._session.query(Appointment.status, func.count(Appointment.id))
            .group_by(Appointment.status)
            .all()
        )
        return {row[0].value: row[1] for row in rows}


class UserRepository(SQLAlchemyRepository):
    """Repositório especializado para utilizadores."""

    def get_by_username(self, username: str):
        from database.models import User
        return self._session.query(User).filter_by(username=username).first()

    def get_active_doctors(self):
        from database.models import User, UserRole, Doctor
        return (
            self._session.query(Doctor)
            .join(User, Doctor.user_id == User.id)
            .filter(User.is_active == True)
            .all()
        )


class TriageRepository(SQLAlchemyRepository):
    """Repositório especializado para triagens."""

    def get_by_patient(self, patient_id: int):
        from database.models import Triage
        return (
            self._session.query(Triage)
            .filter_by(patient_id=patient_id)
            .order_by(Triage.created_at.desc())
            .all()
        )

    def get_recent(self, limit: int = 20):
        from database.models import Triage
        return (
            self._session.query(Triage)
            .order_by(Triage.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_by_priority(self):
        from database.models import Triage
        from sqlalchemy import func
        rows = (
            self._session.query(Triage.priority, func.count(Triage.id))
            .group_by(Triage.priority)
            .all()
        )
        return {row[0].value: row[1] for row in rows}


class MedicalRecordRepository(SQLAlchemyRepository):
    """Repositório especializado para prontuários."""

    def get_by_patient(self, patient_id: int):
        from database.models import MedicalRecord
        return (
            self._session.query(MedicalRecord)
            .filter_by(patient_id=patient_id)
            .order_by(MedicalRecord.created_at.desc())
            .all()
        )
