import copy
from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractSpinBox, QButtonGroup, QMainWindow, QMessageBox
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

        # The tab widget now lives in the .ui file; clear the placeholder page.
        self.scanTabs.clear()
        self.scanTabs.setTabsClosable(True)
        self.scanTabs.setMovable(True)
        self._fit_to_screen()
        self._setup_tool_panels()

        self.setup_connections() # wire signals to the controllers above
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

    def _fit_to_screen(self):
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        self.setGeometry(screen.availableGeometry())

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
        self.btn_show_registration_tools.clicked.connect(self.show_registration_tools)
        self.btn_show_transformation_tools.clicked.connect(self.show_transformation_tools)
        self.actionRegistration_3.triggered.connect(self.show_registration_tools)
        self.actionTransformation_2.triggered.connect(self.show_transformation_tools)
        self.btn_matrix_identity.clicked.connect(self.reset_affine_matrix_to_identity)
        self.btn_matrix_load_current.clicked.connect(self.load_current_affine_matrix)
        self.btn_transform_apply_current.clicked.connect(self.apply_affine_to_current_scan)
        self.btn_transform_duplicate_current.clicked.connect(self.duplicate_with_affine_transform)

    def _setup_tool_panels(self):
        self.toolPanelGroup = QButtonGroup(self)
        self.toolPanelGroup.setExclusive(True)
        self.toolPanelGroup.addButton(self.btn_show_registration_tools)
        self.toolPanelGroup.addButton(self.btn_show_transformation_tools)
        self.combo_global_transform_model.setItemData(0, "rigid")
        self.combo_global_transform_model.setItemData(1, "similarity")

        self._matrix_spinboxes = [
            [getattr(self, f"matrix_{row}{col}") for col in range(4)]
            for row in range(4)
        ]
        for row in self._matrix_spinboxes:
            for spinbox in row:
                spinbox.setDecimals(4)
                spinbox.setRange(-100000.0, 100000.0)
                spinbox.setSingleStep(0.1)
                spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
                spinbox.setMinimumWidth(52)
                spinbox.setMaximumWidth(60)

        self.reset_affine_matrix_to_identity()
        self.show_registration_tools()

    def _on_tab_changed(self, _index):
        self._sync_selection_ui()

    def show_registration_tools(self):
        self.toolsStack.setCurrentWidget(self.page_registration_tools)
        self.btn_show_registration_tools.setChecked(True)

    def show_transformation_tools(self):
        self.toolsStack.setCurrentWidget(self.page_transformation_tools)
        self.btn_show_transformation_tools.setChecked(True)
        self._update_transform_status()

    def reset_affine_matrix_to_identity(self):
        self._set_affine_matrix_ui(np.eye(4, dtype=float))
        self.label_transform_status.setText("Identity matrix loaded.")

    def load_current_affine_matrix(self):
        record = self.current_scan()
        if record is None:
            self.label_transform_status.setText("Select a scan tab to load its matrix.")
            return

        matrix = np.array(record.metadata.get("manual_affine_matrix", np.eye(4)), dtype=float)
        self._set_affine_matrix_ui(matrix)
        self.label_transform_status.setText(f"Loaded matrix for '{record.name}'.")

    def apply_affine_to_current_scan(self):
        self._apply_affine_transform(duplicate=False)

    def duplicate_with_affine_transform(self):
        self._apply_affine_transform(duplicate=True)

    def _get_affine_matrix_ui(self):
        return np.array(
            [[spinbox.value() for spinbox in row] for row in self._matrix_spinboxes],
            dtype=float,
        )

    def _set_affine_matrix_ui(self, matrix):
        for row in range(4):
            for col in range(4):
                self._matrix_spinboxes[row][col].setValue(float(matrix[row][col]))

    def _apply_affine_transform(self, duplicate):
        record = self.current_scan()
        if record is None:
            self.label_transform_status.setText("Select a scan tab before applying a transform.")
            return
        if record.pcd is None:
            self.label_transform_status.setText("The selected tab does not contain a point cloud.")
            return
        if record.is_result:
            self.label_transform_status.setText("Choose an imported scan tab instead of a registration result.")
            return

        matrix = self._get_affine_matrix_ui()
        if matrix.shape != (4, 4):
            self.label_transform_status.setText("Affine matrix must be 4x4.")
            return
        if not np.isclose(matrix[3, 3], 1.0):
            self.label_transform_status.setText("Bottom-right matrix value should usually be 1.0.")
            return

        try:
            if duplicate:
                transformed_pcd = copy.deepcopy(record.pcd)
                transformed_pcd.transform(matrix)

                transformed_mesh = copy.deepcopy(record.mesh) if record.mesh is not None else None
                if transformed_mesh is not None:
                    transformed_mesh.transform(matrix)

                new_metadata = dict(record.metadata)
                new_metadata["manual_affine_matrix"] = matrix.tolist()
                new_metadata["Transform mode"] = "manual affine copy"

                self.add_scan_tab(
                    name=f"{record.name} (Affine)",
                    pcd=transformed_pcd,
                    mesh=transformed_mesh,
                    modality=record.modality,
                    path=record.path,
                    voxel_size_mm=record.voxel_size_mm,
                    metadata=new_metadata,
                )
                self.label_transform_status.setText(f"Created transformed copy of '{record.name}'.")
                self.statusbar.showMessage(f"Created transformed copy of '{record.name}'.")
            else:
                record.pcd.transform(matrix)
                if record.mesh is not None:
                    record.mesh.transform(matrix)
                record.metadata["manual_affine_matrix"] = matrix.tolist()
                record.metadata["Transform mode"] = "manual affine"
                self.update_scan_tab(
                    record.scan_id,
                    info_text=self._build_info_text(record.name, record.modality, record.path, record.metadata),
                    point_clouds=[(record.name, record.pcd, None)],
                    meshes=[(record.name, record.mesh, None)] if record.mesh is not None else [],
                )
                self.label_transform_status.setText(f"Applied affine transform to '{record.name}'.")
                self.statusbar.showMessage(f"Applied affine transform to '{record.name}'.")
        except Exception as exc:
            QMessageBox.critical(self, "Transform Error", str(exc))
            self.label_transform_status.setText("Failed to apply affine transform.")

        self._sync_selection_ui()

    def _update_transform_status(self):
        record = self.current_scan()
        if record is None:
            self.label_transform_status.setText("Select a scan tab to transform.")
            return

        if record.is_result:
            self.label_transform_status.setText(
                f"Current tab '{record.name}' is a registration result. Choose an imported scan."
            )
            return

        self.label_transform_status.setText(f"Ready to transform '{record.name}'.")

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
        
        # Add mesh if provided
        if mesh is not None:
            tab.set_mesh(name, mesh)

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

    def update_scan_tab(self, scan_id, title=None, info_text=None, point_clouds=None, meshes=None):
        record = self.scans.get(scan_id)
        if record is None:
            return

        if title is not None:
            record.name = title

        if info_text is not None:
            record.tab.set_info_text(info_text)

        if point_clouds is not None:
            record.tab.set_point_clouds(point_clouds)

        if meshes is not None:
            record.tab.set_meshes(meshes)

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
        self._update_transform_status()

    # functionality previously implemented here (registration steps, saving,
    # import helpers, etc.) has been moved into dedicated helper classes to keep
    # the main window lean.  See ``GUI/registration_controller.py`` and
    # ``GUI/import_controller.py`` for the full implementations.  The methods
    # above are now simple wrappers that forward to those controllers via the
    # connections established in ``setup_connections``.
