import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import ProjectHubApp
import tkinter as tk

def main():
    # Ensure necessary directories exist
    Path("database").mkdir(exist_ok=True)
    Path("thumbnails").mkdir(exist_ok=True)
    Path("backups").mkdir(exist_ok=True)

    root = tk.Tk()
    app = ProjectHubApp(root)
    root.mainloop()

if __name__ == "__main__":
    main