"""
Módulo de Inteligência Artificial - Triagem Automática de Pacientes.
Utiliza RandomForestClassifier (scikit-learn) para classificar a prioridade
de atendimento com base nos sintomas relatados.
"""
import os
import json
import pickle
import logging
import numpy as np
from typing import Dict, List, Tuple

from core.abstracts import ITriageService
from core.exceptions import AIModelError
from core.decorators import log_action, timer_context

logger = logging.getLogger("HospitalSystem.AI")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "triage_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "triage_scaler.pkl")

# ─── Mapeamento de features ────────────────────────────────────────────────
FEATURE_NAMES = [
    "fever",           # Febre (0=Não, 1=Baixa, 2=Alta)
    "pain_level",      # Nível de dor (0-10)
    "breathing_diff",  # Dificuldade respiratória (0=Não, 1=Leve, 2=Grave)
    "consciousness",   # Nível de consciência (0=Normal, 1=Confuso, 2=Inconsciente)
    "bleeding",        # Sangramento (0=Não, 1=Leve, 2=Grave)
    "vomiting",        # Vómitos (0=Não, 1=Sim)
    "chest_pain",      # Dor torácica (0=Não, 1=Sim)
    "heart_rate_abnormal",  # FC anormal (0=Normal, 1=Sim)
    "age_group",       # Faixa etária (0=Criança, 1=Adulto, 2=Idoso)
    "duration_hours",  # Duração dos sintomas em horas (0-72)
]

# Prioridades (labels)
PRIORITY_LABELS = [
    "Emergência",
    "Urgente",
    "Pouco Urgente",
    "Não Urgente",
    "Normal",
]

PRIORITY_COLORS = {
    "Emergência": "#FF0000",
    "Urgente": "#FF8C00",
    "Pouco Urgente": "#FFD700",
    "Não Urgente": "#32CD32",
    "Normal": "#1E90FF",
}

PRIORITY_RECOMMENDATIONS = {
    "Emergência": (
        "ATENDIMENTO IMEDIATO NECESSÁRIO!\n"
        "O paciente apresenta sinais de risco de vida. "
        "Encaminhar imediatamente para a sala de emergência. "
        "Acionar equipe médica de urgência."
    ),
    "Urgente": (
        "Atendimento prioritário em até 15 minutos.\n"
        "Monitorar sinais vitais continuamente. "
        "Preparar acesso venoso se necessário."
    ),
    "Pouco Urgente": (
        "Atendimento em até 30-60 minutos.\n"
        "Monitorar evolução dos sintomas. "
        "Encaminhar para consulta médica."
    ),
    "Não Urgente": (
        "Atendimento em até 2 horas.\n"
        "Orientar o paciente a aguardar. "
        "Pode ser direcionado para consulta ambulatorial."
    ),
    "Normal": (
        "Atendimento de rotina.\n"
        "Agendar consulta regular. "
        "Sem necessidade de atendimento de urgência."
    ),
}


