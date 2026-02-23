import sys
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
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
    
    def resizeGL(self, w, h):
        """Handle window resize"""
        glViewport(0, 0, w, h)
    
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

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