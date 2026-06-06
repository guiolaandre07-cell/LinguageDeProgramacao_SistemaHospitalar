"""
Painel de controlo (Dashboard) com gráficos Matplotlib.
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class DashboardFrame(ctk.CTkFrame):
    """Frame do dashboard com KPIs e gráficos."""

    def __init__(self, parent, services: dict, current_user: dict):
        super().__init__(parent, fg_color="transparent")
        self._services = services
        self._user = current_user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Título
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            header, text="📊  Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e6edf3"
        ).pack(side="left")

        ctk.CTkButton(
            header, text="⟳  Atualizar", width=110, height=32,
            fg_color="#21262d", hover_color="#30363d",
            font=ctk.CTkFont(size=12),
            command=self.refresh
        ).pack(side="right")

        # KPI cards
        self._kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._kpi_frame.pack(fill="x", padx=20, pady=8)

        self._kpi_vars = {}
        kpis = [
            ("👤", "Pacientes", "patients", "#58a6ff"),
            ("📅", "Consultas", "appointments", "#3fb950"),
            ("🚨", "Triagens Hoje", "triages", "#f85149"),
            ("👨‍⚕️", "Médicos", "doctors", "#d2a8ff"),
        ]
        for i, (icon, label, key, color) in enumerate(kpis):
            card = ctk.CTkFrame(
                self._kpi_frame, fg_color="#161b22",
                corner_radius=10, border_width=1, border_color="#30363d"
            )
            card.grid(row=0, column=i, padx=8, pady=4, sticky="ew")
            self._kpi_frame.columnconfigure(i, weight=1)

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(14, 2))
            var = ctk.StringVar(value="—")
            self._kpi_vars[key] = var
            ctk.CTkLabel(
                card, textvariable=var,
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color=color
            ).pack()
            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=11),
                text_color="#8b949e"
            ).pack(pady=(2, 14))

        # Gráficos
        charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=20, pady=8)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

        self._chart_appt = self._make_chart_frame(charts_frame, "Consultas por Status", 0)
        self._chart_triage = self._make_chart_frame(charts_frame, "Triagens por Prioridade", 1)

        self._canvas_appt = None
        self._canvas_triage = None

    def _make_chart_frame(self, parent, title: str, col: int) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            parent, fg_color="#161b22",
            corner_radius=10, border_width=1, border_color="#30363d"
        )
        frame.grid(row=0, column=col, padx=8, pady=4, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#c9d1d9"
        ).pack(pady=(12, 4))
        return frame

    def refresh(self):
        """Atualiza KPIs e gráficos com dados actuais."""
        try:
            ps = self._services["patient"]
            apts = self._services["appointment"]
            ts = self._services["triage"]
            auth = self._services["auth"]

            total_patients = ps.get_patient_count()
            total_appts = len(apts.get_all_appointments())
            total_triages = len(ts.get_recent_triages(999))
            total_doctors = len(auth.get_active_doctors())

            self._kpi_vars["patients"].set(str(total_patients))
            self._kpi_vars["appointments"].set(str(total_appts))
            self._kpi_vars["triages"].set(str(total_triages))
            self._kpi_vars["doctors"].set(str(total_doctors))

            self._draw_appointments_chart(apts.count_by_status())
            self._draw_triage_chart(ts.count_by_priority())

        except Exception as e:
            print(f"Erro no dashboard: {e}")

    def _draw_appointments_chart(self, data: dict):
        if self._canvas_appt:
            self._canvas_appt.get_tk_widget().destroy()

        labels = list(data.keys()) if data else ["Sem dados"]
        values = list(data.values()) if data else [1]
        colors = ["#f85149", "#ffa657", "#3fb950", "#58a6ff", "#d2a8ff"][:len(labels)]

        fig = Figure(figsize=(4.2, 3.2), dpi=90, facecolor="#161b22")
        ax = fig.add_subplot(111, facecolor="#161b22")
        if data:
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90,
                textprops={"color": "#c9d1d9", "fontsize": 9}
            )
            for at in autotexts:
                at.set_color("#0d1117")
                at.set_fontsize(9)
        else:
            ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                    color="#8b949e", transform=ax.transAxes)

        fig.tight_layout(pad=1.0)
        self._canvas_appt = FigureCanvasTkAgg(fig, master=self._chart_appt)
        self._canvas_appt.draw()
        self._canvas_appt.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 12))
        plt.close(fig)

    def _draw_triage_chart(self, data: dict):
        if self._canvas_triage:
            self._canvas_triage.get_tk_widget().destroy()

        labels = list(data.keys()) if data else ["Sem dados"]
        values = list(data.values()) if data else [1]
        colors = ["#f85149", "#ffa657", "#ffd700", "#3fb950", "#58a6ff"][:len(labels)]

        fig = Figure(figsize=(4.2, 3.2), dpi=90, facecolor="#161b22")
        ax = fig.add_subplot(111, facecolor="#161b22")
        if data:
            bars = ax.barh(labels, values, color=colors, edgecolor="#30363d")
            ax.set_xlabel("Quantidade", color="#8b949e", fontsize=9)
            ax.tick_params(colors="#c9d1d9", labelsize=8)
            ax.spines[:].set_color("#30363d")
            for bar, v in zip(bars, values):
                ax.text(
                    bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", color="#c9d1d9", fontsize=8
                )
        else:
            ax.text(0.5, 0.5, "Sem dados", ha="center", va="center",
                    color="#8b949e", transform=ax.transAxes)

        fig.tight_layout(pad=1.0)
        self._canvas_triage = FigureCanvasTkAgg(fig, master=self._chart_triage)
        self._canvas_triage.draw()
        self._canvas_triage.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 12))
        plt.close(fig)
