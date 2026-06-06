"""
Frame de Gestão de Consultas.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime


class AppointmentsFrame(ctk.CTkFrame):
    """Frame CRUD de consultas médicas."""

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
            header, text="📅  Gestão de Consultas",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e6edf3"
        ).pack(side="left")
        ctk.CTkButton(
            header, text="+ Agendar Consulta", width=155, height=34,
            fg_color="#238636", hover_color="#2ea043",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._open_form
        ).pack(side="right")

        # Filtros
        filt = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=8)
        filt.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(filt, text="Filtrar por estado:", text_color="#8b949e",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=12, pady=8)
        self._filter_var = ctk.StringVar(value="Todos")
        for status in ["Todos", "scheduled", "in_progress", "completed", "cancelled"]:
            ctk.CTkRadioButton(
                filt, text=status.replace("_", " ").capitalize(),
                variable=self._filter_var, value=status,
                command=self._load,
                font=ctk.CTkFont(size=11), text_color="#c9d1d9"
            ).pack(side="left", padx=8, pady=8)

        # Tabela
        table_frame = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=8)

        style = ttk.Style()
        style.configure("Apt.Treeview",
                         background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=30,
                         font=("Helvetica", 11))
        style.configure("Apt.Treeview.Heading",
                         background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 11, "bold"))
        style.map("Apt.Treeview", background=[("selected", "#1f6feb")])

        cols = ("id", "paciente", "medico", "data", "motivo", "estado")
        self._tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            style="Apt.Treeview", selectmode="browse"
        )
        heads = ["ID", "Paciente", "Médico", "Data/Hora", "Motivo", "Estado"]
        widths = [40, 200, 170, 130, 180, 100]
        for col, head, w in zip(cols, heads, widths):
            self._tree.heading(col, text=head)
            self._tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=4, pady=4)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Acções
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=8)

        self._btn_complete = ctk.CTkButton(
            btn_frame, text="✅  Concluir", width=110, height=34,
            fg_color="#238636", hover_color="#2ea043", state="disabled",
            command=self._complete
        )
        self._btn_complete.pack(side="left", padx=(0, 8))
        self._btn_cancel = ctk.CTkButton(
            btn_frame, text="❌  Cancelar", width=110, height=34,
            fg_color="#da3633", hover_color="#f85149", state="disabled",
            command=self._cancel
        )
        self._btn_cancel.pack(side="left", padx=(0, 8))
        self._btn_record = ctk.CTkButton(
            btn_frame, text="📋  Prontuário", width=120, height=34,
            fg_color="#1f6feb", hover_color="#388bfd", state="disabled",
            command=self._open_record
        )
        self._btn_record.pack(side="left")
        self._lbl_count = ctk.CTkLabel(
            btn_frame, text="", font=ctk.CTkFont(size=12), text_color="#8b949e"
        )
        self._lbl_count.pack(side="right")

    def _load(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        apts = self._services["appointment"].get_all_appointments()
        filt = self._filter_var.get()
        if filt != "Todos":
            apts = [a for a in apts if a.status and a.status.value == filt]
        for a in apts:
            self._tree.insert("", "end", iid=str(a.id), values=(
                a.id,
                a.patient.full_name if a.patient else "",
                a.doctor.user.full_name if a.doctor and a.doctor.user else "",
                a.scheduled_date.strftime("%d/%m/%Y %H:%M") if a.scheduled_date else "",
                (a.reason or "")[:40],
                a.status.value.replace("_", " ").capitalize() if a.status else ""
            ))
        self._lbl_count.configure(text=f"{len(apts)} consulta(s)")

    def _on_select(self, event):
        sel = self._tree.selection()
        if sel:
            self._selected_id = int(sel[0])
            self._btn_complete.configure(state="normal")
            self._btn_cancel.configure(state="normal")
            self._btn_record.configure(state="normal")
        else:
            self._selected_id = None
            self._btn_complete.configure(state="disabled")
            self._btn_cancel.configure(state="disabled")
            self._btn_record.configure(state="disabled")

    def _open_form(self):
        AppointmentFormDialog(
            self, self._services,
            on_save=self._load
        )

    def _complete(self):
        if self._selected_id and messagebox.askyesno("Confirmar", "Marcar consulta como concluída?"):
            try:
                self._services["appointment"].complete_appointment(self._selected_id)
                self._load()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def _cancel(self):
        if self._selected_id and messagebox.askyesno("Confirmar", "Cancelar esta consulta?"):
            try:
                self._services["appointment"].cancel_appointment(self._selected_id)
                self._load()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def _open_record(self):
        if not self._selected_id:
            return
        try:
            appt = self._services["appointment"].get_by_id(self._selected_id)
            MedicalRecordDialog(self, self._services, appt)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def refresh(self):
        self._load()


class AppointmentFormDialog(ctk.CTkToplevel):
    """Diálogo de agendamento de consulta."""

    def __init__(self, parent, services, on_save=None):
        super().__init__(parent)
        self._services = services
        self._on_save = on_save
        self.title("Agendar Consulta")
        self.geometry("480x520")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="#0d1117")
        ctk.CTkLabel(
            self, text="Agendar Nova Consulta",
            font=ctk.CTkFont(size=17, weight="bold"), text_color="#e6edf3"
        ).pack(pady=(20, 4))
        ctk.CTkFrame(self, height=1, fg_color="#30363d").pack(fill="x", padx=20, pady=(4, 12))

        def lbl(text):
            ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(fill="x", padx=24)

        def entry(ph=""):
            e = ctk.CTkEntry(self, placeholder_text=ph, height=38, font=ctk.CTkFont(size=13), corner_radius=8)
            e.pack(fill="x", padx=24, pady=(4, 10))
            return e

        # Paciente
        lbl("Pesquisar Paciente *")
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=24, pady=(4, 2))
        self._e_patient_search = ctk.CTkEntry(
            search_row, placeholder_text="Nome ou BI do paciente",
            height=38, font=ctk.CTkFont(size=13), corner_radius=8
        )
        self._e_patient_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            search_row, text="🔍", width=40, height=38,
            fg_color="#21262d", hover_color="#30363d",
            command=self._search_patient
        ).pack(side="left")

        self._combo_patient = ctk.CTkComboBox(
            self, values=["— pesquise acima —"], height=38,
            font=ctk.CTkFont(size=12), corner_radius=8
        )
        self._combo_patient.pack(fill="x", padx=24, pady=(4, 10))
        self._patients_map = {}

        # Médico
        lbl("Médico *")
        doctors = self._services["auth"].get_active_doctors()
        self._doctors_map = {}
        doc_labels = []
        for d in doctors:
            label = f"Dr. {d.user.full_name} — {d.specialty.name if d.specialty else 'Geral'}"
            doc_labels.append(label)
            self._doctors_map[label] = d.id
        self._combo_doctor = ctk.CTkComboBox(
            self, values=doc_labels or ["Sem médicos"], height=38,
            font=ctk.CTkFont(size=12), corner_radius=8
        )
        self._combo_doctor.pack(fill="x", padx=24, pady=(4, 10))

        lbl("Data e Hora * (AAAA-MM-DD HH:MM)")
        self._e_date = entry("ex: 2026-06-15 09:30")
        lbl("Motivo da Consulta")
        self._e_reason = entry("Descreva o motivo")

        self._lbl_err = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="#f85149"
        )
        self._lbl_err.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(4, 20))
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=38,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_row, text="Agendar", width=110, height=38,
                       fg_color="#238636", hover_color="#2ea043",
                       command=self._save).pack(side="right")

    def _search_patient(self):
        q = self._e_patient_search.get().strip()
        if len(q) < 2:
            return
        patients = self._services["patient"].search_patients(q)
        self._patients_map = {}
        labels = []
        for p in patients:
            label = f"{p.full_name} (BI: {p.bi or 'N/A'})"
            labels.append(label)
            self._patients_map[label] = p.id
        self._combo_patient.configure(values=labels or ["Nenhum resultado"])

    def _save(self):
        patient_label = self._combo_patient.get()
        doctor_label = self._combo_doctor.get()
        patient_id = self._patients_map.get(patient_label)
        doctor_id = self._doctors_map.get(doctor_label)

        if not patient_id:
            self._lbl_err.configure(text="Seleccione um paciente válido.")
            return
        if not doctor_id:
            self._lbl_err.configure(text="Seleccione um médico válido.")
            return

        data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "scheduled_date": self._e_date.get().strip(),
            "reason": self._e_reason.get().strip(),
        }
        try:
            self._services["appointment"].schedule_appointment(data)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            self._lbl_err.configure(text=str(e))


class MedicalRecordDialog(ctk.CTkToplevel):
    """Diálogo de criação/visualização de prontuário."""

    def __init__(self, parent, services, appointment):
        super().__init__(parent)
        self._services = services
        self._appt = appointment
        self.title(f"Prontuário — Consulta #{appointment.id}")
        self.geometry("500x600")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="#0d1117")
        ctk.CTkLabel(
            self, text=f"Prontuário — {self._appt.patient.full_name if self._appt.patient else ''}",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#e6edf3"
        ).pack(pady=(16, 4))
        ctk.CTkFrame(self, height=1, fg_color="#30363d").pack(fill="x", padx=20, pady=(4, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4)

        def lbl(text):
            ctk.CTkLabel(scroll, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(fill="x", padx=20)

        def entry(ph=""):
            e = ctk.CTkEntry(scroll, placeholder_text=ph, height=36,
                              font=ctk.CTkFont(size=12), corner_radius=8)
            e.pack(fill="x", padx=20, pady=(3, 8))
            return e

        # Sinais Vitais
        vitals = ctk.CTkFrame(scroll, fg_color="#161b22", corner_radius=8)
        vitals.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(vitals, text="Sinais Vitais", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=12, pady=(8, 4))
        row1 = ctk.CTkFrame(vitals, fg_color="transparent")
        row1.pack(fill="x", padx=8)
        for label, attr in [("Peso (kg)", "_e_weight"), ("Altura (cm)", "_e_height"),
                              ("Temp. (°C)", "_e_temp"), ("FC (bpm)", "_e_hr"),
                              ("PA (mmHg)", "_e_bp")]:
            col = ctk.CTkFrame(row1, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True, padx=4, pady=6)
            ctk.CTkLabel(col, text=label, font=ctk.CTkFont(size=10),
                         text_color="#8b949e").pack()
            e = ctk.CTkEntry(col, height=32, font=ctk.CTkFont(size=12), corner_radius=6, width=70)
            e.pack()
            setattr(self, attr, e)

        lbl("Diagnóstico")
        self._e_diagnosis = ctk.CTkTextbox(scroll, height=80, font=ctk.CTkFont(size=12), corner_radius=8)
        self._e_diagnosis.pack(fill="x", padx=20, pady=(3, 8))

        lbl("Prescrição")
        self._e_prescription = ctk.CTkTextbox(scroll, height=80, font=ctk.CTkFont(size=12), corner_radius=8)
        self._e_prescription.pack(fill="x", padx=20, pady=(3, 8))

        lbl("Observações")
        self._e_obs = ctk.CTkTextbox(scroll, height=60, font=ctk.CTkFont(size=12), corner_radius=8)
        self._e_obs.pack(fill="x", padx=20, pady=(3, 8))

        self._lbl_err = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11), text_color="#f85149")
        self._lbl_err.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(8, 16))
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=38,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self.destroy).pack(side="left")
        ctk.CTkButton(btn_row, text="Guardar Prontuário", width=160, height=38,
                       fg_color="#238636", hover_color="#2ea043",
                       command=self._save).pack(side="right")

    def _save(self):
        data = {
            "patient_id": self._appt.patient_id,
            "appointment_id": self._appt.id,
            "weight": self._e_weight.get().strip(),
            "height": self._e_height.get().strip(),
            "temperature": self._e_temp.get().strip(),
            "heart_rate": self._e_hr.get().strip(),
            "blood_pressure": self._e_bp.get().strip(),
            "diagnosis": self._e_diagnosis.get("1.0", "end").strip(),
            "prescription": self._e_prescription.get("1.0", "end").strip(),
            "observations": self._e_obs.get("1.0", "end").strip(),
        }
        try:
            self._services["record"].create_record(data)
            messagebox.showinfo("Sucesso", "Prontuário guardado com sucesso!")
            self.destroy()
        except Exception as e:
            self._lbl_err.configure(text=str(e))
