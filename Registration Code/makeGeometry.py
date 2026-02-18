import open3d as o3d

# use open3d to make some shapes.
def get_pcd_from_stl(path="TestPart.stl"):
    mesh = o3d.io.read_triangle_mesh(path)
    mesh.compute_vertex_normals()

    pcd = mesh.sample_points_poisson_disk(number_of_points=2000)
    #o3d.visualization.draw([mesh, pcd])

    return pcd
