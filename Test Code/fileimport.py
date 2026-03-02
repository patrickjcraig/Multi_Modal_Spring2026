import os
from PIL import Image
import open3d as o3d
import numpy as np

# TIFF stack → NumPy 3D array → threshold → voxel grid → Open3D point cloud

# Tiff image dimensions 2938 x 2938 pixels @ 3661 x 3661 DPI  - 16 bit depth
# 2x downspampling should be sufficient

# This handles the reconstructed x-ray images
class ImportReconstruction:

    # folder_path (string, path to TIFF stack)
    # downsampling (number, default=2)
    # data (3D numpy array)
    def __init__(self, folder_path, downsampling=2):
        self.folder_path = folder_path
        self.downsampling = downsampling
        self.data = self.load_images()


    def load_images(self):
        # Sort files to preserve slice order
        file_list = sorted(os.listdir(self.folder_path))
        image_files = [f for f in file_list if f.lower().endswith(".tiff")]

        volume = []

        for image_file in image_files:
            image_path = os.path.join(self.folder_path, image_file)

            # Open as grayscale
            image = Image.open(image_path)

            # Downsample
            if self.downsampling > 1:
                new_size = (
                    image.width // self.downsampling,
                    image.height // self.downsampling
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to numpy (preserves 16-bit if present)
            image_array = np.array(image)

            volume.append(image_array)

        # Stack into 3D numpy array (Z, Y, X)
        volume = np.stack(volume, axis=0)

        return volume
    

    