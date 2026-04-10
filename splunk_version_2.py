import csv
import json
import re
from copy import deepcopy
from datetime import datetime
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog

DATA_FILE = "splunk_busquedas.json"

COLOR_MAP = {
    "Rojo": "#f8d7da",
    "Naranja": "#fff3cd",
    "Verde": "#d1e7dd",
    "Azul": "#cfe2ff",
    "Gris": "#e2e3e5",
    "Sin color": "#ffffff",
}

TECH_COLOR_MAP = {
    "Cisco ESA": "Rojo",
    "Proofpoint": "Naranja",
    "M365": "Azul",
    "Proxy": "Gris",
    "Firewall": "Verde",
    "Splunk": "Sin color",
    "OTRO": "Sin color",
}

PRIORIDADES = ["Crítica", "Alta", "Media", "Baja"]
COLORES = list(COLOR_MAP.keys())
ENTORNOS = ["PROD", "PRE", "LAB", "DEV", "OTRO"]
TECNOLOGIAS = ["Cisco ESA", "Proofpoint", "M365", "Proxy", "Firewall", "Splunk", "OTRO"]

SPL_KEYWORDS = {
    "search", "where", "eval", "stats", "chart", "timechart", "transaction", "rename",
    "fields", "table", "sort", "rex", "regex", "dedup", "lookup", "join", "append",
    "appendcols", "eventstats", "streamstats", "bin", "bucket", "fillnull", "mvexpand",
    "spath", "head", "tail", "top", "rare", "convert", "collect", "makemv", "format",
    "inputlookup", "outputlookup", "iplocation", "cluster", "metadata", "tstats", "from",
    "union", "unionall", "anomalies", "predict", "xyseries", "foreach", "case", "if",
    "true", "false", "like", "match", "coalesce", "round", "lower", "upper", "replace",
    "substr", "len", "cidrmatch", "isnull", "isnotnull", "tonumber", "tostring", "relative_time",
    "now", "strptime", "strftime", "stats", "values", "count", "dc", "sum", "avg", "max", "min",
    "by", "as", "and", "or", "not", "in", "earliest", "latest", "index", "sourcetype", "source",
    "host", "tag", "tags", "typeahead", "keeporphans", "keepevicted", "maxspan", "maxpause",
}


