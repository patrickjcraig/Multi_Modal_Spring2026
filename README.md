# Multi_Modal_Spring2026

## Project Milestones
1.	Develop a modular data ingestion framework capable of handling multiple microscopy modalities such as X-ray, scanning acoustic microscopy, and optical imaging.
    a. Implement a CT algorithm for 3D data such as x-ray and model in opencv
  	b. Create a script to seperate non-image data (headers, tool settings) from image data for each modality
  	c. Add support for time-series data such as SAM using FFT methods
  	d. Add preprocessing and smoothening algorithms to reduce noise affects
2.	Implement spatial alignment methods to register datasets acquired at different resolutions and coordinate systems.
    a. Create a feature extraction method (edges, verticies) for our registration model
  	b. Global Registration to roughly align coordinate systems
  	c. Local Registration to best match the 3D features using ICP
  	d. Have a tab for accuracy metrics for our registration
3.	Enable region-based analysis to support localization of defects across modalities
    a. Define regions of interest based on extracted features such as edges and verticies
  	b. Use classifiers to indicate whether a region contains a defect 
  	c.
  	d.
5.	Provide visualization tools for side-by-side and overlaid inspection to highlight complementary information.
    a. Layer slice views for 3D volumes
  	b. 
  	c.
  	d.
6.	Establish a standardized data and metadata structure to support repeatable and scalable workflows.
    a.
  	b.
  	c.
  	d.
