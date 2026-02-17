import open3d as o3d

print(hasattr(o3d.visualization, "draw"))
print(o3d.__version__)
print(o3d._build_config)

mesh = o3d.geometry.TriangleMesh.create_sphere()
mesh.compute_vertex_normals()
o3d.visualization.draw([mesh])