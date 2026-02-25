import sys, os, math
import ctypes
import pandas as pd # will be saving data as Pandas dataframes
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QMouseEvent, QSurfaceFormat
#from PySide6.QtUiTools import QUiLoader
#from PySide6.QtCore import QFile
from ui_mainwindow import Ui_MainWindow
from open3d_ICP import run_full_registration

try:
    import glm
except ImportError:
    print("Warning: PyGLM not installed. Please install it with: pip install PyGLM")
    glm = None

# Shader code for rendering the triangle
VERTEX_SHADER = """#version 400 core

layout (location = 0) in vec3  inPosition;
layout (location = 1) in vec3 inColour;
out vec3 vertColour;
void main()
{
  gl_Position = vec4(inPosition, 1.0);
  vertColour = inColour;
}"""

FRAGMENT_SHADER = """#version 400 core
in vec3 vertColour;
out vec4 fragColour;
void main()
{
  fragColour = vec4(vertColour,1.0);
}
"""


class TriangleWidget(QOpenGLWidget):
    """
    Custom OpenGL widget for rendering a colored triangle.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def initializeGL(self):
        """
        Called once when the OpenGL context is first created.
        Sets up shaders and geometry.
        """
        # Set the background colour to a dark grey
        gl.glClearColor(0.4, 0.4, 0.4, 1.0)
        # Enable depth testing
        gl.glEnable(gl.GL_DEPTH_TEST)
        # Enable multisampling for anti-aliasing
        gl.glEnable(gl.GL_MULTISAMPLE)
        
        self._create_triangle()
        self._load_shader_from_strings(VERTEX_SHADER, FRAGMENT_SHADER)

    def _create_triangle(self):
        """
        Creates the triangle geometry with vertex positions and colors.
        """
        # fmt: off
        VERTEX_DATA = np.array([
            -0.75, -0.75, 0.0, 1.0, 0.0, 0.0,  # Bottom-left vertex (red)
             0.0,   0.75, 0.0, 0.0, 1.0, 0.0,  # Top vertex (green)
             0.75, -0.75, 0.0, 0.0, 0.0, 1.0,  # Bottom-right vertex (blue)
        ], dtype=np.float32)
        # fmt: on
        
        # Allocate a VertexArray
        self.vao_id = gl.glGenVertexArrays(1)
        # Bind the vertex array object
        gl.glBindVertexArray(self.vao_id)

        vbo_id = gl.glGenBuffers(1)
        # Bind this to the VBO buffer
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_id)
        # Allocate the buffer data
        gl.glBufferData(gl.GL_ARRAY_BUFFER, VERTEX_DATA, gl.GL_STATIC_DRAW)
        
        # Set up attribute pointer for position (location 0)
        gl.glVertexAttribPointer(
            0, 3, gl.GL_FLOAT, gl.GL_FALSE, VERTEX_DATA.itemsize * 6, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        
        # Set up attribute pointer for color (location 1)
        gl.glVertexAttribPointer(
            1, 3, gl.GL_FLOAT, gl.GL_FALSE, VERTEX_DATA.itemsize * 6,
            ctypes.c_void_p(VERTEX_DATA.itemsize * 3)
        )
        gl.glEnableVertexAttribArray(1)
        
        gl.glBindVertexArray(0)

    def _load_shader_from_strings(self, vertex, fragment):
        """
        Compiles and links vertex and fragment shaders.
        """
        # Create a program
        self.shader_id = gl.glCreateProgram()

        # Create and compile vertex shader
        vertex_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_id, vertex)
        gl.glCompileShader(vertex_id)
        self._check_shader_compilation_status(vertex_id)

        # Create and compile fragment shader
        fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_id, fragment)
        gl.glCompileShader(fragment_id)
        self._check_shader_compilation_status(fragment_id)
        
        # Attach shaders to program
        gl.glAttachShader(self.shader_id, vertex_id)
        gl.glAttachShader(self.shader_id, fragment_id)

        # Link the program
        gl.glLinkProgram(self.shader_id)
        # Enable it for use
        gl.glUseProgram(self.shader_id)
        
        # Clean up shaders
        gl.glDeleteShader(vertex_id)
        gl.glDeleteShader(fragment_id)

    def _check_shader_compilation_status(self, shader_id):
        """
        Checks if shader compilation was successful.
        """
        if not gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS):
            print(gl.glGetShaderInfoLog(shader_id))
            raise RuntimeError("Shader compilation failed")

    def paintGL(self):
        """
        Called every time the widget needs to be redrawn.
        """
        # Set the viewport
        gl.glViewport(0, 0, self.width(), self.height())
        # Clear the buffers
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        # Activate the shader program
        gl.glUseProgram(self.shader_id)
        # Draw the triangle
        gl.glBindVertexArray(self.vao_id)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)

    def resizeGL(self, w, h):
        """
        Called whenever the widget is resized.
        """
        # Update viewport
        ratio = self.devicePixelRatio()
        self.window_width = int(w * ratio)
        self.window_height = int(h * ratio)

    def keyPressEvent(self, event):
        """
        Handles keyboard events for wireframe/fill toggle.
        """
        key = event.key()
        if key == Qt.Key_W:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)  # Wireframe
        elif key == Qt.Key_S:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)  # Solid fill
        # Trigger a redraw
        self.update()
        super().keyPressEvent(event)


class PointCloudWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering point clouds from open3d.
    Supports multiple point clouds with different colors and transformations.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.point_clouds = {}  # Dictionary to store point cloud data {name: {vertices, colors, VAO, VBO}}
        self.shader_id = None
        
        # Camera parameters
        self.camera_distance = 300.0
        self.camera_angle_x = 30.0
        self.camera_angle_y = 45.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        
        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Shaders for point cloud rendering
        self.point_vertex_shader = """#version 400 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;

