import ctypes
import math
import numpy as np
import OpenGL.GL as gl

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

from Shaders.pointcloud_shaders import POINT_VERTEX_SHADER, POINT_FRAGMENT_SHADER
from Shaders.mesh_shaders import MESH_VERTEX_SHADER, MESH_FRAGMENT_SHADER

try:
    import glm
except ImportError:
    print("Warning: PyGLM not installed. Please install it with: pip install PyGLM")
    glm = None

class PointCloudWidget(QOpenGLWidget):
    """
    OpenGL widget for rendering point clouds and meshes from open3d.
    Supports multiple point clouds and meshes with different colors and transformations.

    Toggle between point cloud and mesh visibility using Ctrl+M from ScanViewerTab.
    The widget can optionally display overlay text (e.g. "RANSAC 5/100")
    in the top‑left corner; the text is set with :meth:`set_overlay_text`.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.point_clouds = {}  # Dictionary to store point cloud data {name: {vertices, colors, VAO, VBO}}
        self.meshes = {}        # Dictionary to store mesh data {name: {vertices, normals, triangles, VAO, VBOs, IBO}}
        self.point_shader_id = None
        self.mesh_shader_id = None
        # overlay text rendered with QPainter after OpenGL draw
        self._overlay_text = ""
        
        # Camera parameters
        self.camera_distance = 300.0
        self.camera_angle_x = 30.0
        self.camera_angle_y = 45.0
        self.rotation_origin = glm.vec3(0.0, 0.0, 0.0) if glm else None
        self.world_up = glm.vec3(0.0, 0.0, 1.0) if glm else None

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
        
        # Visibility and opacity control
        self.pointcloud_opacity = 1.0
        self.mesh_opacity = 0.0
        self.show_pointcloud = True
        self.show_mesh = False

        # Match the xrayrecon/pyqtgraph volume scene so toggling views feels
        # continuous: dark background, muted grid, and bright RGB axes.
        self.background_color = (0.0, 0.0, 0.0, 1.0)
        self.grid_color = (0.32, 0.32, 0.32)
        self.grid_major_color = (0.48, 0.48, 0.48)
        self.axis_colors = {
            "x": (1.0, 0.0, 0.0),
            "y": (0.0, 1.0, 0.0),
            "z": (0.0, 0.0, 1.0),
        }

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

        self.grid_dirty = True

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
            'color': color if color is not None else (0.55, 0.75, 1.0)
        }

        self.grid_dirty = True

    def clear_point_clouds(self):
        """Remove all point clouds from the viewer."""
        self.point_clouds.clear()
        self.grid_dirty = True

    def clear_meshes(self):
        """Remove all meshes from the viewer."""
        self.meshes.clear()
        self.grid_dirty = True

    def toggle_pointcloud_mesh_view(self):
        """Toggle visibility between point cloud and mesh."""
        if self.show_pointcloud:
            # Switch to mesh view
            self.pointcloud_opacity = 0.0
            self.mesh_opacity = 1.0
            self.show_pointcloud = False
            self.show_mesh = True
        else:
            # Switch back to point cloud view
            self.pointcloud_opacity = 1.0
            self.mesh_opacity = 0.0
            self.show_pointcloud = True
            self.show_mesh = False
        
        self.update()

    def _camera_position(self):
        """Return camera position using pyqtgraph/xrayrecon-style z-up axes."""
        pitch = math.radians(self.camera_angle_x)
        yaw = math.radians(self.camera_angle_y)
        camera_x = self.camera_distance * math.sin(yaw) * math.cos(pitch)
        camera_y = self.camera_distance * math.cos(yaw) * math.cos(pitch)
        camera_z = self.camera_distance * math.sin(pitch)
        return self.rotation_origin + glm.vec3(camera_x, camera_y, camera_z)

    def get_camera_state(self):
        """Return current camera state for cross-view synchronization."""
        if glm is None:
            return None
        return {
            "distance": float(self.camera_distance),
            "pitch_deg": float(self.camera_angle_x),
            "yaw_deg": float(self.camera_angle_y),
            "origin_xyz": (
                float(self.rotation_origin.x),
                float(self.rotation_origin.y),
                float(self.rotation_origin.z),
            ),
        }

    def get_scene_bounds(self):
        """Return geometry bounds as (min_xyz, max_xyz) or None if empty."""
        cloud_blocks = [d['points'] for d in self.point_clouds.values() if len(d['points']) > 0]
        mesh_blocks = [d['vertices'] for d in self.meshes.values() if len(d['vertices']) > 0]
        blocks = cloud_blocks + mesh_blocks
        if not blocks:
            return None

        pts = np.concatenate(blocks, axis=0)
        minp = pts.min(axis=0)
        maxp = pts.max(axis=0)
        return (
            (float(minp[0]), float(minp[1]), float(minp[2])),
            (float(maxp[0]), float(maxp[1]), float(maxp[2])),
        )

    def initializeGL(self):
        """Initialize OpenGL context and shaders."""
        gl.glClearColor(*self.background_color)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)
        gl.glPointSize(2.0)
        
        # Compile shaders
        self._load_shaders()
        
        # Setup VAOs/VBOs for all point clouds
        if self.point_clouds:
            self._setup_point_cloud_geometry()
        
        # Setup VAOs/VBOs for all meshes
        if self.meshes:
            self._setup_mesh_geometry()

    def _load_shaders(self):
        """Compile and link both point cloud and mesh shaders."""
        # Load point cloud shader
        self.point_shader_id = gl.glCreateProgram()
        
        vertex_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex_id, POINT_VERTEX_SHADER)
        gl.glCompileShader(vertex_id)
        self._check_shader_compilation(vertex_id)
        
        fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment_id, POINT_FRAGMENT_SHADER)
        gl.glCompileShader(fragment_id)
        self._check_shader_compilation(fragment_id)
        
        gl.glAttachShader(self.point_shader_id, vertex_id)
        gl.glAttachShader(self.point_shader_id, fragment_id)
        gl.glLinkProgram(self.point_shader_id)
        
        gl.glDeleteShader(vertex_id)
        gl.glDeleteShader(fragment_id)
        
        # Load mesh shader
        self.mesh_shader_id = gl.glCreateProgram()
        
        mesh_vertex_id = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(mesh_vertex_id, MESH_VERTEX_SHADER)
        gl.glCompileShader(mesh_vertex_id)
        self._check_shader_compilation(mesh_vertex_id)
        
        mesh_fragment_id = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(mesh_fragment_id, MESH_FRAGMENT_SHADER)
        gl.glCompileShader(mesh_fragment_id)
        self._check_shader_compilation(mesh_fragment_id)
        
        gl.glAttachShader(self.mesh_shader_id, mesh_vertex_id)
        gl.glAttachShader(self.mesh_shader_id, mesh_fragment_id)
        gl.glLinkProgram(self.mesh_shader_id)
        
        gl.glDeleteShader(mesh_vertex_id)
        gl.glDeleteShader(mesh_fragment_id)

    def _check_shader_compilation(self, shader_id):
        """Check if shader compiled successfully."""
        if not gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS):
            print(gl.glGetShaderInfoLog(shader_id))
            raise RuntimeError("Shader compilation failed")

    def _setup_point_cloud_geometry(self):
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

        # If we have cloud data, we will generate grid geometry too
        self.grid_dirty = True

    def _setup_mesh_geometry(self):
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

        self.grid_dirty = True


    def paintGL(self):
        """Render all point clouds and meshes including grid."""
        if glm is None:
            return
        
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glViewport(0, 0, self.width(), self.height())

        # Setup geometry on first paintGL call if needed
        if self.point_clouds:
            needs_setup = any(data['vao'] is None for data in self.point_clouds.values())
            if needs_setup:
                self._setup_point_cloud_geometry()
        
        if self.meshes:
            needs_setup = any(data['vao'] is None for data in self.meshes.values())
            if needs_setup:
                self._setup_mesh_geometry()

        # Return early if nothing to render
        if not self.point_clouds and not self.meshes:
            return

        # Setup projection matrix (shared by both shaders)
        aspect = self.width() / max(self.height(), 1)
        projection = glm.perspective(glm.radians(45.0), aspect, 0.1, 10000.0)

        # Setup view matrix with z-up camera controls to match pyqtgraph/xrayrecon.
        camera_pos = self._camera_position()
        view = glm.lookAt(
            camera_pos,
            self.rotation_origin,
            self.world_up
        )
        self.view = view
        self.projection = projection

        self._update_grid_if_needed()
        self._draw_grid(projection, view)

        # Render point clouds if visible
        if self.pointcloud_opacity > 0.0 and self.point_clouds:
            gl.glUseProgram(self.point_shader_id)
            
            proj_loc = gl.glGetUniformLocation(self.point_shader_id, "projection")
            gl.glUniformMatrix4fv(proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))
            
            view_loc = gl.glGetUniformLocation(self.point_shader_id, "view")
            gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))

            for name, data in self.point_clouds.items():
                if data['vao'] is not None:
                    model = glm.mat4(1.0)
                    model_loc = gl.glGetUniformLocation(self.point_shader_id, "model")
                    gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))

                    gl.glBindVertexArray(data['vao'])
                    gl.glDrawArrays(gl.GL_POINTS, 0, data['vertex_count'])

        # Render meshes if visible
        if self.mesh_opacity > 0.0 and self.meshes:
            gl.glUseProgram(self.mesh_shader_id)
            
            proj_loc = gl.glGetUniformLocation(self.mesh_shader_id, "projection")
            gl.glUniformMatrix4fv(proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))
            
            view_loc = gl.glGetUniformLocation(self.mesh_shader_id, "view")
            gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))

            for name, data in self.meshes.items():
                if data['vao'] is not None:
                    model = glm.mat4(1.0)
                    model_loc = gl.glGetUniformLocation(self.mesh_shader_id, "model")
                    gl.glUniformMatrix4fv(model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
                    
                    # Set mesh color
                    color_loc = gl.glGetUniformLocation(self.mesh_shader_id, "meshColor")
                    gl.glUniform3f(color_loc, data['color'][0], data['color'][1], data['color'][2])

                    gl.glBindVertexArray(data['vao'])
                    gl.glDrawElements(gl.GL_TRIANGLES, data['index_count'], gl.GL_UNSIGNED_INT, ctypes.c_void_p(0))

        # Render overlay text if present
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

        # Collect points from both point clouds and meshes for grid sizing.
        pc_points = np.concatenate([d['points'] for d in self.point_clouds.values() if len(d['points']) > 0], axis=0) if self.point_clouds else np.zeros((0,3), np.float32)
        mesh_points = np.concatenate([d['vertices'] for d in self.meshes.values() if len(d['vertices']) > 0], axis=0) if self.meshes else np.zeros((0,3), np.float32)
        points = np.concatenate([pc_points, mesh_points], axis=0) if (pc_points.shape[0] > 0 or mesh_points.shape[0] > 0) else np.zeros((0,3), np.float32)
        
        if points.shape[0] > 0:
            minp = points.min(axis=0)
            maxp = points.max(axis=0)
            scene_size = float(max(np.max(maxp - minp), 1.0))
        else:
            scene_size = 100.0
        scene_size = max(scene_size, 20.0)

        axis_extent = scene_size * 0.75
        grid_extent = axis_extent
        tick_step = max(1.0, scene_size / 10.0)
        tick_size = axis_extent * 0.02

        lines = []
        colors = []

        axis_color_x = list(self.axis_colors["x"])
        axis_color_y = list(self.axis_colors["y"])
        axis_color_z = list(self.axis_colors["z"])
        grid_color = list(self.grid_color)
        grid_major_color = list(self.grid_major_color)

        # Pyqtgraph-like XY floor grid at Z=0.
        for i in np.arange(-grid_extent, grid_extent + 0.0001, tick_step):
            major = abs(i) < 1e-6
            color = grid_major_color if major else grid_color
            lines.extend([[-grid_extent, i, 0.0], [grid_extent, i, 0.0]])
            colors.extend([color, color])
            lines.extend([[i, -grid_extent, 0.0], [i, grid_extent, 0.0]])
            colors.extend([color, color])

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

    def _draw_grid(self, projection, view):
        if self.grid_vertex_count == 0 or self.grid_vao is None:
            return

        gl.glUseProgram(self.point_shader_id)

        # Keep axes/grid camera transform independent of whether point clouds are visible.
        proj_loc = gl.glGetUniformLocation(self.point_shader_id, "projection")
        gl.glUniformMatrix4fv(proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection))

        view_loc = gl.glGetUniformLocation(self.point_shader_id, "view")
        gl.glUniformMatrix4fv(view_loc, 1, gl.GL_FALSE, glm.value_ptr(view))
        
        model = glm.mat4(1.0)
        model_loc = gl.glGetUniformLocation(self.point_shader_id, "model")
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
        
        ctrl_left_drag = (event.buttons() & Qt.LeftButton) and (event.modifiers() & Qt.ControlModifier)
        left_drag = (event.buttons() & Qt.LeftButton) and not (event.modifiers() & Qt.ControlModifier)

        if left_drag:
            # Rotate view
            self.camera_angle_y += delta_x * 0.5
            self.camera_angle_x += delta_y * 0.5
            self.camera_angle_x = max(-85, min(85, self.camera_angle_x))
        elif ctrl_left_drag:
            # Move rotation origin in view plane
            if glm is not None:
                camera_pos = self._camera_position()

                # View direction from camera to rotation origin
                view_dir = glm.normalize(self.rotation_origin - camera_pos)

                # Right vector (perpendicular to view and world up)
                right = glm.cross(view_dir, self.world_up)
                if glm.length(right) < 1e-6:
                    right = glm.vec3(1.0, 0.0, 0.0)
                right = glm.normalize(right)

                # Up vector in view plane
                up = glm.normalize(glm.cross(right, view_dir))

                # Move rotation origin in view plane
                # Invert pan direction to match pyqtgraph camera interaction.
                movement = -delta_x * right * 0.5 + delta_y * up * 0.5
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
