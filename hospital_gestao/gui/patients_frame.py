"""
Frame de Gestão de Pacientes.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime


class PatientsFrame(ctk.CTkFrame):
    """Frame CRUD de pacientes."""

    def __init__(self, parent, services: dict, current_user: dict):
        super().__init__(parent, fg_color="transparent")
        self._services = services
        self._user = current_user
        self._selected_patient = None
        self._build_ui()
        self._load_patients()

    def _build_ui(self):
        # ── Cabeçalho ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header, text="👤  Gestão de Pacientes",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e6edf3"
        ).pack(side="left")
        ctk.CTkButton(
            header, text="+ Novo Paciente", width=140, height=34,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_form
        ).pack(side="right")

        # ── Barra de pesquisa ──
        search_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=8)
        search_frame.pack(fill="x", padx=20, pady=4)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._search())
        ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            placeholder_text="🔍  Pesquisar por nome, BI, telefone...",
            height=38, border_width=0, fg_color="#161b22",
            font=ctk.CTkFont(size=13), text_color="#e6edf3"
        ).pack(fill="x", padx=8)

        # ── Tabela ──
        table_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Hospital.Treeview",
                         background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=32,
                         font=("Helvetica", 11))
        style.configure("Hospital.Treeview.Heading",
                         background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 11, "bold"))
        style.map("Hospital.Treeview", background=[("selected", "#1f6feb")])

        columns = ("id", "nome", "nascimento", "genero", "bi", "telefone", "sangue")
        self._tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            style="Hospital.Treeview", selectmode="browse"
        )
        heads = ["ID", "Nome Completo", "Nascimento", "Género", "BI", "Telefone", "Tipo Sg."]
        widths = [40, 220, 100, 90, 120, 120, 70]
        for col, head, w in zip(columns, heads, widths):
            self._tree.heading(col, text=head)
            self._tree.column(col, width=w, anchor="center" if w < 150 else "w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=4, pady=4)
        self._tree.bind("<Double-1>", lambda e: self._open_detail())
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Botões de acção ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=8)
        self._btn_edit = ctk.CTkButton(
            btn_frame, text="✏  Editar", width=110, height=34,
            fg_color="#1f6feb", hover_color="#388bfd", state="disabled",
            command=self._open_edit
        )
        self._btn_edit.pack(side="left", padx=(0, 8))
        self._btn_delete = ctk.CTkButton(
            btn_frame, text="🗑  Eliminar", width=110, height=34,
            fg_color="#da3633", hover_color="#f85149", state="disabled",
            command=self._delete_patient
        )
        self._btn_delete.pack(side="left")
        self._lbl_count = ctk.CTkLabel(
            btn_frame, text="", font=ctk.CTkFont(size=12), text_color="#8b949e"
        )
        self._lbl_count.pack(side="right")

    def _load_patients(self, patients=None):
        for row in self._tree.get_children():
            self._tree.delete(row)
        if patients is None:
            patients = self._services["patient"].get_all_patients()
        for p in patients:
            self._tree.insert("", "end", iid=str(p.id), values=(
                p.id, p.full_name,
                p.birth_date.strftime("%d/%m/%Y") if p.birth_date else "",
                p.gender.value if p.gender else "",
                p.bi or "", p.phone or "", p.blood_type or ""
            ))
        self._lbl_count.configure(text=f"{len(patients)} paciente(s)")

    def _search(self):
        q = self._search_var.get().strip()
        if len(q) >= 2:
            results = self._services["patient"].search_patients(q)
        else:
            results = self._services["patient"].get_all_patients()
        self._load_patients(results)

    def _on_select(self, event):
        sel = self._tree.selection()
        if sel:
            self._selected_patient = int(sel[0])
            self._btn_edit.configure(state="normal")
            self._btn_delete.configure(state="normal")
        else:
            self._selected_patient = None
            self._btn_edit.configure(state="disabled")
            self._btn_delete.configure(state="disabled")

    def _open_form(self, patient_data=None):
        PatientFormDialog(
            self, self._services["patient"],
            patient_data=patient_data,
            on_save=lambda: self._load_patients()
        )

    def _open_edit(self):
        if not self._selected_patient:
            return
        try:
            p = self._services["patient"].get_patient(self._selected_patient)
            self._open_form(p)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _open_detail(self):
        self._open_edit()

    def _delete_patient(self):
        if not self._selected_patient:
            return
        if messagebox.askyesno(
            "Confirmar Eliminação",
            "Tem a certeza que deseja eliminar este paciente?\nEsta acção não pode ser revertida."
        ):
            try:
                self._services["patient"].delete_patient(self._selected_patient)
                self._load_patients()
                self._selected_patient = None
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def refresh(self):
        self._load_patients()


class PatientFormDialog(ctk.CTkToplevel):
    """Diálogo de criação/edição de paciente."""

    def __init__(self, parent, patient_service, patient_data=None, on_save=None):
        super().__init__(parent)
        self._svc = patient_service
        self._patient = patient_data
        self._on_save = on_save
        self._is_edit = patient_data is not None

        self.title("Editar Paciente" if self._is_edit else "Novo Paciente")
        self.geometry("560x680")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build_ui()
        if self._is_edit:
            self._populate()

    def _lbl(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#c9d1d9", anchor="w").pack(fill="x", padx=24)

    def _entry(self, parent, placeholder="") -> ctk.CTkEntry:
        e = ctk.CTkEntry(
            parent, placeholder_text=placeholder, height=38,
            font=ctk.CTkFont(size=13), corner_radius=8
        )
        e.pack(fill="x", padx=24, pady=(4, 12))
        return e

    def _build_ui(self):
        self.configure(fg_color="#0d1117")
        ctk.CTkLabel(
            self,
            text="Editar Paciente" if self._is_edit else "Novo Paciente",
            font=ctk.CTkFont(size=17, weight="bold"), text_color="#e6edf3"
        ).pack(pady=(20, 4))
        ctk.CTkFrame(self, height=1, fg_color="#30363d").pack(fill="x", padx=20, pady=(4, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        def lbl(text):
            ctk.CTkLabel(scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(fill="x", padx=24)

        def entry(ph=""):
            e = ctk.CTkEntry(
                scroll, placeholder_text=ph, height=38,
                font=ctk.CTkFont(size=13), corner_radius=8
            )
            e.pack(fill="x", padx=24, pady=(4, 10))
            return e

        lbl("Nome Completo *")
        self._e_name = entry("Nome do paciente")
        lbl("Data de Nascimento * (AAAA-MM-DD)")
        self._e_birth = entry("ex: 1990-01-15")
        lbl("Género *")
        self._combo_gender = ctk.CTkComboBox(
            scroll, values=["Masculino", "Feminino", "Outro"],
            height=38, font=ctk.CTkFont(size=13), corner_radius=8
        )
        self._combo_gender.pack(fill="x", padx=24, pady=(4, 10))
        lbl("Bilhete de Identidade")
        self._e_bi = entry("ex: 004567890LA034")
        lbl("Telefone")
        self._e_phone = entry("ex: +244 912 000 000")
        lbl("Email")
        self._e_email = entry("ex: paciente@email.com")
        lbl("Endereço")
        self._e_addr = ctk.CTkTextbox(
            scroll, height=60, font=ctk.CTkFont(size=13), corner_radius=8
        )
        self._e_addr.pack(fill="x", padx=24, pady=(4, 10))
        lbl("Tipo Sanguíneo")
        self._combo_blood = ctk.CTkComboBox(
            scroll, values=["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
            height=38, font=ctk.CTkFont(size=13), corner_radius=8
        )
        self._combo_blood.pack(fill="x", padx=24, pady=(4, 10))
        lbl("Alergias")
        self._e_allerg = entry("ex: Penicilina, Aspirina")
        lbl("Contacto de Emergência")
        self._e_emerg = entry("Nome e telefone")

        self._lbl_err = ctk.CTkLabel(
            scroll, text="", font=ctk.CTkFont(size=11), text_color="#f85149"
        )
        self._lbl_err.pack(pady=4)

        # Botões
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(8, 20))
        ctk.CTkButton(
            btn_row, text="Cancelar", width=110, height=38,
            fg_color="#21262d", hover_color="#30363d",
            command=self.destroy
        ).pack(side="left")
        ctk.CTkButton(
            btn_row, text="Guardar", width=110, height=38,
            fg_color="#238636", hover_color="#2ea043",
            command=self._save
        ).pack(side="right")

    def _populate(self):
        p = self._patient
        self._e_name.insert(0, p.full_name or "")
        self._e_birth.insert(0, p.birth_date.strftime("%Y-%m-%d") if p.birth_date else "")
        self._combo_gender.set(p.gender.value if p.gender else "Masculino")
        self._e_bi.insert(0, p.bi or "")
        self._e_phone.insert(0, p.phone or "")
        self._e_email.insert(0, p.email or "")
        self._e_addr.insert("1.0", p.address or "")
        self._combo_blood.set(p.blood_type or "")
        self._e_allerg.insert(0, p.allergies or "")
        self._e_emerg.insert(0, p.emergency_contact or "")

    def _save(self):
        data = {
            "full_name": self._e_name.get().strip(),
            "birth_date": self._e_birth.get().strip(),
            "gender": self._combo_gender.get(),
            "bi": self._e_bi.get().strip(),
            "phone": self._e_phone.get().strip(),
            "email": self._e_email.get().strip(),
            "address": self._e_addr.get("1.0", "end").strip(),
            "blood_type": self._combo_blood.get().strip(),
            "allergies": self._e_allerg.get().strip(),
            "emergency_contact": self._e_emerg.get().strip(),
        }
        try:
            if self._is_edit:
                self._svc.update_patient(self._patient.id, data)
            else:
                self._svc.register_patient(data)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            self._lbl_err.configure(text=str(e))