out vec3 vertColor;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main() {
    gl_Position = projection * view * model * vec4(position, 1.0);
    vertColor = color;
}"""
        
        self.point_fragment_shader = """#version 400 core
in vec3 vertColor;
out vec4 fragColor;

void main() {
    fragColor = vec4(vertColor, 1.0);
}"""

    def add_point_cloud(self, name, pcd, color=None):
        """
        Add an open3d point cloud to the viewer.
        
        Args:
            name: Identifier for the point cloud
            pcd: open3d.geometry.PointCloud
            color: Optional RGB color tuple (defaults to point cloud's colors)
        """
        points = np.asarray(pcd.points, dtype=np.float32)
        
        if color is not None:
            # Use specified color for all points
            colors = np.full((len(points), 3), color, dtype=np.float32)
        elif pcd.has_colors():
            # Use point cloud's colors
            colors = np.asarray(pcd.colors, dtype=np.float32)
        else:
            # Default white
            colors = np.ones((len(points), 3), dtype=np.float32)
        
        # Store the data
        self.point_clouds[name] = {
            'points': points,
            'colors': colors,
            'vao': None,
            'vbo_vertices': None,
            'vbo_colors': None,
            'vertex_count': len(points)
        }

    def clear_point_clouds(self):
        """Remove all point clouds from the viewer."""
        self.point_clouds.clear()

    def initializeGL(self):
        """Initialize OpenGL context and shaders."""
        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)
        gl.glPointSize(2.0)
        
        # Compile shaders
        self._load_shaders()
        
        # Setup VAOs/VBOs for all point clouds
        if self.point_clouds:
            self._setup_geometry()

    def _load_shaders(self):
        """Compile and link shaders."""
        self.shader_id = gl.glCreateProgram()
        
        # Vertex shader
        vertex_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_id, self.point_vertex_shader)
        gl.glCompileShader(vertex_id)
        self._check_shader_compilation(vertex_id)
        
        # Fragment shader
        fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_id, self.point_fragment_shader)
        gl.glCompileShader(fragment_id)
        self._check_shader_compilation(fragment_id)
        
        # Link program
        gl.glAttachShader(self.shader_id, vertex_id)
        gl.glAttachShader(self.shader_id, fragment_id)
        gl.glLinkProgram(self.shader_id)
        
        gl.glDeleteShader(vertex_id)
        gl.glDeleteShader(fragment_id)

    def _check_shader_compilation(self, shader_id):
        """Check if shader compiled successfully."""
        if not gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS):
            print(gl.glGetShaderInfoLog(shader_id))
            raise RuntimeError("Shader compilation failed")

    def _setup_geometry(self):
        """Setup VAO and VBO for all point clouds."""
        for name, data in self.point_clouds.items():
            if data['vao'] is None:
                # Create VAO
                vao = gl.glGenVertexArrays(1)
                gl.glBindVertexArray(vao)
                
                # Create and fill vertex VBO
                vbo_vertices = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_vertices)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, data['points'].nbytes, data['points'], gl.GL_STATIC_DRAW)
                gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, ctypes.c_void_p(0))
                gl.glEnableVertexAttribArray(0)
                
                # Create and fill color VBO
                vbo_colors = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_colors)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, data['colors'].nbytes, data['colors'], gl.GL_STATIC_DRAW)
                gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, ctypes.c_void_p(0))
                gl.glEnableVertexAttribArray(1)
                
                gl.glBindVertexArray(0)
                
                data['vao'] = vao
                data['vbo_vertices'] = vbo_vertices
                data['vbo_colors'] = vbo_colors

    def paintGL(self):
        """Render all point clouds."""
        if glm is None:
            return
            
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glViewport(0, 0, self.width(), self.height())
        
        # Setup geometry on first paintGL call if needed
        if self.point_clouds:
            needs_setup = any(data['vao'] is None for data in self.point_clouds.values())
            if needs_setup:
                self._setup_geometry()
        
        if not self.point_clouds:
            return
        
        gl.glUseProgram(self.shader_id)
        
        # Setup projection matrix
        aspect = self.width() / max(self.height(), 1)
        projection = glm.perspective(glm.radians(45.0), aspect, 0.1, 10000.0)
        proj_loc = gl.glGetUniformLocation(self.shader_id, "projection")
        gl.glUniformMatrix4fv(proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))
        
        # Setup view matrix with camera controls
        camera_x = self.camera_distance * math.sin(math.radians(self.camera_angle_y)) * math.cos(math.radians(self.camera_angle_x))
        camera_y = self.camera_distance * math.sin(math.radians(self.camera_angle_x))
        camera_z = self.camera_distance * math.cos(math.radians(self.camera_angle_y)) * math.cos(math.radians(self.camera_angle_x))
        
        view = glm.lookAt(
            glm.vec3(camera_x + self.pan_x, camera_y + self.pan_y, camera_z),
            glm.vec3(self.pan_x, self.pan_y, 0.0),
            glm.vec3(0.0, 1.0, 0.0)
        )
        view_loc = gl.glGetUniformLocation(self.shader_id, "view")
        gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))
        
        # Render each point cloud
        for name, data in self.point_clouds.items():
            if data['vao'] is not None:
                model = glm.mat4(1.0)
                model_loc = gl.glGetUniformLocation(self.shader_id, "model")
                gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
                
                gl.glBindVertexArray(data['vao'])
                gl.glDrawArrays(gl.GL_POINTS, 0, data['vertex_count'])

    def resizeGL(self, w, h):
        """Handle window resize."""
        gl.glViewport(0, 0, w, h)

    def mousePressEvent(self, event: QMouseEvent):
        """Track mouse press for camera control."""
        self.last_mouse_x = event.position().x()
        self.last_mouse_y = event.position().y()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement for camera rotation and panning."""
        current_x = event.position().x()
        current_y = event.position().y()
        
        delta_x = current_x - self.last_mouse_x
        delta_y = current_y - self.last_mouse_y
        
        if event.buttons() == Qt.LeftButton:
            # Rotate view
            self.camera_angle_y += delta_x * 0.5
            self.camera_angle_x += delta_y * 0.5
            self.camera_angle_x = max(-85, min(85, self.camera_angle_x))
        elif event.buttons() == Qt.RightButton:
            # Pan view
            self.pan_x -= delta_x * 0.5
            self.pan_y += delta_y * 0.5
        
        self.last_mouse_x = current_x
        self.last_mouse_y = current_y
        self.update()

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        self.camera_distance -= event.angleDelta().y() * 0.1
        self.camera_distance = max(10.0, self.camera_distance)
        self.update()


class ICPWorkerThread(QThread):
    """
    Worker thread for running ICP registration without blocking the UI.
    """
    finished = Signal(dict)  # Signal emitted when registration is complete
    error = Signal(str)       # Signal emitted if an error occurs
    
    def __init__(self, voxel_size=2.0, ransac_dist_mult=1.5, ransac_max_iter=100000,
                 ransac_validation=1000, icp_dist_mult=0.4):
        super().__init__()
        self.voxel_size = voxel_size
        self.ransac_dist_mult = ransac_dist_mult
        self.ransac_max_iter = ransac_max_iter
        self.ransac_validation = ransac_validation
        self.icp_dist_mult = icp_dist_mult
    
    def run(self):
        """Run the ICP registration in a background thread."""
        try:
            results = run_full_registration(
                voxel_size=self.voxel_size,
                ransac_dist_multiplier=self.ransac_dist_mult,
                ransac_max_iter=self.ransac_max_iter,
                ransac_validation=self.ransac_validation,
                icp_dist_multiplier=self.icp_dist_mult
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class PointCloudViewerWindow(QMainWindow):
    """
    Standalone window for viewing point clouds with OpenGL.
    Can be used independently or integrated into the main GUI.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Point Cloud Viewer - OpenGL")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create the OpenGL widget
        self.viewer = PointCloudWidget()
        self.setCentralWidget(self.viewer)
        
        # Create status bar with controls info
        self.statusBar().showMessage("Left Mouse: Rotate | Right Mouse: Pan | Scroll: Zoom")
    
    def add_point_cloud(self, name, pcd, color=None):
        """Add a point cloud to the viewer."""
        self.viewer.add_point_cloud(name, pcd, color)
        # Don't setup geometry here - let it happen during first paint call
        self.viewer.update()
    
    def clear(self):
        """Clear all point clouds."""
        self.viewer.clear_point_clouds()
        self.viewer.update()


class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')
        
        # Initialize worker thread for ICP
        self.icp_thread = None
        
        # Replace the placeholder OpenGL widget with our custom triangle widget
        self._setup_opengl_widget()
        
        self.setup_connections() # this function will be used to assign values to the widgets

        # old code from using QUiLoader, switching to using pyside6-uic since this makes the widgets work 
        # all of a sudden for some reason

        #base_dir = os.path.dirname(__file__)
        #ui_path = os.path.join(base_dir, "UI_V1.ui") # setting correct filepath
        #ui_file = QFile(ui_path)
        #ui_file.open(QFile.ReadOnly)

        #loader = QUiLoader()
        #loader.load(ui_file, self)
        #print(self.findChildren(object))
        #ui_file.close()

        #self.setCentralWidget(self.ui)

    def _setup_opengl_widget(self):
        """
        Replace the placeholder OpenGL widget with our custom TriangleWidget.
        """
        # Get the geometry of the existing placeholder widget
        geometry = self.openGLWidget.geometry()
        parent = self.openGLWidget.parent()
        
        # Remove the old widget
        self.openGLWidget.setParent(None)
        self.openGLWidget.deleteLater()
        
        # Create and set up the new custom OpenGL widget
        self.openGLWidget = TriangleWidget(parent)
        self.openGLWidget.setGeometry(geometry)
        self.openGLWidget.show()

    def setup_connections(self):
        self.toolButton.clicked.connect(self.run_scan)
        self.toolButton_2.clicked.connect(self.save_df)
        self.btn_prev_step.clicked.connect(self._prev_step)
        self.btn_next_step.clicked.connect(self._next_step)
        
        # Initialize step tracking
        self.current_step = 0  # 0 = original, 1 = RANSAC, 2 = ICP

    # functions for running registration and saving as df
    def run_scan(self): # function for running 3D scan from open3d_ICP file
        # Disable the button while running
        self.toolButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.statusbar.showMessage('Currently running ICP registration...')
        
        # Clear previous results
        self.label_ransac_fitness.setText("--")
        self.label_ransac_rmse.setText("--")
        self.label_icp_fitness.setText("--")
        self.label_icp_rmse.setText("--")
        
        # Read parameter values from the UI
        voxel_size = self.spinBox_voxel_size.value()
        ransac_dist_mult = self.spinBox_ransac_dist.value()
        ransac_max_iter = self.spinBox_ransac_max_iter.value()
        ransac_validation = self.spinBox_ransac_validation.value()
        icp_dist_mult = self.spinBox_icp_dist.value()
        
        # Create and start the worker thread with parameters
        self.icp_thread = ICPWorkerThread(
            voxel_size=voxel_size,
            ransac_dist_mult=ransac_dist_mult,
            ransac_max_iter=ransac_max_iter,
            ransac_validation=ransac_validation,
            icp_dist_mult=icp_dist_mult
        )
        self.icp_thread.finished.connect(self._on_registration_complete)
        self.icp_thread.error.connect(self._on_registration_error)
        self.icp_thread.start()
    
    def _on_registration_complete(self, results):
        """Called when ICP registration is complete."""
        # Store the results
        self.pcd1 = results['pcd1']
        self.pcd2 = results['pcd2']
        self.ransac_result = results['ransac']
        self.icp_result = results['icp']
        
        # Update the results labels
        self._update_results_display()
        
        # Display the registered point clouds in the OpenGL viewer (start at final ICP result)
        self.current_step = 2
        self._display_registration_results()
        
        # Enable navigation buttons
        self.btn_prev_step.setEnabled(True)
        self.btn_next_step.setEnabled(False)  # Already at last step
        
        # Update UI
        self.progressBar.setValue(100)
        self.statusbar.showMessage('Registration complete! Fitness: {:.6f}, RMSE: {:.6f}'.format(
            self.icp_result.fitness, self.icp_result.inlier_rmse))
        
        # Re-enable the button
        self.toolButton.setEnabled(True)
    
    def _update_results_display(self):
        """Update the results labels with RANSAC and ICP statistics."""
        # Update RANSAC results
        self.label_ransac_fitness.setText(f"{self.ransac_result.fitness:.6f}")
        self.label_ransac_rmse.setText(f"{self.ransac_result.inlier_rmse:.6f}")
        
        # Update ICP results
        self.label_icp_fitness.setText(f"{self.icp_result.fitness:.6f}")
        self.label_icp_rmse.setText(f"{self.icp_result.inlier_rmse:.6f}")
    
    def _on_registration_error(self, error_msg):
        """Called if an error occurs during registration."""
        self.statusbar.showMessage(f'Error during registration: {error_msg}')
        self.toolButton.setEnabled(True)
    
    def _display_registration_results(self):
        """Display the registration results in the OpenGL viewer based on current step."""
        # Replace the triangle widget with a point cloud viewer if needed
        if not isinstance(self.openGLWidget, PointCloudWidget):
            geometry = self.openGLWidget.geometry()
            parent = self.openGLWidget.parent()
            
            # Remove the old widget
            self.openGLWidget.setParent(None)
            self.openGLWidget.deleteLater()
            
            # Create the new point cloud widget
            self.openGLWidget = PointCloudWidget(parent)
            self.openGLWidget.setGeometry(geometry)
            self.openGLWidget.show()
        else:
            # Clear existing point clouds
            self.openGLWidget.point_clouds.clear()
        
        # Prepare point clouds with colors
        import copy
        source_temp = copy.deepcopy(self.pcd1)
        target_temp = copy.deepcopy(self.pcd2)
        
        source_temp.paint_uniform_color([1.0, 0.706, 0.0])  # Orange
        target_temp.paint_uniform_color([0.0, 0.651, 0.929])  # Blue
        
        # Apply transformation based on current step
        if self.current_step == 0:
            # Step 0: Original offset point clouds (no transformation)
            self.label_step_info.setText("Step 1/3: Original Point Clouds")
        elif self.current_step == 1:
            # Step 1: RANSAC alignment
            source_temp.transform(self.ransac_result.transformation)
            self.label_step_info.setText("Step 2/3: RANSAC Alignment")
        elif self.current_step == 2:
            # Step 2: Final ICP alignment
            source_temp.transform(self.icp_result.transformation)
            self.label_step_info.setText("Step 3/3: ICP Refinement")
        
        # Add to the viewer
        self.openGLWidget.add_point_cloud("Source", source_temp)
        self.openGLWidget.add_point_cloud("Target", target_temp)
        self.openGLWidget.update()
    
    def _prev_step(self):
        """Navigate to the previous registration step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._display_registration_results()
            
            # Update button states
            self.btn_next_step.setEnabled(True)
            if self.current_step == 0:
                self.btn_prev_step.setEnabled(False)
    
    def _next_step(self):
        """Navigate to the next registration step."""
        if self.current_step < 2:
            self.current_step += 1
            self._display_registration_results()
            
            # Update button states
            self.btn_prev_step.setEnabled(True)
            if self.current_step == 2:
                self.btn_next_step.setEnabled(False)

    def save_df(self):
        if not hasattr(self, 'pcd1'):
            self.statusbar.showMessage('No valid data is available.')
            return
        
        # saving pcd1, pcd2, ICP and RANSAC results into separate Pandas dfs
        pcd1_df = pcd_to_df(self.pcd1)
        pcd2_df = pcd_to_df(self.pcd2)
        icp_tf_df = tf_to_df(self.icp_result) # transformation matrix of ICP registration
        icp_df = reg_to_df(self.icp_result) # metadata of ICP registration
        ransac_tf_df = tf_to_df(self.ransac_result) # transformation matrix of RANSAC
        ransac_df = reg_to_df(self.ransac_result) # metadata of RANSAC

        code_dir = os.path.dirname(os.path.abspath(__file__)) # finding directory for this file
        ws_dir = os.path.dirname(code_dir) # go into Multi_Modal_Spring2026 folder
        base = os.path.join(ws_dir, 'TestData') # go into TestData folder to save the CSVs
        
        # Create TestData directory if it doesn't exist
        os.makedirs(base, exist_ok=True)
        
        # save CSV files for each df
        pcd1_df.to_csv(os.path.join(base, 'pcd1_raw.csv'), index=False)
        pcd2_df.to_csv(os.path.join(base, 'pcd2_raw.csv'), index=False)
        icp_tf_df.to_csv(os.path.join(base, 'icp_transform.csv'), index=False)
        icp_df.to_csv(os.path.join(base, 'icp_metadata.csv'), index=False)
        ransac_tf_df.to_csv(os.path.join(base, 'ransac_transform.csv'), index=False)
        ransac_df.to_csv(os.path.join(base, 'ransac_metadata.csv'), index=False)
        # right now, this is just the names of the files, we can change this later to have a current date and time if we want to

        self.statusbar.showMessage('The data has been saved successfully.')

# miscellaneous helper functions to simplify code inside class
def pcd_to_df(pcd): # helper function for converting pcds to df
    points = np.asarray(pcd.points)
    df = pd.DataFrame(points, columns=['X','Y','Z'])
    return df

def tf_to_df(result): # helper function to store the transformation matrix of result data
    return pd.DataFrame(result.transformation, columns=['C1','C2','C3','C4'], index=['R1','R2','R3','R4'])

def reg_to_df(result): # helper function to store the metadata of result data
    return pd.DataFrame({'Fitness':[result.fitness], 'Inlier RMSE':[result.inlier_rmse]})

# start main app
if __name__ == "__main__":
    from PySide6.QtGui import QSurfaceFormat
    
    # Configure OpenGL surface format
    format = QSurfaceFormat()
    format.setSamples(4)  # 4x multisampling for anti-aliasing
    format.setMajorVersion(4)
    format.setMinorVersion(1)
    format.setProfile(QSurfaceFormat.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)
    
    app = QApplication(sys.argv)
    window = AppTest()
    window.show()
    sys.exit(app.exec())

# Important Note: Every time a change is made to UI_V1.ui, make sure to rerun the following line in the terminal:
#
# pyside6-uic Code/UI_V1.ui -o ui_mainwindow.py
#
# This is assuming you are working in the directory folder for Multi_Modal_Spring2026. Then afterward, since the 
# file will be made in that directory, move the newly created file into the Code folder so it is in the same
# directory as the main Python file that will run this code.
# Addendum: When replacing the ui_mainwindow.py file, for some reason it adds 'Code.' to the import at the beginning
# of this file. Make sure to fix that back to the way it was before (without Code. at the beginning) for this to run.