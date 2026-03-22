tyle='Card.TFrame')
        top.pack(fill='x', pady=(0, 10))
        ttk.Button(top, text='◀', width=4, command=self._prev_month, style='Secondary.TButton').pack(side='left')
        ttk.Label(top, textvariable=self.header_var, style='Section.TLabel').pack(side='left', expand=True, padx=12)
        ttk.Button(top, text='▶', width=4, command=self._next_month, style='Secondary.TButton').pack(side='right')

        self.days_frame = ttk.Frame(self.body, style='Card.TFrame')
        self.days_frame.pack()

        bottom = ttk.Frame(self.body, style='Card.TFrame')
        bottom.pack(fill='x', pady=(10, 0))
        ttk.Button(bottom, text='Hoy', command=self._select_today, style='Primary.TButton').pack(side='left')
        ttk.Button(bottom, text='Cancelar', command=self.destroy, style='Secondary.TButton').pack(side='right')

    def _draw_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.header_var.set(f"{calendar.month_name[self.month].capitalize()} {self.year}")

        week_days = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        for col, day in enumerate(week_days):
            ttk.Label(self.days_frame, text=day, width=4, anchor='center', style='Muted.TLabel').grid(row=0, column=col, padx=3, pady=3)

        month_cal = calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)
        today = datetime.now()
        for row_idx, week in enumerate(month_cal, start=1):
            for col_idx, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text=' ', width=4, style='Card.TLabel').grid(row=row_idx, column=col_idx, padx=3, pady=3)
                    continue
                date_str = f'{self.year:04d}-{self.month:02d}-{day:02d}'
                style = 'Calendar.TButton'
                if day == self.selected_day:
                    style = 'CalendarSelected.TButton'
                elif self.year == today.year and self.month == today.month and day == today.day:
                    style = 'CalendarToday.TButton'
                ttk.Button(
                    self.days_frame,
                    text=str(day),
                    width=4,
                    style=style,
                    command=lambda ds=date_str, d=day: self._select(ds, d)
                ).grid(row=row_idx, column=col_idx, padx=3, pady=3)

    def _select(self, date_str, day):
        self.selected_day = day
        if self.callback:
            self.callback(date_str)
        self.destroy()

    def _select_today(self):
        today = datetime.now().strftime(DATE_FORMAT)
        if self.callback:
            self.callback(today)
        self.destroy()

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._draw_calendar()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._draw_calendar()


class TrabajoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Gestión de trabajo')
        self.geometry('1380x860')
        self.minsize(1180, 760)
        self.configure(bg=COLORS['bg'])

        self.csv_manager = CSVManager(CSV_FILE)
        self.current_frame = None
        self.last_search_state = {'fecha': '', 'tipo': 'Todos', 'keyword': ''}

        self._configure_styles()
        self._build_header()
        self.show_main_menu()

    def _configure_styles(self):
        style = ttk.Style(self)
        for theme in ('vista', 'clam', 'alt', 'default'):
            if theme in style.theme_names():
                try:
                    style.theme_use(theme)
                    break
                except Exception:
                    pass

        style.configure('.', font=('Segoe UI', 10))
        style.configure('App.TFrame', background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['panel'])
        style.configure('Card.TLabelframe', background=COLORS['panel'])
        style.configure('Card.TLabelframe.Label', background=COLORS['panel'], foreground=COLORS['primary_dark'], font=('Segoe UI', 10, 'bold'))
        style.configure('Header.TLabel', background=COLORS['bg'], foreground=COLORS['primary_dark'], font=('Segoe UI', 22, 'bold'))
        style.configure('Section.TLabel', background=COLORS['panel'], foreground=COLORS['primary_dark'], font=('Segoe UI', 14, 'bold'))
        style.configure('Card.TLabel', background=COLORS['panel'], foreground=COLORS['text'])
        style.configure('Muted.TLabel', background=COLORS['panel'], foreground=COLORS['muted'])
        style.configure('Badge.TLabel', background=COLORS['header_light'], foreground=COLORS['primary_dark'], padding=(10, 6))

        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), padding=(12, 8))
        style.map('Primary.TButton', background=[('active', COLORS['primary'])], foreground=[('active', '#FFFFFF')])

        style.configure('Secondary.TButton', padding=(10, 8))
        style.configure('Danger.TButton', padding=(10, 8))

        style.configure('Treeview', rowheight=28, font=('Segoe UI', 10), fieldbackground=COLORS['panel'])
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', COLORS['select'])], foreground=[('selected', COLORS['text'])])

        style.configure('Calendar.TButton', padding=(4, 4))
        style.configure('CalendarToday.TButton', padding=(4, 4))
        style.configure('CalendarSelected.TButton', padding=(4, 4))

    def _build_header(self):
        wrapper = ttk.Frame(self, style='App.TFrame', padding=(16, 14))
        wrapper.pack(fill='x')

        left = ttk.Frame(wrapper, style='App.TFrame')
        left.pack(side='left', fill='x', expand=True)
        ttk.Label(left, text='Aplicación de gestión de trabajo', style='Header.TLabel').pack(anchor='w')
        ttk.Label(left, text='Registra peticiones e incidencias, filtra información y exporta a Excel.', style='Muted.TLabel').pack(anchor='w', pady=(2, 0))

        right = ttk.Frame(wrapper, style='App.TFrame')
        right.pack(side='right')
        self.status_var = tk.StringVar(value=f'CSV: {os.path.abspath(CSV_FILE)}')
        ttk.Label(right, textvariable=self.status_var, style='Badge.TLabel').pack(anchor='e')

    def set_content(self, frame):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame
        self.current_frame.pack(fill='both', expand=True, padx=16, pady=(0, 16))

    def _make_page(self, title, subtitle=''):
        page = ttk.Frame(self, style='App.TFrame')
        card = ttk.Frame(page, style='Card.TFrame', padding=16)
        card.pack(fill='both', expand=True)
        top = ttk.Frame(card, style='Card.TFrame')
        top.pack(fill='x', pady=(0, 10))
        ttk.Label(top, text=title, style='Section.TLabel').pack(anchor='w')
        if subtitle:
            ttk.Label(top, text=subtitle, style='Muted.TLabel').pack(anchor='w', pady=(4, 0))
        return page, card

    def back_button(self, parent, command=None):
        if command is None:
            command = self.show_main_menu
        ttk.Button(parent, text='← Retroceder', command=command, style='Secondary.TButton').pack(anchor='w', pady=(0, 10))

    def create_tree(self, parent):
        outer = ttk.Frame(parent, style='Card.TFrame')
        outer.pack(fill='both', expand=True)
        columns = ('fecha', 'numero_peticion', 'tipo', 'problema', 'resolucion', 'observaciones')
        tree = ttk.Treeview(outer, columns=columns, show='headings', height=18)
        config = {
            'fecha': ('Fecha', 100),
            'numero_peticion': ('Nº petición', 140),
            'tipo': ('Tipo', 120),
            'problema': ('Problema', 320),
            'resolucion': ('Resolución', 320),
            'observaciones': ('Observaciones', 280),
        }
        for col in columns:
            text, width = config[col]
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor='w')

        vsb = ttk.Scrollbar(outer, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(outer, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        return tree

    def shorten(self, text, size=90):
        text = (text or '').replace('\n', ' ')
        return text if len(text) <= size else text[:size - 3] + '...'

    def populate_tree(self, tree, rows):
        for item in tree.get_children():
            tree.delete(item)
        for row in rows:
            tree.insert('', 'end', iid=str(row['_id']), values=(
                row.get('fecha', ''),
                row.get('numero_peticion', ''),
                row.get('tipo', ''),
                self.shorten(row.get('problema', ''), 100),
                self.shorten(row.get('resolucion', ''), 100),
                self.shorten(row.get('observaciones', ''), 90),
            ))

    def validate_record(self, record):
        if not record['fecha'].strip():
            return 'La fecha es obligatoria.'
        try:
            datetime.strptime(record['fecha'].strip(), DATE_FORMAT)
        except ValueError:
            return 'La fecha debe tener formato AAAA-MM-DD.'
        if not record['numero_peticion'].strip():
            return 'El número de petición es obligatorio.'
        if record['tipo'] not in TIPOS:
            return 'El tipo debe ser Petición o Incidencia.'
        if not record['problema'].strip():
            return 'El campo problema es obligatorio.'
        return None

    def open_date_picker(self, var):
        DatePicker(self, initial_date=var.get().strip(), callback=lambda value: var.set(value))

    def build_form(self, parent, record=None):
        record = record or {}
        form = ttk.Frame(parent, style='Card.TFrame')

        # Top fields
        top = ttk.Frame(form, style='Card.TFrame')
        top.pack(fill='x', pady=(0, 8))

        ttk.Label(top, text='Fecha:', style='Card.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 8), pady=6)
        fecha_var = tk.StringVar(value=record.get('fecha', datetime.now().strftime(DATE_FORMAT)))
        fecha_entry = ttk.Entry(top, textvariable=fecha_var, width=18)
        fecha_entry.grid(row=0, column=1, sticky='w', pady=6)
        ttk.Button(top, text='📅', width=4, command=lambda: self.open_date_picker(fecha_var), style='Secondary.TButton').grid(row=0, column=2, padx=(6, 18), pady=6)

        ttk.Label(top, text='Número petición:', style='Card.TLabel').grid(row=0, column=3, sticky='w', padx=(0, 8), pady=6)
        num_var = tk.StringVar(value=record.get('numero_peticion', ''))
        ttk.Entry(top, textvariable=num_var, width=28).grid(row=0, column=4, sticky='w', pady=6)

        ttk.Label(top, text='Tipo:', style='Card.TLabel').grid(row=0, column=5, sticky='w', padx=(18, 8), pady=6)
        tipo_var = tk.StringVar(value=record.get('tipo', TIPOS[0]))
        ttk.Combobox(top, textvariable=tipo_var, values=TIPOS, state='readonly', width=18).grid(row=0, column=6, sticky='w', pady=6)
        top.columnconfigure(7, weight=1)

        def labeled_text(frame, label, value, height):
            ttk.Label(frame, text=label, style='Card.TLabel').pack(anchor='w', pady=(8, 4))
            wrapper = tk.Frame(frame, bg=COLORS['border'], highlightthickness=0)
            wrapper.pack(fill='x', pady=(0, 4))
            text = tk.Text(wrapper, width=120, height=height, wrap='word', relief='flat', bd=0, font=('Segoe UI', 10), fg=COLORS['text'])
            text.pack(fill='both', expand=True, padx=1, pady=1)
            text.insert('1.0', value)
            return text

        problema_txt = labeled_text(form, 'Problema:', record.get('problema', ''), 7)
        resolucion_txt = labeled_text(form, 'Resolución:', record.get('resolucion', ''), 9)
        observaciones_txt = labeled_text(form, 'Observaciones:', record.get('observaciones', ''), 7)

        def get_record():
            return {
                'fecha': fecha_var.get().strip(),
                'numero_peticion': num_var.get().strip(),
                'tipo': tipo_var.get().strip(),
                'problema': problema_txt.get('1.0', 'end-1c'),
                'resolucion': resolucion_txt.get('1.0', 'end-1c'),
                'observaciones': observaciones_txt.get('1.0', 'end-1c'),
            }

        return form, get_record

    def show_main_menu(self):
        page, card = self._make_page('Menú principal', 'Accede a los registros del día, añade, modifica, elimina, busca o exporta información.')

        stats = ttk.Frame(card, style='Card.TFrame')
        stats.pack(fill='x', pady=(8, 18))
        rows = self.csv_manager.read_all()
        today = datetime.now().strftime(DATE_FORMAT)
        total_hoy = len([r for r in rows if r.get('fecha') == today])
        total_peticiones = len([r for r in rows if r.get('tipo') == 'Petición'])
        total_incidencias = len([r for r in rows if r.get('tipo') == 'Incidencia'])
        for text in [f'Registros totales: {len(rows)}', f'Hoy: {total_hoy}', f'Peticiones: {total_peticiones}', f'Incidencias: {total_incidencias}']:
            ttk.Label(stats, text=text, style='Badge.TLabel').pack(side='left', padx=(0, 10))

        grid = ttk.Frame(card, style='Card.TFrame')
        grid.pack(fill='both', expand=True)
        buttons = [
            ('Registros del día', self.show_day_records),
            ('Añadir nuevo registro', self.show_add_record),
            ('Modificar registro', self.show_modify_record_list),
            ('Borrar registro', self.show_delete_record_list),
            ('Búsqueda avanzada', self.show_search_records),
            ('Exportar a Excel', self.export_to_excel),
            ('Salir', self.destroy),
        ]
        for i, (text, cmd) in enumerate(buttons):
            btn = ttk.Button(grid, text=text, command=cmd, style='Primary.TButton')
            r, c = divmod(i, 2)
            btn.grid(row=r, column=c, sticky='nsew', padx=12, pady=12, ipadx=20, ipady=16)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.set_content(page)

    def show_day_records(self):
        page, card = self._make_page('Registros del día', 'Vista rápida de las peticiones e incidencias de la fecha actual.')
        self.back_button(card)

        today = datetime.now().strftime(DATE_FORMAT)
        rows = [r for r in self.csv_manager.read_all() if r.get('fecha') == today]
        info = ttk.Frame(card, style='Card.TFrame')
        info.pack(fill='x', pady=(0, 10))
        ttk.Label(info, text=f'Fecha actual: {today}', style='Badge.TLabel').pack(side='left', padx=(0, 10))
        ttk.Label(info, text=f'Total registros: {len(rows)}', style='Badge.TLabel').pack(side='left')

        tree = self.create_tree(card)
        self.populate_tree(tree, rows)

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(10, 0))
        ttk.Button(actions, text='Ver detalle', command=lambda: self._view_selected_from_tree(tree, fallback=self.show_day_records), style='Secondary.TButton').pack(side='left')
        ttk.Button(actions, text='Refrescar', command=self.show_day_records, style='Primary.TButton').pack(side='right')

        self.set_content(page)

    def show_add_record(self):
        page, card = self._make_page('Añadir nuevo registro', 'Completa los datos y guarda el registro en el CSV.')
        self.back_button(card)
        form, get_record = self.build_form(card)
        form.pack(fill='x')

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(14, 0))

        def save_record():
            record = get_record()
            error = self.validate_record(record)
            if error:
                messagebox.showerror('Error de validación', error)
                return
            self.csv_manager.add(record)
            messagebox.showinfo('Guardado', 'Registro añadido correctamente.')
            self.show_main_menu()

        ttk.Button(actions, text='Guardar', command=save_record, style='Primary.TButton').pack(side='left')
        ttk.Button(actions, text='Limpiar', command=self.show_add_record, style='Secondary.TButton').pack(side='left', padx=8)
        self.set_content(page)

    def show_modify_record_list(self):
        page, card = self._make_page('Modificar registro', 'Selecciona un registro para editar su contenido.')
        self.back_button(card)
        rows = self.csv_manager.read_all()
        tree = self.create_tree(card)
        self.populate_tree(tree, rows)

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(10, 0))

        def edit_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning('Aviso', 'Seleccione un registro para editar.')
                return
            row_id = int(selection[0])
            selected = next((r for r in rows if r['_id'] == row_id), None)
            if selected is None:
                messagebox.showerror('Error', 'No se encontró el registro seleccionado.')
                return
            self.show_edit_form(selected)

        ttk.Button(actions, text='Editar seleccionado', command=edit_selected, style='Primary.TButton').pack(side='left')
        ttk.Button(actions, text='Ver detalle', command=lambda: self._view_selected_from_tree(tree, fallback=self.show_modify_record_list), style='Secondary.TButton').pack(side='left', padx=8)
        ttk.Button(actions, text='Refrescar', command=self.show_modify_record_list, style='Secondary.TButton').pack(side='right')
        self.set_content(page)

    def show_edit_form(self, record):
        page, card = self._make_page('Editar registro', 'Modifica la información y guarda los cambios.')
        self.back_button(card, self.show_modify_record_list)
        form, get_record = self.build_form(card, record)
        form.pack(fill='x')

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(14, 0))

        def save_changes():
            updated = get_record()
            error = self.validate_record(updated)
            if error:
                messagebox.showerror('Error de validación', error)
                return
            self.csv_manager.update(record['_id'], updated)
            messagebox.showinfo('Actualizado', 'Registro modificado correctamente.')
            self.show_modify_record_list()

        ttk.Button(actions, text='Guardar cambios', command=save_changes, style='Primary.TButton').pack(side='left')
        self.set_content(page)

    def show_delete_record_list(self):
        page, card = self._make_page('Borrar registro', 'Selecciona un registro y elimínalo del CSV.')
        self.back_button(card)
        rows = self.csv_manager.read_all()
        tree = self.create_tree(card)
        self.populate_tree(tree, rows)

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(10, 0))

        def delete_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning('Aviso', 'Seleccione un registro para borrar.')
                return
            row_id = int(selection[0])
            selected = next((r for r in rows if r['_id'] == row_id), None)
            if selected is None:
                messagebox.showerror('Error', 'No se encontró el registro seleccionado.')
                return
            resumen = f"{selected.get('fecha', '')} | {selected.get('numero_peticion', '')} | {selected.get('tipo', '')}"
            if not messagebox.askyesno('Confirmar borrado', f'¿Desea borrar este registro?\n\n{resumen}'):
                return
            self.csv_manager.delete(row_id)
            messagebox.showinfo('Borrado', 'Registro eliminado correctamente.')
            self.show_delete_record_list()

        ttk.Button(actions, text='Borrar seleccionado', command=delete_selected, style='Danger.TButton').pack(side='left')
        ttk.Button(actions, text='Ver detalle', command=lambda: self._view_selected_from_tree(tree, fallback=self.show_delete_record_list), style='Secondary.TButton').pack(side='left', padx=8)
        ttk.Button(actions, text='Refrescar', command=self.show_delete_record_list, style='Secondary.TButton').pack(side='right')
        self.set_content(page)

    def filter_rows(self, rows, fecha='', tipo='Todos', keyword=''):
        fecha = (fecha or '').strip()
        tipo = (tipo or 'Todos').strip()
        keyword = (keyword or '').strip().lower()
        filtered = []
        for row in rows:
            if fecha and row.get('fecha', '').strip() != fecha:
                continue
            if tipo != 'Todos' and row.get('tipo', '').strip() != tipo:
                continue
            if keyword:
                search_blob = ' '.join((row.get(field, '') or '') for field in FIELDNAMES).lower()
                if keyword not in search_blob:
                    continue
            filtered.append(row)
        return filtered

    def show_search_records(self):
        page, card = self._make_page('Búsqueda avanzada', 'Filtra por fecha, tipo o palabra clave en todos los campos.')
        self.back_button(card)

        filters = ttk.LabelFrame(card, text='Filtros', style='Card.TLabelframe', padding=12)
        filters.pack(fill='x', pady=(0, 10))

        fecha_var = tk.StringVar(value=self.last_search_state.get('fecha', ''))
        tipo_var = tk.StringVar(value=self.last_search_state.get('tipo', 'Todos'))
        keyword_var = tk.StringVar(value=self.last_search_state.get('keyword', ''))

        ttk.Label(filters, text='Fecha:', style='Card.TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(filters, textvariable=fecha_var, width=18).grid(row=0, column=1, sticky='w', padx=5, pady=6)
        ttk.Button(filters, text='📅', width=4, command=lambda: self.open_date_picker(fecha_var), style='Secondary.TButton').grid(row=0, column=2, sticky='w', padx=(0, 12), pady=6)

        ttk.Label(filters, text='Tipo:', style='Card.TLabel').grid(row=0, column=3, sticky='w', padx=5, pady=6)
        ttk.Combobox(filters, textvariable=tipo_var, values=['Todos'] + TIPOS, state='readonly', width=18).grid(row=0, column=4, sticky='w', padx=5, pady=6)

        ttk.Label(filters, text='Palabra clave:', style='Card.TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=6)
        ttk.Entry(filters, textvariable=keyword_var, width=60).grid(row=1, column=1, columnspan=4, sticky='we', padx=5, pady=6)
        filters.columnconfigure(4, weight=1)

        tree = self.create_tree(card)

        footer = ttk.Frame(card, style='Card.TFrame')
        footer.pack(fill='x', pady=(10, 0))
        result_var = tk.StringVar(value='Resultados: 0')
        ttk.Label(footer, textvariable=result_var, style='Badge.TLabel').pack(side='left')

        def perform_search():
            self.last_search_state = {'fecha': fecha_var.get().strip(), 'tipo': tipo_var.get().strip(), 'keyword': keyword_var.get().strip()}
            rows = self.csv_manager.read_all()
            filtered = self.filter_rows(rows, fecha_var.get(), tipo_var.get(), keyword_var.get())
            self.populate_tree(tree, filtered)
            result_var.set(f'Resultados: {len(filtered)}')

        actions = ttk.Frame(card, style='Card.TFrame')
        actions.pack(fill='x', pady=(10, 0))
        ttk.Button(actions, text='Buscar', command=perform_search, style='Primary.TButton').pack(side='left')
        ttk.Button(actions, text='Limpiar filtros', command=lambda: [fecha_var.set(''), tipo_var.set('Todos'), keyword_var.set(''), perform_search()], style='Secondary.TButton').pack(side='left', padx=8)
        ttk.Button(actions, text='Ver detalle', command=lambda: self._view_selected_from_tree(tree, fallback=self.show_search_records), style='Secondary.TButton').pack(side='left')
        ttk.Button(actions, text='Exportar resultados a Excel', command=lambda: self.export_to_excel(self.filter_rows(self.csv_manager.read_all(), fecha_var.get(), tipo_var.get(), keyword_var.get())), style='Primary.TButton').pack(side='right')

        perform_search()
        self.set_content(page)

    def _view_selected_from_tree(self, tree, fallback=None):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning('Aviso', 'Seleccione un registro para ver el detalle.')
            return
        row_id = int(selection[0])
        rows = self.csv_manager.read_all()
        record = next((r for r in rows if r['_id'] == row_id), None)
        if record is None:
            messagebox.showerror('Error', 'No se encontró el registro.')
            return
        self.show_record_detail(record, fallback=fallback)

    def show_record_detail(self, record, fallback=None):
        page, card = self._make_page('Detalle del registro', 'Visualización completa de todos los campos.')
        self.back_button(card, fallback or self.show_search_records)

        info = ttk.Frame(card, style='Card.TFrame')
        info.pack(fill='both', expand=True)

        fields = [
            ('Fecha', record.get('fecha', '')),
            ('Número petición', record.get('numero_peticion', '')),
            ('Tipo', record.get('tipo', '')),
            ('Problema', record.get('problema', '')),
            ('Resolución', record.get('resolucion', '')),
            ('Observaciones', record.get('observaciones', '')),
        ]

        for i, (label, value) in enumerate(fields):
            ttk.Label(info, text=f'{label}:', style='Card.TLabel').grid(row=i, column=0, sticky='nw', padx=(0, 10), pady=6)
            wrapper = tk.Frame(info, bg=COLORS['border'], highlightthickness=0)
            wrapper.grid(row=i, column=1, sticky='nsew', pady=6)
            height = max(2, min(10, value.count('\n') + 2))
            text = tk.Text(wrapper, width=100, height=height, wrap='word', relief='flat', bd=0, font=('Segoe UI', 10))
            text.pack(fill='both', expand=True, padx=1, pady=1)
            text.insert('1.0', value)
            text.configure(state='disabled')
        info.columnconfigure(1, weight=1)
        self.set_content(page)

    def export_to_excel(self, rows=None):
        if not OPENPYXL_AVAILABLE:
            messagebox.showerror('Exportación no disponible', 'No se pudo cargar openpyxl. Instálalo con: pip install openpyxl')
            return

        all_rows = self.csv_manager.read_all() if rows is None else rows
        cleaned_rows = [{k: row.get(k, '') for k in FIELDNAMES} for row in all_rows]
        if not cleaned_rows:
            messagebox.showwarning('Sin datos', 'No hay registros para exportar.')
            return

        filename = filedialog.asksaveasfilename(
            title='Guardar archivo Excel',
            defaultextension='.xlsx',
            filetypes=[('Excel', '*.xlsx')],
            initialfile=f'gestion_trabajo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        if not filename:
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = 'Registros'

            thin = Side(style='thin', color='D6DCE5')
            header_fill = PatternFill('solid', fgColor='1F4E79')
            header_font = Font(color='FFFFFF', bold=True)
            wrap_alignment = Alignment(vertical='top', wrap_text=True)
            center_alignment = Alignment(horizontal='center', vertical='center')

            ws.append(['Fecha', 'Nº petición', 'Tipo', 'Problema', 'Resolución', 'Observaciones'])
            for row in cleaned_rows:
                ws.append([
                    row['fecha'], row['numero_peticion'], row['tipo'], row['problema'], row['resolucion'], row['observaciones']
                ])

            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_alignment
                cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=6):
                for cell in row:
                    cell.alignment = wrap_alignment
                    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

            widths = {1: 14, 2: 18, 3: 14, 4: 42, 5: 48, 6: 42}
            for col, width in widths.items():
                ws.column_dimensions[get_column_letter(col)].width = width

            for r in range(2, ws.max_row + 1):
                ws.row_dimensions[r].height = 42

            ws.freeze_panes = 'A2'
            ws.auto_filter.ref = ws.dimensions

            summary = wb.create_sheet('Resumen')
            summary['A1'] = 'Resumen de exportación'
            summary['A1'].font = Font(size=14, bold=True, color='1F4E79')
            summary['A3'] = 'Fecha exportación'
            summary['B3'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            summary['A4'] = 'Total registros'
            summary['B4'] = len(cleaned_rows)
            summary['A5'] = 'Total peticiones'
            summary['B5'] = len([r for r in cleaned_rows if r['tipo'] == 'Petición'])
            summary['A6'] = 'Total incidencias'
            summary['B6'] = len([r for r in cleaned_rows if r['tipo'] == 'Incidencia'])
            summary['A8'] = 'Origen CSV'
            summary['B8'] = os.path.abspath(CSV_FILE)
            summary.column_dimensions['A'].width = 22
            summary.column_dimensions['B'].width = 42

            wb.save(filename)
            messagebox.showinfo('Exportación completada', f'Archivo Excel guardado correctamente.\n\n{filename}')
        except Exception as e:
            messagebox.showerror('Error al exportar', f'No se pudo exportar a Excel.\n\n{e}')


if __name__ == '__main__':
    app = TrabajoApp()
    app.mainloop()