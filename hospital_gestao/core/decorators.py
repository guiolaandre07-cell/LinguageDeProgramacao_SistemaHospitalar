"""
Decoradores e Context Managers personalizados.
Implementa padrões de logging, validação e gestão de transações.
"""
import logging
import functools
import time
from contextlib import contextmanager
from typing import Callable, Any

from core.exceptions import ValidationError, DatabaseError

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("hospital_system.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("HospitalSystem")


def log_action(action_name: str = None):
    """
    Decorador: regista chamadas de funções com nome, args e tempo de execução.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = action_name or func.__name__
            start = time.time()
            logger.info(f"INÍCIO: {name}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"FIM: {name} | Tempo: {elapsed:.3f}s")
                return result
            except Exception as e:
                logger.error(f"ERRO em {name}: {e}")
                raise
        return wrapper
    return decorator


def validate_required(*fields):
    """
    Decorador: valida que os campos obrigatórios estão presentes no 1º argumento dict.
    Espera que o 1º argumento posicional após self seja um dict 'data'.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Procura o argumento 'data' (2º arg após self)
            data = None
            if len(args) > 1 and isinstance(args[1], dict):
                data = args[1]
            elif "data" in kwargs and isinstance(kwargs["data"], dict):
                data = kwargs["data"]

            if data is not None:
                for field in fields:
                    if field not in data or data[field] in (None, "", []):
                        raise ValidationError(
                            f"O campo '{field}' é obrigatório.", field=field
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles):
    """
    Decorador: verifica se o utilizador atual tem um dos papéis exigidos.
    O objeto self deve ter um atributo 'current_user'.
    """
    from core.exceptions import AuthorizationError

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            user = getattr(self, "current_user", None)
            if user is None or user.get("role") not in roles:
                raise AuthorizationError(
                    f"Acesso negado. Papel necessário: {', '.join(roles)}"
                )
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 0.5):
    """
    Decorador: tenta executar a função até max_attempts vezes em caso de exceção.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except DatabaseError as e:
                    last_error = e
                    logger.warning(
                        f"Tentativa {attempt}/{max_attempts} falhou: {e}"
                    )
                    time.sleep(delay)
            raise DatabaseError(
                f"Operação falhou após {max_attempts} tentativas: {last_error}"
            )
        return wrapper
    return decorator


@contextmanager
def database_transaction(session):
    """
    Context Manager: garante commit ou rollback automático de transações SQLAlchemy.
    Uso:
        with database_transaction(session):
            session.add(obj)
    """
    try:
        yield session
        session.commit()
        logger.debug("Transação confirmada (commit).")
    except Exception as e:
        session.rollback()
        logger.error(f"Transação revertida (rollback): {e}")
        raise DatabaseError(f"Erro na transação: {e}")


@contextmanager
def timer_context(label: str = "Operação"):
    """
    Context Manager: mede e loga o tempo de execução de um bloco.
    Uso:
        with timer_context("Carregar dados"):
            ...
    """
    start = time.time()
    logger.info(f"[TIMER] Início: {label}")
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.info(f"[TIMER] Fim: {label} | {elapsed:.3f}s")
