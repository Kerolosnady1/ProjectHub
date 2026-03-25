import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import shutil

class AddProjectDialog:
    def __init__(self, parent, project_manager, callback, project_to_edit=None):
        self.parent = parent
        self.pm = project_manager
        self.callback = callback
        self.project = project_to_edit

        self.win = tk.Toplevel(parent)
        self.win.title("Add New Project" if not project_to_edit else "Edit Project")
        self.win.geometry("500x550")
        self.win.resizable(False, False)

        self.create_widgets()
        if project_to_edit:
            self.load_project_data()

    def create_widgets(self):
        row = 0
        ttk.Label(self.win, text="Project Name:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.name_entry = ttk.Entry(self.win, width=40)
        self.name_entry.grid(row=row, column=1, padx=10, pady=5, columnspan=2)
        row += 1

        ttk.Label(self.win, text="Project Path:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.path_entry = ttk.Entry(self.win, width=30)
        self.path_entry.grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(self.win, text="Browse", command=self.browse_path).grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(self.win, text="Category:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.win, textvariable=self.category_var, 
                                           values=["Python", "Java", "Web", "AI", "Game", "Other"], width=37)
        self.category_combo.grid(row=row, column=1, padx=10, pady=5, columnspan=2)
        row += 1

        ttk.Label(self.win, text="Description:").grid(row=row, column=0, padx=10, pady=5, sticky='nw')
        self.desc_text = tk.Text(self.win, height=4, width=40)
        self.desc_text.grid(row=row, column=1, padx=10, pady=5, columnspan=2)
        row += 1

        ttk.Label(self.win, text="GitHub URL:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.github_entry = ttk.Entry(self.win, width=40)
        self.github_entry.grid(row=row, column=1, padx=10, pady=5, columnspan=2)
        row += 1

        ttk.Label(self.win, text="Thumbnail:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.thumbnail_path = tk.StringVar()
        ttk.Entry(self.win, textvariable=self.thumbnail_path, width=30).grid(row=row, column=1, padx=5, pady=5)
        ttk.Button(self.win, text="Choose Image", command=self.browse_thumbnail).grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(self.win, text="Estimated Hours:").grid(row=row, column=0, padx=10, pady=5, sticky='w')
        self.hours_entry = ttk.Entry(self.win, width=10)
        self.hours_entry.grid(row=row, column=1, padx=10, pady=5, sticky='w')
        row += 1

        btn_frame = ttk.Frame(self.win)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.win.destroy).pack(side='left', padx=10)

    def browse_path(self):
        path = filedialog.askdirectory(title="Select project folder")
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def browse_thumbnail(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        filename = filedialog.askopenfilename(title="Select thumbnail", filetypes=filetypes)
        if filename:
            dest = Path("thumbnails") / Path(filename).name
            shutil.copy2(filename, dest)
            self.thumbnail_path.set(str(dest))

    def load_project_data(self):
        self.name_entry.insert(0, self.project['name'])
        self.path_entry.insert(0, self.project['path'])
        self.category_combo.set(self.project.get('category', ''))
        self.desc_text.insert('1.0', self.project.get('description', ''))
        self.github_entry.insert(0, self.project.get('github_url', ''))
        self.thumbnail_path.set(self.project.get('thumbnail', ''))
        self.hours_entry.insert(0, str(self.project.get('estimated_hours', 0)))

    def save(self):
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()
        if not name or not path:
            messagebox.showerror("Error", "Please enter project name and path")
            return
        data = {
            "name": name,
            "path": path,
            "description": self.desc_text.get("1.0", "end-1c").strip(),
            "category": self.category_var.get(),
            "github_url": self.github_entry.get().strip(),
            "thumbnail": self.thumbnail_path.get(),
            "estimated_hours": int(self.hours_entry.get()) if self.hours_entry.get().isdigit() else 0
        }
        if self.project:
            self.pm.update_project(self.project['id'], **data)
        else:
            self.pm.add_project(**data)
        self.callback()
        self.win.destroy()