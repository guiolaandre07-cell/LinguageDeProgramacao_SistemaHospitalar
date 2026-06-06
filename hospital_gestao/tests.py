"""
Testes Unitários e de Integração — Sistema de Gestão Hospitalar Kivi.
Execute com: python -m pytest tests.py -v
"""
import sys
import os
import unittest
from datetime import date, datetime

# Adicionar raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ─── Fixtures ────────────────────────────────────────────────────────────────
def get_test_session():
    """Cria uma sessão de base de dados em memória para testes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ─── Testes de Excepções ─────────────────────────────────────────────────────
class TestExceptions(unittest.TestCase):

    def test_hospital_system_error(self):
        from core.exceptions import HospitalSystemError
        e = HospitalSystemError("Erro teste", "ERR_001")
        self.assertIn("ERR_001", str(e))
        self.assertIn("Erro teste", str(e))

    def test_validation_error_has_field(self):
        from core.exceptions import ValidationError
        e = ValidationError("Campo inválido", field="full_name")
        self.assertEqual(e.field, "full_name")

    def test_patient_not_found(self):
        from core.exceptions import PatientNotFoundError
        e = PatientNotFoundError(42)
        self.assertIn("42", str(e))

    def test_auth_error(self):
        from core.exceptions import AuthenticationError
        with self.assertRaises(Exception):
            raise AuthenticationError()


# ─── Testes de Decoradores ───────────────────────────────────────────────────
class TestDecorators(unittest.TestCase):

    def test_validate_required_passes(self):
        from core.decorators import validate_required

        class Svc:
            @validate_required("name", "age")
            def create(self, data):
                return True

        svc = Svc()
        result = svc.create({"name": "João", "age": 30})
        self.assertTrue(result)

    def test_validate_required_raises(self):
        from core.decorators import validate_required
        from core.exceptions import ValidationError

        class Svc:
            @validate_required("name")
            def create(self, data):
                return True

        svc = Svc()
        with self.assertRaises(ValidationError):
            svc.create({"name": ""})

    def test_log_action_runs(self):
        from core.decorators import log_action

        @log_action("TestAction")
        def dummy(x):
            return x * 2

        self.assertEqual(dummy(5), 10)

    def test_timer_context(self):
        from core.decorators import timer_context
        import time
        with timer_context("TestTimer"):
            time.sleep(0.01)  # deve completar sem erro


# ─── Testes de Repositório ───────────────────────────────────────────────────
class TestPatientRepository(unittest.TestCase):

    def setUp(self):
        self.session = get_test_session()
        from database.models import Patient, Gender
        from database.repositories import PatientRepository
        self.repo = PatientRepository(self.session, Patient)
        self.Gender = Gender

    def _make_patient(self, name="Maria Silva", bi=None):
        from database.models import Patient, Gender
        return Patient(
            full_name=name,
            birth_date=date(1990, 5, 15),
            gender=Gender.FEMALE,
            bi=bi,
            phone="+244 912 000 001",
        )

    def test_create_patient(self):
        p = self._make_patient()
        saved = self.repo.create(p)
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.full_name, "Maria Silva")

    def test_get_by_id(self):
        p = self._make_patient()
        saved = self.repo.create(p)
        fetched = self.repo.get_by_id(saved.id)
        self.assertEqual(fetched.full_name, "Maria Silva")

    def test_get_by_id_not_found(self):
        result = self.repo.get_by_id(9999)
        self.assertIsNone(result)

    def test_get_all(self):
        self.repo.create(self._make_patient("Ana"))
        self.repo.create(self._make_patient("João"))
        all_patients = self.repo.get_all()
        self.assertGreaterEqual(len(all_patients), 2)

    def test_update_patient(self):
        p = self._make_patient()
        saved = self.repo.create(p)
        saved.phone = "+244 999 999 999"
        updated = self.repo.update(saved)
        self.assertEqual(updated.phone, "+244 999 999 999")

    def test_delete_patient(self):
        p = self._make_patient()
        saved = self.repo.create(p)
        pid = saved.id
        result = self.repo.delete(pid)
        self.assertTrue(result)
        self.assertIsNone(self.repo.get_by_id(pid))

    def test_search_by_name(self):
        self.repo.create(self._make_patient("Carlos Gomes"))
        results = self.repo.search("Carlos")
        self.assertTrue(any("Carlos" in p.full_name for p in results))


# ─── Testes de Serviço de Pacientes ─────────────────────────────────────────
class TestPatientService(unittest.TestCase):

    def setUp(self):
        self.session = get_test_session()
        from services.patient_service import PatientService
        self.svc = PatientService(self.session)

    def _base_data(self, name="Test Patient", bi=None):
        return {
            "full_name": name,
            "birth_date": "1985-03-20",
            "gender": "Masculino",
            "bi": bi,
            "phone": "+244 900 000 000",
        }

    def test_register_patient_success(self):
        p = self.svc.register_patient(self._base_data())
        self.assertIsNotNone(p.id)

    def test_register_patient_missing_name(self):
        from core.exceptions import ValidationError
        data = self._base_data()
        data["full_name"] = ""
        with self.assertRaises(ValidationError):
            self.svc.register_patient(data)

    def test_register_duplicate_bi(self):
        from core.exceptions import DuplicateRecordError
        self.svc.register_patient(self._base_data(bi="BI-TEST-001"))
        with self.assertRaises(DuplicateRecordError):
            self.svc.register_patient(self._base_data("Outro", bi="BI-TEST-001"))

    def test_get_patient_not_found(self):
        from core.exceptions import PatientNotFoundError
        with self.assertRaises(PatientNotFoundError):
            self.svc.get_patient(99999)

    def test_update_patient(self):
        p = self.svc.register_patient(self._base_data())
        updated = self.svc.update_patient(p.id, {"phone": "+244 111 111 111"})
        self.assertEqual(updated.phone, "+244 111 111 111")

    def test_delete_patient(self):
        p = self.svc.register_patient(self._base_data())
        result = self.svc.delete_patient(p.id)
        self.assertTrue(result)

    def test_calculate_age(self):
        birth = date(2000, 1, 1)
        age = self.svc.calculate_age(birth)
        self.assertGreaterEqual(age, 25)


# ─── Testes de Autenticação ──────────────────────────────────────────────────
class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.session = get_test_session()
        # Seed: criar admin
        import hashlib
        from database.models import User, UserRole
        pw = hashlib.sha256(b"secret123").hexdigest()
        admin = User(
            username="testadmin",
            password_hash=pw,
            full_name="Admin Teste",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.session.add(admin)
        self.session.commit()
        from services.hospital_services import AuthService
        self.svc = AuthService(self.session)

    def test_login_success(self):
        user = self.svc.login("testadmin", "secret123")
        self.assertEqual(user["username"], "testadmin")

    def test_login_wrong_password(self):
        from core.exceptions import AuthenticationError
        with self.assertRaises(AuthenticationError):
            self.svc.login("testadmin", "wrongpass")

    def test_login_unknown_user(self):
        from core.exceptions import AuthenticationError
        with self.assertRaises(AuthenticationError):
            self.svc.login("nonexistent", "pass")

    def test_change_password(self):
        result = self.svc.change_password(1, "secret123", "newpass456")
        self.assertTrue(result)
        user = self.svc.login("testadmin", "newpass456")
        self.assertIsNotNone(user)

    def test_change_password_wrong_old(self):
        from core.exceptions import AuthenticationError
        with self.assertRaises(AuthenticationError):
            self.svc.change_password(1, "wrongold", "newpass")


# ─── Testes do Modelo IA ─────────────────────────────────────────────────────
class TestTriageAIModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Treina o modelo uma vez para todos os testes desta classe."""
        # Remove modelo existente para forçar treino limpo
        import os
        for f in ["ai/triage_model.pkl", "ai/triage_scaler.pkl"]:
            if os.path.exists(f):
                os.remove(f)
        from ai.triage_model import TriageAIModel, PRIORITY_LABELS
        cls.model = TriageAIModel()
        cls.PRIORITY_LABELS = PRIORITY_LABELS

    def test_model_is_trained(self):
        self.assertTrue(self.model._is_trained)

    def test_predict_returns_priority(self):
        symptoms = {
            "fever": 2, "pain_level": 9, "breathing_diff": 2,
            "consciousness": 1, "bleeding": 2, "vomiting": 1,
            "chest_pain": 1, "heart_rate_abnormal": 1,
            "age_group": 2, "duration_hours": 2,
        }
        result = self.model.predict_priority(symptoms)
        self.assertIn("priority", result)
        self.assertIn(result["priority"], self.PRIORITY_LABELS)

    def test_predict_confidence_between_0_and_1(self):
        symptoms = {k: 0 for k in [
            "fever","pain_level","breathing_diff","consciousness",
            "bleeding","vomiting","chest_pain","heart_rate_abnormal",
            "age_group","duration_hours"
        ]}
        result = self.model.predict_priority(symptoms)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_emergency_scenario(self):
        """Sintomas graves devem resultar em Emergência ou Urgente."""
        symptoms = {
            "fever": 2, "pain_level": 10, "breathing_diff": 2,
            "consciousness": 2, "bleeding": 2, "vomiting": 1,
            "chest_pain": 1, "heart_rate_abnormal": 1,
            "age_group": 2, "duration_hours": 1,
        }
        result = self.model.predict_priority(symptoms)
        self.assertIn(result["priority"], ["Emergência", "Urgente"])

    def test_normal_scenario(self):
        """Sintomas mínimos devem resultar em Normal ou Não Urgente."""
        symptoms = {
            "fever": 0, "pain_level": 1, "breathing_diff": 0,
            "consciousness": 0, "bleeding": 0, "vomiting": 0,
            "chest_pain": 0, "heart_rate_abnormal": 0,
            "age_group": 1, "duration_hours": 60,
        }
        result = self.model.predict_priority(symptoms)
        self.assertIn(result["priority"], ["Normal", "Não Urgente", "Pouco Urgente"])

    def test_get_recommendation(self):
        rec = self.model.get_recommendation("Emergência")
        self.assertIn("IMEDIATO", rec)

    def test_feature_importance_has_all_features(self):
        from ai.triage_model import FEATURE_NAMES
        importance = self.model.get_feature_importance()
        for feat in FEATURE_NAMES:
            self.assertIn(feat, importance)

    def test_model_metrics(self):
        metrics = self.model.get_model_metrics()
        self.assertEqual(metrics["model_type"], "RandomForestClassifier")
        self.assertEqual(metrics["n_features"], 10)
        self.assertEqual(metrics["n_classes"], 5)


# ─── Execução ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ordenar suites da mais simples para a mais complexa
    for test_class in [
        TestExceptions,
        TestDecorators,
        TestPatientRepository,
        TestPatientService,
        TestAuthService,
        TestTriageAIModel,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
