from dataclasses import dataclass, field
from uuid import uuid4

from PySide6.QtWidgets import QMainWindow, QTabWidget
from ui_mainwindow import Ui_MainWindow
from GUI.workspace_controller import WorkspaceController
from GUI.scan_viewer_tab import ScanViewerTab

# split main_window responsibilities into smaller controllers
from GUI.registration_controller import RegistrationController
from GUI.import_controller import ImportController


@dataclass
class ScanRecord:
    scan_id: str
    name: str
    modality: str
    path: str = ""
    voxel_size_mm: float | None = None
    pcd: object | None = None
    mesh: object | None = None
    tab: object | None = None
    is_result: bool = False
    metadata: dict = field(default_factory=dict)


class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')

        self.scans = {}
        self.source_scan_id = None
        self.target_scan_id = None

        # controllers encapsulate the bulk of the logic so the window stays small
        self.workspace_controller = WorkspaceController(self)
        self.registration = RegistrationController(self)
        self.importer = ImportController(self)

        # Replace the placeholder OpenGL widget with a tabbed scan workspace.
        self._setup_scan_tabs()

        self.setup_connections() # wire signals to the controllers above
        self._configure_action_buttons()
        self._sync_selection_ui()

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

    def _setup_scan_tabs(self):
        """Replace the placeholder OpenGL widget with a tabbed viewer area."""
        geometry = self.openGLWidget.geometry()
        parent = self.openGLWidget.parent()

        self.openGLWidget.setParent(None)
        self.openGLWidget.deleteLater()

        self.scanTabs = QTabWidget(parent)
        self.scanTabs.setObjectName("scanTabs")
        self.scanTabs.setGeometry(geometry)
        self.scanTabs.setTabsClosable(True)
        self.scanTabs.setMovable(True)
        self.scanTabs.show()

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
        self.toolButton_4.clicked.connect(self.mark_current_as_source)
        self.toolButton_5.clicked.connect(self.mark_current_as_target)
        self.scanTabs.currentChanged.connect(self._on_tab_changed)
        self.scanTabs.tabCloseRequested.connect(self.remove_scan_tab)

    def _configure_action_buttons(self):
        self.toolButton_4.setText("Set Current As Source")
        self.toolButton_5.setText("Set Current As Target")
        self.label.setText("Scans Workspace")

    def _on_tab_changed(self, _index):
        self._sync_selection_ui()

    def current_scan_id(self):
        index = self.scanTabs.currentIndex()
        if index < 0:
            return None

        tab = self.scanTabs.widget(index)
        for scan_id, record in self.scans.items():
            if record.tab is tab:
                return scan_id
        return None

    def current_scan(self):
        scan_id = self.current_scan_id()
        return self.scans.get(scan_id)

    def add_scan_tab(
        self,
        name,
        pcd=None,
        mesh=None,
        modality="scan",
        path="",
        voxel_size_mm=None,
        metadata=None,
        is_result=False,
        make_current=True,
    ):
        metadata = metadata or {}
        scan_id = str(uuid4())
        tab = ScanViewerTab(self.scanTabs)
        tab.set_info_text(self._build_info_text(name, modality, path, metadata))
        if pcd is not None:
            tab.set_point_clouds([(name, pcd, None)])

        self.scans[scan_id] = ScanRecord(
            scan_id=scan_id,
            name=name,
            modality=modality,
            path=path,
            voxel_size_mm=voxel_size_mm,
            pcd=pcd,
            mesh=mesh,
            tab=tab,
            is_result=is_result,
            metadata=dict(metadata),
        )

        index = self.scanTabs.addTab(tab, name)
        if make_current:
            self.scanTabs.setCurrentIndex(index)

        self._sync_selection_ui()
        return scan_id

    def update_scan_tab(self, scan_id, title=None, info_text=None, point_clouds=None):
        record = self.scans.get(scan_id)
        if record is None:
            return

        if title is not None:
            record.name = title

        if info_text is not None:
            record.tab.set_info_text(info_text)

        if point_clouds is not None:
            record.tab.set_point_clouds(point_clouds)

        index = self.scanTabs.indexOf(record.tab)
        if index >= 0:
            self.scanTabs.setTabText(index, self._display_title(record))

    def remove_scan_tab(self, index):
        tab = self.scanTabs.widget(index)
        if tab is None:
            return

        removed_scan_id = None
        for scan_id, record in list(self.scans.items()):
            if record.tab is tab:
                removed_scan_id = scan_id
                del self.scans[scan_id]
                break

        self.scanTabs.removeTab(index)
        tab.deleteLater()

        if removed_scan_id == self.source_scan_id:
            self.source_scan_id = None
        if removed_scan_id == self.target_scan_id:
            self.target_scan_id = None

        self._sync_selection_ui()

    def clear_scan_tabs(self):
        while self.scanTabs.count():
            self.remove_scan_tab(0)

    def mark_current_as_source(self):
        record = self.current_scan()
        if record is None:
            self.statusbar.showMessage("Import or create a scan tab first.")
            return
        if record.is_result:
            self.statusbar.showMessage("Choose an imported scan tab as the source input.")
            return
        self.source_scan_id = record.scan_id
        self._sync_selection_ui()
        self.statusbar.showMessage(f"Source scan set to '{record.name}'.")

    def mark_current_as_target(self):
        record = self.current_scan()
        if record is None:
            self.statusbar.showMessage("Import or create a scan tab first.")
            return
        if record.is_result:
            self.statusbar.showMessage("Choose an imported scan tab as the target input.")
            return
        self.target_scan_id = record.scan_id
        self._sync_selection_ui()
        self.statusbar.showMessage(f"Target scan set to '{record.name}'.")

    def get_registration_pair(self):
        source = self.scans.get(self.source_scan_id)
        target = self.scans.get(self.target_scan_id)
        return source, target

    def _build_info_text(self, name, modality, path, metadata):
        parts = [f"Name: {name}", f"Mode: {modality}"]
        if path:
            parts.append(f"Path: {path}")
        for key, value in metadata.items():
            parts.append(f"{key}: {value}")
        return " | ".join(parts)

    def _display_title(self, record):
        title = record.name
        markers = []
        if record.scan_id == self.source_scan_id:
            markers.append("S")
        if record.scan_id == self.target_scan_id:
            markers.append("T")
        if markers:
            title = f"[{'/'.join(markers)}] {title}"
        return title

    def _sync_selection_ui(self):
        for index in range(self.scanTabs.count()):
            tab = self.scanTabs.widget(index)
            for record in self.scans.values():
                if record.tab is tab:
                    self.scanTabs.setTabText(index, self._display_title(record))
                    break

        source = self.scans.get(self.source_scan_id)
        target = self.scans.get(self.target_scan_id)

        source_name = source.name if source is not None else "Unset"
        target_name = target.name if target is not None else "Unset"
        self.toolButton_4.setToolTip(f"Source scan: {source_name}")
        self.toolButton_5.setToolTip(f"Target scan: {target_name}")
        self.label_step_info.setText(f"Source: {source_name} | Target: {target_name}")

    # functionality previously implemented here (registration steps, saving,
    # import helpers, etc.) has been moved into dedicated helper classes to keep
    # the main window lean.  See ``GUI/registration_controller.py`` and
    # ``GUI/import_controller.py`` for the full implementations.  The methods
    # above are now simple wrappers that forward to those controllers via the
    # connections established in ``setup_connections``.
