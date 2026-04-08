import ctypes
import math
import numpy as np
import OpenGL.GL as gl

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

from Shaders.mesh_shaders import MESH_VERTEX_SHADER, MESH_FRAGMENT_SHADER

try:
    import glm
except ImportError:
    print("Warning: PyGLM not installed. Please install it with: pip install PyGLM")
    glm = None

class MeshWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering triangle meshes from open3d.
    Supports multiple meshes with different colors and transformations.
    Shares camera controls with PointCloudWidget for unified viewing.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.meshes = {}  # Dictionary to store mesh data {name: {vertices, normals, indices, VAO, VBO, IBO, index_count}}
        self.shader_id = None
        self._overlay_text = ""
        
        # Camera parameters (shared with PointCloudWidget)
        self.camera_distance = 300.0
        self.camera_angle_x = 30.0
        self.camera_angle_y = 45.0
        self.rotation_origin = glm.vec3(0.0, 0.0, 0.0) if glm else None

        # Grid state
        self.grid_vao = None
        self.grid_vbo = None
        self.grid_vertex_count = 0
        self.grid_dirty = True

        # Mouse tracking
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Matrices for picking
        self.projection = None
        self.view = None
        
        # Mesh color (default semi-transparent blue)
        self.mesh_color = (0.3, 0.5, 0.9)

    def add_mesh(self, name, mesh, color=None):
        """
        Add an open3d triangle mesh to the viewer.
        
        Args:
            name: Identifier for the mesh
            mesh: open3d.geometry.TriangleMesh
            color: Optional RGB color tuple (0-1 range)
        """
        vertices = np.asarray(mesh.vertices, dtype=np.float32)
        triangles = np.asarray(mesh.triangles, dtype=np.uint32)
        
        # Compute or use provided normals
        if mesh.has_vertex_normals():
            normals = np.asarray(mesh.vertex_normals, dtype=np.float32)
        else:
            mesh.compute_vertex_normals()
            normals = np.asarray(mesh.vertex_normals, dtype=np.float32)
        
        # Store the data
        self.meshes[name] = {
            'vertices': vertices,
            'normals': normals,
            'triangles': triangles,
            'vao': None,
            'vbo_vertices': None,
            'vbo_normals': None,
            'ibo': None,
            'index_count': len(triangles) * 3,
            'color': color if color is not None else self.mesh_color
        }

        self.grid_dirty = True

    def clear_meshes(self):
        """Remove all meshes from the viewer."""
        self.meshes.clear()
        self.grid_dirty = True

    def initializeGL(self):
        """Initialize OpenGL context and shaders."""
        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)
        
        # Enable smooth shading
        gl.glShadeModel(gl.GL_SMOOTH)
        
        # Compile shaders
        self._load_shaders()
        
        # Setup VAOs/VBOs for all meshes
        if self.meshes:
            self._setup_geometry()

    def _load_shaders(self):
        """Compile and link shaders."""
        self.shader_id = gl.glCreateProgram()
        
        # Vertex shader
        vertex_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_id, MESH_VERTEX_SHADER)
        gl.glCompileShader(vertex_id)
        self._check_shader_compilation(vertex_id)
        
        # Fragment shader
        fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_id, MESH_FRAGMENT_SHADER)
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
        """Setup VAO, VBO, and IBO for all meshes."""
        for name, data in self.meshes.items():
            if data['vao'] is None:
                # Create VAO
                vao = gl.glGenVertexArrays(1)
                gl.glBindVertexArray(vao)
                
                # Create and fill vertex VBO
                vbo_vertices = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_vertices)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, data['vertices'].nbytes, data['vertices'], gl.GL_STATIC_DRAW)
                gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, ctypes.c_void_p(0))
                gl.glEnableVertexAttribArray(0)
                
                # Create and fill normal VBO
                vbo_normals = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo_normals)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, data['normals'].nbytes, data['normals'], gl.GL_STATIC_DRAW)
                gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, ctypes.c_void_p(0))
                gl.glEnableVertexAttribArray(1)
                
                # Create and fill index buffer object (IBO)
                ibo = gl.glGenBuffers(1)
                gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ibo)
                gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, data['triangles'].nbytes, data['triangles'], gl.GL_STATIC_DRAW)
                
                gl.glBindVertexArray(0)
                
                data['vao'] = vao
                data['vbo_vertices'] = vbo_vertices
                data['vbo_normals'] = vbo_normals
                data['ibo'] = ibo

        # Generate grid geometry if we have mesh data
        self.grid_dirty = True

    def paintGL(self):
        """Render all meshes including grid."""
        if glm is None:
            return
        
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glViewport(0, 0, self.width(), self.height())

        # Setup geometry on first paintGL call if needed
        if self.meshes:
            needs_setup = any(data['vao'] is None for data in self.meshes.values())
            if needs_setup:
                self._setup_geometry()

        if not self.meshes:
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

        self._update_grid_if_needed()
        self._draw_grid()

        # Render each mesh
        for name, data in self.meshes.items():
            if data['vao'] is not None:
                model = glm.mat4(1.0)
                model_loc = gl.glGetUniformLocation(self.shader_id, "model")
                gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
                
                # Set mesh color
                color_loc = gl.glGetUniformLocation(self.shader_id, "meshColor")
                gl.glUniform3f(color_loc, data['color'][0], data['color'][1], data['color'][2])

                gl.glBindVertexArray(data['vao'])
                gl.glDrawElements(gl.GL_TRIANGLES, data['index_count'], gl.GL_UNSIGNED_INT, ctypes.c_void_p(0))

        # Render overlay text
        from PySide6.QtGui import QPainter, QColor, QFont
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(10, 20, self._overlay_text)
        painter.end()

    def _update_grid_if_needed(self):
        if not self.grid_dirty:
            return

        points = np.concatenate([d['vertices'] for d in self.meshes.values() if len(d['vertices']) > 0], axis=0) if self.meshes else np.zeros((0,3), np.float32)
        if points.shape[0] > 0:
            minp = points.min(axis=0)
            maxp = points.max(axis=0)
            scene_size = float(np.linalg.norm(maxp - minp))
        else:
            scene_size = 100.0
        scene_size = max(scene_size, 20.0)

        axis_extent = scene_size * 1.2
        tick_step = max(1.0, scene_size / 10.0)
        tick_size = axis_extent * 0.02

        lines = []
        colors = []

        axis_color_x = [1.0, 0.0, 0.0]
        axis_color_y = [0.0, 1.0, 0.0]
        axis_color_z = [0.0, 0.0, 1.0]

        # Axis lines
        lines.extend([[-axis_extent, 0.0, 0.0], [axis_extent, 0.0, 0.0]])
        colors.extend([axis_color_x, axis_color_x])
        lines.extend([[0.0, -axis_extent, 0.0], [0.0, axis_extent, 0.0]])
        colors.extend([axis_color_y, axis_color_y])
        lines.extend([[0.0, 0.0, -axis_extent], [0.0, 0.0, axis_extent]])
        colors.extend([axis_color_z, axis_color_z])

        # Tick marks
        for i in np.arange(-axis_extent, axis_extent + 0.0001, tick_step):
            if abs(i) < 1e-6:
                continue
            # X tick (along Z)
            lines.extend([[i, 0.0, -tick_size], [i, 0.0, tick_size]])
            colors.extend([axis_color_x, axis_color_x])
            # Y tick (along X)
            lines.extend([[-tick_size, i, 0.0], [tick_size, i, 0.0]])
            colors.extend([axis_color_y, axis_color_y])
            # Z tick (along X)
            lines.extend([[-tick_size, 0.0, i], [tick_size, 0.0, i]])
            colors.extend([axis_color_z, axis_color_z])

        lines_np = np.array(lines, dtype=np.float32)
        colors_np = np.array(colors, dtype=np.float32)

        if self.grid_vao is None:
            self.grid_vao = gl.glGenVertexArrays(1)
        if self.grid_vbo is None:
            self.grid_vbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.grid_vao)

        interleaved = np.zeros((lines_np.shape[0], 6), dtype=np.float32)
        interleaved[:, 0:3] = lines_np
        interleaved[:, 3:6] = colors_np

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.grid_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, interleaved.nbytes, interleaved, gl.GL_STATIC_DRAW)

        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(12))

        gl.glBindVertexArray(0)

        self.grid_vertex_count = lines_np.shape[0]
        self.grid_dirty = False

    def _draw_grid(self):
        if self.grid_vertex_count == 0 or self.grid_vao is None:
            return

        model = glm.mat4(1.0)
        model_loc = gl.glGetUniformLocation(self.shader_id, "model")
        gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))

        gl.glBindVertexArray(self.grid_vao)
        gl.glDrawArrays(gl.GL_LINES, 0, self.grid_vertex_count)
        gl.glBindVertexArray(0)

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
                movement = delta_x * right * 0.5 - delta_y * up * 0.5
                self.rotation_origin += movement
        
        self.last_mouse_x = current_x
        self.last_mouse_y = current_y
        self.update()

    def set_overlay_text(self, text: str):
        """Set the overlay string shown in the upper left of the widget."""
        self._overlay_text = text
        self.update()

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        self.camera_distance -= event.angleDelta().y() * 0.1
        self.camera_distance = max(10.0, self.camera_distance)
        self.update()
