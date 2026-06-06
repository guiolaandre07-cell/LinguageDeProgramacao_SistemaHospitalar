"""
Ponto de entrada principal do Sistema de Gestão Hospitalar Kivi.
Inicializa a base de dados, o modelo de IA e lança a interface gráfica.
"""
import sys
import os
import logging

# Garante que o directório raiz do projecto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("HospitalSystem")


def main():
    """Função principal de arranque da aplicação."""
    print("=" * 60)
    print("        Sistema de Gestão Hospitalar Kivi")
    print("=" * 60)

    # 1. Inicializar base de dados
    print("\n[1/4] Inicializando base de dados...")
    try:
        from database.connection import init_db, get_session
        init_db()
        session = get_session()
        print("      ✅ Base de dados pronta.")
    except Exception as e:
        print(f"      ❌ Erro na base de dados: {e}")
        sys.exit(1)

    # 2. Carregar/treinar modelo de IA
    print("\n[2/4] Carregando modelo de Inteligência Artificial...")
    try:
        from ai.triage_model import TriageAIModel
        ai_model = TriageAIModel()
        metrics = ai_model.get_model_metrics()
        print(f"      ✅ Modelo pronto: {metrics.get('model_type', 'N/A')}")
        print(f"         Classes: {metrics.get('classes', [])}")
    except Exception as e:
        print(f"      ❌ Erro no modelo IA: {e}")
        sys.exit(1)

    # 3. Instanciar serviços de negócio
    print("\n[3/4] Inicializando serviços...")
    try:
        from services.patient_service import PatientService
        from services.hospital_services import (
            AuthService, AppointmentService, TriageService, MedicalRecordService
        )

        services = {
            "auth":        AuthService(session),
            "patient":     PatientService(session),
            "appointment": AppointmentService(session),
            "triage":      TriageService(session, ai_model),
            "record":      MedicalRecordService(session),
        }
        print("      ✅ Serviços prontos.")
    except Exception as e:
        print(f"      ❌ Erro nos serviços: {e}")
        sys.exit(1)

    # 4. Lançar interface gráfica
    print("\n[4/4] Lançando interface gráfica...")
    try:
        import customtkinter as ctk
        from gui.login_window import LoginWindow
        from gui.main_window import MainWindow

        def on_login_success(user: dict):
            """Callback executado após login bem-sucedido."""
            print(f"\n      👤 Sessão iniciada: {user['full_name']} [{user['role']}]")
            main_win = MainWindow(services, user)
            main_win.mainloop()

        login_win = LoginWindow(services["auth"], on_login_success)
        print("      ✅ Interface pronta.\n")
        login_win.mainloop()

    except ImportError as e:
        print(f"      ❌ Dependência em falta: {e}")
        print("         Execute: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"      ❌ Erro na interface: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[✅] Aplicação encerrada. Até logo!")


if __name__ == "__main__":
    main()
