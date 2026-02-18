import open3d as o3d
import open3d.core as o3c
import numpy as np
import matplotlib.pyplot as plt
import copy
import os
import sys

# Only needed for tutorial, monkey patches visualization
#sys.path.append("..")
#import open3d_tutorial as o3dtut
# Change to True if you want to interact with the visualization windows
#o3dtut.interactive = not "CI" in os.environ

# Create a empty point cloud on CPU.
#pcd = o3d.t.geometry.PointCloud()
#print(pcd, "\n")

# To create a point cloud on CUDA, specify the device.
pcd = o3d.t.geometry.PointCloud(o3c.Device("cuda:0"))
print(pcd, "\n")

# Create a point cloud from open3d tensor with dtype of float32.
pcd = o3d.t.geometry.PointCloud(o3c.Tensor([[0, 0, 0], [1, 1, 1]], o3c.float32))
print(pcd, "\n")

# Create a point cloud from open3d tensor with dtype of float64.
pcd = o3d.t.geometry.PointCloud(o3c.Tensor([[0, 0, 0], [1, 1, 1]], o3c.float64))
print(pcd, "\n")

# Create a point cloud from numpy array. The array will be copied.
pcd = o3d.t.geometry.PointCloud(
    np.array([[0, 0, 0], [1, 1, 1]], dtype=np.float32))
print(pcd, "\n")

# Create a point cloud from python list.
pcd = o3d.t.geometry.PointCloud([[0., 0., 0.], [1., 1., 1.]])
print(pcd, "\n")

# Error creation. The point cloud must have shape of (N, 3).
#try:
#    pcd = o3d.t.geometry.PointCloud(o3c.Tensor([0, 0, 0, 0], o3c.float32))
#except:
#    print(f"Error creation. The point cloud must have shape of (N, 3).")


# 1. Create a 3D shape (a sphere)
mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0, resolution=20)
mesh.compute_vertex_normals() # Recommended for better visualization

# 2. Turn the mesh into a point cloud by sampling points on its surface
pcd = mesh.sample_points_poisson_disk(number_of_points=2000)

# Optional: Visualize the point cloud
print("Visualizing point cloud...")
o3d.visualization.draw([pcd])

# Optional: Save the point cloud to a file
# o3d.io.write_point_cloud("my_shape.ply", pcd)
