-- ============================================================
--  Sistema de Gestão Hospitalar Kivi — Script SQL (SQLite)
--  Gerado automaticamente pelo SQLAlchemy ORM
--  Uso: referência / importação manual
-- ============================================================

PRAGMA foreign_keys = ON;

-- Utilizadores do sistema
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name     VARCHAR(120) NOT NULL,
    email         VARCHAR(120) UNIQUE,
    role          VARCHAR(20)  NOT NULL DEFAULT 'receptionist',
    is_active     BOOLEAN      DEFAULT 1,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    last_login    DATETIME
);

-- Especialidades médicas
CREATE TABLE IF NOT EXISTS specialties (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Perfil de médico (extensão de users)
CREATE TABLE IF NOT EXISTS doctors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER UNIQUE NOT NULL REFERENCES users(id),
    specialty_id INTEGER REFERENCES specialties(id),
    crm          VARCHAR(20) UNIQUE NOT NULL,
    phone        VARCHAR(20)
);

-- Pacientes
CREATE TABLE IF NOT EXISTS patients (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name         VARCHAR(150) NOT NULL,
    birth_date        DATE         NOT NULL,
    gender            VARCHAR(15)  NOT NULL,
    bi                VARCHAR(20)  UNIQUE,
    phone             VARCHAR(20),
    email             VARCHAR(120),
    address           TEXT,
    blood_type        VARCHAR(5),
    allergies         TEXT,
    emergency_contact VARCHAR(120),
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Consultas
CREATE TABLE IF NOT EXISTS appointments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(id),
    doctor_id      INTEGER NOT NULL REFERENCES doctors(id),
    scheduled_date DATETIME NOT NULL,
    status         VARCHAR(20) DEFAULT 'scheduled',
    reason         TEXT,
    notes          TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Prontuários médicos
CREATE TABLE IF NOT EXISTS medical_records (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(id),
    appointment_id INTEGER REFERENCES appointments(id),
    diagnosis      TEXT,
    prescription   TEXT,
    observations   TEXT,
    weight         REAL,
    height         REAL,
    blood_pressure VARCHAR(20),
    temperature    REAL,
    heart_rate     INTEGER,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Triagens (resultado da IA)
CREATE TABLE IF NOT EXISTS triages (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(id),
    symptoms       TEXT    NOT NULL,
    priority       VARCHAR(20) NOT NULL,
    ai_confidence  REAL,
    recommendation TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    attended_by    INTEGER REFERENCES users(id)
);

-- ─── Índices para optimização de consultas ─────────────────
CREATE INDEX IF NOT EXISTS idx_patients_name    ON patients(full_name);
CREATE INDEX IF NOT EXISTS idx_patients_bi      ON patients(bi);
CREATE INDEX IF NOT EXISTS idx_appts_patient    ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appts_doctor     ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appts_date       ON appointments(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_triages_patient  ON triages(patient_id);
CREATE INDEX IF NOT EXISTS idx_triages_priority ON triages(priority);
CREATE INDEX IF NOT EXISTS idx_records_patient  ON medical_records(patient_id);