class JSONDatabase:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.records = []
        self._load()

    def _load(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.records = data
            else:
                self.records = []
        except FileNotFoundError:
            self.records = []
        except json.JSONDecodeError:
            backup_name = f"{self.data_file}.corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(self.data_file, "r", encoding="utf-8") as src, open(backup_name, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            except Exception:
                pass
            self.records = []

    def _save(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def _next_id(self):
        max_id = 0
        for item in self.records:
            try:
                max_id = max(max_id, int(item.get("id", 0)))
            except (TypeError, ValueError):
                continue
        return max_id + 1

    def save(self, data, record_id=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = deepcopy(data)

        if record_id is not None:
            for idx, item in enumerate(self.records):
                if int(item.get("id", -1)) == int(record_id):
                    payload["id"] = int(record_id)
                    payload["fecha_creacion"] = item.get("fecha_creacion", now)
                    payload["fecha_modificacion"] = now
                    self.records[idx] = payload
                    self._save()
                    return int(record_id)

        payload["id"] = self._next_id()
        payload["fecha_creacion"] = now
        payload["fecha_modificacion"] = now
        self.records.append(payload)
        self._save()
        return payload["id"]

    def delete(self, record_id):
        self.records = [item for item in self.records if int(item.get("id", -1)) != int(record_id)]
        self._save()

    def get(self, record_id):
        for item in self.records:
            if int(item.get("id", -1)) == int(record_id):
                return deepcopy(item)
        return None

    def list(self, filters=None):
        filters = filters or {}
        text = (filters.get("text") or "").strip().lower()
        categoria = (filters.get("categoria") or "").strip()
        tecnologia = (filters.get("tecnologia") or "").strip()
        color = (filters.get("color") or "").strip()
        entorno = (filters.get("entorno") or "").strip()
        prioridad = (filters.get("prioridad") or "").strip()

        rows = []
        for item in self.records:
            if text:
                haystack = " ".join([
                    item.get("nombre", ""), item.get("spl", ""), item.get("descripcion", ""),
                    item.get("observaciones", ""), item.get("categoria", ""), item.get("tecnologia", "")
                ]).lower()
                if text not in haystack:
                    continue
            if categoria and categoria != "Todos" and item.get("categoria", "") != categoria:
                continue
            if tecnologia and tecnologia != "Todos" and item.get("tecnologia", "") != tecnologia:
                continue
            if color and color != "Todos" and item.get("color", "") != color:
                continue
            if entorno and entorno != "Todos" and item.get("entorno", "") != entorno:
                continue
            if prioridad and prioridad != "Todos" and item.get("prioridad", "") != prioridad:
                continue
            rows.append(deepcopy(item))

        rows.sort(key=lambda x: (x.get("fecha_modificacion", ""), int(x.get("id", 0))), reverse=True)
        return rows

    def categories(self):
        values = sorted({item.get("categoria", "") for item in self.records if item.get("categoria", "").strip()})
        return values


class SearchManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de búsquedas Splunk PRO")
        self.root.geometry("1540x900")
        self.db = JSONDatabase()
        self.selected_id = None
        self._highlight_job = None

        self._setup_styles()
        self._build_variables()
        self._build_ui()
        self.refresh_tree()
        self.clear_form()

    def _build_variables(self):
        self.var_nombre = tk.StringVar()
        self.var_categoria = tk.StringVar()
        self.var_entorno = tk.StringVar(value="PROD")
        self.var_tecnologia = tk.StringVar(value="Splunk")
        self.var_prioridad = tk.StringVar(value="Media")
        self.var_color = tk.StringVar(value="Sin color")

        self.var_filter_text = tk.StringVar()
        self.var_filter_categoria = tk.StringVar(value="Todos")
        self.var_filter_tecnologia = tk.StringVar(value="Todos")
        self.var_filter_color = tk.StringVar(value="Todos")
        self.var_filter_entorno = tk.StringVar(value="Todos")
        self.var_filter_prioridad = tk.StringVar(value="Todos")


    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", font=("Segoe UI", 8), rowheight=22)
        style.configure("Treeview.Heading", font=("Segoe UI", 8, "bold"))
        style.configure("TLabel", font=("Segoe UI", 8))
        style.configure("TButton", font=("Segoe UI", 8))
        style.configure("TEntry", font=("Segoe UI", 8))
        style.configure("TCombobox", font=("Segoe UI", 8))

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        left = ttk.Frame(main, padding=8)
        center = ttk.Frame(main, padding=8)
        right = ttk.Frame(main, padding=8)

        main.add(left, weight=1)
        main.add(center, weight=8)
        main.add(right, weight=12)

        self._build_filters(left)
        self._build_table(center)
        self._build_editor(right)

    def _build_filters(self, parent):
        ttk.Label(parent, text="Filtros", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(parent, text="Texto").grid(row=1, column=0, sticky="w")
        ent = ttk.Entry(parent, textvariable=self.var_filter_text)
        ent.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ent.bind("<KeyRelease>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Categoría").grid(row=3, column=0, sticky="w")
        self.cmb_filter_categoria = ttk.Combobox(parent, textvariable=self.var_filter_categoria, state="readonly")
        self.cmb_filter_categoria.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.cmb_filter_categoria.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Tecnología").grid(row=5, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_tecnologia, state="readonly", values=["Todos"] + TECNOLOGIAS)
        cmb.grid(row=6, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Entorno").grid(row=7, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_entorno, state="readonly", values=["Todos"] + ENTORNOS)
        cmb.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Prioridad").grid(row=9, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_prioridad, state="readonly", values=["Todos"] + PRIORIDADES)
        cmb.grid(row=10, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Color").grid(row=11, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_color, state="readonly", values=["Todos"] + COLORES)
        cmb.grid(row=12, column=0, sticky="ew", pady=(0, 12))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Button(parent, text="Limpiar filtros", command=self.clear_filters).grid(row=13, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Exportar CSV", command=self.export_csv).grid(row=14, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Exportar JSON", command=self.export_json).grid(row=15, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Importar JSON", command=self.import_json).grid(row=16, column=0, sticky="ew", pady=(0, 6))

        parent.columnconfigure(0, weight=1)
        self.reload_category_filter()

    def _build_table(self, parent):
        ttk.Label(parent, text="Biblioteca de búsquedas", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        columns = ("id", "nombre", "categoria", "tecnologia", "fecha")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=28)
        headers = {
            "id": "ID", "nombre": "Nombre", "categoria": "Categoría", "tecnologia": "Tecnología",
            "fecha": "Última modificación"
        }
        for col, title in headers.items():
            self.tree.heading(col, text=title)

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("nombre", width=300)
        self.tree.column("categoria", width=140)
        self.tree.column("tecnologia", width=130)
        self.tree.column("fecha", width=155, anchor="center")

        scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(fill="both", expand=True, side="top")
        scrollbar_y.pack(fill="y", side="right")
        scrollbar_x.pack(fill="x", side="bottom")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        for color_name, bg in COLOR_MAP.items():
            self.tree.tag_configure(color_name, background=bg)

    def autoajustar_columnas_biblioteca(self):
        if not hasattr(self, "tree"):
            return

        tree = self.tree
        font_body = tkfont.nametofont("TkDefaultFont")
        try:
            font_head = tkfont.nametofont("TkHeadingFont")
        except tk.TclError:
            font_head = font_body

        limites = {
            "id": 55,
            "nombre": 300,
            "categoria": 150,
            "tecnologia": 160,
            "fecha": 165,
        }

        for col in tree["columns"]:
            heading_text = tree.heading(col, "text") or col
            ancho = font_head.measure(str(heading_text))

            for item in tree.get_children():
                valor = tree.set(item, col)
                ancho = max(ancho, font_body.measure(str(valor)))

            ancho = min(ancho + 24, limites.get(col, 180))
            tree.column(col, width=ancho)

    def _build_editor(self, parent):
        ttk.Label(parent, text="Detalle / edición", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        row = 1
        ttk.Label(parent, text="Nombre *").grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_nombre).grid(row=row, column=1, sticky="ew", pady=3, padx=(0, 12))

        ttk.Label(parent, text="Categoría").grid(row=row, column=2, sticky="w")
        ttk.Entry(parent, textvariable=self.var_categoria).grid(row=row, column=3, sticky="ew", pady=3, padx=(0, 12))

        ttk.Label(parent, text="Tecnología").grid(row=row, column=4, sticky="w")
        cmb_tecnologia = ttk.Combobox(parent, textvariable=self.var_tecnologia, state="readonly", values=TECNOLOGIAS)
        cmb_tecnologia.grid(row=row, column=5, sticky="ew", pady=3)
        cmb_tecnologia.bind("<<ComboboxSelected>>", lambda e: self.on_tecnologia_changed())

        row += 1
        ttk.Label(parent, text="Entorno").grid(row=row, column=0, sticky="w")
        ttk.Combobox(parent, textvariable=self.var_entorno, state="readonly", values=ENTORNOS).grid(row=row, column=1, sticky="ew", pady=3, padx=(0, 12))

        ttk.Label(parent, text="Prioridad").grid(row=row, column=2, sticky="w")
        ttk.Combobox(parent, textvariable=self.var_prioridad, state="readonly", values=PRIORIDADES).grid(row=row, column=3, sticky="ew", pady=3, padx=(0, 12))

        ttk.Label(parent, text="Color asignado").grid(row=row, column=4, sticky="w")
        color_frame = ttk.Frame(parent)
        color_frame.grid(row=row, column=5, sticky="w", pady=3)
        self.lbl_color_asignado = ttk.Label(color_frame, textvariable=self.var_color)
        self.lbl_color_asignado.pack(side="left")
        ttk.Label(color_frame, text="  Vista color:").pack(side="left", padx=(8, 4))
        self.color_preview = tk.Label(color_frame, text="      ", relief="solid", bd=1, bg=COLOR_MAP["Sin color"])
        self.color_preview.pack(side="left")

        row += 1
        ttk.Label(parent, text="Acciones rápidas").grid(row=row, column=0, sticky="w", pady=(4, 0))
        quick = ttk.Frame(parent)
        quick.grid(row=row, column=1, columnspan=5, sticky="ew", pady=(4, 0))
        ttk.Button(quick, text="Formatear SPL", command=self.format_spl).pack(side="left", padx=(0, 6))
        ttk.Button(quick, text="Copiar todo", command=self.copy_spl).pack(side="left", padx=(0, 6))
        ttk.Button(quick, text="Copiar selección", command=self.copy_selected_spl).pack(side="left", padx=(0, 6))
        ttk.Button(quick, text="Snippet ESA", command=lambda: self.insert_snippet("ESA")).pack(side="left", padx=(0, 6))
        ttk.Button(quick, text="Snippet M365", command=lambda: self.insert_snippet("M365")).pack(side="left")

        row += 1
        ttk.Label(parent, text="SPL *").grid(row=row, column=0, sticky="nw", pady=(6, 0))
        spl_frame = ttk.Frame(parent)
        spl_frame.grid(row=row, column=1, columnspan=5, sticky="nsew", pady=(6, 3))
        spl_frame.rowconfigure(1, weight=1)
        spl_frame.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(spl_frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(toolbar, text="Editor SPL con colores", font=("Segoe UI", 8, "bold")).pack(side="left")
        self.lbl_status = ttk.Label(toolbar, text="", foreground="#666666")
        self.lbl_status.pack(side="right")

        self.txt_spl = tk.Text(
            spl_frame,
            height=18,
            wrap="none",
            undo=True,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            selectbackground="#264f78",
            relief="flat",
            font=("Consolas", 9),
            padx=10,
            pady=10,
            tabs=(28,)
        )
        self.txt_spl.grid(row=1, column=0, sticky="nsew")

        spl_scroll_y = ttk.Scrollbar(spl_frame, orient=tk.VERTICAL, command=self.txt_spl.yview)
        spl_scroll_y.grid(row=1, column=1, sticky="ns")
        spl_scroll_x = ttk.Scrollbar(spl_frame, orient=tk.HORIZONTAL, command=self.txt_spl.xview)
        spl_scroll_x.grid(row=2, column=0, sticky="ew")
        self.txt_spl.configure(yscrollcommand=spl_scroll_y.set, xscrollcommand=spl_scroll_x.set)

        self._configure_spl_tags()
        self.txt_spl.bind("<KeyRelease>", self.schedule_spl_highlight)
        self.txt_spl.bind("<<Paste>>", self.schedule_spl_highlight)
        self.txt_spl.bind("<ButtonRelease-1>", self.update_cursor_status)
        self.txt_spl.bind("<KeyRelease>", self.on_spl_keyrelease, add="+")

        row += 1
        ttk.Label(parent, text="Descripción").grid(row=row, column=0, sticky="nw")
        self.txt_descripcion = tk.Text(parent, height=7, wrap="word", font=("Segoe UI", 8))
        self.txt_descripcion.grid(row=row, column=1, columnspan=5, sticky="nsew", pady=3)

        row += 1
        ttk.Label(parent, text="Observaciones").grid(row=row, column=0, sticky="nw")
        self.txt_observaciones = tk.Text(parent, height=4, wrap="word", font=("Segoe UI", 8))
        self.txt_observaciones.grid(row=row, column=1, columnspan=5, sticky="nsew", pady=3)

        row += 1
        actions = ttk.Frame(parent)
        actions.grid(row=row, column=0, columnspan=6, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="Nuevo", command=self.clear_form).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Guardar", command=self.save_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Duplicar", command=self.duplicate_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Borrar", command=self.delete_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Copiar todo", command=self.copy_spl).pack(side="left", padx=6)
        ttk.Button(actions, text="Copiar selección", command=self.copy_selected_spl).pack(side="left", padx=6)
        ttk.Button(actions, text="Refrescar", command=self.refresh_tree).pack(side="left", padx=6)

        parent.columnconfigure(1, weight=3)
        parent.columnconfigure(3, weight=2)
        parent.columnconfigure(5, weight=2)
        parent.rowconfigure(4, weight=4)
        parent.rowconfigure(5, weight=1)
        parent.rowconfigure(6, weight=0)
        self.on_tecnologia_changed()

    def _configure_spl_tags(self):
        self.txt_spl.tag_configure("keyword", foreground="#569CD6")
        self.txt_spl.tag_configure("string", foreground="#CE9178")
        self.txt_spl.tag_configure("comment", foreground="#6A9955")
        self.txt_spl.tag_configure("number", foreground="#B5CEA8")
        self.txt_spl.tag_configure("field", foreground="#9CDCFE")
        self.txt_spl.tag_configure("operator", foreground="#D4D4D4")
        self.txt_spl.tag_configure("pipe", foreground="#C586C0")
        self.txt_spl.tag_configure("paren", foreground="#FFD700")

    def on_tecnologia_changed(self):
        tecnologia = self.var_tecnologia.get().strip() or "OTRO"
        self.var_color.set(TECH_COLOR_MAP.get(tecnologia, "Sin color"))
        self.update_color_preview()

    def update_color_preview(self):
        self.color_preview.configure(bg=COLOR_MAP.get(self.var_color.get(), "#ffffff"))

    def clear_filters(self):
        self.var_filter_text.set("")
        self.var_filter_categoria.set("Todos")
        self.var_filter_tecnologia.set("Todos")
        self.var_filter_color.set("Todos")
        self.var_filter_entorno.set("Todos")
        self.var_filter_prioridad.set("Todos")
        self.refresh_tree()

    def get_filters(self):
        return {
            "text": self.var_filter_text.get(),
            "categoria": self.var_filter_categoria.get(),
            "tecnologia": self.var_filter_tecnologia.get(),
            "color": self.var_filter_color.get(),
            "entorno": self.var_filter_entorno.get(),
            "prioridad": self.var_filter_prioridad.get(),
        }

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.db.list(self.get_filters())
        for row in rows:
            tag = row.get("color") if row.get("color") in COLOR_MAP else "Sin color"
            self.tree.insert(
                "", "end",
                iid=str(row.get("id")),
                values=(
                    row.get("id"), row.get("nombre", ""), row.get("categoria", ""), row.get("tecnologia", ""),
                    row.get("fecha_modificacion", "")
                ),
                tags=(tag,)
            )
        self.reload_category_filter()

    def reload_category_filter(self):
        current = self.var_filter_categoria.get() or "Todos"
        values = ["Todos"] + self.db.categories()
        self.cmb_filter_categoria.configure(values=values)
        self.var_filter_categoria.set(current if current in values else "Todos")

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        record_id = int(selected[0])
        row = self.db.get(record_id)
        if not row:
            return

        self.selected_id = record_id
        self.var_nombre.set(row.get("nombre", ""))
        self.var_categoria.set(row.get("categoria", ""))
        self.var_entorno.set(row.get("entorno", "PROD"))
        self.var_tecnologia.set(row.get("tecnologia", "Splunk"))
        self.var_prioridad.set(row.get("prioridad", "Media"))
        self.var_color.set(TECH_COLOR_MAP.get(self.var_tecnologia.get(), row.get("color", "Sin color")))

        self.txt_spl.delete("1.0", tk.END)
        self.txt_spl.insert("1.0", row.get("spl", ""))
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_descripcion.insert("1.0", row.get("descripcion", ""))
        self.txt_observaciones.delete("1.0", tk.END)
        self.txt_observaciones.insert("1.0", row.get("observaciones", ""))
        self.on_tecnologia_changed()
        self.highlight_spl()

    def get_form_data(self):
        return {
            "nombre": self.var_nombre.get().strip(),
            "categoria": self.var_categoria.get().strip(),
            "entorno": self.var_entorno.get().strip(),
            "tecnologia": self.var_tecnologia.get().strip(),
            "prioridad": self.var_prioridad.get().strip(),
            "color": TECH_COLOR_MAP.get(self.var_tecnologia.get().strip(), "Sin color"),
            "spl": self.txt_spl.get("1.0", tk.END).strip(),
            "descripcion": self.txt_descripcion.get("1.0", tk.END).strip(),
            "observaciones": self.txt_observaciones.get("1.0", tk.END).strip(),
        }

    def validate_form(self, data):
        if not data["nombre"]:
            messagebox.showwarning("Validación", "El nombre es obligatorio.")
            return False
        if not data["spl"]:
            messagebox.showwarning("Validación", "La consulta SPL es obligatoria.")
            return False
        return True

    def save_record(self):
        data = self.get_form_data()
        if not self.validate_form(data):
            return
        saved_id = self.db.save(data, self.selected_id)
        self.selected_id = saved_id
        self.refresh_tree()
        self._select_by_id(saved_id)
        messagebox.showinfo("OK", "Registro guardado correctamente.")

    def _select_by_id(self, record_id):
        item_id = str(record_id)
        if item_id in self.tree.get_children():
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
            self.tree.see(item_id)
            self.on_select()

    def clear_form(self):
        self.selected_id = None
        self.var_nombre.set("")
        self.var_categoria.set("")
        self.var_entorno.set("PROD")
        self.var_tecnologia.set("Splunk")
        self.var_prioridad.set("Media")
        self.var_color.set(TECH_COLOR_MAP.get("Splunk", "Sin color"))
        self.txt_spl.delete("1.0", tk.END)
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_observaciones.delete("1.0", tk.END)
        self.tree.selection_remove(self.tree.selection())
        self.on_tecnologia_changed()
        self.highlight_spl()

    def duplicate_record(self):
        if self.selected_id is None:
            messagebox.showwarning("Duplicar", "Selecciona un registro primero.")
            return
        data = self.get_form_data()
        data["nombre"] = f"{data['nombre']} - copia"
        new_id = self.db.save(data)
        self.refresh_tree()
        self._select_by_id(new_id)
        messagebox.showinfo("OK", "Registro duplicado.")

    def delete_record(self):
        if self.selected_id is None:
            messagebox.showwarning("Borrar", "Selecciona un registro primero.")
            return
        if not messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar este registro?"):
            return
        self.db.delete(self.selected_id)
        self.clear_form()
        self.refresh_tree()
        messagebox.showinfo("OK", "Registro eliminado.")

    def _copy_to_clipboard(self, content, success_message):
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        messagebox.showinfo("OK", success_message)

    def copy_spl(self):
        spl = self.txt_spl.get("1.0", tk.END).strip()
        if not spl:
            messagebox.showwarning("Copiar", "No hay SPL para copiar.")
            return
        self._copy_to_clipboard(spl, "Todo el SPL se ha copiado al portapapeles.")

    def copy_selected_spl(self):
        try:
            selected_text = self.txt_spl.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except tk.TclError:
            selected_text = ""

        if not selected_text:
            messagebox.showwarning("Copiar selección", "No hay texto seleccionado en el editor SPL.")
            return

        self._copy_to_clipboard(selected_text, "La selección del SPL se ha copiado al portapapeles.")

    def format_spl(self):
        text = self.txt_spl.get("1.0", tk.END).strip()
        if not text:
            return
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s*\|\s*", "\n| ", text)
        text = re.sub(r"\s*,\s*", ", ", text)
        self.txt_spl.delete("1.0", tk.END)
        self.txt_spl.insert("1.0", text)
        self.highlight_spl()

    def insert_snippet(self, kind):
        snippets = {
            "ESA": (
                'index=siem-cloud-ciscoesa sourcetype=*esa*\n'
                '| stats count by host sender recipient subject\n'
                '| sort - count'
            ),
            "M365": (
                'index=o365 sourcetype=*exchange*\n'
                '| stats count by UserId Operation ResultStatus\n'
                '| sort - count'
            ),
        }
        snippet = snippets.get(kind, "")
        if not snippet:
            return
        current = self.txt_spl.get("1.0", tk.END).strip()
        if current:
            self.txt_spl.insert(tk.INSERT, "\n\n" + snippet)
        else:
            self.txt_spl.insert("1.0", snippet)
        self.highlight_spl()

    def export_csv(self):
        path = filedialog.asksaveasfilename(title="Exportar a CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        rows = self.db.list(self.get_filters())
        headers = [
            "id", "nombre", "spl", "categoria", "entorno", "tecnologia", "prioridad",
            "color", "descripcion", "observaciones", "fecha_creacion", "fecha_modificacion"
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([row.get(h, "") for h in headers])
        messagebox.showinfo("OK", f"Exportación CSV completada:\n{path}")

    def export_json(self):
        path = filedialog.asksaveasfilename(title="Exportar a JSON", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        rows = self.db.list(self.get_filters())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("OK", f"Exportación JSON completada:\n{path}")

    def import_json(self):
        path = filedialog.askopenfilename(title="Importar JSON", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
            count = 0
            for item in items:
                data = {
                    "nombre": str(item.get("nombre", "")).strip(),
                    "spl": str(item.get("spl", "")).strip(),
                    "categoria": str(item.get("categoria", "")).strip(),
                    "entorno": str(item.get("entorno", "PROD")).strip(),
                    "tecnologia": str(item.get("tecnologia", "Splunk")).strip(),
                    "prioridad": str(item.get("prioridad", "Media")).strip(),
                    "color": str(item.get("color", "Sin color")).strip(),
                    "descripcion": str(item.get("descripcion", "")).strip(),
                    "observaciones": str(item.get("observaciones", "")).strip(),
                }
                if data["nombre"] and data["spl"]:
                    self.db.save(data)
                    count += 1
            self.refresh_tree()
            messagebox.showinfo("OK", f"Importación completada. Registros añadidos: {count}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el JSON.\n{e}")

    def on_spl_keyrelease(self, _event=None):
        self.schedule_spl_highlight()
        self.update_cursor_status()

    def schedule_spl_highlight(self, _event=None):
        if self._highlight_job is not None:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(120, self.highlight_spl)

    def update_cursor_status(self, _event=None):
        try:
            line, col = self.txt_spl.index(tk.INSERT).split(".")
            total_lines = int(self.txt_spl.index("end-1c").split(".")[0])
            self.lbl_status.configure(text=f"Línea {line}, Col {int(col)+1} · {total_lines} líneas")
        except Exception:
            self.lbl_status.configure(text="")

    def highlight_spl(self):
        self._highlight_job = None
        text = self.txt_spl.get("1.0", "end-1c")

        for tag in ("keyword", "string", "comment", "number", "field", "operator", "pipe", "paren"):
            self.txt_spl.tag_remove(tag, "1.0", tk.END)

        if not text:
            self.update_cursor_status()
            return

        # Comentarios con # al inicio de línea
        for match in re.finditer(r"(?m)^\s*#.*$", text):
            self._apply_tag("comment", match.start(), match.end())

        # Strings con comillas simples o dobles
        for match in re.finditer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', text):
            self._apply_tag("string", match.start(), match.end())

        # Pipes
        for match in re.finditer(r"\|", text):
            self._apply_tag("pipe", match.start(), match.end())

        # Paréntesis
        for match in re.finditer(r"[()]", text):
            self._apply_tag("paren", match.start(), match.end())

        # Números
        for match in re.finditer(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])", text):
            self._apply_tag("number", match.start(), match.end())

        # Campos antes de '='
        for match in re.finditer(r"\b([A-Za-z_][\w.:/-]*)\s*=", text):
            self._apply_tag("field", match.start(1), match.end(1))
            self._apply_tag("operator", match.end(1), match.end(1) + 1)

        # Campos dentro de by / as stats / sort, enfoque ligero
        for match in re.finditer(r"\bby\s+([A-Za-z_][\w.:/-]*(?:\s*,\s*[A-Za-z_][\w.:/-]*)*)", text, flags=re.IGNORECASE):
            block = match.group(1)
            offset = match.start(1)
            for name_match in re.finditer(r"[A-Za-z_][\w.:/-]*", block):
                self._apply_tag("field", offset + name_match.start(), offset + name_match.end())

        # Keywords SPL
        for match in re.finditer(r"\b[A-Za-z_][\w]*\b", text):
            token = match.group(0)
            if token.lower() in SPL_KEYWORDS:
                self._apply_tag("keyword", match.start(), match.end())

        self.update_cursor_status()

    def _apply_tag(self, tag, start_offset, end_offset):
        start_index = f"1.0+{start_offset}c"
        end_index = f"1.0+{end_offset}c"
        self.txt_spl.tag_add(tag, start_index, end_index)


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    app = SearchManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
