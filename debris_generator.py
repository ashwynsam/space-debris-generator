import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.spatial import ConvexHull, distance_matrix
import trimesh

class RandomDebrisGenerator:
    def __init__(self, num_vertices=10, characteristic_length_mm=10, irregularity=0.5):
        self.num_vertices = num_vertices
        self.characteristic_length_mm = characteristic_length_mm
        self.irregularity = irregularity

    def generate_3d_polygon(self):
        # Generate random points on a sphere
        theta = np.random.uniform(0, 2*np.pi, self.num_vertices)
        phi = np.random.uniform(0, np.pi, self.num_vertices)
        x = np.sin(phi) * np.cos(theta)
        y = np.sin(phi) * np.sin(theta)
        z = np.cos(phi)

        # Add irregularity
        noise = np.random.normal(0, self.irregularity, (self.num_vertices, 3))
        vertices = np.column_stack((x, y, z)) + noise

        # Calculate the largest distance
        dist_matrix = distance_matrix(vertices, vertices)
        max_distance = np.max(dist_matrix)

        # Scale vertices to match the characteristic length in mm
        scale_factor = self.characteristic_length_mm / max_distance
        vertices *= scale_factor

        # Calculate the convex hull to get faces
        hull = ConvexHull(vertices)
        
        return vertices, hull.simplices, max_distance * scale_factor

class DebrisGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("3D Debris Generator")
        self.setup_ui()
        self.current_vertices = None
        self.current_faces = None

    def setup_ui(self):
        self.num_vertices_label = ttk.Label(self.master, text="Number of Vertices (5-20):")
        self.num_vertices_entry = ttk.Entry(self.master)
        self.num_vertices_entry.insert(0, "10")

        self.char_length_label = ttk.Label(self.master, text="Characteristic Length (1-100 mm):")
        self.char_length_entry = ttk.Entry(self.master)
        self.char_length_entry.insert(0, "10")

        self.irregularity_label = ttk.Label(self.master, text="Irregularity (0.0-1.0):")
        self.irregularity_entry = ttk.Entry(self.master)
        self.irregularity_entry.insert(0, "0.5")

        self.generate_button = ttk.Button(self.master, text="Generate Debris", command=self.generate_debris)
        self.save_stl_button = ttk.Button(self.master, text="Save STL", command=self.save_stl)
        self.save_stl_button.config(state='disabled')  # Initially disabled

        self.num_vertices_label.pack()
        self.num_vertices_entry.pack()
        self.char_length_label.pack()
        self.char_length_entry.pack()
        self.irregularity_label.pack()
        self.irregularity_entry.pack()
        self.generate_button.pack()
        self.save_stl_button.pack()

        self.fig = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.info_label = ttk.Label(self.master, text="")
        self.info_label.pack()

    def generate_debris(self):
        try:
            num_vertices = int(self.num_vertices_entry.get())
            char_length_mm = float(self.char_length_entry.get())
            irregularity = float(self.irregularity_entry.get())

            if not (5 <= num_vertices <= 20):
                raise ValueError("Number of vertices must be between 5 and 20")
            if not (1 <= char_length_mm <= 100):
                raise ValueError("Characteristic Length must be between 1 and 100 mm")
            if not (0.0 <= irregularity <= 1.0):
                raise ValueError("Irregularity must be between 0.0 and 1.0")

            generator = RandomDebrisGenerator(num_vertices, char_length_mm, irregularity)
            vertices, faces, actual_max_distance = generator.generate_3d_polygon()

            self.current_vertices = vertices
            self.current_faces = faces

            self.ax.clear()
            poly3d = [vertices[face] for face in faces]
            collection = Poly3DCollection(poly3d, alpha=0.8, edgecolor='k')
            collection.set_facecolor('cyan')
            self.ax.add_collection3d(collection)

            self.ax.set_xlabel('X (mm)')
            self.ax.set_ylabel('Y (mm)')
            self.ax.set_zlabel('Z (mm)')
            self.ax.set_title("3D Debris Preview")

            max_range = np.array([np.ptp(vertices[:,0]), np.ptp(vertices[:,1]), np.ptp(vertices[:,2])]).max() / 2.0
            mid_x = vertices[:,0].mean()
            mid_y = vertices[:,1].mean()
            mid_z = vertices[:,2].mean()
            self.ax.set_xlim(mid_x - max_range, mid_x + max_range)
            self.ax.set_ylim(mid_y - max_range, mid_y + max_range)
            self.ax.set_zlim(mid_z - max_range, mid_z + max_range)

            self.canvas.draw()

            self.info_label.config(text=f"Actual max distance: {actual_max_distance:.2f} mm ({actual_max_distance/10:.2f} cm)")
            self.save_stl_button.config(state='normal')  # Enable the Save STL button

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def save_stl(self):
        if self.current_vertices is None or self.current_faces is None:
            messagebox.showerror("Error", "No debris generated yet. Please generate debris first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".stl", filetypes=[("STL files", "*.stl")])
        if file_path:
            # Create a trimesh object
            debris_mesh = trimesh.Trimesh(vertices=self.current_vertices, faces=self.current_faces)
            
            # Save the mesh as STL
            debris_mesh.export(file_path)
            messagebox.showinfo("Success", f"STL file saved successfully to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DebrisGeneratorGUI(root)
    root.mainloop()