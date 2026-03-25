import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class ThumbnailLabel(ttk.Label):
    def __init__(self, parent, image_path=None, default_icon=None, size=(80, 80), **kwargs):
        super().__init__(parent, **kwargs)
        self.size = size
        self.default_icon = default_icon
        self.set_image(image_path)

    def set_image(self, image_path):
        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                img.thumbnail(self.size, Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.config(image=self.photo)
                return
            except:
                pass
        if self.default_icon and os.path.exists(self.default_icon):
            try:
                img = Image.open(self.default_icon)
                img.thumbnail(self.size, Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.config(image=self.photo)
            except:
                self.config(image='')
        else:
            self.config(text="📁", font=('Arial', 40))