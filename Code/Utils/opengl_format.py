from PySide6.QtGui import QSurfaceFormat

# Configure OpenGL surface format
def configure_opengl():
    format = QSurfaceFormat()
    format.setSamples(4)  # 4x multisampling for anti-aliasing
    format.setMajorVersion(4)
    format.setMinorVersion(1)
    format.setProfile(QSurfaceFormat.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)