"""
Modelos de base de dados com SQLAlchemy ORM.
Define todas as tabelas e relacionamentos do sistema hospitalar.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float,
    ForeignKey, Text, Boolean, Enum
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"


class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TriagePriority(enum.Enum):
    EMERGENCY = "Emergência"
    URGENT = "Urgente"
    LESS_URGENT = "Pouco Urgente"
    NON_URGENT = "Não Urgente"
    NORMAL = "Normal"


class Gender(enum.Enum):
    MALE = "Masculino"
    FEMALE = "Feminino"
    OTHER = "Outro"


# ─── Tabelas ────────────────────────────────────────────────────────────────

class User(Base):
    """Utilizadores do sistema (médicos, enfermeiros, recepcionistas, admins)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RECEPTIONIST)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
        }


class Specialty(Base):
    """Especialidades médicas."""
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    doctors = relationship("Doctor", back_populates="specialty")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class Doctor(Base):
    """Perfil de médico (extensão de User)."""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=True)
    crm = Column(String(20), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="doctor_profile")
    specialty = relationship("Specialty", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.user.full_name if self.user else "",
            "crm": self.crm,
            "specialty": self.specialty.name if self.specialty else "N/A",
            "phone": self.phone,
        }


class Patient(Base):
    """Pacientes cadastrados no hospital."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    bi = Column(String(20), unique=True, nullable=True)       # Bilhete de Identidade
    phone = Column(String(20), nullable=True)
    email = Column(String(120), nullable=True)
    address = Column(Text, nullable=True)
    blood_type = Column(String(5), nullable=True)
    allergies = Column(Text, nullable=True)
    emergency_contact = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    triages = relationship("Triage", back_populates="patient")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "birth_date": self.birth_date.strftime("%d/%m/%Y") if self.birth_date else "",
            "gender": self.gender.value if self.gender else "",
            "bi": self.bi,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "blood_type": self.blood_type,
            "allergies": self.allergies,
            "emergency_contact": self.emergency_contact,
        }


class Appointment(Base):
    """Consultas médicas agendadas."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    medical_record = relationship("MedicalRecord", back_populates="appointment", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.full_name if self.patient else "",
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.user.full_name if self.doctor and self.doctor.user else "",
            "scheduled_date": self.scheduled_date.strftime("%d/%m/%Y %H:%M") if self.scheduled_date else "",
            "status": self.status.value if self.status else "",
            "reason": self.reason,
            "notes": self.notes,
        }


class MedicalRecord(Base):
    """Prontuário médico do paciente por consulta."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    blood_pressure = Column(String(20), nullable=True)
    temperature = Column(Float, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="medical_records")
    appointment = relationship("Appointment", back_populates="medical_record")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "observations": self.observations,
            "weight": self.weight,
            "height": self.height,
            "blood_pressure": self.blood_pressure,
            "temperature": self.temperature,
            "heart_rate": self.heart_rate,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
        }


class Triage(Base):
    """Triagem de pacientes com resultado da IA."""
    __tablename__ = "triages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    symptoms = Column(Text, nullable=False)             # JSON serializado
    priority = Column(Enum(TriagePriority), nullable=False)
    ai_confidence = Column(Float, nullable=True)        # Confiança do modelo (0-1)
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    attended_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient", back_populates="triages")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.full_name if self.patient else "",
            "symptoms": self.symptoms,
            "priority": self.priority.value if self.priority else "",
            "ai_confidence": self.ai_confidence,
            "recommendation": self.recommendation,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
        }
