"""
Frame de Triagem Inteligente com IA.
"""
import customtkinter as ctk
from tkinter import messagebox, ttk
import threading


class TriageFrame(ctk.CTkFrame):
    """Frame de triagem automática com modelo de IA."""

    def __init__(self, parent, services: dict, current_user: dict):
        super().__init__(parent, fg_color="transparent")
        self._services = services
        self._user = current_user
        self._patients_map = {}
        self._build_ui()
        self._load_history()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header, text="🚨  Triagem Inteligente (IA)",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e6edf3"
        ).pack(side="left")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=4)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # Painel esquerdo
        left = ctk.CTkFrame(main, fg_color="#161b22", corner_radius=10,
                             border_width=1, border_color="#30363d")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        ctk.CTkLabel(left, text="Dados do Paciente e Sintomas",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#58a6ff").pack(anchor="w", padx=16, pady=(12, 8))

        ctk.CTkLabel(left, text="Pesquisar Paciente",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#c9d1d9", anchor="w").pack(fill="x", padx=16)
        row = ctk.CTkFrame(left, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(3, 6))
        self._e_search = ctk.CTkEntry(row, placeholder_text="Nome ou BI",
                                       height=34, font=ctk.CTkFont(size=12))
        self._e_search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="🔍", width=36, height=34,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self._search_patient).pack(side="left")

        self._combo_patient = ctk.CTkComboBox(left, values=["— pesquise acima —"],
                                               height=34, font=ctk.CTkFont(size=12))
        self._combo_patient.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkFrame(left, height=1, fg_color="#30363d").pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(left, text="Sintomas e Avaliação",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#c9d1d9").pack(anchor="w", padx=16, pady=(4, 8))

        scroll_form = ctk.CTkScrollableFrame(left, fg_color="transparent", height=340)
        scroll_form.pack(fill="both", expand=True, padx=8)

        self._symptom_vars = {}
        symptoms_def = [
            ("fever",               "Febre",                    0, 2,  2,  "0=Não  1=Baixa  2=Alta"),
            ("pain_level",          "Nível de Dor",             0, 10, 10, "0=Sem dor  →  10=Insuportável"),
            ("breathing_diff",      "Dificuldade Respiratória", 0, 2,  2,  "0=Nenhuma  1=Leve  2=Grave"),
            ("consciousness",       "Nível de Consciência",     0, 2,  2,  "0=Normal  1=Confuso  2=Inconsciente"),
            ("bleeding",            "Sangramento",              0, 2,  2,  "0=Não  1=Leve  2=Grave"),
            ("vomiting",            "Vómitos",                  0, 1,  1,  "0=Não  1=Sim"),
            ("chest_pain",          "Dor Torácica",             0, 1,  1,  "0=Não  1=Sim"),
            ("heart_rate_abnormal", "FC Anormal",               0, 1,  1,  "0=Normal  1=Anormal"),
            ("age_group",           "Faixa Etária",             0, 2,  2,  "0=Criança  1=Adulto  2=Idoso"),
            ("duration_hours",      "Duração (horas)",          0, 72, 72, "Horas com os sintomas"),
        ]

        for key, label, frm, to, steps, hint in symptoms_def:
            container = ctk.CTkFrame(scroll_form, fg_color="#0d1117", corner_radius=6)
            container.pack(fill="x", padx=4, pady=3)
            top_row = ctk.CTkFrame(container, fg_color="transparent")
            top_row.pack(fill="x", padx=8, pady=(6, 0))
            ctk.CTkLabel(top_row, text=label, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#c9d1d9", anchor="w").pack(side="left")
            var = ctk.DoubleVar(value=0)
            self._symptom_vars[key] = var
            ctk.CTkLabel(top_row, textvariable=var, width=30,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#58a6ff").pack(side="right")
            ctk.CTkSlider(container, from_=frm, to=to, number_of_steps=steps,
                           variable=var, height=16).pack(fill="x", padx=8, pady=(2, 2))
            ctk.CTkLabel(container, text=hint, font=ctk.CTkFont(size=9),
                         text_color="#484f58").pack(anchor="w", padx=8, pady=(0, 4))

        self._btn_triage = ctk.CTkButton(
            left, text="⚡  Executar Triagem IA", height=44,
            fg_color="#f85149", hover_color="#da3633",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._run_triage
        )
        self._btn_triage.pack(fill="x", padx=16, pady=(8, 16))

        # Painel direito
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self._result_card = ctk.CTkFrame(right, fg_color="#161b22", corner_radius=10,
                                          border_width=2, border_color="#30363d")
        self._result_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(self._result_card, text="Resultado da Triagem",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8b949e").pack(anchor="w", padx=16, pady=(12, 4))

        self._lbl_priority = ctk.CTkLabel(
            self._result_card, text="— Aguardando —",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#484f58"
        )
        self._lbl_priority.pack(pady=6)

        self._progressbar = ctk.CTkProgressBar(self._result_card, height=10)
        self._progressbar.pack(fill="x", padx=16, pady=(0, 4))
        self._progressbar.set(0)

        self._lbl_confidence = ctk.CTkLabel(
            self._result_card, text="", font=ctk.CTkFont(size=11), text_color="#8b949e"
        )
        self._lbl_confidence.pack()

        self._lbl_rec = ctk.CTkLabel(
            self._result_card, text="",
            font=ctk.CTkFont(size=11), text_color="#c9d1d9",
            wraplength=300, justify="left"
        )
        self._lbl_rec.pack(padx=16, pady=(6, 16))

        # Histórico
        hist_card = ctk.CTkFrame(right, fg_color="#161b22", corner_radius=10,
                                  border_width=1, border_color="#30363d")
        hist_card.grid(row=1, column=0, sticky="nsew")

        top_hist = ctk.CTkFrame(hist_card, fg_color="transparent")
        top_hist.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top_hist, text="Histórico de Triagens",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8b949e").pack(side="left")
        ctk.CTkButton(top_hist, text="⟳", width=30, height=26,
                       fg_color="#21262d", hover_color="#30363d",
                       command=self._load_history).pack(side="right")

        style = ttk.Style()
        style.configure("Tri.Treeview", background="#161b22", foreground="#e6edf3",
                         fieldbackground="#161b22", rowheight=26, font=("Helvetica", 10))
        style.configure("Tri.Treeview.Heading", background="#21262d", foreground="#8b949e",
                         font=("Helvetica", 10, "bold"))
        style.map("Tri.Treeview", background=[("selected", "#1f6feb")])

        cols = ("data", "paciente", "prioridade", "conf")
        self._tree = ttk.Treeview(hist_card, columns=cols, show="headings",
                                   style="Tri.Treeview", selectmode="browse")
        for col, head, w in zip(cols, ["Data", "Paciente", "Prioridade", "Conf."],
                                  [120, 150, 110, 60]):
            self._tree.heading(col, text=head)
            self._tree.column(col, width=w)
        sb = ttk.Scrollbar(hist_card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 4))
        self._tree.pack(fill="both", expand=True, padx=4, pady=(0, 8))

    def _search_patient(self):
        q = self._e_search.get().strip()
        if len(q) < 2:
            return
        patients = self._services["patient"].search_patients(q)
        self._patients_map = {}
        labels = []
        for p in patients:
            label = f"{p.full_name}  (BI: {p.bi or 'N/A'})"
            labels.append(label)
            self._patients_map[label] = p.id
        self._combo_patient.configure(values=labels or ["Nenhum resultado"])
        if labels:
            self._combo_patient.set(labels[0])

    def _run_triage(self):
        patient_label = self._combo_patient.get()
        patient_id = self._patients_map.get(patient_label)
        if not patient_id:
            messagebox.showwarning("Atenção", "Seleccione um paciente válido antes de executar a triagem.")
            return

        symptoms = {k: int(v.get()) for k, v in self._symptom_vars.items()}

        self._btn_triage.configure(state="disabled", text="⏳  A analisar…")
        self._lbl_priority.configure(text="A processar…", text_color="#8b949e")

        def _thread():
            try:
                result = self._services["triage"].triage_patient(
                    patient_id, symptoms, self._user.get("id")
                )
                self.after(0, lambda r=result: self._show_result(r))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Erro IA", str(err)))
            finally:
                self.after(0, lambda: self._btn_triage.configure(
                    state="normal", text="⚡  Executar Triagem IA"
                ))

        threading.Thread(target=_thread, daemon=True).start()

    def _show_result(self, result: dict):
        priority   = result.get("priority", "N/A")
        confidence = result.get("confidence", 0)
        color      = result.get("color", "#ffffff")
        rec        = result.get("recommendation", "")

        self._result_card.configure(border_color=color)
        self._lbl_priority.configure(text=f"● {priority}", text_color=color)
        self._progressbar.set(confidence)
        self._lbl_confidence.configure(text=f"Confiança do modelo: {confidence * 100:.1f}%")
        self._lbl_rec.configure(text=rec)
        self._load_history()

    def _load_history(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        triages = self._services["triage"].get_recent_triages(30)
        for t in triages:
            self._tree.insert("", "end", values=(
                t.created_at.strftime("%d/%m/%Y %H:%M") if t.created_at else "",
                t.patient.full_name if t.patient else "",
                t.priority.value if t.priority else "",
                f"{t.ai_confidence * 100:.0f}%" if t.ai_confidence is not None else ""
            ))

    def refresh(self):
        self._load_history()
