"""
Frame de Gestão de Utilizadores (Admin).
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
from database.models import UserRole


class UsersFrame(ctk.CTkFrame):
    """Frame de gestão de utilizadores — acesso apenas para admin."""

    def __init__(self, parent, services: dict, current_user: dict):
        super().__init__(parent, fg_color="transparent")
        self._services = services
        self._user = current_user
        self._selected_id = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header, text="⚙  Gestão de Utilizadores",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e6edf3"
        ).pack(side="left")
        if self._user.get("role") == "admin":
            ctk.CTkButton(
                header, text="+ Novo Utilizador", width=150, height=34,
                fg_color="#238636", hover_color="#2ea043",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self._open_form
            ).pack(side="right")

        # Tabela
        table_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=8)

        style = ttk.Style()
        style.configure("Usr.Treeview", background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=30, font=("Helvetica", 11))
        style.configure("Usr.Treeview.Heading", background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 11, "bold"))
        style.map("Usr.Treeview", background=[("selected", "#1f6feb")])

        cols = ("id", "username", "nome", "email", "role", "ativo", "ultimo_login")
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                   style="Usr.Treeview", selectmode="browse")
        heads = ["ID", "Username", "Nome", "Email", "Papel", "Ativo", "Último Login"]
        widths = [40, 120, 180, 180, 110, 60, 140]
        for col, head, w in zip(cols, heads, widths):
            self._tree.heading(col, text=head)
            self._tree.column(col, width=w)
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Botão alterar palavra-passe
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=8)
        ctk.CTkButton(
            btn_frame, text="🔒  Alterar Minha Palavra-passe", width=220, height=34,
            fg_color="#1f6feb", hover_color="#388bfd",
            command=self._change_password
        ).pack(side="left")

    def _load(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        users = self._services["auth"].get_all_users()
        for u in users:
            self._tree.insert("", "end", iid=str(u.id), values=(
                u.id, u.username, u.full_name, u.email or "",
                u.role.value if u.role else "",
                "Sim" if u.is_active else "Não",
                u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else "—"
            ))

    def _open_form(self):
        UserFormDialog(self, self._services["auth"], on_save=self._load)

    def _change_password(self):
        ChangePasswordDialog(self, self._services["auth"], self._user["id"])

    def refresh(self):
        self._load()


class UserFormDialog(ctk.CTkToplevel):
    """Diálogo de criação de utilizador."""

    def __init__(self, parent, auth_service, on_save=None):
        super().__init__(parent)
        self._svc = auth_service
        self._on_save = on_save
        self.title("Novo Utilizador")
        self.geometry("440x480")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="#0d1117")
        ctk.CTkLabel(self, text="Novo Utilizador",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="#e6edf3").pack(pady=(20, 4))
        ctk.CTkFrame(self, height=1, fg_color="#30363d").pack(fill="x", padx=20, pady=(4, 16))

        def lbl(text):
            ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(fill="x", padx=24)

        def entry(ph="", show=None):
            kwargs = dict(placeholder_text=ph, height=38, font=ctk.CTkFont(size=13), corner_radius=8)
            if show:
                kwargs["show"] = show
            e = ctk.CTkEntry(self, **kwargs)
            e.pack(fill="x", padx=24, pady=(4, 10))
            return e

        lbl("Username *")
        self._e_user = entry("Nome de utilizador")
        lbl("Nome Completo *")
        self._e_name = entry("Nome completo")
        lbl("Email")
        self._e_email = entry("email@hospital.ao")
        lbl("Palavra-passe *")
        self._e_pw = entry("Mínimo 6 caracteres", show="•")
        lbl("Papel *")
        self._combo_role = ctk.CTkComboBox(
            self, values=[r.value for r in UserRole],
            height=38, font=ctk.CTkFont(size=13), corner_radius=8
        )
        self._combo_role.pack(fill="x", padx=24, pady=(4, 10))

        self._lbl_err = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="#f85149")
        self._lbl_err.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(4, 20))
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=38,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_row, text="Criar", width=110, height=38,
                       fg_color="#238636", hover_color="#2ea043",
                       command=self._save).pack(side="right")

    def _save(self):
        role_val = self._combo_role.get()
        role_enum = next((r for r in UserRole if r.value == role_val), UserRole.RECEPTIONIST)
        data = {
            "username": self._e_user.get().strip(),
            "full_name": self._e_name.get().strip(),
            "email": self._e_email.get().strip(),
            "password": self._e_pw.get().strip(),
            "role": role_enum,
        }
        if not data["username"] or not data["full_name"] or not data["password"]:
            self._lbl_err.configure(text="Preencha os campos obrigatórios.")
            return
        try:
            self._svc.create_user(data)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            self._lbl_err.configure(text=str(e))


class ChangePasswordDialog(ctk.CTkToplevel):
    """Diálogo de alteração de palavra-passe."""

    def __init__(self, parent, auth_service, user_id):
        super().__init__(parent)
        self._svc = auth_service
        self._uid = user_id
        self.title("Alterar Palavra-passe")
        self.geometry("380x320")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="#0d1117")
        ctk.CTkLabel(self, text="Alterar Palavra-passe",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#e6edf3").pack(pady=(20, 4))
        ctk.CTkFrame(self, height=1, fg_color="#30363d").pack(fill="x", padx=20, pady=(4, 16))

        def lbl(text):
            ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(fill="x", padx=24)

        lbl("Palavra-passe Actual")
        self._e_old = ctk.CTkEntry(self, show="•", height=38, font=ctk.CTkFont(size=13), corner_radius=8)
        self._e_old.pack(fill="x", padx=24, pady=(4, 10))
        lbl("Nova Palavra-passe")
        self._e_new = ctk.CTkEntry(self, show="•", height=38, font=ctk.CTkFont(size=13), corner_radius=8)
        self._e_new.pack(fill="x", padx=24, pady=(4, 10))
        lbl("Confirmar Nova Palavra-passe")
        self._e_conf = ctk.CTkEntry(self, show="•", height=38, font=ctk.CTkFont(size=13), corner_radius=8)
        self._e_conf.pack(fill="x", padx=24, pady=(4, 10))

        self._lbl_err = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="#f85149")
        self._lbl_err.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(4, 20))
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=38,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_row, text="Guardar", width=110, height=38,
                       fg_color="#238636", hover_color="#2ea043",
                       command=self._save).pack(side="right")

    def _save(self):
        old = self._e_old.get().strip()
        new = self._e_new.get().strip()
        conf = self._e_conf.get().strip()
        if new != conf:
            self._lbl_err.configure(text="As palavras-passe não coincidem.")
            return
        try:
            self._svc.change_password(self._uid, old, new)
            messagebox.showinfo("Sucesso", "Palavra-passe alterada com sucesso!")
            self.destroy()
        except Exception as e:
            self._lbl_err.configure(text=str(e))
