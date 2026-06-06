"""
Exceções personalizadas do Sistema de Gestão Hospitalar.
Define a hierarquia de erros do domínio da aplicação.
"""


class HospitalSystemError(Exception):
    """Exceção base para todos os erros do sistema hospitalar."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class AuthenticationError(HospitalSystemError):
    """Levantada quando a autenticação falha."""

    def __init__(self, message: str = "Credenciais inválidas."):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(HospitalSystemError):
    """Levantada quando o utilizador não tem permissões necessárias."""

    def __init__(self, message: str = "Acesso não autorizado."):
        super().__init__(message, "AUTHZ_ERROR")


class ValidationError(HospitalSystemError):
    """Levantada quando a validação de dados falha."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class PatientNotFoundError(HospitalSystemError):
    """Levantada quando um paciente não é encontrado."""

    def __init__(self, patient_id=None):
        msg = (
            f"Paciente com ID {patient_id} não encontrado."
            if patient_id
            else "Paciente não encontrado."
        )
        super().__init__(msg, "PATIENT_NOT_FOUND")


class DoctorNotFoundError(HospitalSystemError):
    """Levantada quando um médico não é encontrado."""

    def __init__(self, doctor_id=None):
        msg = (
            f"Médico com ID {doctor_id} não encontrado."
            if doctor_id
            else "Médico não encontrado."
        )
        super().__init__(msg, "DOCTOR_NOT_FOUND")


class AppointmentNotFoundError(HospitalSystemError):
    """Levantada quando uma consulta não é encontrada."""

    def __init__(self, appointment_id=None):
        msg = (
            f"Consulta com ID {appointment_id} não encontrada."
            if appointment_id
            else "Consulta não encontrada."
        )
        super().__init__(msg, "APPOINTMENT_NOT_FOUND")


class DuplicateRecordError(HospitalSystemError):
    """Levantada ao tentar criar um registo duplicado."""

    def __init__(self, message: str = "Registo duplicado."):
        super().__init__(message, "DUPLICATE_RECORD")


class DatabaseError(HospitalSystemError):
    """Levantada quando uma operação de base de dados falha."""

    def __init__(self, message: str = "Erro na operação da base de dados."):
        super().__init__(message, "DB_ERROR")


class AIModelError(HospitalSystemError):
    """Levantada quando uma operação do modelo de IA falha."""

    def __init__(self, message: str = "Erro no modelo de IA."):
        super().__init__(message, "AI_ERROR")


class RecordNotFoundError(HospitalSystemError):
    """Levantada quando um prontuário não é encontrado."""

    def __init__(self, record_id=None):
        msg = (
            f"Prontuário com ID {record_id} não encontrado."
            if record_id
            else "Prontuário não encontrado."
        )
        super().__init__(msg, "RECORD_NOT_FOUND")
