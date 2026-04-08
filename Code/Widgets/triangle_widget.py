import ctypes
import numpy as np
import OpenGL.GL as gl

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt

from Shaders.triangle_shaders import VERTEX_SHADER, FRAGMENT_SHADER

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