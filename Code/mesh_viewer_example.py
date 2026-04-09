"""
Example: Using the Mesh & Point Cloud Viewer with TIF Stack Reconstruction

This example demonstrates how to use the updated PointCloudViewerWindow to display
both point cloud and mesh reconstructions from a TIF stack, with toggle capability
between the two views using Ctrl+T.

The mesh reconstruction is performed using marching cubes algorithm, and both the
point cloud and mesh are rendered in the same OpenGL window using different shaders
and rendering techniques.
"""

import os
import numpy as np
from defaults import DEFAULT_VOXEL_SIZE_MM
from makeGeometry import get_pcd_from_ct_stack
from GUI.icp_worker import PointCloudViewerWindow


def example_view_tif_stack_with_mesh():
    """
    Load a TIF stack, generate both point cloud and mesh, 
    and display them in a viewer with toggle capability.
    """
    # Path to TIF stack folder
    tiff_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '120kv_FDK')
    )
    
    # Generate point cloud AND mesh from CT stack
    # get_pcd_from_ct_stack returns (pcd, mesh, level)
    pcd, mesh, level = get_pcd_from_ct_stack(
        folder_path=tiff_folder,
        voxel_size_mm=DEFAULT_VOXEL_SIZE_MM,  # Adjust based on your scanning parameters
        downsample_zyx=4,      # Downsample by factor of 4 in Z, Y, X
        crop_zyx=(256, 256, 256),  # Crop to 256x256x256 region (can be adjusted)
        level=None,            # Auto-detect iso-level (None) or specify manually
        n_points=5000,         # Number of points to sample for the point cloud
    )
    
    print(f"MC level used: {level}")
    print(f"Point cloud points: {np.asarray(pcd.points).shape[0]}")
    print(f"Mesh vertices: {np.asarray(mesh.vertices).shape[0]}")
    print(f"Mesh triangles: {np.asarray(mesh.triangles).shape[0]}")
    
    # Create the integrated viewer window
    viewer = PointCloudViewerWindow()
    
    # Add the point cloud (displayed by default)
    viewer.add_point_cloud("CT Stack Point Cloud", pcd)
    
    # Add the mesh (hidden by default, toggle with Ctrl+T)
    viewer.add_mesh("CT Stack Mesh", mesh)
    
    # Show the viewer
    viewer.show()
    
    return viewer


def example_compare_meshes():
    """
    Example: Load two TIF stacks and compare their meshes.
    """
    tiff_folder1 = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '120kv_FDK')
    )
    
    pcd1, mesh1, level1 = get_pcd_from_ct_stack(
        folder_path=tiff_folder1,
        downsample_zyx=4,
        crop_zyx=(256, 256, 256),
        level=None,
        n_points=3000,
    )
    
    # Create viewer and add first mesh
    viewer = PointCloudViewerWindow()
    viewer.add_mesh("Mesh 1", mesh1, color=(0.3, 0.5, 0.9))  # Blue
    
    # Add as point cloud too for comparison
    viewer.add_point_cloud("Point Cloud 1", pcd1, color=(0.3, 0.5, 0.9))
    
    viewer.show()
    return viewer


# ============================================================================
# KEYBOARD CONTROLS:
# ============================================================================
# Left Mouse Drag      : Rotate the view
# Right Mouse Drag     : Pan the rotation center
# Mouse Wheel          : Zoom in/out
# Ctrl + T             : Toggle between Point Cloud and Mesh views
# ============================================================================


# MESH WIDGET IMPLEMENTATION NOTES:
# ============================================================================
# The MeshWidget class in Code/Widgets/mesh_widget.py:
# 
# 1. Stores mesh data as vertices, normals, and triangle indices
# 2. Uses element buffer objects (EBO) for efficient triangle rendering
# 3. Uses Phong-like shading for better visualization
# 4. Shares the same camera system as PointCloudWidget
# 5. Automatically synchronizes camera state when toggling views
# 6. Renders the same grid coordinate system for spatial reference
# 
# SHADERS:
# The mesh shaders in Code/Shaders/mesh_shaders.py implement:
# - Vertex shader: transforms vertices and normals using view/projection matrices
# - Fragment shader: applies Phong-like lighting based on surface normals
# ============================================================================
