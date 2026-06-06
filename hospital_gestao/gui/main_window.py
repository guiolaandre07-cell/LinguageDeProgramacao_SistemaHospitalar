"""
Janela Principal do Sistema de Gestão Hospitalar.
Implementa navegação lateral com CustomTkinter.
"""
import customtkinter as ctk
from tkinter import messagebox

from gui.dashboard_frame import DashboardFrame
from gui.patients_frame import PatientsFrame
from gui.appointments_frame import AppointmentsFrame
from gui.triage_frame import TriageFrame
from gui.records_frame import MedicalRecordsFrame
from gui.users_frame import UsersFrame


class MainWindow(ctk.CTk):
    """Janela principal com barra lateral e navegação entre módulos."""

    def __init__(self, services: dict, current_user: dict):
        super().__init__()
        self._services = services
        self._user = current_user

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"Hospital Kivi  —  {current_user['full_name']}  [{current_user['role'].upper()}]")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self._center_window(1280, 800)

        self._frames = {}
        self._active_btn = None
        self._build_ui()
        self._navigate("dashboard")

    def _center_window(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        self.configure(fg_color="#0d1117")

        # ── Sidebar ──
        self._sidebar = ctk.CTkFrame(
            self, width=220, fg_color="#161b22",
            corner_radius=0, border_width=1, border_color="#30363d"
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 8))
        ctk.CTkLabel(logo_frame, text="🏥", font=ctk.CTkFont(size=36)).pack()
        ctk.CTkLabel(
            logo_frame, text="Hospital Kivi",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#e6edf3"
        ).pack()
        ctk.CTkLabel(
            logo_frame, text="SGH Inteligente",
            font=ctk.CTkFont(size=10), text_color="#8b949e"
        ).pack()

        ctk.CTkFrame(self._sidebar, height=1, fg_color="#30363d").pack(fill="x", padx=12, pady=12)

        # Menus de navegação
        role = self._user.get("role", "")
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("👤", "Pacientes", "patients"),
            ("📅", "Consultas", "appointments"),
            ("🚨", "Triagem IA", "triage"),
            ("📋", "Prontuários", "records"),
        ]
        if role == "admin":
            nav_items.append(("⚙", "Utilizadores", "users"))

        self._nav_btns = {}
        for icon, label, key in nav_items:
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}",
                anchor="w", height=44,
                corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#21262d",
                text_color="#c9d1d9",
                command=lambda k=key: self._navigate(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = btn

        # Espaçador
        ctk.CTkFrame(self._sidebar, fg_color="transparent").pack(fill="y", expand=True)

        # Informação do utilizador + logout
        ctk.CTkFrame(self._sidebar, height=1, fg_color="#30363d").pack(fill="x", padx=12, pady=6)
        user_info = ctk.CTkFrame(self._sidebar, fg_color="#0d1117", corner_radius=8)
        user_info.pack(fill="x", padx=10, pady=(4, 4))
        ctk.CTkLabel(
            user_info, text=f"👤  {self._user['full_name'][:22]}",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#e6edf3", anchor="w"
        ).pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            user_info, text=self._user["role"].upper(),
            font=ctk.CTkFont(size=9), text_color="#3fb950", anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            self._sidebar, text="↩  Sair", height=38,
            fg_color="#21262d", hover_color="#da3633",
            font=ctk.CTkFont(size=12), text_color="#f85149",
            command=self._logout
        ).pack(fill="x", padx=10, pady=(0, 16))

        # ── Conteúdo principal ──
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(side="left", fill="both", expand=True)

    def _navigate(self, key: str):
        # Esconder todos
        for frame in self._frames.values():
            frame.pack_forget()

        # Highlight botão activo
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color="#21262d", text_color="#58a6ff")
            else:
                btn.configure(fg_color="transparent", text_color="#c9d1d9")

        # Criar frame se não existir
        if key not in self._frames:
            frame_class = {
                "dashboard": DashboardFrame,
                "patients": PatientsFrame,
                "appointments": AppointmentsFrame,
                "triage": TriageFrame,
                "records": MedicalRecordsFrame,
                "users": UsersFrame,
            }.get(key)
            if frame_class:
                frame = frame_class(self._content, self._services, self._user)
                self._frames[key] = frame

        if key in self._frames:
            self._frames[key].pack(fill="both", expand=True)
            # Actualizar dados ao navegar
            if hasattr(self._frames[key], "refresh"):
                self._frames[key].refresh()

    def _logout(self):
        if messagebox.askyesno("Sair", "Tem a certeza que deseja terminar a sessão?"):
            self._services["auth"].logout(self._user["id"])
            self.destroy()
