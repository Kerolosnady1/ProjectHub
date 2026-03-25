# ui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import webbrowser
import json
import tempfile
import zipfile

from core.project_manager import ProjectManager
from ui.dialogs import AddProjectDialog
from ui.widgets import ThumbnailLabel
from utils.backup import BackupManager
from utils.git_helper import GitHelper
from utils import statistics


class ProjectHubApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ProjectHub - Project Manager")
        self.root.geometry("1000x650")

        self.pm = ProjectManager()
        self.backup_mgr = BackupManager(db_path=self.pm.db_path, projects_dir=None)

        self.dark_mode = False
        self.setup_ui()
        self.load_projects()

        self.apply_theme()

    # ----------------------------------------------------------------------
    # UI Setup
    # ----------------------------------------------------------------------
    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Project", command=self.add_project)
        file_menu.add_command(label="Import Project", command=self.import_project)
        file_menu.add_command(label="Export Project", command=self.export_project)
        file_menu.add_separator()
        file_menu.add_command(label="Backup", command=self.create_backup)
        file_menu.add_command(label="Restore", command=self.restore_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Statistics", command=self.show_statistics)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Search and filter bar
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill='x', pady=5)

        ttk.Label(filter_frame, text="Search:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_projects())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)

        ttk.Label(filter_frame, text="Category:").pack(side='left', padx=(20, 5))
        self.filter_category = tk.StringVar()
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category,
                                           values=["All"], width=15)
        self.category_combo.pack(side='left', padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_projects())

        # Canvas + scrollbar for project grid
        self.list_frame = ttk.Frame(main_frame)
        self.list_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(self.list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.update_categories_list()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ----------------------------------------------------------------------
    # Data loading and filtering
    # ----------------------------------------------------------------------
    def update_categories_list(self):
        categories = set(p.get('category', 'Uncategorized') for p in self.pm.projects)
        categories.add('All')
        self.category_combo['values'] = list(categories)
        self.filter_category.set('All')

    def filter_projects(self):
        search_text = self.search_var.get().lower()
        selected_cat = self.filter_category.get()
        filtered = []
        for p in self.pm.projects:
            if selected_cat != 'All' and p.get('category', 'Uncategorized') != selected_cat:
                continue
            if search_text:
                if (search_text in p['name'].lower() or
                    search_text in p.get('description', '').lower() or
                    search_text in p.get('category', '').lower()):
                    filtered.append(p)
            else:
                filtered.append(p)
        self.display_projects(filtered)

    def display_projects(self, projects):
        # Clear scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not projects:
            ttk.Label(self.scrollable_frame, text="No projects found").pack(pady=50)
            return

        row = 0
        col = 0
        max_cols = 3
        for proj in projects:
            # Card frame
            frame = ttk.Frame(self.scrollable_frame, relief='ridge', borderwidth=1, padding=5)
            frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            frame.bind("<Button-1>", lambda e, p=proj: self.show_project_details(p))

            # Thumbnail
            thumb = ThumbnailLabel(frame, image_path=proj.get('thumbnail', ''), size=(100, 100))
            thumb.grid(row=0, column=0, rowspan=2, padx=5, pady=5)
            thumb.bind("<Button-1>", lambda e, p=proj: self.show_project_details(p))

            # Project name
            name_label = ttk.Label(frame, text=proj['name'], font=('Arial', 12, 'bold'))
            name_label.grid(row=0, column=1, sticky='w', padx=5)
            name_label.bind("<Button-1>", lambda e, p=proj: self.show_project_details(p))

            # Category
            cat = proj.get('category', 'Uncategorized')
            ttk.Label(frame, text=f"Category: {cat}", font=('Arial', 9)).grid(row=1, column=1, sticky='w', padx=5)

            # Buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

            ttk.Button(btn_frame, text="Run", command=lambda p=proj: self.run_project(p['id'])).pack(side='left', padx=2)
            ttk.Button(btn_frame, text="Edit", command=lambda p=proj: self.edit_project(p)).pack(side='left', padx=2)
            ttk.Button(btn_frame, text="Delete", command=lambda p=proj: self.delete_project(p['id'])).pack(side='left', padx=2)
            if proj.get('github_url'):
                ttk.Button(btn_frame, text="GitHub", command=lambda u=proj['github_url']: webbrowser.open(u)).pack(side='left', padx=2)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Configure columns to expand
        for i in range(max_cols):
            self.scrollable_frame.columnconfigure(i, weight=1)

    def load_projects(self):
        self.update_categories_list()
        self.filter_projects()

    # ----------------------------------------------------------------------
    # Project operations
    # ----------------------------------------------------------------------
    def add_project(self):
        AddProjectDialog(self.root, self.pm, self.load_projects)

    def edit_project(self, project):
        AddProjectDialog(self.root, self.pm, self.load_projects, project_to_edit=project)

    def delete_project(self, proj_id):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this project?"):
            self.pm.delete_project(proj_id)
            self.load_projects()

    def run_project(self, proj_id):
        self.pm.run_project(proj_id)

    # ----------------------------------------------------------------------
    # Project details window
    # ----------------------------------------------------------------------
    def show_project_details(self, project):
        win = tk.Toplevel(self.root)
        win.title(f"Project Details: {project['name']}")
        win.geometry("500x500")

        ttk.Label(win, text=project['name'], font=('Arial', 16, 'bold')).pack(pady=10)

        # Thumbnail
        thumb_path = project.get('thumbnail', '')
        if thumb_path and Path(thumb_path).exists():
            from PIL import Image, ImageTk
            try:
                img = Image.open(thumb_path)
                img.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(img)
                lbl_img = ttk.Label(win, image=photo)
                lbl_img.image = photo
                lbl_img.pack()
            except:
                pass

        details = [
            ("Path", project['path']),
            ("Category", project.get('category', 'Uncategorized')),
            ("Description", project.get('description', 'No description')),
            ("GitHub URL", project.get('github_url', 'None')),
            ("Estimated Hours", f"{project.get('estimated_hours', 0)} hours"),
            ("Created", project.get('created', 'Unknown')),
            ("Last Run", project.get('last_run', 'Never'))
        ]

        for label, value in details:
            frame = ttk.Frame(win)
            frame.pack(fill='x', padx=20, pady=2)
            ttk.Label(frame, text=f"{label}:", font=('Arial', 10, 'bold')).pack(side='left')
            ttk.Label(frame, text=value, wraplength=300).pack(side='left', padx=10)

        # Git info if applicable
        if GitHelper.is_git_repo(project['path']):
            git_info = GitHelper.get_repo_info(project['path'])
            if 'error' not in git_info:
                ttk.Label(win, text=f"Git Branch: {git_info['branch']} - Last commit: {git_info['last_commit']}").pack(pady=5)
                if git_info['has_uncommitted']:
                    ttk.Label(win, text="⚠ Uncommitted changes", foreground='orange').pack()

        ttk.Button(win, text="Close", command=win.destroy).pack(pady=15)

    # ----------------------------------------------------------------------
    # Backup / Restore
    # ----------------------------------------------------------------------
    def create_backup(self):
        path = self.backup_mgr.create_backup(include_projects=False)
        messagebox.showinfo("Success", f"Backup created at:\n{path}")

    def restore_backup(self):
        filename = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip")])
        if filename:
            if messagebox.askyesno("Confirm", "This will replace the current database. Continue?"):
                self.backup_mgr.restore_backup(filename)
                self.pm = ProjectManager()  # reload
                self.load_projects()
                messagebox.showinfo("Done", "Restore completed")

    # ----------------------------------------------------------------------
    # Export / Import
    # ----------------------------------------------------------------------
    def import_project(self):
        filename = filedialog.askopenfilename(filetypes=[("ProjectHub files", "*.projhub"), ("Zip files", "*.zip")])
        if filename:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(filename, 'r') as zipf:
                    zipf.extractall(tmpdir)
                json_path = Path(tmpdir) / "projects_db.json"
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        imported = json.load(f)
                    for proj in imported:
                        if not any(p['path'] == proj['path'] for p in self.pm.projects):
                            self.pm.add_project(
                                name=proj['name'],
                                path=proj['path'],
                                description=proj.get('description', ''),
                                category=proj.get('category', ''),
                                tags=proj.get('tags', []),
                                github_url=proj.get('github_url', ''),
                                thumbnail=proj.get('thumbnail', '')
                            )
                    self.load_projects()
                    messagebox.showinfo("Success", "Projects imported successfully")
                else:
                    messagebox.showerror("Error", "Invalid project file")

    def export_project(self):
        if not self.pm.projects:
            messagebox.showwarning("Warning", "No projects to export")
            return

        # Simple selection dialog
        win = tk.Toplevel(self.root)
        win.title("Select Project to Export")
        win.geometry("300x150")
        ttk.Label(win, text="Select project:").pack(pady=10)
        var = tk.StringVar()
        combo = ttk.Combobox(win, textvariable=var, values=[p['name'] for p in self.pm.projects], state='readonly')
        combo.pack(pady=5)

        def do_export():
            name = var.get()
            if not name:
                return
            proj = next(p for p in self.pm.projects if p['name'] == name)
            save_path = filedialog.asksaveasfilename(defaultextension=".projhub",
                                                     filetypes=[("ProjectHub files", "*.projhub")])
            if save_path:
                with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr("projects_db.json", json.dumps([proj], ensure_ascii=False, indent=4))
                    if proj.get('thumbnail') and Path(proj['thumbnail']).exists():
                        zipf.write(proj['thumbnail'], arcname=f"thumbnails/{Path(proj['thumbnail']).name}")
                messagebox.showinfo("Success", f"Project exported to {save_path}")
                win.destroy()

        ttk.Button(win, text="Export", command=do_export).pack(pady=20)

    # ----------------------------------------------------------------------
    # Statistics
    # ----------------------------------------------------------------------
    def show_statistics(self):
        stats = self.pm.get_statistics()
        statistics.show_statistics_window(self.root, stats)

    # ----------------------------------------------------------------------
    # Theme / Dark Mode
    # ----------------------------------------------------------------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        style = ttk.Style()
        if self.dark_mode:
            bg = "#2b2b2b"
            fg = "#ffffff"
            selectbg = "#3c3c3c"
            style.theme_use('clam')
            style.configure('TFrame', background=bg)
            style.configure('TLabel', background=bg, foreground=fg)
            style.configure('TButton', background=selectbg, foreground=fg)
            style.configure('TEntry', fieldbackground=selectbg, foreground=fg)
            self.root.configure(bg=bg)
        else:
            style.theme_use('vista' if 'vista' in style.theme_names() else 'default')
            self.root.configure(bg='SystemButtonFace')

        # Update existing widgets (simplified: just refresh display)
        self.load_projects()

    # ----------------------------------------------------------------------
    # About
    # ----------------------------------------------------------------------
    def show_about(self):
        messagebox.showinfo("About", "ProjectHub v1.0\nA comprehensive project manager\nDeveloped as a graduation project")