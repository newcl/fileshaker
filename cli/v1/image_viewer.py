import json
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ImageDisplayApp:
    def __init__(self, master, json_file):
        self.master = master
        self.master.title("Similar Images Viewer")
        self.master.geometry("1000x800")  # Increased window size
        self.data = self.load_data(json_file)
        self.create_widgets()
        self.current_group = 0
        self.show_group(self.current_group)
    
    def load_data(self, json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data
    
    def create_widgets(self):
        # Configure the grid in the root window to allow resizing
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.frame = ttk.Frame(self.master)
        self.frame.grid(row=0, column=0, sticky='nsew')
        
        # Configure the grid in the frame
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Navigation buttons
        self.prev_button = ttk.Button(self.frame, text="<< Previous", command=self.prev_group)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        self.next_button = ttk.Button(self.frame, text="Next >>", command=self.next_group)
        self.next_button.grid(row=0, column=2, padx=5, pady=5, sticky='e')
        
        # Group label
        self.group_label = ttk.Label(self.frame, text="")
        self.group_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Frame to display images
        self.canvas = tk.Frame(self.frame)
        self.canvas.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')

        # Configure the grid in the canvas to adjust for images
        self.canvas.columnconfigure(0, weight=1)
        self.canvas.rowconfigure(0, weight=1)
        
        self.image_labels = []
    
    def show_group(self, index):
        if 0 <= index < len(self.data):
            self.clear_canvas()
            group = self.data[index]
            self.group_label.config(text=f"Group {index + 1} of {len(self.data)}")
            images = [group['largest_image']] + group.get('similar_images', [])
            num_images = len(images)
            for i, image_path in enumerate(images):
                self.canvas.columnconfigure(i, weight=1)
                self.display_image(image_path, i)
        else:
            print("Index out of range.")
    
    def display_image(self, image_path, position):
        try:
            img = Image.open(image_path)
            # Set a maximum size for images
            max_size = (300, 300)
            img.thumbnail(max_size)
            img_tk = ImageTk.PhotoImage(img)
            label = ttk.Label(self.canvas, image=img_tk, anchor='center')
            label.image = img_tk  # Keep a reference
            label.grid(row=0, column=position, padx=5, pady=5, sticky='nsew')
            self.image_labels.append(label)
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
    
    def clear_canvas(self):
        for label in self.image_labels:
            label.destroy()
        self.image_labels = []
    
    def prev_group(self):
        if self.current_group > 0:
            self.current_group -= 1
            self.show_group(self.current_group)
    
    def next_group(self):
        if self.current_group < len(self.data) - 1:
            self.current_group += 1
            self.show_group(self.current_group)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDisplayApp(root, "similar_images.json")
    root.mainloop()
