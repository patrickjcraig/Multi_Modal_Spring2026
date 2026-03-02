import os
import PIL
import open3d as o3d


# This handles the reconstructed x-ray images
class ImportReconstruction:

    folder_path = None
    downsampling = None
    data = None

    # For a given tiff stack, we need to know the folder, how much downsampling, 
    def __init__(self, folder_path, downsampling):
        self.folder_path = folder_path
        self.downsampling = downsampling
        self.data = self.load_images()

    def load_images(self):
        # Get a list of all files in the folder
        file_list = os.listdir(self.folder_path)

        # Filter for tiff images
        image_files = [f for f in file_list if f.lower().endswith(('.tiff'))]

        # Tiff image dimensions 2938 x 2938 pixels @ 3661 x 3661 DPI    
        # Make a tiff stack from the images.
        # DOWNSAMPLE

