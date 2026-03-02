import open3d as o3d
import os

# use open3d to make some shapes.
def get_pcd_from_stl(path=None):
    if path is None:
        # Default to TestPart.stl in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "TestPart.stl")
    
    mesh = o3d.io.read_triangle_mesh(path)
    mesh.compute_vertex_normals()

    pcd = mesh.sample_points_poisson_disk(number_of_points=2000)
    #o3d.visualization.draw([mesh, pcd])

    return pcd
