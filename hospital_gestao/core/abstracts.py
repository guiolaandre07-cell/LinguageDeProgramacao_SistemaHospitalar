"""
Classes Abstratas e Interfaces do Sistema Hospitalar.
Define os contratos de serviço obrigatórios (POO Avançada).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any


class BaseEntity(ABC):
    """Entidade base para todos os modelos do domínio."""

    @abstractmethod
    def to_dict(self) -> dict:
        """Serializa a entidade para dicionário."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Valida os dados da entidade."""
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.to_dict()}>"


class IRepository(ABC):
    """Interface genérica de repositório (padrão DAO)."""

    @abstractmethod
    def create(self, entity) -> Any:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    def update(self, entity) -> Any:
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        pass


class IPatientService(ABC):
    """Interface de serviço para gestão de pacientes."""

    @abstractmethod
    def register_patient(self, data: dict) -> Any:
        pass

    @abstractmethod
    def get_patient(self, patient_id: int) -> Any:
        pass

    @abstractmethod
    def search_patients(self, query: str) -> List[Any]:
        pass

    @abstractmethod
    def update_patient(self, patient_id: int, data: dict) -> Any:
        pass

    @abstractmethod
    def delete_patient(self, patient_id: int) -> bool:
        pass


class IAppointmentService(ABC):
    """Interface de serviço para gestão de consultas."""

    @abstractmethod
    def schedule_appointment(self, data: dict) -> Any:
        pass

    @abstractmethod
    def cancel_appointment(self, appointment_id: int) -> bool:
        pass

    @abstractmethod
    def get_appointments_by_patient(self, patient_id: int) -> List[Any]:
        pass

    @abstractmethod
    def get_appointments_by_doctor(self, doctor_id: int) -> List[Any]:
        pass


class ITriageService(ABC):
    """Interface de serviço de triagem com IA."""

    @abstractmethod
    def predict_priority(self, symptoms: dict) -> dict:
        """Prevê a prioridade de triagem com base nos sintomas."""
        pass

    @abstractmethod
    def get_recommendation(self, priority: str) -> str:
        """Retorna recomendação clínica com base na prioridade."""
        pass


class IAuthService(ABC):
    """Interface de serviço de autenticação."""

    @abstractmethod
    def login(self, username: str, password: str) -> Optional[Any]:
        pass

    @abstractmethod
    def logout(self, user_id: int) -> None:
        pass

    @abstractmethod
    def change_password(self, user_id: int, old_pw: str, new_pw: str) -> bool:
        pass
