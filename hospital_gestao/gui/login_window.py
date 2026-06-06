"""
Janela de Login do Sistema Hospitalar.
Interface de autenticação com CustomTkinter.
"""
import customtkinter as ctk
from tkinter import messagebox
import threading


class LoginWindow(ctk.CTk):
    """Janela de autenticação."""

    def __init__(self, auth_service, on_success_callback):
        super().__init__()
        self._auth_service = auth_service
        self._on_success = on_success_callback

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Sistema de Gestão Hospitalar — Login")
        self.geometry("440x560")
        self.resizable(False, False)
        self._center_window(440, 560)

        self._build_ui()
        self.after(100, lambda: self._entry_username.focus())

    def _center_window(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Fundo principal
        self.configure(fg_color="#0d1117")

        # Card central
        card = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=16,
                             border_width=1, border_color="#30363d")
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

        # Ícone / Logo
        icon_lbl = ctk.CTkLabel(
            card, text="🏥", font=ctk.CTkFont(size=52),
            text_color="#58a6ff"
        )
        icon_lbl.pack(pady=(36, 6))

        title = ctk.CTkLabel(
            card, text="Hospital Kivi",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#e6edf3"
        )
        title.pack(pady=(0, 4))

        subtitle = ctk.CTkLabel(
            card, text="Sistema de Gestão Hospitalar Inteligente",
            font=ctk.CTkFont(size=11),
            text_color="#8b949e"
        )
        subtitle.pack(pady=(0, 28))

        # Separador
        ctk.CTkFrame(card, height=1, fg_color="#30363d").pack(
            fill="x", padx=20, pady=(0, 24)
        )

        # Campos
        ctk.CTkLabel(card, text="Utilizador", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#c9d1d9", anchor="w").pack(fill="x", padx=28)
        self._entry_username = ctk.CTkEntry(
            card, placeholder_text="ex: admin",
            height=42, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color="#0d1117", border_color="#30363d",
            text_color="#e6edf3"
        )
        self._entry_username.pack(fill="x", padx=28, pady=(4, 14))

        ctk.CTkLabel(card, text="Palavra-passe", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#c9d1d9", anchor="w").pack(fill="x", padx=28)
        self._entry_password = ctk.CTkEntry(
            card, placeholder_text="••••••••",
            height=42, corner_radius=8, show="•",
            font=ctk.CTkFont(size=13),
            fg_color="#0d1117", border_color="#30363d",
            text_color="#e6edf3"
        )
        self._entry_password.pack(fill="x", padx=28, pady=(4, 6))
        self._entry_password.bind("<Return>", lambda e: self._do_login())

        # Mensagem de erro
        self._lbl_error = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=11),
            text_color="#f85149"
        )
        self._lbl_error.pack(pady=(4, 0))

        # Botão de login
        self._btn_login = ctk.CTkButton(
            card, text="Entrar",
            height=44, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#238636", hover_color="#2ea043",
            command=self._do_login
        )
        self._btn_login.pack(fill="x", padx=28, pady=(14, 8))

        # Hint de credenciais
        ctk.CTkLabel(
            card,
            text="Demo — admin / admin123  |  dr.silva / med123  |  recepcao / rec123",
            font=ctk.CTkFont(size=10),
            text_color="#484f58"
        ).pack(pady=(8, 0))

    def _do_login(self):
        username = self._entry_username.get().strip()
        password = self._entry_password.get().strip()

        if not username or not password:
            self._show_error("Preencha todos os campos.")
            return

        self._btn_login.configure(state="disabled", text="A autenticar...")
        self._lbl_error.configure(text="")

        def _login_thread():
            try:
                user = self._auth_service.login(username, password)
                self.after(0, lambda: self._login_success(user))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
            finally:
                self.after(0, lambda: self._btn_login.configure(
                    state="normal", text="Entrar"
                ))

        threading.Thread(target=_login_thread, daemon=True).start()

    def _show_error(self, msg: str):
        self._lbl_error.configure(text=f"⚠  {msg}")

    def _login_success(self, user: dict):
        self.withdraw()
        self._on_success(user)
