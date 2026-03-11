from PySide6.QtWidgets import QMainWindow
from ui_mainwindow import Ui_MainWindow
from Widgets.triangle_widget import TriangleWidget
from GUI.workspace_controller import WorkspaceController

# split main_window responsibilities into smaller controllers
from GUI.registration_controller import RegistrationController
from GUI.import_controller import ImportController

class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')
        
        # controllers encapsulate the bulk of the logic so the window stays small
        self.workspace_controller = WorkspaceController(self)
        self.registration = RegistrationController(self)
        self.importer = ImportController(self)

        # Replace the placeholder OpenGL widget with our custom triangle widget
        self._setup_opengl_widget()
        
        self.setup_connections() # wire signals to the controllers above

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
        # wire widget signals to the helper controllers rather than implementing
        # all of the logic directly in this class.  ``RegistrationController`` and
        # ``ImportController`` are both created in __init__.
        self.toolButton.clicked.connect(self.registration.run_scan)
        self.toolButton_2.clicked.connect(self.registration.save_dataframes)
        self.toolButton_3.clicked.connect(self.importer.ct_demo)

        self.btn_prev_step.clicked.connect(self.registration.prev_step)
        self.btn_next_step.clicked.connect(self.registration.next_step)

        self.actionSave_Workspace.triggered.connect(self.workspace_controller.save)
        self.actionLoad_Workspace.triggered.connect(self.workspace_controller.load)

        self.actionImport_XRay.triggered.connect(self.importer.open_xray_dialog)

    # functionality previously implemented here (registration steps, saving,
    # import helpers, etc.) has been moved into dedicated helper classes to keep
    # the main window lean.  See ``GUI/registration_controller.py`` and
    # ``GUI/import_controller.py`` for the full implementations.  The methods
    # above are now simple wrappers that forward to those controllers via the
    # connections established in ``setup_connections``.