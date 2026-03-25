import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

def show_statistics_window(parent, stats):
    win = tk.Toplevel(parent)
    win.title("Project Statistics")
    win.geometry("600x500")

    ttk.Label(win, text=f"Total Projects: {stats['total']}", font=('Arial', 14)).pack(pady=5)
    ttk.Label(win, text=f"Total Estimated Hours: {stats['total_estimated_hours']}", font=('Arial', 14)).pack(pady=5)

    fig, ax = plt.subplots(figsize=(5, 3))
    categories = stats['categories']
    if categories:
        ax.bar(categories.keys(), categories.values())
        ax.set_xlabel("Category")
        ax.set_ylabel("Number of Projects")
        ax.set_title("Project Distribution by Category")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)
    else:
        ttk.Label(win, text="No data for chart").pack()

    ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)