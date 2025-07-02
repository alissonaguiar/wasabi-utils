# wasabi_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Listbox, MULTIPLE
import subprocess
import os
import sys
import threading
import time
from jproperties import Properties

class ToolTip:
    def __init__(self, widget, delay=300):
        self.widget = widget
        self.delay = delay  # delay em milissegundos
        self.tip_window = None
        self.id = None
        self.text = ""
        self.active_item = None

    def show_tip(self, text, x=None, y=None):
        self.text = text
        self.x = x
        self.y = y
        self.cancel_scheduled()
        self.id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.x if self.x is not None else self.widget.winfo_pointerx() + 10
            y = self.y if self.y is not None else self.widget.winfo_pointery() + 10
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                tw,
                text=self.text,
                justify=tk.LEFT,
                background="#ffffe0",
                foreground="#000000",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Arial", 10),
                padx=5,
                pady=3
            )
            label.pack(ipadx=1)
        except Exception as e:
            print("Erro no tooltip:", e)

    def hide_tip(self):
        self.cancel_scheduled()
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def cancel_scheduled(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

class WasabiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wasabi Explorer")
        self.root.geometry("800x600")
        
        # Configurações iniciais
        self.current_path = ''
        self.credentials = self.load_credentials()
        self.sort_column = None
        self.sort_reverse = False
        
        # Cache de arquivos
        self.file_cache = {}  # {path: {'folders': [], 'files': [], 'timestamp': float}}
        self.cache_expiration = 60  # segundos

        # Variável para controlar update automático
        self.auto_update_var = tk.BooleanVar(value=True)
        
        # Cria a interface
        self.create_widgets()
        
        # Mostrar splash screen após a criação da interface
        self.root.after(100, self.show_splash_screen)
        
        # Atualiza cache e lista de arquivos
        self.root.after(300, lambda: self.update_file_list(initial_load=True))
        
        # Inicia verificação periódica do cache
        self.root.after(1000 * self.cache_expiration, self.check_cache_expiration)
        
        # Configura eventos de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_splash_screen(self):
        """Mostra uma tela de splash durante o carregamento"""
        self.splash = tk.Toplevel(self.root)
        self.splash.title("Carregando")
        self.splash.geometry("300x100")
        self.splash.overrideredirect(True)  # Remove bordas da janela
        
        # Força a atualização da interface para obter dimensões corretas
        self.root.update_idletasks()
        
        # Obtém a posição e dimensões da janela principal
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        # Calcula a posição central relativa à janela principal
        x = root_x + (root_width - 300) // 2
        y = root_y + (root_height - 100) // 2
        
        # Se a janela principal ainda não tem dimensões válidas, usa o centro da tela
        if root_width <= 1 or root_height <= 1:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 100) // 2
        
        self.splash.geometry(f"+{x}+{y}")
        
        tk.Label(
            self.splash, 
            text="Carregando dados...", 
            font=("Arial", 12)
        ).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        self.splash.lift()
        self.splash.update()

    def hide_splash_screen(self):
        """Esconde a tela de splash"""
        if hasattr(self, 'splash') and self.splash:
            self.splash.destroy()
            self.splash = None

    def on_auto_update_toggle(self):
        """Callback quando checkbox de update automático muda"""
        if self.auto_update_var.get():
            self.status_var.set("Update Automático ativado")
            # Se quiser, pode chamar a atualização imediata aqui
            self.update_file_list(force_refresh=True)
        else:
            self.status_var.set("Update Automático desativado")

    def check_cache_expiration(self):
        """Verifica periodicamente se o cache expirou"""
        if not self.auto_update_var.get():
            # Se desabilitado, não faz nada e agenda nova checagem
            self.root.after(1000 * self.cache_expiration, self.check_cache_expiration)
            return
        
        current_time = time.time()
        if self.current_path in self.file_cache:
            cache_entry = self.file_cache[self.current_path]
            if current_time - cache_entry['timestamp'] > self.cache_expiration:
                # Força atualização e mostra splash
                self.show_splash_screen()
                self.update_file_list(force_refresh=True)
        
        # Agenda a próxima verificação
        self.root.after(1000 * self.cache_expiration, self.check_cache_expiration)

    def format_size(self, size_bytes):
        """Converte bytes em tamanho legível (KB, MB, etc.)"""
        try:
            size = int(size_bytes)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} PB"
        except:
            return size_bytes  # retorna como está se falhar

    def load_credentials(self):
        """Carrega as credenciais exatamente como no wasabi_util.py"""
        try:
            configs = Properties()
            with open('wasabi_credentials.properties', 'rb') as config_file:
                configs.load(config_file)

            required_keys = [
                'WASABI_ENDPOINT',
                'WASABI_REGION',
                'WASABI_ACCESS_KEY',
                'WASABI_SECRET_KEY',
                'WASABI_BUCKET'
            ]
            creds = {}
            for key in required_keys:
                value = configs.get(key)
                if not value:
                    raise ValueError(f"Chave {key} não encontrada no arquivo de configurações")
                creds[key] = value.data
            return creds

        except FileNotFoundError:
            messagebox.showerror("Erro", "Arquivo wasabi_credentials.properties não encontrado.")
            self.root.destroy()
            sys.exit(1)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler configurações: {str(e)}")
            self.root.destroy()
            sys.exit(1)

    def run_command(self, command, args):
        """Executa um comando CLI e retorna a saída"""
        try:
            cmd = [sys.executable, os.path.join('src', 'wasabi_util.py'), command] + args
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout or result.stderr
        except Exception as e:
            return f"Erro ao executar comando: {str(e)}"

    def list_files(self, path='', force_refresh=False):
        """Lista arquivos no caminho especificado, usando cache quando possível"""
        if path == '/':
            path = ''
        
        # Verifica se temos cache válido para este caminho
        current_time = time.time()
        cache_valid = (
            not force_refresh and 
            path in self.file_cache and 
            (current_time - self.file_cache[path]['timestamp']) <= self.cache_expiration
        )
        
        if cache_valid:
            return (
                self.file_cache[path]['folders'], 
                self.file_cache[path]['files']
            )
        
        # Busca os dados diretamente do Wasabi
        output = self.run_command('list', [path])
        folders = []
        files = []

        if "Erro" in output:
            # Tenta usar cache anterior se disponível
            if path in self.file_cache:
                return (
                    self.file_cache[path]['folders'], 
                    self.file_cache[path]['files']
                )
            return folders, files

        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            if '[Pasta]' in line:
                parts = line.split('[Pasta] ')
                if len(parts) > 1:
                    folder_name = parts[1].strip().rstrip('/')
                    folders.append(folder_name)
            elif '[Arquivo]' in line:
                parts = line.split('[Arquivo] ')
                if len(parts) > 1:
                    content = parts[1].strip()
                    if ' (' in content and content.endswith('bytes)'):
                        name_part, size_part = content.rsplit(' (', 1)
                        file_name = name_part.strip()
                        size_bytes = size_part.replace('bytes)', '').strip()
                        files.append((file_name, size_bytes))
                    else:
                        files.append((content, ''))
        
        # Atualiza o cache
        self.file_cache[path] = {
            'folders': folders,
            'files': files,
            'timestamp': time.time()
        }
        
        return folders, files

    def create_widgets(self):
        """Cria todos os componentes da interface"""
        # Barra de status
        self.status_var = tk.StringVar()
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Adiciona o estilo customizado para o cabeçalho da coluna "Nome"
        style = ttk.Style()
        style.configure("Treeview.Heading", anchor="center")  # padrão
        style.configure("LeftAlignedHeading.Treeview.Heading", anchor="w")  # novo estilo

        # Barra de navegação
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(nav_frame, text="Voltar", command=self.go_back).pack(side=tk.LEFT)
        tk.Button(nav_frame, text="Raiz", command=self.go_root).pack(side=tk.LEFT, padx=5)
        # Botão Atualizar: mostra splash e força atualização
        tk.Button(nav_frame, text="Atualizar", command=self.force_refresh).pack(side=tk.LEFT)

        # Barra de caminho
        path_frame = tk.Frame(self.root)
        path_frame.pack(fill=tk.X, padx=5)

        tk.Label(path_frame, text="Bucket:").pack(side=tk.LEFT)
        tk.Label(path_frame, text=self.credentials['WASABI_BUCKET']).pack(side=tk.LEFT, padx=5)

        self.path_var = tk.StringVar()
        tk.Label(path_frame, textvariable=self.path_var).pack(side=tk.LEFT, padx=10)

        # Lista de arquivos
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('Name', 'Size', 'Type')
        self.tree = ttk.Treeview(file_frame, columns=columns, show='headings')

        # Configuração das colunas
        self.tree.heading('Name', text='Nome', anchor='w', 
                          command=lambda: self.sort_treeview('Name', False))
        self.tree.heading('Size', text='Tamanho', anchor='center',
                          command=lambda: self.sort_treeview('Size', False))
        self.tree.heading('Type', text='Tipo', anchor='center',
                          command=lambda: self.sort_treeview('Type', False))

        # Aplica estilo à esquerda para o cabeçalho "Nome"
        self.tree.tag_configure('left_align_name', anchor='w')  # para conteúdo (redundante aqui)
        self.tree.column('Name', width=480, anchor='w')
        self.tree.column('Size', width=70, anchor='center')
        self.tree.column('Type', width=50, anchor='center')
        
        # Barra de rolagem
        vsb = ttk.Scrollbar(file_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(file_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_rowconfigure(0, weight=1)
        
        # Evento de clique duplo para entrar em pastas
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Tooltips
        self.tooltip = ToolTip(self.tree)
        self.tree.bind("<Motion>", self.on_motion)
        self.tree.bind("<Leave>", self.on_leave)
        
        # Botões de ação
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        upload_menu = tk.Menubutton(btn_frame, text="Upload", relief=tk.RAISED)
        upload_menu.menu = tk.Menu(upload_menu, tearoff=0)
        upload_menu["menu"] = upload_menu.menu

        upload_menu.menu.add_command(label="Arquivo(s)", command=self.upload_file)
        upload_menu.menu.add_command(label="Uma pasta", command=lambda: self.upload_folder(multiple=False))
        upload_menu.menu.add_command(label="Múltiplas pastas", command=lambda: self.upload_folder(multiple=True))

        upload_menu.pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Download", command=self.download_files).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Gerar Link", command=self.generate_link).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Deletar", command=self.delete_files).pack(side=tk.LEFT, padx=2)

        # Checkbox para Update Automático
        chk_auto_update = tk.Checkbutton(
            btn_frame,
            text="Update Automático",
            variable=self.auto_update_var,
            onvalue=True,
            offvalue=False,
            command=self.on_auto_update_toggle
        )
        chk_auto_update.pack(side=tk.LEFT, padx=15)

    def force_refresh(self):
        """Força a atualização da lista de arquivos mostrando o splash"""
        self.show_splash_screen()
        self.update_file_list(force_refresh=True)

    def on_motion(self, event):
        """Mostra tooltip quando o mouse se move sobre um item"""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            if self.tooltip.active_item != row_id:
                self.tooltip.hide_tip()  # Oculta imediatamente se item mudou
                self.tooltip.active_item = row_id
                item_values = self.tree.item(row_id, 'values')
                if item_values:
                    item_text = item_values[0]
                    x = self.tree.winfo_pointerx() + 10
                    y = self.tree.winfo_pointery() + 10
                    self.tooltip.show_tip(item_text, x, y)
        else:
            self.tooltip.active_item = None
            self.tooltip.hide_tip()

    def on_leave(self, event):
        """Esconde o tooltip quando o mouse sai"""
        self.tooltip.hide_tip()

    def sort_treeview(self, column, reverse):
        """Ordena a treeview pela coluna clicada"""
        # Obtém todos os itens
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # Determina o tipo de ordenação
        if column == 'Size':
            # Ordenação numérica para tamanho
            try:
                items.sort(key=lambda t: float(t[0].split()[0]) if t[0] else 0, reverse=reverse)
            except:
                items.sort(key=lambda t: t[0], reverse=reverse)
        else:
            # Ordenação alfabética para nome e tipo
            items.sort(key=lambda t: t[0], reverse=reverse)
        
        # Reorganiza os itens na treeview
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # Inverte a ordem para o próximo clique
        self.tree.heading(column, 
                         command=lambda: self.sort_treeview(column, not reverse))

    def update_file_list(self, initial_load=False, force_refresh=False):
        """Atualiza a lista de arquivos na interface"""
        try:
            folders, files = self.list_files(self.current_path, force_refresh=force_refresh)
            self.path_var.set(f"Caminho: /{self.current_path}")

            # Limpa a lista atual
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Adiciona pastas
            for folder in folders:
                self.tree.insert('', 'end', values=(folder, '', 'Pasta'))

            # Adiciona arquivos com tipo (extensão) e tamanho humanizado
            for file_name, size in files:
                # Tipo = extensão ou "desconhecido"
                if '.' in file_name:
                    file_type = file_name.rsplit('.', 1)[1].lower()
                else:
                    file_type = 'desconhecido'

                human_size = self.format_size(size)
                self.tree.insert('', 'end', values=(file_name, human_size, file_type))

            # Atualiza informação de cache na barra de status
            if self.current_path in self.file_cache:
                cache_time = time.strftime(
                    "%H:%M:%S", 
                    time.localtime(self.file_cache[self.current_path]['timestamp'])
                )
                self.status_var.set(
                    f"{len(folders)} pastas, {len(files)} arquivos | " +
                    f"Cache atualizado em: {cache_time}"
                )
            else:
                self.status_var.set(f"{len(folders)} pastas e {len(files)} arquivos listados")
            
            # Fecha splash screen após carregamento
            if initial_load or force_refresh:
                self.root.after(500, self.hide_splash_screen)
                
        except Exception as e:
            self.status_var.set(f"Erro ao listar arquivos: {str(e)}")
            if initial_load or force_refresh:
                self.root.after(500, self.hide_splash_screen)

    def invalidate_cache(self, path=None):
        """Invalida o cache para o caminho especificado ou para todos"""
        if path:
            if path in self.file_cache:
                del self.file_cache[path]
        else:
            self.file_cache.clear()

    def get_selected_items(self):
        """Retorna os itens selecionados"""
        selected = []
        for item in self.tree.selection():
            values = self.tree.item(item, 'values')
            if values:  # Garante que tem valores
                name = values[0]
                item_type = values[2]  # Tipo está na terceira coluna
                selected.append((name, item_type))
        return selected

    def go_back(self):
        """Volta para o diretório anterior"""
        if not self.current_path:
            return
            
        parts = self.current_path.split('/')
        if len(parts) > 1:
            # Remove o último nível
            self.current_path = '/'.join(parts[:-2])
        else:
            self.current_path = ''
            
        self.update_file_list()

    def go_root(self):
        """Vai para a raiz do bucket"""
        self.current_path = ''
        self.update_file_list()

    def on_double_click(self, event):
        """Entra em uma pasta ao clicar duas vezes"""
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, 'values')
            if values and values[2] == 'Pasta':  # Tipo está na terceira coluna
                folder_name = values[0]
                self.current_path += folder_name + '/'
                self.update_file_list()

    def download_files(self):
        """Faz download dos arquivos selecionados"""
        selected = self.get_selected_items()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo ou pasta")
            return
        
        dest = filedialog.askdirectory(title="Selecione a pasta de destino")
        if not dest:
            return
        
        for item, item_type in selected:
            # Pasta
            if item_type == 'Pasta':
                command = 'download'
                source = self.current_path + item + '/'
                target = os.path.join(dest, item)
                args = [source, target]
            # Arquivo
            else:
                command = 'download'
                source = self.current_path + item
                target = os.path.join(dest, item)
                args = [source, target]
            
            # Executa em thread separada
            threading.Thread(
                target=self.run_command,
                args=(command, args),
                daemon=True
            ).start()
        
        self.status_var.set("Download iniciado em segundo plano")

    def delete_files(self):
        """Deleta os arquivos selecionados"""
        selected = self.get_selected_items()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo ou pasta")
            return
        
        confirm = messagebox.askyesno(
            "Confirmação", 
            f"Tem certeza que deseja deletar {len(selected)} itens?",
            parent=self.root
        )

        if not confirm:
            return
        
        for item, item_type in selected:
            path = self.current_path + (item + '/' if item_type == 'Pasta' else item)
            threading.Thread(
                target=self.run_command,
                args=('delete', [path]),
                daemon=True
            ).start()
        
        # Invalida cache após exclusão
        self.invalidate_cache(self.current_path)
        
        self.status_var.set("Exclusão iniciada em segundo plano")
        # Atualiza a lista após um pequeno delay
        self.root.after(4000, self.update_file_list)

    def generate_link(self):
        """Gera link temporário para um arquivo"""
        selected = self.get_selected_items()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um arquivo")
            return
        
        if len(selected) > 1:
            messagebox.showwarning("Aviso", "Selecione apenas um arquivo")
            return
        
        item, item_type = selected[0]
        # Verifica se é uma pasta (tipo "Pasta")
        if item_type == 'Pasta':
            messagebox.showwarning("Aviso", "Selecione um arquivo, não uma pasta")
            return
        
        # Pede o tempo de expiração
        time_val = tk.simpledialog.askinteger(
            "Tempo de validade",
            "Tempo de validade (segundos):",
            initialvalue=3600,
            minvalue=1,
            maxvalue=86400
        )
        if not time_val:
            return
        
        # Executa o comando
        path = self.current_path + item
        output = self.run_command('link', [path, '--expires', str(time_val)])
        
        # Mostra o resultado em uma nova janela
        link_window = tk.Toplevel(self.root)
        link_window.title("Link Temporário")
        link_window.geometry("600x200")
        
        tk.Label(link_window, text="Link gerado:").pack(pady=5)
        
        text = scrolledtext.ScrolledText(link_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text.insert(tk.INSERT, output)
        text.config(state=tk.DISABLED)
        
        tk.Button(link_window, text="Fechar", command=link_window.destroy).pack(pady=5)

    def upload_file(self):
        """Faz upload de múltiplos arquivos"""
        files = filedialog.askopenfilenames(title="Selecione os arquivos")
        if not files:
            return
        
        # Pede o caminho de destino (único para todos os arquivos)
        dest = tk.simpledialog.askstring(
            "Destino",
            "Caminho de destino (deixe em branco para raiz):",
            initialvalue=self.current_path
        )
        if dest is None:  # Usuário cancelou
            return
        
        # Processa cada arquivo individualmente
        for file_path in files:
            # Obtém o nome do arquivo
            file_name = os.path.basename(file_path)
            
            # Constrói o caminho completo de destino
            if dest == '':
                full_dest = file_name
            else:
                if not dest.endswith('/'):
                    dest += '/'
                full_dest = dest + file_name
            
            # Inicia o upload em thread separada para cada arquivo
            threading.Thread(
                target=self.run_command,
                args=('upload', [file_path, full_dest]),
                daemon=True
            ).start()
        
        # Invalida cache após upload
        self.invalidate_cache(dest)
        
        self.status_var.set(f"Iniciado upload de {len(files)} arquivos")
        self.root.after(2000, self.update_file_list)

    def upload_folder(self, multiple=True):
        if not multiple:
            folder = filedialog.askdirectory(title="Selecione a pasta")
            if not folder:
                return
            folders = [folder]
            # ... o restante da lógica pode ser igual à de `start_upload`
            # Chame o `start_upload` direto, sem abrir nova janela
            dest = tk.simpledialog.askstring(
                "Destino",
                "Caminho de destino (deixe em branco para raiz):",
                initialvalue=self.current_path
            )
            if dest is None:
                return

            for folder in folders:
                folder_name = os.path.basename(folder)
                if dest == '':
                    full_dest = folder_name + '/'
                else:
                    if not dest.endswith('/'):
                        dest += '/'
                    full_dest = dest + folder_name + '/'

                threading.Thread(
                    target=self.run_command,
                    args=('upload', [folder, full_dest]),
                    daemon=True
                ).start()

                self.invalidate_cache(full_dest)

            self.status_var.set(f"Iniciado upload da pasta {folder_name}")
            self.root.after(3000, self.update_file_list)
            return
        
        """Faz upload de uma ou mais pastas mantendo a estrutura"""
        # Cria uma nova janela para seleção múltipla
        folder_window = tk.Toplevel(self.root)
        folder_window.title("Selecionar Pastas")
        folder_window.geometry("500x400")

        # Centraliza a janela em relação à janela principal
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()

        win_w = 500
        win_h = 400
        pos_x = main_x + (main_w - win_w) // 2
        pos_y = main_y + (main_h - win_h) // 2
        folder_window.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        folder_window.transient(self.root)
        folder_window.grab_set()
        
        # Frame principal
        main_frame = tk.Frame(folder_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista de pastas selecionadas
        tk.Label(main_frame, text="Pastas selecionadas:").pack(anchor=tk.W)
        folder_list = Listbox(
            main_frame, 
            selectmode=MULTIPLE,
            height=10
        )
        folder_list.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Frame de botões
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Botão para adicionar pastas
        def add_folders():
            folder = filedialog.askdirectory(title="Selecione uma pasta")
            if folder:
                folder_list.insert(tk.END, folder)
        
        # Botão para remover pastas selecionadas
        def remove_folders():
            selected = folder_list.curselection()
            for index in selected[::-1]:
                folder_list.delete(index)
        
        # Botão para iniciar o upload
        def start_upload():
            folders = folder_list.get(0, tk.END)
            if not folders:
                messagebox.showwarning("Aviso", "Selecione pelo menos uma pasta")
                return
                
            folder_window.destroy()
            
            # Pede o caminho de destino
            dest = tk.simpledialog.askstring(
                "Destino",
                "Caminho de destino (deixe em branco para raiz):",
                initialvalue=self.current_path
            )
            if dest is None:  # Usuário cancelou
                return
            
            # Processa cada pasta
            for folder in folders:
                folder_name = os.path.basename(folder)
                
                # Constrói o caminho completo de destino
                if dest == '':
                    full_dest = folder_name + '/'
                else:
                    if not dest.endswith('/'):
                        dest += '/'
                    full_dest = dest + folder_name + '/'
                
                # Inicia o upload em thread separada para cada pasta
                threading.Thread(
                    target=self.run_command,
                    args=('upload', [folder, full_dest]),
                    daemon=True
                ).start()
                
                # Invalida cache após upload
                self.invalidate_cache(full_dest)
            
            self.status_var.set(f"Iniciado upload de {len(folders)} pastas")
            self.root.after(3000, self.update_file_list)
        
        # Adiciona os botões
        tk.Button(btn_frame, text="Adicionar", command=add_folders).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Remover Seleção", command=remove_folders).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Iniciar Upload", command=start_upload).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=folder_window.destroy).pack(side=tk.RIGHT, padx=5)

    def on_close(self):
        """Lidar com o fechamento da janela"""
        if messagebox.askokcancel("Sair", "Deseja realmente sair?"):
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = WasabiGUI(root)
    root.mainloop()