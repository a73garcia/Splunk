import csv
import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DB_FILE = "splunk_busquedas.db"

COLOR_MAP = {
    "Rojo": "#f8d7da",
    "Naranja": "#fff3cd",
    "Verde": "#d1e7dd",
    "Azul": "#cfe2ff",
    "Gris": "#e2e3e5",
    "Sin color": "#ffffff",
}

PRIORIDADES = ["Crítica", "Alta", "Media", "Baja"]
COLORES = list(COLOR_MAP.keys())
ENTORNOS = ["PROD", "PRE", "LAB", "DEV", "OTRO"]
TECNOLOGIAS = ["Cisco ESA", "Proofpoint", "M365", "Proxy", "Firewall", "Splunk", "OTRO"]


class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS busquedas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            spl TEXT NOT NULL,
            categoria TEXT,
            entorno TEXT,
            tecnologia TEXT,
            prioridad TEXT,
            color TEXT,
            descripcion TEXT,
            observaciones TEXT,
            fecha_creacion TEXT,
            fecha_modificacion TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save(self, data, record_id=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if record_id:
            query = """
            UPDATE busquedas
            SET nombre=?, spl=?, categoria=?, entorno=?, tecnologia=?, prioridad=?,
                color=?, descripcion=?, observaciones=?, fecha_modificacion=?
            WHERE id=?
            """
            self.conn.execute(
                query,
                (
                    data["nombre"], data["spl"], data["categoria"], data["entorno"],
                    data["tecnologia"], data["prioridad"], data["color"],
                    data["descripcion"], data["observaciones"], now, record_id
                )
            )
        else:
            query = """
            INSERT INTO busquedas (
                nombre, spl, categoria, entorno, tecnologia, prioridad, color,
                descripcion, observaciones, fecha_creacion, fecha_modificacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.conn.execute(
                query,
                (
                    data["nombre"], data["spl"], data["categoria"], data["entorno"],
                    data["tecnologia"], data["prioridad"], data["color"],
                    data["descripcion"], data["observaciones"], now, now
                )
            )
        self.conn.commit()

    def delete(self, record_id):
        self.conn.execute("DELETE FROM busquedas WHERE id=?", (record_id,))
        self.conn.commit()

    def get(self, record_id):
        cur = self.conn.execute("SELECT * FROM busquedas WHERE id=?", (record_id,))
        return cur.fetchone()

    def list(self, filters=None):
        filters = filters or {}
        query = "SELECT * FROM busquedas WHERE 1=1"
        params = []

        text = filters.get("text", "").strip()
        categoria = filters.get("categoria", "").strip()
        tecnologia = filters.get("tecnologia", "").strip()
        color = filters.get("color", "").strip()
        entorno = filters.get("entorno", "").strip()
        prioridad = filters.get("prioridad", "").strip()

        if text:
            query += """ AND (
                nombre LIKE ? OR spl LIKE ? OR descripcion LIKE ?
                OR observaciones LIKE ? OR categoria LIKE ? OR tecnologia LIKE ?
            )"""
            like = f"%{text}%"
            params.extend([like] * 6)

        if categoria and categoria != "Todos":
            query += " AND categoria = ?"
            params.append(categoria)

        if tecnologia and tecnologia != "Todos":
            query += " AND tecnologia = ?"
            params.append(tecnologia)

        if color and color != "Todos":
            query += " AND color = ?"
            params.append(color)

        if entorno and entorno != "Todos":
            query += " AND entorno = ?"
            params.append(entorno)

        if prioridad and prioridad != "Todos":
            query += " AND prioridad = ?"
            params.append(prioridad)

        query += " ORDER BY fecha_modificacion DESC, id DESC"
        cur = self.conn.execute(query, params)
        return cur.fetchall()

    def categories(self):
        cur = self.conn.execute(
            "SELECT DISTINCT categoria FROM busquedas WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria"
        )
        return [r[0] for r in cur.fetchall()]


class SearchManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de búsquedas Splunk")
        self.root.geometry("1480x860")
        self.db = Database()
        self.selected_id = None

        self._build_variables()
        self._build_ui()
        self.refresh_tree()

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

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        left = ttk.Frame(main, padding=8)
        center = ttk.Frame(main, padding=8)
        right = ttk.Frame(main, padding=8)

        main.add(left, weight=1)
        main.add(center, weight=2)
        main.add(right, weight=2)

        self._build_filters(left)
        self._build_table(center)
        self._build_editor(right)

    def _build_filters(self, parent):
        ttk.Label(parent, text="Filtros", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(parent, text="Texto").grid(row=1, column=0, sticky="w")
        ent = ttk.Entry(parent, textvariable=self.var_filter_text)
        ent.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ent.bind("<KeyRelease>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Categoría").grid(row=3, column=0, sticky="w")
        self.cmb_filter_categoria = ttk.Combobox(parent, textvariable=self.var_filter_categoria, state="readonly")
        self.cmb_filter_categoria.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.cmb_filter_categoria.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Tecnología").grid(row=5, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_tecnologia, state="readonly",
                           values=["Todos"] + TECNOLOGIAS)
        cmb.grid(row=6, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Entorno").grid(row=7, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_entorno, state="readonly",
                           values=["Todos"] + ENTORNOS)
        cmb.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Prioridad").grid(row=9, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_prioridad, state="readonly",
                           values=["Todos"] + PRIORIDADES)
        cmb.grid(row=10, column=0, sticky="ew", pady=(0, 8))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Label(parent, text="Color").grid(row=11, column=0, sticky="w")
        cmb = ttk.Combobox(parent, textvariable=self.var_filter_color, state="readonly",
                           values=["Todos"] + COLORES)
        cmb.grid(row=12, column=0, sticky="ew", pady=(0, 12))
        cmb.bind("<<ComboboxSelected>>", lambda e: self.refresh_tree())

        ttk.Button(parent, text="Limpiar filtros", command=self.clear_filters).grid(row=13, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Exportar CSV", command=self.export_csv).grid(row=14, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Exportar JSON", command=self.export_json).grid(row=15, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(parent, text="Importar JSON", command=self.import_json).grid(row=16, column=0, sticky="ew", pady=(0, 6))

        parent.columnconfigure(0, weight=1)
        self.reload_category_filter()

    def _build_table(self, parent):
        ttk.Label(parent, text="Biblioteca de búsquedas", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        columns = ("id", "nombre", "categoria", "tecnologia", "entorno", "prioridad", "color", "fecha")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=26)
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("tecnologia", text="Tecnología")
        self.tree.heading("entorno", text="Entorno")
        self.tree.heading("prioridad", text="Prioridad")
        self.tree.heading("color", text="Color")
        self.tree.heading("fecha", text="Última modificación")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("nombre", width=260)
        self.tree.column("categoria", width=120)
        self.tree.column("tecnologia", width=120)
        self.tree.column("entorno", width=80, anchor="center")
        self.tree.column("prioridad", width=80, anchor="center")
        self.tree.column("color", width=100, anchor="center")
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

    def _build_editor(self, parent):
        ttk.Label(parent, text="Detalle / edición", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        row = 1
        ttk.Label(parent, text="Nombre *").grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_nombre).grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        ttk.Label(parent, text="Categoría").grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=self.var_categoria).grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        ttk.Label(parent, text="Entorno").grid(row=row, column=0, sticky="w")
        ttk.Combobox(parent, textvariable=self.var_entorno, state="readonly", values=ENTORNOS).grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        ttk.Label(parent, text="Tecnología").grid(row=row, column=0, sticky="w")
        ttk.Combobox(parent, textvariable=self.var_tecnologia, state="readonly", values=TECNOLOGIAS).grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        ttk.Label(parent, text="Prioridad").grid(row=row, column=0, sticky="w")
        ttk.Combobox(parent, textvariable=self.var_prioridad, state="readonly", values=PRIORIDADES).grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        ttk.Label(parent, text="Color").grid(row=row, column=0, sticky="w")
        color_combo = ttk.Combobox(parent, textvariable=self.var_color, state="readonly", values=COLORES)
        color_combo.grid(row=row, column=1, sticky="ew", pady=3)
        color_combo.bind("<<ComboboxSelected>>", lambda e: self.update_color_preview())

        row += 1
        ttk.Label(parent, text="Vista color").grid(row=row, column=0, sticky="w")
        self.color_preview = tk.Label(parent, text="      ", relief="solid", bd=1, bg=COLOR_MAP["Sin color"])
        self.color_preview.grid(row=row, column=1, sticky="w", pady=6)
        self.update_color_preview()

        row += 1
        ttk.Label(parent, text="SPL *").grid(row=row, column=0, sticky="nw")
        self.txt_spl = tk.Text(parent, height=10, wrap="word")
        self.txt_spl.grid(row=row, column=1, sticky="nsew", pady=3)

        row += 1
        ttk.Label(parent, text="Descripción").grid(row=row, column=0, sticky="nw")
        self.txt_descripcion = tk.Text(parent, height=6, wrap="word")
        self.txt_descripcion.grid(row=row, column=1, sticky="nsew", pady=3)

        row += 1
        ttk.Label(parent, text="Observaciones").grid(row=row, column=0, sticky="nw")
        self.txt_observaciones = tk.Text(parent, height=6, wrap="word")
        self.txt_observaciones.grid(row=row, column=1, sticky="nsew", pady=3)

        row += 1
        actions = ttk.Frame(parent)
        actions.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(actions, text="Nuevo", command=self.clear_form).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Guardar", command=self.save_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Duplicar", command=self.duplicate_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Borrar", command=self.delete_record).pack(side="left", padx=6)
        ttk.Button(actions, text="Copiar SPL", command=self.copy_spl).pack(side="left", padx=6)
        ttk.Button(actions, text="Refrescar", command=self.refresh_tree).pack(side="left", padx=6)

        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(7, weight=2)
        parent.rowconfigure(8, weight=1)
        parent.rowconfigure(9, weight=1)

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
            tag = row["color"] if row["color"] in COLOR_MAP else "Sin color"
            self.tree.insert(
                "", "end",
                iid=str(row["id"]),
                values=(
                    row["id"], row["nombre"], row["categoria"], row["tecnologia"],
                    row["entorno"], row["prioridad"], row["color"], row["fecha_modificacion"]
                ),
                tags=(tag,)
            )
        self.reload_category_filter()

    def reload_category_filter(self):
        current = self.var_filter_categoria.get() or "Todos"
        values = ["Todos"] + self.db.categories()
        self.cmb_filter_categoria.configure(values=values)
        if current in values:
            self.var_filter_categoria.set(current)
        else:
            self.var_filter_categoria.set("Todos")

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        record_id = int(selected[0])
        row = self.db.get(record_id)
        if not row:
            return

        self.selected_id = record_id
        self.var_nombre.set(row["nombre"] or "")
        self.var_categoria.set(row["categoria"] or "")
        self.var_entorno.set(row["entorno"] or "PROD")
        self.var_tecnologia.set(row["tecnologia"] or "Splunk")
        self.var_prioridad.set(row["prioridad"] or "Media")
        self.var_color.set(row["color"] or "Sin color")

        self.txt_spl.delete("1.0", tk.END)
        self.txt_spl.insert("1.0", row["spl"] or "")

        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_descripcion.insert("1.0", row["descripcion"] or "")

        self.txt_observaciones.delete("1.0", tk.END)
        self.txt_observaciones.insert("1.0", row["observaciones"] or "")

        self.update_color_preview()

    def get_form_data(self):
        return {
            "nombre": self.var_nombre.get().strip(),
            "categoria": self.var_categoria.get().strip(),
            "entorno": self.var_entorno.get().strip(),
            "tecnologia": self.var_tecnologia.get().strip(),
            "prioridad": self.var_prioridad.get().strip(),
            "color": self.var_color.get().strip(),
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

        self.db.save(data, self.selected_id)
        self.refresh_tree()
        self._select_last_by_name(data["nombre"])
        messagebox.showinfo("OK", "Registro guardado correctamente.")

    def _select_last_by_name(self, name):
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if len(values) > 1 and values[1] == name:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                self.on_select()
                break

    def clear_form(self):
        self.selected_id = None
        self.var_nombre.set("")
        self.var_categoria.set("")
        self.var_entorno.set("PROD")
        self.var_tecnologia.set("Splunk")
        self.var_prioridad.set("Media")
        self.var_color.set("Sin color")
        self.txt_spl.delete("1.0", tk.END)
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_observaciones.delete("1.0", tk.END)
        self.tree.selection_remove(self.tree.selection())
        self.update_color_preview()

    def duplicate_record(self):
        if self.selected_id is None:
            messagebox.showwarning("Duplicar", "Selecciona un registro primero.")
            return
        data = self.get_form_data()
        data["nombre"] = f"{data['nombre']} - copia"
        self.db.save(data)
        self.refresh_tree()
        self._select_last_by_name(data["nombre"])
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

    def copy_spl(self):
        spl = self.txt_spl.get("1.0", tk.END).strip()
        if not spl:
            messagebox.showwarning("Copiar", "No hay SPL para copiar.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(spl)
        self.root.update()
        messagebox.showinfo("OK", "SPL copiado al portapapeles.")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Exportar a CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )
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
                writer.writerow([row[h] for h in headers])

        messagebox.showinfo("OK", f"Exportación CSV completada:\n{path}")

    def export_json(self):
        path = filedialog.asksaveasfilename(
            title="Exportar a JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        rows = self.db.list(self.get_filters())
        data = [dict(row) for row in rows]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("OK", f"Exportación JSON completada:\n{path}")

    def import_json(self):
        path = filedialog.askopenfilename(
            title="Importar JSON",
            filetypes=[("JSON", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
            count = 0
            for item in items:
                data = {
                    "nombre": item.get("nombre", "").strip(),
                    "spl": item.get("spl", "").strip(),
                    "categoria": item.get("categoria", "").strip(),
                    "entorno": item.get("entorno", "PROD").strip(),
                    "tecnologia": item.get("tecnologia", "Splunk").strip(),
                    "prioridad": item.get("prioridad", "Media").strip(),
                    "color": item.get("color", "Sin color").strip(),
                    "descripcion": item.get("descripcion", "").strip(),
                    "observaciones": item.get("observaciones", "").strip(),
                }
                if data["nombre"] and data["spl"]:
                    self.db.save(data)
                    count += 1
            self.refresh_tree()
            messagebox.showinfo("OK", f"Importación completada. Registros añadidos: {count}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el JSON.\n{e}")


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
