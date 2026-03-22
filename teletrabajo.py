import csv
import os
import calendar
from datetime import datetime, timedelta, date
import tkinter as tk
from tkinter import ttk, messagebox

FILE = "teletrabajo_registro.csv"

ESTADOS = [
    "teletrabajo",
    "oficina",
    "vacaciones",
    "asuntos propios",
    "festivo",
    "fin de semana",
]

ABREV = {
    "teletrabajo": "TT",
    "oficina": "OF",
    "vacaciones": "VA",
    "asuntos propios": "AP",
    "festivo": "FE",
    "fin de semana": "FS",
}

VACACIONES_TOTALES = 24
ASUNTOS_PROPIOS_TOTALES = 4

COLOR_BG = "#eef2f7"
COLOR_CARD = "#ffffff"
COLOR_HEADER = "#1f4e79"
COLOR_TEXT = "#1f2937"
COLOR_MUTED = "#5b6573"
COLOR_TT = "#2e7d32"
COLOR_OF = "#f59e0b"
COLOR_WEEKEND = "#e5e7eb"
COLOR_TODAY = "#06b6d4"
COLOR_BORDER = "#cbd5e1"


class TeletrabajoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de teletrabajo")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)
        self.root.configure(bg=COLOR_BG)

        self.style = ttk.Style()
        try:
            if "vista" in self.style.theme_names():
                self.style.theme_use("vista")
            elif "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        self.configurar_estilos()

        hoy = date.today()
        self.current_month = hoy.month
        self.current_year = hoy.year
        self.calendar_active = False
        self.datos = {}

        self.init_file()
        self.datos = self.leer()
        self.completar_fines_de_semana_faltantes()

        self.root.bind("5", self.handle_key_5)
        self.root.bind("<Left>", self.handle_left)
        self.root.bind("<Right>", self.handle_right)

        self.container = ttk.Frame(self.root, style="App.TFrame", padding=16)
        self.container.pack(fill="both", expand=True)

        self.topbar = ttk.Frame(self.container, style="App.TFrame")
        self.topbar.pack(fill="x", pady=(0, 12))

        self.content = ttk.Frame(self.container, style="App.TFrame")
        self.content.pack(fill="both", expand=True)

        self.render_inicio()

    def configurar_estilos(self):
        self.style.configure("App.TFrame", background=COLOR_BG)
        self.style.configure("Card.TFrame", background=COLOR_CARD)
        self.style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 20, "bold"))
        self.style.configure("SubTitle.TLabel", background=COLOR_BG, foreground=COLOR_MUTED, font=("Segoe UI", 10))
        self.style.configure("Section.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=("Segoe UI", 12, "bold"))
        self.style.configure("CardText.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=("Segoe UI", 10))
        self.style.configure("Muted.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED, font=("Segoe UI", 9))
        self.style.configure("TopInfo.TLabel", background=COLOR_BG, foreground=COLOR_MUTED, font=("Segoe UI", 10, "italic"))
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        self.style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(12, 8))
        self.style.configure("TEntry", padding=6)
        self.style.configure("TCombobox", padding=6)

    def clear_view(self):
        for w in self.topbar.winfo_children():
            w.destroy()
        for w in self.content.winfo_children():
            w.destroy()
        self.calendar_active = False

    def init_file(self):
        if not os.path.exists(FILE):
            with open(FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["fecha", "estado"])

    def leer(self):
        datos = {}
        if os.path.exists(FILE):
            with open(FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fecha = row.get("fecha", "").strip()
                    estado = row.get("estado", "").strip()
                    if fecha and estado:
                        datos[fecha] = estado
        return datos

    def guardar(self):
        with open(FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fecha", "estado"])
            for fecha, estado in sorted(self.datos.items()):
                writer.writerow([fecha, estado])

    def completar_fines_de_semana_faltantes(self):
        if self.datos:
            fechas = sorted(datetime.strptime(f, "%Y-%m-%d").date() for f in self.datos.keys())
            inicio = fechas[0]
        else:
            inicio = date.today()

        fin = date.today()
        cambios = 0
        actual = inicio
        while actual <= fin:
            fecha_str = actual.strftime("%Y-%m-%d")
            if actual.weekday() >= 5 and fecha_str not in self.datos:
                self.datos[fecha_str] = "fin de semana"
                cambios += 1
            actual += timedelta(days=1)

        if cambios:
            self.guardar()

    def validar_fecha(self, fecha_txt):
        try:
            datetime.strptime(fecha_txt, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def contar_periodo(self, inicio, fin):
        tt = 0
        of = 0
        vac = 0
        ap = 0
        fest = 0
        fs = 0

        actual = inicio
        while actual <= fin:
            fecha_str = actual.strftime("%Y-%m-%d")
            estado = self.datos.get(fecha_str)
            if estado == "teletrabajo":
                tt += 1
            elif estado == "oficina":
                of += 1
            elif estado == "vacaciones":
                vac += 1
            elif estado == "asuntos propios":
                ap += 1
            elif estado == "festivo":
                fest += 1
            elif estado == "fin de semana":
                fs += 1
            actual += timedelta(days=1)

        total = tt + of
        return {
            "teletrabajo": tt,
            "oficina": of,
            "vacaciones": vac,
            "asuntos_propios": ap,
            "festivo": fest,
            "fin_de_semana": fs,
            "total_calculo": total,
        }

    def obtener_trimestre(self, fecha):
        trimestre = ((fecha.month - 1) // 3) + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        inicio = fecha.replace(month=mes_inicio, day=1)
        if mes_inicio == 10:
            fin = fecha.replace(month=12, day=31)
        else:
            siguiente = fecha.replace(month=mes_inicio + 3, day=1)
            fin = siguiente - timedelta(days=1)
        return trimestre, inicio, fin

    def calcular_recomendacion_semanal(self):
        hoy = datetime.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)

        resumen = self.contar_periodo(inicio_semana, fin_semana)
        tt = resumen["teletrabajo"]
        of = resumen["oficina"]
        total = tt + of

        dias_restantes_laborables = 0
        for i in range(7):
            dia = inicio_semana + timedelta(days=i)
            fecha_str = dia.strftime("%Y-%m-%d")
            if dia.weekday() < 5 and fecha_str not in self.datos:
                dias_restantes_laborables += 1

        if total == 0 and dias_restantes_laborables == 0:
            return "No hay datos suficientes para recomendar esta semana"

        total_final_estimado = total + dias_restantes_laborables
        objetivo_tt = round(total_final_estimado * 0.6)
        recomendados_tt = max(0, objetivo_tt - tt)
        if recomendados_tt > dias_restantes_laborables:
            recomendados_tt = dias_restantes_laborables
        recomendados_of = max(0, dias_restantes_laborables - recomendados_tt)

        if dias_restantes_laborables == 0:
            objetivo_actual = round(total * 0.6) if total > 0 else 0
            diferencia = tt - objetivo_actual
            if diferencia < 0:
                return f"Semana cerrada: faltaron {abs(diferencia)} dia(s) de teletrabajo"
            if diferencia > 0:
                return f"Semana cerrada: sobran {diferencia} dia(s) de teletrabajo"
            return "Semana cerrada: objetivo 60/40 cumplido"

        return (
            f"Semana {inicio_semana.strftime('%Y-%m-%d')} a {fin_semana.strftime('%Y-%m-%d')}  |  "
            f"Pendiente: TT {recomendados_tt}  /  OF {recomendados_of}"
        )

    def handle_key_5(self, event=None):
        self.root.destroy()

    def handle_left(self, event=None):
        if self.calendar_active:
            self.mes_anterior()

    def handle_right(self, event=None):
        if self.calendar_active:
            self.mes_siguiente()

    def render_topbar(self, titulo, subtitulo="Pulsa la tecla 5 para salir de la aplicacion"):
        ttk.Label(self.topbar, text=titulo, style="Title.TLabel").pack(side="left")
        ttk.Label(self.topbar, text=subtitulo, style="TopInfo.TLabel").pack(side="right", pady=(8, 0))

    def render_inicio(self):
        hoy = datetime.today().strftime("%Y-%m-%d")
        if hoy in self.datos:
            self.render_resumen()
        else:
            self.render_registro_hoy()

    def crear_card(self, parent, padding=14):
        outer = tk.Frame(parent, bg=COLOR_BORDER, bd=0, highlightthickness=0)
        inner = tk.Frame(outer, bg=COLOR_CARD, bd=0, highlightthickness=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        body = ttk.Frame(inner, style="Card.TFrame", padding=padding)
        body.pack(fill="both", expand=True)
        return outer, body

    def render_registro_hoy(self):
        self.clear_view()
        self.render_topbar("Registro de hoy")

        card_outer, card = self.crear_card(self.content, padding=18)
        card_outer.pack(fill="x", pady=10)

        hoy = datetime.today().strftime("%Y-%m-%d")

        ttk.Label(card, text="Hoy no tiene registro", style="Section.TLabel").pack(anchor="w")
        ttk.Label(card, text=f"Fecha actual: {hoy}", style="CardText.TLabel").pack(anchor="w", pady=(8, 4))
        ttk.Label(card, text="Debes anadir el estado de hoy antes de continuar.", style="CardText.TLabel").pack(anchor="w", pady=(0, 12))

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack(anchor="w")

        ttk.Label(form, text="Estado", style="CardText.TLabel").pack(side="left", padx=(0, 10))
        combo = ttk.Combobox(form, values=ESTADOS, state="readonly", width=28)
        combo.pack(side="left")
        combo.set(ESTADOS[0])

        def guardar_hoy():
            estado = combo.get().strip()
            if not estado:
                messagebox.showwarning("Aviso", "Selecciona un estado")
                return
            self.datos[hoy] = estado
            self.guardar()
            self.render_resumen()

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.pack(anchor="w", pady=(16, 0))
        ttk.Button(btns, text="Guardar y continuar", command=guardar_hoy, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="5. Salir", command=self.root.destroy, style="Secondary.TButton").pack(side="left", padx=8)

    def render_resumen(self):
        self.clear_view()
        self.render_topbar("Resumen y estadisticas")

        hoy = datetime.today()
        inicio_mes = hoy.replace(day=1)
        if hoy.month == 12:
            fin_mes = hoy.replace(month=12, day=31)
        else:
            fin_mes = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)

        trimestre, inicio_trim, fin_trim = self.obtener_trimestre(hoy)
        resumen_mes = self.contar_periodo(inicio_mes, fin_mes)
        resumen_trim = self.contar_periodo(inicio_trim, fin_trim)

        stats_row = ttk.Frame(self.content, style="App.TFrame")
        stats_row.pack(fill="x", pady=(0, 12))

        self.crear_tarjeta_resumen(stats_row, f"Mes actual ({hoy.strftime('%Y-%m')})", resumen_mes).pack(
            side="left", fill="both", expand=True, padx=(0, 6)
        )
        self.crear_tarjeta_resumen(stats_row, f"Trimestre actual (T{trimestre} {hoy.year})", resumen_trim).pack(
            side="left", fill="both", expand=True, padx=(6, 0)
        )

        rec_outer, rec_card = self.crear_card(self.content, padding=16)
        rec_outer.pack(fill="x", pady=(0, 12))
        ttk.Label(rec_card, text="Recomendacion semanal", style="Section.TLabel").pack(anchor="w")
        ttk.Label(rec_card, text=self.calcular_recomendacion_semanal(), style="CardText.TLabel").pack(anchor="w", pady=(10, 0))

        menu_outer, menu_card = self.crear_card(self.content, padding=16)
        menu_outer.pack(fill="x")

        ttk.Label(menu_card, text="Menu", style="Section.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))
        ttk.Button(menu_card, text="1. Anadir dato", command=self.render_anadir, style="Primary.TButton").grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        ttk.Button(menu_card, text="2. Modificar dato", command=self.render_modificar, style="Primary.TButton").grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        ttk.Button(menu_card, text="3. Ver calendario", command=self.render_calendario, style="Primary.TButton").grid(row=1, column=2, padx=6, pady=6, sticky="ew")
        ttk.Button(menu_card, text="5. Salir", command=self.root.destroy, style="Secondary.TButton").grid(row=1, column=3, padx=6, pady=6, sticky="ew")

        for i in range(4):
            menu_card.columnconfigure(i, weight=1)

    def crear_tarjeta_resumen(self, parent, titulo, resumen):
        outer, card = self.crear_card(parent, padding=16)

        ttk.Label(card, text=titulo, style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        vacaciones_disfrutadas = resumen["vacaciones"]
        vacaciones_pendientes = max(0, VACACIONES_TOTALES - vacaciones_disfrutadas)

        asuntos_disfrutados = resumen["asuntos_propios"]
        asuntos_pendientes = max(0, ASUNTOS_PROPIOS_TOTALES - asuntos_disfrutados)

        gridf = ttk.Frame(card, style="Card.TFrame")
        gridf.pack(fill="x")

        filas = [
            ("Teletrabajo", resumen["teletrabajo"]),
            ("Oficina", resumen["oficina"]),
            ("Vacaciones disfrutadas", vacaciones_disfrutadas),
            ("Vacaciones pendientes", vacaciones_pendientes),
            ("Asuntos propios disfrutados", asuntos_disfrutados),
            ("Asuntos propios pendientes", asuntos_pendientes),
            ("Festivo", resumen["festivo"]),
            ("Fin de semana", resumen["fin_de_semana"]),
        ]

        for i, (label, value) in enumerate(filas):
            ttk.Label(gridf, text=label, style="CardText.TLabel").grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(gridf, text=str(value), style="CardText.TLabel").grid(row=i, column=1, sticky="e", padx=(18, 0), pady=2)

        total = resumen["total_calculo"]
        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=12)

        if total > 0:
            pct_tt = (resumen["teletrabajo"] / total) * 100
            pct_of = (resumen["oficina"] / total) * 100
            ttk.Label(card, text=f"% teletrabajo: {pct_tt:.2f}", style="Section.TLabel").pack(anchor="w")
            ttk.Label(card, text=f"% oficina: {pct_of:.2f}", style="CardText.TLabel").pack(anchor="w", pady=(4, 0))
        else:
            ttk.Label(card, text="Sin dias validos para calculo", style="Section.TLabel").pack(anchor="w")

        ttk.Label(card, text="Solo cuentan teletrabajo y oficina", style="Muted.TLabel").pack(anchor="w", pady=(10, 0))
        return outer

    def render_anadir(self):
        self.clear_view()
        self.render_topbar("Anadir dato")

        outer, card = self.crear_card(self.content, padding=18)
        outer.pack(fill="x", pady=10)

        ttk.Label(card, text="Nuevo registro", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(card, text="Fecha (YYYY-MM-DD)", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        fecha_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        fecha_entry = ttk.Entry(card, textvariable=fecha_var, width=18)
        fecha_entry.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(card, text="Estado", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        estado_combo = ttk.Combobox(card, values=ESTADOS, state="readonly", width=28)
        estado_combo.grid(row=2, column=1, sticky="w", pady=6)
        estado_combo.set(ESTADOS[0])

        def guardar_nuevo():
            fecha = fecha_var.get().strip()
            estado = estado_combo.get().strip()
            if not self.validar_fecha(fecha):
                messagebox.showerror("Error", "Fecha no valida. Usa YYYY-MM-DD")
                return
            if not estado:
                messagebox.showerror("Error", "Selecciona un estado")
                return
            self.datos[fecha] = estado
            self.guardar()
            self.render_resumen()

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        ttk.Button(btns, text="Guardar", command=guardar_nuevo, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="0. Volver", command=self.render_resumen, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(btns, text="5. Salir", command=self.root.destroy, style="Secondary.TButton").pack(side="left")

    def render_modificar(self):
        self.clear_view()
        self.render_topbar("Modificar dato")

        outer, card = self.crear_card(self.content, padding=18)
        outer.pack(fill="x", pady=10)

        ttk.Label(card, text="Editar registro existente", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        fechas = sorted(self.datos.keys())
        if not fechas:
            ttk.Label(card, text="No hay datos para modificar", style="CardText.TLabel").pack(anchor="w", pady=8)
            ttk.Button(card, text="0. Volver", command=self.render_resumen, style="Secondary.TButton").pack(anchor="w", pady=8)
            return

        ttk.Label(card, text="Fecha", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        fecha_combo = ttk.Combobox(card, values=fechas, state="readonly", width=18)
        fecha_combo.grid(row=1, column=1, sticky="w", pady=6)
        fecha_combo.set(fechas[-1])

        ttk.Label(card, text="Estado", style="CardText.TLabel").grid(row=2, column=0, sticky="w", pady=6)
        estado_combo = ttk.Combobox(card, values=ESTADOS, state="readonly", width=28)
        estado_combo.grid(row=2, column=1, sticky="w", pady=6)
        estado_combo.set(self.datos[fecha_combo.get()])

        def cargar_estado(event=None):
            fecha = fecha_combo.get().strip()
            if fecha in self.datos:
                estado_combo.set(self.datos[fecha])

        fecha_combo.bind("<<ComboboxSelected>>", cargar_estado)

        def guardar_cambio():
            fecha = fecha_combo.get().strip()
            estado = estado_combo.get().strip()
            if fecha not in self.datos:
                messagebox.showerror("Error", "La fecha no existe")
                return
            self.datos[fecha] = estado
            self.guardar()
            self.render_resumen()

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))
        ttk.Button(btns, text="Guardar cambios", command=guardar_cambio, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="0. Volver", command=self.render_resumen, style="Secondary.TButton").pack(side="left", padx=8)
        ttk.Button(btns, text="5. Salir", command=self.root.destroy, style="Secondary.TButton").pack(side="left")

    def render_calendario(self):
        self.clear_view()
        self.calendar_active = True
        self.render_topbar("Calendario", "Usa flecha izquierda y derecha para cambiar de mes. Pulsa 5 para salir")

        controls_outer, controls = self.crear_card(self.content, padding=12)
        controls_outer.pack(fill="x", pady=(0, 10))
        ttk.Button(controls, text="â Mes anterior", command=self.mes_anterior, style="Primary.TButton").pack(side="left")
        ttk.Button(controls, text="Mes siguiente â", command=self.mes_siguiente, style="Primary.TButton").pack(side="left", padx=8)
        ttk.Button(controls, text="0. Volver", command=self.render_resumen, style="Secondary.TButton").pack(side="right")

        self.title_label = ttk.Label(self.content, text="", style="Title.TLabel")
        self.title_label.pack(anchor="center", pady=(0, 10))

        legend_outer, legend = self.crear_card(self.content, padding=10)
        legend_outer.pack(fill="x", pady=(0, 10))

        items = [
            ("TT", "teletrabajo", COLOR_TT, "white"),
            ("OF", "oficina", COLOR_OF, "black"),
            ("VA", "vacaciones", COLOR_CARD, COLOR_TEXT),
            ("AP", "asuntos propios", COLOR_CARD, COLOR_TEXT),
            ("FE", "festivo", COLOR_CARD, COLOR_TEXT),
            ("FS", "fin de semana", COLOR_WEEKEND, COLOR_TEXT),
        ]

        for i, (ab, label, bg, fg) in enumerate(items):
            pill = tk.Label(legend, text=ab, bg=bg, fg=fg, font=("Segoe UI", 10, "bold"), padx=10, pady=4, relief="solid", bd=1)
            pill.grid(row=0, column=i * 2, padx=(0, 6), pady=2)
            txt = tk.Label(legend, text=label, bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 10))
            txt.grid(row=0, column=i * 2 + 1, padx=(0, 14), pady=2, sticky="w")

        cal_outer, cal_card = self.crear_card(self.content, padding=10)
        cal_outer.pack(fill="both", expand=True)
        self.calendar_table = tk.Frame(cal_card, bg=COLOR_CARD)
        self.calendar_table.pack(fill="both", expand=True)

        self.pintar_calendario()

    def mes_anterior(self):
        if self.current_month == 1:
            self.current_year -= 1
            self.current_month = 12
        else:
            self.current_month -= 1
        self.pintar_calendario()

    def mes_siguiente(self):
        if self.current_month == 12:
            self.current_year += 1
            self.current_month = 1
        else:
            self.current_month += 1
        self.pintar_calendario()

    def pintar_calendario(self):
        if not self.calendar_active:
            return

        for widget in self.calendar_table.winfo_children():
            widget.destroy()

        self.title_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        headers = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        for col, head in enumerate(headers):
            lbl = tk.Label(
                self.calendar_table,
                text=head,
                bg=COLOR_HEADER,
                fg="white",
                font=("Segoe UI", 10, "bold"),
                width=14,
                height=2,
                relief="solid",
                bd=1,
            )
            lbl.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)

        cal = calendar.Calendar(firstweekday=0)
        hoy = date.today()
        semanas = cal.monthdatescalendar(self.current_year, self.current_month)

        for row, semana in enumerate(semanas, start=1):
            for col, dia in enumerate(semana):
                fecha_str = dia.strftime("%Y-%m-%d")
                estado = self.datos.get(fecha_str, "")
                texto_estado = ABREV.get(estado, "--")

                bg = COLOR_CARD
                fg = COLOR_TEXT
                border = COLOR_BORDER

                if estado == "teletrabajo":
                    bg = COLOR_TT
                    fg = "white"
                elif estado == "oficina":
                    bg = COLOR_OF
                    fg = "black"
                elif dia.weekday() >= 5:
                    bg = COLOR_WEEKEND

                if dia == hoy:
                    border = COLOR_TODAY

                celda = tk.Frame(self.calendar_table, bg=border, bd=0, highlightthickness=0)
                celda.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

                inner = tk.Frame(celda, bg=bg)
                inner.pack(fill="both", expand=True, padx=2, pady=2)

                top = tk.Label(inner, text=f"{dia.day:02d}", bg=bg, fg=fg, font=("Segoe UI", 11, "bold"))
                top.pack(pady=(10, 2))

                mid = tk.Label(inner, text=texto_estado, bg=bg, fg=fg, font=("Consolas", 12, "bold"))
                mid.pack()

                if dia.month != self.current_month:
                    top.configure(fg="#94a3b8")
                    mid.configure(fg="#94a3b8")

        for col in range(7):
            self.calendar_table.columnconfigure(col, weight=1, uniform="col")
        total_rows = max(6, len(semanas)) + 1
        for row in range(total_rows):
            self.calendar_table.rowconfigure(row, weight=1)


def main():
    root = tk.Tk()
    TeletrabajoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()