import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget


class SliceViewerTab:
    """Encapsulates 2D slice controls and rendering for a volume preview."""

    def __init__(self, parent=None, on_slice_changed=None):
        self._parent = parent
        self._on_slice_changed = on_slice_changed
        self._active = False
        self._volume_xyz = None
        self._slice_axis = 2
        self._current_slice_index = 0

        self.controls_frame = QFrame(parent)
        controls_layout = QHBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        self.controls_frame.setVisible(False)

        self.slice_label = QLabel("Slice Z")
        controls_layout.addWidget(self.slice_label)

        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setRange(0, 0)
        self.slice_slider.setSingleStep(1)
        self.slice_slider.setPageStep(8)
        self.slice_slider.setEnabled(False)
        self.slice_slider.valueChanged.connect(self._on_slice_slider_changed)
        controls_layout.addWidget(self.slice_slider, 1)

        self.axis_combo = QComboBox(self.controls_frame)
        self.axis_combo.addItem("X", 0)
        self.axis_combo.addItem("Y", 1)
        self.axis_combo.addItem("Z", 2)
        self.axis_combo.setCurrentIndex(2)
        self.axis_combo.setMinimumWidth(56)
        self.axis_combo.currentIndexChanged.connect(self._on_axis_changed)
        controls_layout.addWidget(self.axis_combo)

        self.slice_index_label = QLabel("0 / 0")
        controls_layout.addWidget(self.slice_index_label)

        self.page = QWidget(parent)
        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(6)

        self.slice_image_label = QLabel("Enable Slice Viewer to inspect slices.")
        self.slice_image_label.setAlignment(Qt.AlignCenter)
        self.slice_image_label.setMinimumHeight(280)
        self.slice_image_label.setStyleSheet("background-color: #101010; color: #dddddd;")
        page_layout.addWidget(self.slice_image_label, 1)

        self.slice_image_meta_label = QLabel("Slice: --")
        self.slice_image_meta_label.setAlignment(Qt.AlignCenter)
        page_layout.addWidget(self.slice_image_meta_label)

    def set_active(self, active: bool):
        self._active = bool(active)
        self.controls_frame.setVisible(self._active)
        if not self._active:
            self.slice_slider.setEnabled(False)
            self.slice_image_label.setPixmap(QPixmap())
            self.slice_image_label.setText("Enable Slice Viewer to inspect slices.")
            self.slice_image_meta_label.setText("Slice: --")

    def set_loading_message(self):
        self.slice_slider.setEnabled(False)
        self.slice_image_label.setPixmap(QPixmap())
        self.slice_image_label.setText("Loading volume preview for slicing...")
        self.slice_image_meta_label.setText("Slice: loading")

    def set_unavailable_message(self):
        self.slice_image_label.setPixmap(QPixmap())
        self.slice_image_label.setText("Slice Viewer needs a volume-backed scan.")
        self.slice_image_meta_label.setText("Slice: unavailable")

    def set_error_message(self, message: str):
        self.slice_image_label.setPixmap(QPixmap())
        self.slice_image_label.setText(f"Slice error: {message}")
        self.slice_image_meta_label.setText("Slice: error")

    def clear_volume(self):
        self._volume_xyz = None
        self._current_slice_index = 0
        self.slice_slider.blockSignals(True)
        self.slice_slider.setRange(0, 0)
        self.slice_slider.setValue(0)
        self.slice_slider.blockSignals(False)
        self._emit_slice_changed()

    def set_volume(self, volume_xyz):
        self._volume_xyz = volume_xyz
        self._setup_slice_controls_for_volume(volume_xyz.shape)
        self._render_current_slice()
        self._emit_slice_changed()

    def step_slice(self, delta: int):
        if not self._active:
            return
        if not self.slice_slider.isEnabled():
            return
        next_value = int(self.slice_slider.value()) + int(delta)
        next_value = max(self.slice_slider.minimum(), min(self.slice_slider.maximum(), next_value))
        if next_value != self.slice_slider.value():
            self.slice_slider.setValue(next_value)

    def refresh(self):
        if self._active and self._volume_xyz is not None:
            self._render_current_slice()

    def get_slice_index(self):
        return int(self._current_slice_index)

    def get_slice_count(self):
        if self.slice_slider.maximum() < self.slice_slider.minimum():
            return 0
        return int(self.slice_slider.maximum()) + 1

    def get_slice_axis(self):
        return int(self._slice_axis)

    def _setup_slice_controls_for_volume(self, shape_xyz):
        depth = max(1, int(shape_xyz[self._slice_axis]))
        max_index = depth - 1
        self.slice_slider.blockSignals(True)
        self.slice_slider.setRange(0, max_index)
        self._current_slice_index = max(0, min(max_index, self._current_slice_index))
        self.slice_slider.setValue(self._current_slice_index)
        self.slice_slider.blockSignals(False)
        self.slice_slider.setEnabled(True)
        self._update_slice_index_label()

    def _on_slice_slider_changed(self, index):
        self._current_slice_index = int(index)
        self._render_current_slice()
        self._emit_slice_changed()

    def _on_axis_changed(self, combo_index):
        axis_value = self.axis_combo.itemData(int(combo_index))
        if axis_value is None:
            return
        self._slice_axis = int(axis_value)
        self.slice_label.setText(f"Slice {self._axis_name()}")

        if self._volume_xyz is not None:
            self._setup_slice_controls_for_volume(self._volume_xyz.shape)
            self._render_current_slice()

        self._emit_slice_changed()

    def _extract_slice_uint8(self, volume_xyz, slice_index):
        if self._slice_axis == 0:
            # YZ plane sampled at X
            plane = np.asarray(volume_xyz[int(slice_index), :, :], dtype=np.uint8)
        elif self._slice_axis == 1:
            # XZ plane sampled at Y
            plane = np.asarray(volume_xyz[:, int(slice_index), :], dtype=np.uint8)
        else:
            # XY plane sampled at Z
            plane = np.asarray(volume_xyz[:, :, int(slice_index)], dtype=np.uint8)
        return np.ascontiguousarray(np.flipud(plane.T))

    def _render_current_slice(self):
        if not self._active or self._volume_xyz is None:
            return

        max_index = max(0, int(self._volume_xyz.shape[self._slice_axis]) - 1)
        self._current_slice_index = max(0, min(max_index, int(self._current_slice_index)))

        slice_2d = self._extract_slice_uint8(self._volume_xyz, self._current_slice_index)
        h, w = slice_2d.shape
        image = QImage(slice_2d.data, w, h, slice_2d.strides[0], QImage.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(image)

        if not pixmap.isNull():
            target = self.slice_image_label.size()
            if target.width() > 8 and target.height() > 8:
                pixmap = pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.slice_image_label.setPixmap(pixmap)
            self.slice_image_label.setText("")

        self._update_slice_index_label()

    def _update_slice_index_label(self):
        if self.slice_slider.maximum() < self.slice_slider.minimum():
            self.slice_index_label.setText("0 / 0")
            self.slice_image_meta_label.setText("Slice: --")
            return

        current = int(self._current_slice_index) + 1
        total = int(self.slice_slider.maximum()) + 1
        self.slice_index_label.setText(f"{current} / {total}")
        self.slice_image_meta_label.setText(
            f"Slice {self._axis_name()} index: {self._current_slice_index} | Use Up/Down arrows for fine stepping"
        )

    def _emit_slice_changed(self):
        if self._on_slice_changed is None:
            return
        self._on_slice_changed(self.get_slice_index(), self.get_slice_count(), self.get_slice_axis())

    def _axis_name(self):
        return "XYZ"[int(self._slice_axis)]
