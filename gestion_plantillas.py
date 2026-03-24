import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import sqlite3
from datetime import datetime


DB_NAME = "plantillas.db"


class PlantillasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Plantillas")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 750)

        self.selected_id = None

        self.crear_bd()
        self.crear_estilos()
        self.crear_interfaz()
        self.cargar_registros()

    def crear_bd(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                nombre TEXT NOT NULL,
                numero_peticion TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                respuesta TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def crear_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", padding=4)

    def crear_interfaz(self):
        self.frame_filtros = ttk.LabelFrame(self.root, text="Filtros avanzados")
        self.frame_filtros.pack(fill="x", padx=10, pady=8)

        ttk.Label(self.frame_filtros, text="Palabra clave:").grid(row=0, column=0, padx=(6, 2), pady=6, sticky="w")
        self.entry_busqueda = ttk.Entry(self.frame_filtros, width=28)
        self.entry_busqueda.grid(row=0, column=1, padx=(0, 8), pady=6, sticky="w")

        ttk.Label(self.frame_filtros, text="Nombre:").grid(row=0, column=2, padx=(6, 2), pady=6, sticky="w")
        self.entry_filtro_nombre = ttk.Entry(self.frame_filtros, width=22)
        self.entry_filtro_nombre.grid(row=0, column=3, padx=(0, 8), pady=6, sticky="w")

        ttk.Label(self.frame_filtros, text="Nº Petición:").grid(row=0, column=4, padx=(6, 2), pady=6, sticky="w")
        self.entry_filtro_peticion = ttk.Entry(self.frame_filtros, width=22)
        self.entry_filtro_peticion.grid(row=0, column=5, padx=(0, 8), pady=6, sticky="w")

        ttk.Label(self.frame_filtros, text="Fecha desde:").grid(row=1, column=0, padx=(6, 2), pady=6, sticky="w")
        self.entry_fecha_desde = ttk.Entry(self.frame_filtros, width=15)
        self.entry_fecha_desde.grid(row=1, column=1, padx=(0, 8), pady=6, sticky="w")

        ttk.Label(self.frame_filtros, text="Fecha hasta:").grid(row=1, column=2, padx=(6, 2), pady=6, sticky="w")
        self.entry_fecha_hasta = ttk.Entry(self.frame_filtros, width=15)
        self.entry_fecha_hasta.grid(row=1, column=3, padx=(0, 8), pady=6, sticky="w")

        ttk.Label(self.frame_filtros, text="Formato fecha: YYYY-MM-DD").grid(row=1, column=4, padx=(6, 2), pady=6, sticky="w")

        frame_botones_filtro = ttk.Frame(self.frame_filtros)
        frame_botones_filtro.grid(row=0, column=6, rowspan=2, padx=10, pady=4, sticky="ns")

        ttk.Button(frame_botones_filtro, text="Buscar", command=self.buscar_registros).pack(fill="x", pady=3)
        ttk.Button(frame_botones_filtro, text="Mostrar todo", command=self.mostrar_todo).pack(fill="x", pady=3)
        ttk.Button(frame_botones_filtro, text="Limpiar filtros", command=self.limpiar_filtros).pack(fill="x", pady=3)

        self.entry_busqueda.bind("<Return>", lambda e: self.buscar_registros())
        self.entry_filtro_nombre.bind("<Return>", lambda e: self.buscar_registros())
        self.entry_filtro_peticion.bind("<Return>", lambda e: self.buscar_registros())
        self.entry_fecha_desde.bind("<Return>", lambda e: self.buscar_registros())
        self.entry_fecha_hasta.bind("<Return>", lambda e: self.buscar_registros())

        self.frame_tabla = ttk.LabelFrame(self.root, text="Plantillas registradas")
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=8)

        columnas = ("id", "fecha", "nombre", "numero_peticion", "descripcion", "respuesta")
        self.tree = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("numero_peticion", text="Nº Petición")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("respuesta", text="Respuesta")

        self.tree.column("id", width=70, anchor="center")
        self.tree.column("fecha", width=110, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("numero_peticion", width=130, anchor="center")
        self.tree.column("descripcion", width=400, anchor="w")
        self.tree.column("respuesta", width=400, anchor="w")

        scroll_y = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self.frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.frame_tabla.rowconfigure(0, weight=1)
        self.frame_tabla.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_registro)
        self.tree.bind("<Double-1>", self.abrir_registro_doble_click)

        self.frame_form = ttk.LabelFrame(self.root, text="Formulario de plantilla")
        self.frame_form.pack(fill="both", padx=10, pady=8)

        ttk.Label(self.frame_form, text="ID:").grid(row=0, column=0, padx=(8, 2), pady=8, sticky="w")
        self.var_id = tk.StringVar()
        self.entry_id = ttk.Entry(
            self.frame_form,
            textvariable=self.var_id,
            width=10,
            state="readonly"
        )
        self.entry_id.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="w")

        ttk.Label(self.frame_form, text="Fecha:").grid(row=0, column=2, padx=(8, 2), pady=8, sticky="w")
        self.var_fecha = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha = ttk.Entry(self.frame_form, textvariable=self.var_fecha, width=16)
        self.entry_fecha.grid(row=0, column=3, padx=(0, 8), pady=8, sticky="w")

        ttk.Label(self.frame_form, text="Nombre:").grid(row=0, column=4, padx=(8, 2), pady=8, sticky="w")
        self.var_nombre = tk.StringVar()
        self.entry_nombre = ttk.Entry(self.frame_form, textvariable=self.var_nombre, width=45)
        self.entry_nombre.grid(row=0, column=5, padx=(0, 8), pady=8, sticky="w")

        ttk.Label(self.frame_form, text="Nº Petición:").grid(row=0, column=6, padx=(8, 2), pady=8, sticky="w")
        self.var_numero_peticion = tk.StringVar()
        self.entry_numero_peticion = ttk.Entry(self.frame_form, textvariable=self.var_numero_peticion, width=24)
        self.entry_numero_peticion.grid(row=0, column=7, padx=(0, 8), pady=8, sticky="w")

        ttk.Label(self.frame_form, text="Descripción:").grid(row=1, column=0, padx=(8, 2), pady=8, sticky="nw")
        self.txt_descripcion = ScrolledText(self.frame_form, wrap="word", width=75, height=10, font=("Segoe UI", 10))
        self.txt_descripcion.grid(row=1, column=1, columnspan=4, padx=(0, 8), pady=8, sticky="nsew")

        frame_desc = ttk.Frame(self.frame_form)
        frame_desc.grid(row=1, column=5, padx=8, pady=8, sticky="n")

        ttk.Button(frame_desc, text="Copiar descripción", command=self.copiar_descripcion).pack(fill="x", pady=3)
        ttk.Button(frame_desc, text="Limpiar descripción", command=lambda: self.txt_descripcion.delete("1.0", tk.END)).pack(fill="x", pady=3)

        ttk.Label(self.frame_form, text="Respuesta:").grid(row=2, column=0, padx=(8, 2), pady=8, sticky="nw")
        self.txt_respuesta = ScrolledText(self.frame_form, wrap="word", width=75, height=10, font=("Segoe UI", 10))
        self.txt_respuesta.grid(row=2, column=1, columnspan=4, padx=(0, 8), pady=8, sticky="nsew")

        frame_resp = ttk.Frame(self.frame_form)
        frame_resp.grid(row=2, column=5, padx=8, pady=8, sticky="n")

        ttk.Button(frame_resp, text="Copiar respuesta", command=self.copiar_respuesta).pack(fill="x", pady=3)
        ttk.Button(frame_resp, text="Limpiar respuesta", command=lambda: self.txt_respuesta.delete("1.0", tk.END)).pack(fill="x", pady=3)

        frame_acciones = ttk.Frame(self.frame_form)
        frame_acciones.grid(row=3, column=0, columnspan=8, pady=12)

        ttk.Button(frame_acciones, text="Nuevo / Limpiar", command=self.limpiar_formulario).grid(row=0, column=0, padx=8)
        ttk.Button(frame_acciones, text="Guardar", command=self.guardar_registro).grid(row=0, column=1, padx=8)
        ttk.Button(frame_acciones, text="Modificar", command=self.modificar_registro).grid(row=0, column=2, padx=8)
        ttk.Button(frame_acciones, text="Eliminar", command=self.eliminar_registro).grid(row=0, column=3, padx=8)
        ttk.Button(frame_acciones, text="Salir", command=self.cerrar).grid(row=0, column=4, padx=8)

        self.lbl_estado = ttk.Label(self.root, text="Listo", anchor="w")
        self.lbl_estado.pack(fill="x", padx=10, pady=(0, 8))

        self.frame_form.columnconfigure(1, weight=0)
        self.frame_form.columnconfigure(3, weight=0)
        self.frame_form.columnconfigure(5, weight=1)
        self.frame_form.rowconfigure(1, weight=1)
        self.frame_form.rowconfigure(2, weight=1)

    def actualizar_estado(self, texto):
        self.lbl_estado.config(text=texto)

    def copiar_descripcion(self):
        contenido = self.txt_descripcion.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showwarning("Aviso", "La descripción está vacía.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(contenido)
        self.root.update()
        self.actualizar_estado("Descripción copiada al portapapeles.")

    def copiar_respuesta(self):
        contenido = self.txt_respuesta.get("1.0", tk.END).strip()
        if not contenido:
            messagebox.showwarning("Aviso", "La respuesta está vacía.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(contenido)
        self.root.update()
        self.actualizar_estado("Respuesta copiada al portapapeles.")

    def limpiar_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insertar_en_tabla(self, registros):
        self.limpiar_treeview()
        for fila in registros:
            self.tree.insert("", tk.END, values=fila)
        self.actualizar_estado(f"Registros mostrados: {len(registros)}")

    def cargar_registros(self):
        self.cursor.execute("""
            SELECT id, fecha, nombre, numero_peticion, descripcion, respuesta
            FROM plantillas
            ORDER BY id DESC
        """)
        registros = self.cursor.fetchall()
        self.insertar_en_tabla(registros)

    def validar_fecha(self, fecha_texto):
        if not fecha_texto.strip():
            return True
        try:
            datetime.strptime(fecha_texto, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def buscar_registros(self):
        palabra = self.entry_busqueda.get().strip()
        nombre = self.entry_filtro_nombre.get().strip()
        peticion = self.entry_filtro_peticion.get().strip()
        fecha_desde = self.entry_fecha_desde.get().strip()
        fecha_hasta = self.entry_fecha_hasta.get().strip()

        if fecha_desde and not self.validar_fecha(fecha_desde):
            messagebox.showerror("Fecha incorrecta", "Fecha desde no tiene formato YYYY-MM-DD.")
            return

        if fecha_hasta and not self.validar_fecha(fecha_hasta):
            messagebox.showerror("Fecha incorrecta", "Fecha hasta no tiene formato YYYY-MM-DD.")
            return

        consulta = """
            SELECT id, fecha, nombre, numero_peticion, descripcion, respuesta
            FROM plantillas
            WHERE 1=1
        """
        parametros = []

        if palabra:
            consulta += """
                AND (
                    CAST(id AS TEXT) LIKE ?
                    OR fecha LIKE ?
                    OR nombre LIKE ?
                    OR numero_peticion LIKE ?
                    OR descripcion LIKE ?
                    OR respuesta LIKE ?
                )
            """
            valor = f"%{palabra}%"
            parametros.extend([valor, valor, valor, valor, valor, valor])

        if nombre:
            consulta += " AND nombre LIKE ?"
            parametros.append(f"%{nombre}%")

        if peticion:
            consulta += " AND numero_peticion LIKE ?"
            parametros.append(f"%{peticion}%")

        if fecha_desde:
            consulta += " AND fecha >= ?"
            parametros.append(fecha_desde)

        if fecha_hasta:
            consulta += " AND fecha <= ?"
            parametros.append(fecha_hasta)

        consulta += " ORDER BY id DESC"

        self.cursor.execute(consulta, parametros)
        resultados = self.cursor.fetchall()
        self.insertar_en_tabla(resultados)

    def mostrar_todo(self):
        self.cargar_registros()

    def limpiar_filtros(self):
        self.entry_busqueda.delete(0, tk.END)
        self.entry_filtro_nombre.delete(0, tk.END)
        self.entry_filtro_peticion.delete(0, tk.END)
        self.entry_fecha_desde.delete(0, tk.END)
        self.entry_fecha_hasta.delete(0, tk.END)
        self.cargar_registros()

    def seleccionar_registro(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        if not valores:
            return

        self.cargar_formulario_desde_valores(valores)

    def abrir_registro_doble_click(self, event=None):
        item_id = self.tree.identify_row(event.y) if event else None
        if item_id:
            self.tree.selection_set(item_id)
            item = self.tree.item(item_id)
            valores = item["values"]
            if valores:
                self.cargar_formulario_desde_valores(valores)
                self.actualizar_estado(f"Registro ID {valores[0]} abierto con doble clic.")

    def cargar_formulario_desde_valores(self, valores):
        self.selected_id = valores[0]
        self.var_id.set(valores[0])
        self.var_fecha.set(valores[1])
        self.var_nombre.set(valores[2])
        self.var_numero_peticion.set(valores[3])

        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_descripcion.insert("1.0", valores[4])

        self.txt_respuesta.delete("1.0", tk.END)
        self.txt_respuesta.insert("1.0", valores[5])

    def validar_campos(self):
        fecha = self.var_fecha.get().strip()
        nombre = self.var_nombre.get().strip()
        numero_peticion = self.var_numero_peticion.get().strip()
        descripcion = self.txt_descripcion.get("1.0", tk.END).strip()
        respuesta = self.txt_respuesta.get("1.0", tk.END).strip()

        if not fecha or not nombre or not numero_peticion or not descripcion or not respuesta:
            messagebox.showwarning("Campos obligatorios", "Todos los campos son obligatorios.")
            return None

        if not self.validar_fecha(fecha):
            messagebox.showerror("Fecha incorrecta", "La fecha debe tener formato YYYY-MM-DD.")
            return None

        return fecha, nombre, numero_peticion, descripcion, respuesta

    def guardar_registro(self):
        datos = self.validar_campos()
        if not datos:
            return

        fecha, nombre, numero_peticion, descripcion, respuesta = datos

        self.cursor.execute("""
            INSERT INTO plantillas (fecha, nombre, numero_peticion, descripcion, respuesta)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, nombre, numero_peticion, descripcion, respuesta))
        self.conn.commit()

        nuevo_id = self.cursor.lastrowid
        self.cargar_registros()
        self.limpiar_formulario()
        self.actualizar_estado(f"Plantilla guardada correctamente con ID {nuevo_id}.")
        messagebox.showinfo("Guardado", f"Plantilla guardada correctamente con ID {nuevo_id}.")

    def modificar_registro(self):
        if not self.selected_id:
            messagebox.showwarning("Selección requerida", "Selecciona un registro para modificar.")
            return

        datos = self.validar_campos()
        if not datos:
            return

        fecha, nombre, numero_peticion, descripcion, respuesta = datos

        self.cursor.execute("""
            UPDATE plantillas
            SET fecha = ?, nombre = ?, numero_peticion = ?, descripcion = ?, respuesta = ?
            WHERE id = ?
        """, (fecha, nombre, numero_peticion, descripcion, respuesta, self.selected_id))
        self.conn.commit()

        self.cargar_registros()
        self.actualizar_estado(f"Registro ID {self.selected_id} modificado correctamente.")
        messagebox.showinfo("Modificado", f"Registro ID {self.selected_id} modificado correctamente.")

    def eliminar_registro(self):
        if not self.selected_id:
            messagebox.showwarning("Selección requerida", "Selecciona un registro para eliminar.")
            return

        confirmar = messagebox.askyesno("Confirmar borrado", f"¿Deseas eliminar el registro ID {self.selected_id}?")
        if not confirmar:
            return

        eliminado = self.selected_id
        self.cursor.execute("DELETE FROM plantillas WHERE id = ?", (self.selected_id,))
        self.conn.commit()

        self.cargar_registros()
        self.limpiar_formulario()
        self.actualizar_estado(f"Registro ID {eliminado} eliminado correctamente.")
        messagebox.showinfo("Eliminado", f"Registro ID {eliminado} eliminado correctamente.")

    def limpiar_formulario(self):
        self.selected_id = None
        self.var_id.set("")
        self.var_fecha.set(datetime.now().strftime("%Y-%m-%d"))
        self.var_nombre.set("")
        self.var_numero_peticion.set("")
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_respuesta.delete("1.0", tk.END)

        seleccion = self.tree.selection()
        if seleccion:
            self.tree.selection_remove(seleccion)

    def cerrar(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PlantillasApp(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()