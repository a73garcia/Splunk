import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime

ARCHIVO_JSON = "busquedas_splunk.json"

COLORES_PREDEFINIDOS = [
    "#FFCDD2",  # rojo suave
    "#F8BBD0",  # rosa
    "#E1BEE7",  # morado suave
    "#D1C4E9",  # lila
    "#BBDEFB",  # azul suave
    "#C8E6C9",  # verde suave
    "#FFF9C4",  # amarillo suave
]


class AppBusquedasSplunk:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de búsquedas Splunk")
        self.root.geometry("1250x700")
        self.root.minsize(1050, 620)

        self.busquedas = []
        self.id_actual = None

        self.crear_interfaz()
        self.cargar_busquedas()
        self.refrescar_tabla()

    # =========================
    # Persistencia JSON
    # =========================
    def cargar_busquedas(self):
        if os.path.exists(ARCHIVO_JSON):
            try:
                with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
                    self.busquedas = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo JSON:\n{e}")
                self.busquedas = []
        else:
            self.busquedas = []

    def guardar_busquedas_en_archivo(self):
        try:
            with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
                json.dump(self.busquedas, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo JSON:\n{e}")

    def generar_nuevo_id(self):
        if not self.busquedas:
            return 1
        return max(item["id"] for item in self.busquedas) + 1

    # =========================
    # Interfaz
    # =========================
    def crear_interfaz(self):
        frame_principal = ttk.Frame(self.root, padding=10)
        frame_principal.pack(fill="both", expand=True)

        # Ahora el formulario es más grande
        frame_izq = ttk.LabelFrame(frame_principal, text="Formulario", padding=10)
        frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Búsquedas guardadas más pequeño
        frame_der = ttk.LabelFrame(frame_principal, text="Búsquedas guardadas", padding=10)
        frame_der.pack(side="left", fill="both", expand=False)
        frame_der.config(width=430)
        frame_der.pack_propagate(False)

        # -------------------------
        # FORMULARIO
        # -------------------------
        ttk.Label(frame_izq, text="Nombre de la búsqueda:").pack(anchor="w", pady=(0, 5))
        self.entry_nombre = ttk.Entry(frame_izq)
        self.entry_nombre.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_izq, text="Descripción:").pack(anchor="w", pady=(0, 5))
        self.text_descripcion = tk.Text(frame_izq, height=4, wrap="word")
        self.text_descripcion.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_izq, text="Tecnología:").pack(anchor="w", pady=(0, 5))
        self.entry_tecnologia = ttk.Entry(frame_izq)
        self.entry_tecnologia.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_izq, text="Fecha:").pack(anchor="w", pady=(0, 5))
        self.entry_fecha = ttk.Entry(frame_izq)
        self.entry_fecha.pack(fill="x", pady=(0, 10))
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(frame_izq, text="Color:").pack(anchor="w", pady=(0, 5))

        frame_color = ttk.Frame(frame_izq)
        frame_color.pack(fill="x", pady=(0, 8))

        self.color_var = tk.StringVar(value=COLORES_PREDEFINIDOS[4])
        self.entry_color = ttk.Entry(frame_color, textvariable=self.color_var, width=22)
        self.entry_color.pack(side="left", fill="x", expand=True)

        ttk.Button(frame_color, text="Elegir color", command=self.elegir_color).pack(side="left", padx=(5, 0))

        ttk.Label(frame_izq, text="Paleta rápida (7 colores):").pack(anchor="w", pady=(5, 5))
        frame_paleta = ttk.Frame(frame_izq)
        frame_paleta.pack(anchor="w", fill="x", pady=(0, 10))

        for color in COLORES_PREDEFINIDOS:
            lbl = tk.Label(
                frame_paleta,
                bg=color,
                width=4,
                height=2,
                relief="solid",
                bd=1,
                cursor="hand2"
            )
            lbl.pack(side="left", padx=4)
            lbl.bind("<Button-1>", lambda event, c=color: self.seleccionar_color_predefinido(c))

        ttk.Label(frame_izq, text="Consulta Splunk:").pack(anchor="w", pady=(0, 5))
        self.text_consulta = tk.Text(frame_izq, height=13, wrap="word")
        self.text_consulta.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Label(frame_izq, text="Vista previa color:").pack(anchor="w", pady=(5, 5))
        self.label_preview = tk.Label(
            frame_izq,
            text="      ",
            bg=self.color_var.get(),
            relief="solid",
            bd=1
        )
        self.label_preview.pack(anchor="w", ipadx=35, ipady=10, pady=(0, 10))

        frame_botones = ttk.Frame(frame_izq)
        frame_botones.pack(fill="x", pady=(10, 0))

        ttk.Button(frame_botones, text="Nuevo", command=self.nuevo_registro).pack(side="left", padx=(0, 5))
        ttk.Button(frame_botones, text="Guardar", command=self.guardar_registro).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar", command=self.eliminar_registro).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Copiar consulta", command=self.copiar_consulta).pack(side="left", padx=5)

        self.color_var.trace_add("write", self.actualizar_preview_color)

        # -------------------------
        # BÚSQUEDAS GUARDADAS
        # -------------------------
        frame_filtro = ttk.Frame(frame_der)
        frame_filtro.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_filtro, text="Buscar:").pack(side="left")
        self.entry_filtro = ttk.Entry(frame_filtro)
        self.entry_filtro.pack(side="left", fill="x", expand=True, padx=(5, 5))
        self.entry_filtro.bind("<KeyRelease>", lambda event: self.refrescar_tabla())

        ttk.Button(frame_filtro, text="Limpiar", command=self.limpiar_filtro).pack(side="left")

        columnas = ("id", "nombre", "descripcion")
        self.tree = ttk.Treeview(frame_der, columns=columnas, show="headings", height=24)

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("descripcion", text="Descripción")

        self.tree.column("id", width=55, anchor="center")
        self.tree.column("nombre", width=150, anchor="w")
        self.tree.column("descripcion", width=200, anchor="w")

        scrollbar_y = ttk.Scrollbar(frame_der, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.cargar_registro_seleccionado)
        self.tree.bind("<Double-1>", self.cargar_registro_seleccionado)

    # =========================
    # Utilidades UI
    # =========================
    def seleccionar_color_predefinido(self, color):
        self.color_var.set(color)

    def elegir_color(self):
        color = colorchooser.askcolor(title="Selecciona un color")
        if color and color[1]:
            self.color_var.set(color[1])

    def actualizar_preview_color(self, *args):
        color = self.color_var.get().strip()
        try:
            self.label_preview.config(bg=color)
        except tk.TclError:
            self.label_preview.config(bg="#ffffff")

    def limpiar_filtro(self):
        self.entry_filtro.delete(0, tk.END)
        self.refrescar_tabla()

    def nuevo_registro(self):
        self.id_actual = None
        self.entry_nombre.delete(0, tk.END)
        self.text_descripcion.delete("1.0", tk.END)
        self.entry_tecnologia.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.color_var.set(COLORES_PREDEFINIDOS[4])
        self.text_consulta.delete("1.0", tk.END)

        seleccion = self.tree.selection()
        if seleccion:
            self.tree.selection_remove(seleccion)

    def copiar_consulta(self):
        consulta = self.text_consulta.get("1.0", tk.END).strip()
        if not consulta:
            messagebox.showwarning("Aviso", "No hay consulta para copiar.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(consulta)
        self.root.update()
        messagebox.showinfo("Copiado", "La consulta ha sido copiada al portapapeles.")

    # =========================
    # CRUD
    # =========================
    def guardar_registro(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.text_descripcion.get("1.0", tk.END).strip()
        tecnologia = self.entry_tecnologia.get().strip()
        fecha = self.entry_fecha.get().strip()
        color = self.color_var.get().strip()
        consulta = self.text_consulta.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showwarning("Validación", "Debes indicar un nombre.")
            return

        if not descripcion:
            messagebox.showwarning("Validación", "Debes indicar una descripción.")
            return

        if not tecnologia:
            messagebox.showwarning("Validación", "Debes indicar una tecnología.")
            return

        if not fecha:
            messagebox.showwarning("Validación", "Debes indicar una fecha.")
            return

        if not self.es_fecha_valida(fecha):
            messagebox.showwarning("Validación", "La fecha no es válida. Usa formato YYYY-MM-DD.")
            return

        if not consulta:
            messagebox.showwarning("Validación", "Debes escribir una consulta.")
            return

        if not color:
            color = COLORES_PREDEFINIDOS[4]

        if not self.es_color_valido(color):
            messagebox.showwarning("Validación", "El color no es válido. Usa formato tipo #AABBCC.")
            return

        if self.id_actual is None:
            nuevo = {
                "id": self.generar_nuevo_id(),
                "nombre": nombre,
                "descripcion": descripcion,
                "tecnologia": tecnologia,
                "fecha": fecha,
                "color": color,
                "consulta": consulta
            }
            self.busquedas.append(nuevo)
            messagebox.showinfo("Guardado", "Búsqueda guardada correctamente.")
        else:
            for item in self.busquedas:
                if item["id"] == self.id_actual:
                    item["nombre"] = nombre
                    item["descripcion"] = descripcion
                    item["tecnologia"] = tecnologia
                    item["fecha"] = fecha
                    item["color"] = color
                    item["consulta"] = consulta
                    break
            messagebox.showinfo("Actualizado", "Búsqueda actualizada correctamente.")

        self.guardar_busquedas_en_archivo()
        self.refrescar_tabla()
        self.nuevo_registro()

    def eliminar_registro(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Selecciona una búsqueda para eliminar.")
            return

        item_id = int(self.tree.item(seleccion[0], "values")[0])

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Seguro que quieres eliminar esta búsqueda?"
        )
        if not confirmar:
            return

        self.busquedas = [item for item in self.busquedas if item["id"] != item_id]
        self.guardar_busquedas_en_archivo()
        self.refrescar_tabla()
        self.nuevo_registro()
        messagebox.showinfo("Eliminado", "Búsqueda eliminada correctamente.")

    def cargar_registro_seleccionado(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            return

        valores = self.tree.item(seleccion[0], "values")
        if not valores:
            return

        item_id = int(valores[0])

        for item in self.busquedas:
            if item["id"] == item_id:
                self.id_actual = item["id"]

                self.entry_nombre.delete(0, tk.END)
                self.entry_nombre.insert(0, item.get("nombre", ""))

                self.text_descripcion.delete("1.0", tk.END)
                self.text_descripcion.insert("1.0", item.get("descripcion", ""))

                self.entry_tecnologia.delete(0, tk.END)
                self.entry_tecnologia.insert(0, item.get("tecnologia", ""))

                self.entry_fecha.delete(0, tk.END)
                self.entry_fecha.insert(0, item.get("fecha", ""))

                self.color_var.set(item.get("color", COLORES_PREDEFINIDOS[4]))

                self.text_consulta.delete("1.0", tk.END)
                self.text_consulta.insert("1.0", item.get("consulta", ""))
                break

    # =========================
    # Tabla
    # =========================
    def refrescar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtro = self.entry_filtro.get().strip().lower()

        for item in self.busquedas:
            nombre = item.get("nombre", "")
            descripcion = item.get("descripcion", "")
            tecnologia = item.get("tecnologia", "")
            fecha = item.get("fecha", "")
            color = item.get("color", COLORES_PREDEFINIDOS[4])
            consulta = item.get("consulta", "")

            texto_busqueda = f"{nombre} {descripcion} {tecnologia} {fecha} {color} {consulta}".lower()

            if filtro and filtro not in texto_busqueda:
                continue

            tag_name = f"color_{item['id']}"
            self.tree.insert(
                "",
                "end",
                values=(item["id"], nombre, descripcion),
                tags=(tag_name,)
            )
            self.tree.tag_configure(tag_name, background=color)

    # =========================
    # Validaciones
    # =========================
    def es_color_valido(self, color):
        if not color.startswith("#"):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

    def es_fecha_valida(self, fecha):
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            return True
        except ValueError:
            return False


def main():
    root = tk.Tk()
    app = AppBusquedasSplunk(root)
    root.mainloop()


if __name__ == "__main__":
    main()