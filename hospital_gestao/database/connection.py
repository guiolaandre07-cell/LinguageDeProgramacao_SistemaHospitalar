"""
Configuração e gestão da conexão com a base de dados SQLite via SQLAlchemy.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
import logging

logger = logging.getLogger("HospitalSystem.Database")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hospital.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

# Activa chaves estrangeiras no SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Cria todas as tabelas e insere dados iniciais."""
    Base.metadata.create_all(bind=engine)
    logger.info("Base de dados inicializada com sucesso.")
    _seed_initial_data()


def get_session() -> Session:
    """Retorna uma sessão de base de dados."""
    return SessionLocal()


def _seed_initial_data():
    """Insere dados iniciais (admin, especialidades) se ainda não existirem."""
    from database.models import User, UserRole, Specialty, Doctor
    import hashlib

    session = SessionLocal()
    try:
        # Admin padrão
        if not session.query(User).filter_by(username="admin").first():
            admin = User(
                username="admin",
                password_hash=_hash_password("admin123"),
                full_name="Administrador do Sistema",
                email="admin@hospital.ao",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)
            logger.info("Utilizador admin criado.")

        # Utilizador médico de demonstração
        if not session.query(User).filter_by(username="dr.silva").first():
            doctor_user = User(
                username="dr.silva",
                password_hash=_hash_password("med123"),
                full_name="Dr. António Silva",
                email="antonio.silva@hospital.ao",
                role=UserRole.DOCTOR,
                is_active=True,
            )
            session.add(doctor_user)
            session.flush()

            # Especialidades
            specs = [
                "Clínica Geral", "Cardiologia", "Pediatria",
                "Ortopedia", "Neurologia", "Ginecologia",
                "Dermatologia", "Urgência",
            ]
            spec_objs = {}
            for s in specs:
                existing = session.query(Specialty).filter_by(name=s).first()
                if not existing:
                    sp = Specialty(name=s)
                    session.add(sp)
                    session.flush()
                    spec_objs[s] = sp
                else:
                    spec_objs[s] = existing

            geral = spec_objs.get("Clínica Geral") or session.query(Specialty).filter_by(name="Clínica Geral").first()

            if not session.query(Doctor).filter_by(crm="AO-001234").first():
                doc = Doctor(
                    user_id=doctor_user.id,
                    specialty_id=geral.id if geral else None,
                    crm="AO-001234",
                    phone="+244 912 345 678",
                )
                session.add(doc)

        # Utilizador recepcionista de demonstração
        if not session.query(User).filter_by(username="recepcao").first():
            rec = User(
                username="recepcao",
                password_hash=_hash_password("rec123"),
                full_name="Maria Fernanda",
                email="recepcao@hospital.ao",
                role=UserRole.RECEPTIONIST,
                is_active=True,
            )
            session.add(rec)

        session.commit()
        logger.info("Dados iniciais inseridos com sucesso.")
    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao inserir dados iniciais: {e}")
    finally:
        session.close()


def _hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
