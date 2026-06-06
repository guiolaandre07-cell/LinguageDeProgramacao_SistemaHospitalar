"""
Frame de Prontuários Médicos.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk


class MedicalRecordsFrame(ctk.CTkFrame):
    """Frame de visualização de prontuários médicos."""

    def __init__(self, parent, services: dict, current_user: dict):
        super().__init__(parent, fg_color="transparent")
        self._services = services
        self._user = current_user
        self._selected_patient_id = None
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header, text="📋  Prontuários Médicos",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e6edf3"
        ).pack(side="left")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=4)
        main.columnconfigure(0, weight=1, minsize=220)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(0, weight=1)

        # ── Painel pacientes ──
        left = ctk.CTkFrame(main, fg_color="#161b22", corner_radius=10,
                             border_width=1, border_color="#30363d")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(left, text="Pacientes", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=12, pady=(12, 6))

        self._e_search = ctk.CTkEntry(left, placeholder_text="🔍 Pesquisar...",
                                       height=34, font=ctk.CTkFont(size=12))
        self._e_search.pack(fill="x", padx=8, pady=(0, 6))
        self._e_search.bind("<Return>", lambda e: self._search_patients())

        style = ttk.Style()
        style.configure("Pat.Treeview", background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=28, font=("Helvetica", 10))
        style.configure("Pat.Treeview.Heading", background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 10, "bold"))
        style.map("Pat.Treeview", background=[("selected", "#1f6feb")])

        self._patient_list = ttk.Treeview(
            left, columns=("id", "nome"), show="headings",
            style="Pat.Treeview", selectmode="browse"
        )
        self._patient_list.heading("id", text="ID")
        self._patient_list.heading("nome", text="Nome")
        self._patient_list.column("id", width=40)
        self._patient_list.column("nome", width=160)
        sb = ttk.Scrollbar(left, orient="vertical", command=self._patient_list.yview)
        self._patient_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._patient_list.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        self._patient_list.bind("<<TreeviewSelect>>", self._on_patient_select)

        self._load_patients()

        # ── Painel prontuários ──
        right = ctk.CTkFrame(main, fg_color="#161b22", corner_radius=10,
                              border_width=1, border_color="#30363d")
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="Registos do Paciente", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=16, pady=(12, 6))

        cols = ("data", "diagnostico", "prescricao", "pa", "temp", "fc")
        style.configure("Rec.Treeview", background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=28, font=("Helvetica", 10))
        style.configure("Rec.Treeview.Heading", background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 10, "bold"))
        style.map("Rec.Treeview", background=[("selected", "#1f6feb")])

        self._records_tree = ttk.Treeview(
            right, columns=cols, show="headings",
            style="Rec.Treeview", selectmode="browse"
        )
        heads = ["Data", "Diagnóstico", "Prescrição", "PA", "Temp.", "FC"]
        widths = [120, 200, 180, 70, 60, 60]
        for col, head, w in zip(cols, heads, widths):
            self._records_tree.heading(col, text=head)
            self._records_tree.column(col, width=w)

        sb2 = ttk.Scrollbar(right, orient="vertical", command=self._records_tree.yview)
        self._records_tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self._records_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._records_tree.bind("<Double-1>", self._view_detail)

        # Info box
        self._info_frame = ctk.CTkFrame(right, fg_color="#0d1117", corner_radius=8)
        self._info_frame.pack(fill="x", padx=8, pady=8)
        self._lbl_detail = ctk.CTkLabel(
            self._info_frame, text="Seleccione um paciente e clique duas vezes num registo para ver detalhes.",
            font=ctk.CTkFont(size=11), text_color="#8b949e", wraplength=400, justify="left"
        )
        self._lbl_detail.pack(padx=12, pady=8)

    def _load_patients(self, patients=None):
        for row in self._patient_list.get_children():
            self._patient_list.delete(row)
        if patients is None:
            patients = self._services["patient"].get_all_patients()
        for p in patients:
            self._patient_list.insert("", "end", iid=str(p.id), values=(p.id, p.full_name))

    def _search_patients(self):
        q = self._e_search.get().strip()
        if len(q) >= 2:
            results = self._services["patient"].search_patients(q)
        else:
            results = self._services["patient"].get_all_patients()
        self._load_patients(results)

    def _on_patient_select(self, event):
        sel = self._patient_list.selection()
        if not sel:
            return
        patient_id = int(sel[0])
        self._selected_patient_id = patient_id
        self._load_records(patient_id)

    def _load_records(self, patient_id: int):
        for row in self._records_tree.get_children():
            self._records_tree.delete(row)
        records = self._services["record"].get_records_by_patient(patient_id)
        for r in records:
            self._records_tree.insert("", "end", iid=str(r.id), values=(
                r.created_at.strftime("%d/%m/%Y %H:%M") if r.created_at else "",
                (r.diagnosis or "")[:35],
                (r.prescription or "")[:35],
                r.blood_pressure or "",
                f"{r.temperature}°C" if r.temperature else "",
                f"{r.heart_rate}bpm" if r.heart_rate else ""
            ))

    def _view_detail(self, event):
        sel = self._records_tree.selection()
        if not sel:
            return
        record_id = int(sel[0])
        try:
            rec = self._services["record"].get_record(record_id)
            detail = (
                f"Data: {rec.created_at.strftime('%d/%m/%Y %H:%M') if rec.created_at else 'N/A'}\n"
                f"Peso: {rec.weight} kg  |  Altura: {rec.height} cm\n"
                f"Temperatura: {rec.temperature}°C  |  FC: {rec.heart_rate} bpm  |  PA: {rec.blood_pressure}\n\n"
                f"Diagnóstico:\n{rec.diagnosis or '—'}\n\n"
                f"Prescrição:\n{rec.prescription or '—'}\n\n"
                f"Observações:\n{rec.observations or '—'}"
            )
            self._lbl_detail.configure(text=detail)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def refresh(self):
        self._load_patients()
        if self._selected_patient_id:
            self._load_records(self._selected_patient_id)