class TriageAIModel(ITriageService):
    """
    Serviço de triagem automática baseado em Machine Learning.
    Treina ou carrega um modelo RandomForest para classificar prioridades.
    """

    def __init__(self):
        self._model = None
        self._scaler = None
        self._is_trained = False
        self._load_or_train()

    def _load_or_train(self):
        """Carrega modelo existente ou treina um novo."""
        with timer_context("Carregamento/Treino do Modelo de IA"):
            if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
                try:
                    self._load_model()
                    logger.info("Modelo de triagem carregado do ficheiro.")
                    return
                except Exception as e:
                    logger.warning(f"Falha ao carregar modelo: {e}. Retreinando...")
            self._train_model()

    def _load_model(self):
        """Carrega o modelo e scaler serializados."""
        with open(MODEL_PATH, "rb") as f:
            self._model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            self._scaler = pickle.load(f)
        self._is_trained = True

    def _save_model(self):
        """Persiste o modelo e scaler em disco."""
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self._model, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self._scaler, f)
        logger.info("Modelo de triagem guardado em disco.")

    def _generate_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Gera dados sintéticos de treino com base em regras clínicas.
        Retorna (X, y) onde y são os índices das prioridades.
        """
        np.random.seed(42)
        X, y = [], []
        n_per_class = 300

        # Classe 0 - Emergência
        for _ in range(n_per_class):
            X.append([
                np.random.choice([1, 2], p=[0.3, 0.7]),   # febre alta
                np.random.randint(7, 11),                   # dor intensa
                np.random.choice([1, 2], p=[0.3, 0.7]),   # respiração
                np.random.choice([1, 2], p=[0.5, 0.5]),   # consciência
                np.random.choice([0, 1, 2], p=[0.2, 0.3, 0.5]),
                np.random.choice([0, 1], p=[0.4, 0.6]),
                np.random.choice([0, 1], p=[0.3, 0.7]),   # dor peito
                1,
                np.random.randint(0, 3),
                np.random.randint(0, 6),
            ])
            y.append(0)

        # Classe 1 - Urgente
        for _ in range(n_per_class):
            X.append([
                np.random.choice([0, 1, 2], p=[0.2, 0.5, 0.3]),
                np.random.randint(5, 9),
                np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2]),
                np.random.choice([0, 1], p=[0.7, 0.3]),
                np.random.choice([0, 1], p=[0.5, 0.5]),
                np.random.choice([0, 1], p=[0.5, 0.5]),
                np.random.choice([0, 1], p=[0.5, 0.5]),
                np.random.choice([0, 1], p=[0.4, 0.6]),
                np.random.randint(0, 3),
                np.random.randint(4, 24),
            ])
            y.append(1)

        # Classe 2 - Pouco Urgente
        for _ in range(n_per_class):
            X.append([
                np.random.choice([0, 1], p=[0.5, 0.5]),
                np.random.randint(3, 7),
                np.random.choice([0, 1], p=[0.7, 0.3]),
                0,
                np.random.choice([0, 1], p=[0.8, 0.2]),
                np.random.choice([0, 1], p=[0.6, 0.4]),
                0,
                np.random.choice([0, 1], p=[0.7, 0.3]),
                np.random.randint(0, 3),
                np.random.randint(12, 48),
            ])
            y.append(2)

        # Classe 3 - Não Urgente
        for _ in range(n_per_class):
            X.append([
                np.random.choice([0, 1], p=[0.8, 0.2]),
                np.random.randint(1, 5),
                0,
                0,
                0,
                np.random.choice([0, 1], p=[0.8, 0.2]),
                0,
                0,
                np.random.randint(0, 3),
                np.random.randint(24, 72),
            ])
            y.append(3)

        # Classe 4 - Normal
        for _ in range(n_per_class):
            X.append([
                0,
                np.random.randint(0, 3),
                0,
                0,
                0,
                0,
                0,
                0,
                np.random.randint(0, 3),
                np.random.randint(48, 73),
            ])
            y.append(4)

        return np.array(X, dtype=float), np.array(y)

    def _train_model(self):
        """Treina o modelo de classificação RandomForest."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report

            logger.info("Treinando modelo de triagem com RandomForestClassifier...")
            X, y = self._generate_training_data()

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            self._scaler = StandardScaler()
            X_train_scaled = self._scaler.fit_transform(X_train)
            X_test_scaled = self._scaler.transform(X_test)

            self._model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight="balanced",
            )
            self._model.fit(X_train_scaled, y_train)

            y_pred = self._model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"Modelo treinado. Acurácia: {accuracy:.4f}")
            logger.info(
                f"\n{classification_report(y_test, y_pred, target_names=PRIORITY_LABELS)}"
            )

            self._is_trained = True
            self._save_model()

        except ImportError:
            raise AIModelError(
                "scikit-learn não está instalado. Execute: pip install scikit-learn"
            )
        except Exception as e:
            raise AIModelError(f"Erro ao treinar modelo: {e}")

    @log_action("AI.predict_priority")
    def predict_priority(self, symptoms: dict) -> dict:
        """
        Prevê a prioridade de triagem.
        Args:
            symptoms: dicionário com as features do paciente.
        Returns:
            dict com priority, confidence, all_probabilities.
        """
        if not self._is_trained:
            raise AIModelError("Modelo não está treinado.")

        try:
            features = self._extract_features(symptoms)
            features_scaled = self._scaler.transform([features])
            prediction = self._model.predict(features_scaled)[0]
            probabilities = self._model.predict_proba(features_scaled)[0]
            confidence = float(probabilities[prediction])
            priority_label = PRIORITY_LABELS[prediction]

            all_probs = {
                PRIORITY_LABELS[i]: float(probabilities[i])
                for i in range(len(PRIORITY_LABELS))
            }

            return {
                "priority": priority_label,
                "confidence": confidence,
                "probabilities": all_probs,
                "color": PRIORITY_COLORS[priority_label],
            }
        except Exception as e:
            raise AIModelError(f"Erro na predição: {e}")

    def _extract_features(self, symptoms: dict) -> List[float]:
        """Converte o dicionário de sintomas para vector de features."""
        return [
            float(symptoms.get("fever", 0)),
            float(symptoms.get("pain_level", 0)),
            float(symptoms.get("breathing_diff", 0)),
            float(symptoms.get("consciousness", 0)),
            float(symptoms.get("bleeding", 0)),
            float(symptoms.get("vomiting", 0)),
            float(symptoms.get("chest_pain", 0)),
            float(symptoms.get("heart_rate_abnormal", 0)),
            float(symptoms.get("age_group", 1)),
            float(symptoms.get("duration_hours", 24)),
        ]

    def get_recommendation(self, priority: str) -> str:
        """Retorna recomendação clínica para a prioridade dada."""
        return PRIORITY_RECOMMENDATIONS.get(priority, "Sem recomendação disponível.")

    def get_feature_importance(self) -> Dict[str, float]:
        """Retorna a importância de cada feature para interpretabilidade."""
        if not self._is_trained:
            return {}
        importances = self._model.feature_importances_
        return {
            FEATURE_NAMES[i]: float(importances[i])
            for i in range(len(FEATURE_NAMES))
        }

    def get_model_metrics(self) -> dict:
        """Retorna métricas resumidas do modelo."""
        if not self._is_trained:
            return {}
        from sklearn.ensemble import RandomForestClassifier
        return {
            "model_type": "RandomForestClassifier",
            "n_estimators": self._model.n_estimators,
            "n_features": len(FEATURE_NAMES),
            "n_classes": len(PRIORITY_LABELS),
            "classes": PRIORITY_LABELS,
        }
