import ctypes
import math
import numpy as np
import OpenGL.GL as gl

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

from Shaders.pointcloud_shaders import POINT_VERTEX_SHADER, POINT_FRAGMENT_SHADER

try:
    import glm
except ImportError:
    print("Warning: PyGLM not installed. Please install it with: pip install PyGLM")
    glm = None

class PointCloudWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering point clouds from open3d.
    Supports multiple point clouds with different colors and transformations.

    The widget can optionally display overlay text (e.g. "RANSAC 5/100")
    in the top‑left corner; the text is set with :meth:`set_overlay_text`.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.point_clouds = {}  # Dictionary to store point cloud data {name: {vertices, colors, VAO, VBO}}
        self.shader_id = None
        # overlay text rendered with QPainter after OpenGL draw
        self._overlay_text = ""
        
        # Camera parameters
        self.camera_distance = 300.0
        self.camera_angle_x = 30.0
        self.camera_angle_y = 45.0
        self.rotation_origin = glm.vec3(0.0, 0.0, 0.0) if glm else None
        
        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Matrices for picking
        self.projection = None
        self.view = None
        
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
        gl.glShaderSource(vertex_id, POINT_VERTEX_SHADER)
        gl.glCompileShader(vertex_id)
        self._check_shader_compilation(vertex_id)
        
        # Fragment shader
        fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_id, POINT_FRAGMENT_SHADER)
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
        
        camera_pos = self.rotation_origin + glm.vec3(camera_x, camera_y, camera_z)
        view = glm.lookAt(
            camera_pos,
            self.rotation_origin,
            glm.vec3(0.0, 1.0, 0.0)
        )
        self.view = view
        self.projection = projection
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
        # after rendering all clouds, draw overlay text if present
        from PySide6.QtGui import QPainter, QColor, QFont
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(10, 20, self._overlay_text)
        painter.end()

    def resizeGL(self, w, h):
        """Handle window resize."""
        gl.glViewport(0, 0, w, h)

    def mousePressEvent(self, event: QMouseEvent):
        """Track mouse press for camera control."""
        self.last_mouse_x = event.position().x()
        self.last_mouse_y = event.position().y()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse movement for camera rotation and moving rotation origin."""
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
            # Move rotation origin in view plane
            if glm is not None:
                # Compute current camera position
                camera_x = self.camera_distance * math.sin(math.radians(self.camera_angle_y)) * math.cos(math.radians(self.camera_angle_x))
                camera_y = self.camera_distance * math.sin(math.radians(self.camera_angle_x))
                camera_z = self.camera_distance * math.cos(math.radians(self.camera_angle_y)) * math.cos(math.radians(self.camera_angle_x))
                camera_pos = self.rotation_origin + glm.vec3(camera_x, camera_y, camera_z)
                
                # View direction from camera to rotation origin
                view_dir = glm.normalize(self.rotation_origin - camera_pos)
                
                # Right vector (perpendicular to view and world up)
                right = glm.normalize(glm.cross(view_dir, glm.vec3(0.0, 1.0, 0.0)))
                
                # Up vector in view plane
                up = glm.cross(right, view_dir)
                
                # Move rotation origin in view plane
                movement = delta_x * right * 0.5 - delta_y * up * 0.5  # Note: -delta_y because screen Y is inverted
                self.rotation_origin += movement
        
        self.last_mouse_x = current_x
        self.last_mouse_y = current_y
        self.update()


    def set_overlay_text(self, text: str):
        """Set the overlay string shown in the upper left of the widget.

        The text is rendered after all point clouds have been drawn in
        :meth:`paintGL` so that it remains unobscured by the 3D scene.
        """
        self._overlay_text = text
        self.update()

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        self.camera_distance -= event.angleDelta().y() * 0.1
        self.camera_distance = max(10.0, self.camera_distance)
        self.update()