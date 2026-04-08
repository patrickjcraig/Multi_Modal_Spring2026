import sys
import math
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
import os

# Import the UI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "UI"))
from ui_OpenGLTest import Ui_Dialog

class OpenGLRenderer(QOpenGLWidget):
    def initializeGL(self):
        """Initialize OpenGL settings"""
        
        format : QSurfaceFormat = QSurfaceFormat()
        format.setSamples(4)
        format.setMajorVersion(3)
        format.setMinorVersion(3)

        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        
        # Set up projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / self.height() if self.height() > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def resizeGL(self, w, h):
        """Handle window resize"""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / h if h > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -3.0)
        
        # Draw a cube
        self.draw_cube()
    
    def draw_cube(self):
        """Draw a simple cube"""
        glBegin(GL_QUADS)
        
        # Front face (white)
        glColor3f(1.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0,  1.0)
        glVertex3f( 1.0, -1.0,  1.0)
        glVertex3f( 1.0,  1.0,  1.0)
        glVertex3f(-1.0,  1.0,  1.0)
        
        # Back face (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(-1.0,  1.0, -1.0)
        glVertex3f( 1.0,  1.0, -1.0)
        glVertex3f( 1.0, -1.0, -1.0)
        
        # Top face (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(-1.0,  1.0, -1.0)
        glVertex3f(-1.0,  1.0,  1.0)
        glVertex3f( 1.0,  1.0,  1.0)
        glVertex3f( 1.0,  1.0, -1.0)
        
        # Bottom face (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f( 1.0, -1.0, -1.0)
        glVertex3f( 1.0, -1.0,  1.0)
        glVertex3f(-1.0, -1.0,  1.0)
        
        # Right face (yellow)
        glColor3f(1.0, 1.0, 0.0)
        glVertex3f( 1.0, -1.0, -1.0)
        glVertex3f( 1.0,  1.0, -1.0)
        glVertex3f( 1.0,  1.0,  1.0)
        glVertex3f( 1.0, -1.0,  1.0)
        
        # Left face (cyan)
        glColor3f(0.0, 1.0, 1.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glVertex3f(-1.0, -1.0,  1.0)
        glVertex3f(-1.0,  1.0,  1.0)
        glVertex3f(-1.0,  1.0, -1.0)
        
        glEnd()

class AppTest(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle('3D Environment')
        
        # Replace the generic QOpenGLWidget with our custom OpenGLRenderer
        old_widget = self.ui.openGLWidget
        self.opengl_widget = OpenGLRenderer()
        self.opengl_widget.setGeometry(old_widget.geometry())
        self.opengl_widget.setParent(self)
        old_widget.setParent(None)
        self.ui.openGLWidget = self.opengl_widget
        
        self.resize(500, 400)

app = QApplication(sys.argv)
window = AppTest()
window.show()
sys.exit(app.exec())