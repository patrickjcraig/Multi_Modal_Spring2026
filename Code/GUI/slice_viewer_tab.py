import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QSlider, QVBoxLayout, QWidget

from Utils.image_enhancement import apply_gamma_contrast_uint8


class SliceViewerTab:
    """Encapsulates tri-planar 2D slice controls and rendering for a volume preview."""

    def __init__(self, parent=None, on_slice_changed=None):
        self._parent = parent
        self._on_slice_changed = on_slice_changed
        self._active = False
        self._volume_xyz = None
        self._active_axis = 2
        self._slice_indices = {0: 0, 1: 0, 2: 0}
        self._gamma = 1.0
        self._contrast = 1.0

        self.controls_frame = QFrame(parent)
        controls_layout = QHBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        self.controls_frame.setVisible(False)

        self.active_axis_label = QLabel("Arrow-key axis: Z")
        controls_layout.addWidget(self.active_axis_label)

        self.step_hint_label = QLabel("Use Up/Down arrows to step active axis")
        controls_layout.addWidget(self.step_hint_label, 1)

        self._axis_nav_widgets = {}
        for axis, axis_name in ((0, "X"), (1, "Y"), (2, "Z")):
            controls_layout.addWidget(QLabel(axis_name))

            nav_slider = QSlider(Qt.Horizontal)
            nav_slider.setRange(0, 0)
            nav_slider.setSingleStep(1)
            nav_slider.setPageStep(8)
            nav_slider.setEnabled(False)
            nav_slider.setMinimumWidth(90)
            nav_slider.sliderPressed.connect(lambda a=axis: self._set_active_axis(a))
            nav_slider.valueChanged.connect(lambda idx, a=axis: self._on_axis_slider_changed(a, idx, source="nav"))
            controls_layout.addWidget(nav_slider)

            nav_label = QLabel("0/0")
            controls_layout.addWidget(nav_label)

            self._axis_nav_widgets[axis] = {
                "slider": nav_slider,
                "label": nav_label,
            }

        self.enhancement_controls_frame = QFrame(parent)
        enhancement_layout = QHBoxLayout(self.enhancement_controls_frame)
        enhancement_layout.setContentsMargins(0, 0, 0, 0)
        enhancement_layout.setSpacing(8)
        self.enhancement_controls_frame.setVisible(False)

        self.gamma_label = QLabel("Gamma 1.00")
        enhancement_layout.addWidget(self.gamma_label)

        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setRange(20, 300)  # maps to [0.20, 3.00]
        self.gamma_slider.setValue(100)
        self.gamma_slider.setSingleStep(1)
        self.gamma_slider.setPageStep(10)
        self.gamma_slider.setMinimumWidth(120)
        self.gamma_slider.valueChanged.connect(self._on_gamma_changed)
        enhancement_layout.addWidget(self.gamma_slider)

        self.contrast_label = QLabel("Contrast 1.00")
        enhancement_layout.addWidget(self.contrast_label)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 300)  # maps to [0.50, 3.00]
        self.contrast_slider.setValue(100)
        self.contrast_slider.setSingleStep(1)
        self.contrast_slider.setPageStep(10)
        self.contrast_slider.setMinimumWidth(120)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        enhancement_layout.addWidget(self.contrast_slider)

        self.page = QWidget(parent)
        page_layout = QVBoxLayout(self.page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(6)

        self._axis_widgets = {}
        tri_panel = QWidget(self.page)
        tri_layout = QGridLayout(tri_panel)
        tri_layout.setContentsMargins(0, 0, 0, 0)
        tri_layout.setHorizontalSpacing(8)
        tri_layout.setVerticalSpacing(6)
        page_layout.addWidget(tri_panel, 1)

        for axis, axis_name in ((0, "X"), (1, "Y"), (2, "Z")):
            panel = QFrame(tri_panel)
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.setSpacing(4)

            title_label = QLabel(f"Slice {axis_name}")
            panel_layout.addWidget(title_label)

            image_label = QLabel("Enable Slice Viewer to inspect slices.")
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setMinimumHeight(140)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            image_label.setStyleSheet("background-color: #101010; color: #dddddd;")
            panel_layout.addWidget(image_label, 1)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 0)
            slider.setSingleStep(1)
            slider.setPageStep(8)
            slider.setEnabled(False)
            slider.sliderPressed.connect(lambda a=axis: self._set_active_axis(a))
            slider.valueChanged.connect(lambda idx, a=axis: self._on_axis_slider_changed(a, idx))
            panel_layout.addWidget(slider)

            index_label = QLabel("0 / 0")
            panel_layout.addWidget(index_label)

            tri_layout.addWidget(panel, 0, axis)
            self._axis_widgets[axis] = {
                "panel": panel,
                "title_label": title_label,
                "image_label": image_label,
                "slider": slider,
                "index_label": index_label,
            }

        self.slice_image_meta_label = QLabel("Slice: --")
        self.slice_image_meta_label.setAlignment(Qt.AlignCenter)
        page_layout.addWidget(self.slice_image_meta_label)

    def set_active(self, active: bool):
        self._active = bool(active)
        self.controls_frame.setVisible(self._active)
        self.enhancement_controls_frame.setVisible(self._active)
        if not self._active:
            for nav_data in self._axis_nav_widgets.values():
                nav_data["slider"].setEnabled(False)
                nav_data["label"].setText("0/0")
            for axis_data in self._axis_widgets.values():
                axis_data["slider"].setEnabled(False)
                axis_data["image_label"].setPixmap(QPixmap())
                axis_data["image_label"].setText("Enable Slice Viewer to inspect slices.")
            self.slice_image_meta_label.setText("Slice: --")

    def set_loading_message(self):
        for nav_data in self._axis_nav_widgets.values():
            nav_data["slider"].setEnabled(False)
            nav_data["label"].setText("0/0")
        for axis_data in self._axis_widgets.values():
            axis_data["slider"].setEnabled(False)
            axis_data["image_label"].setPixmap(QPixmap())
            axis_data["image_label"].setText("Loading volume preview for slicing...")
        self.slice_image_meta_label.setText("Slice: loading")

    def set_unavailable_message(self):
        for axis_data in self._axis_widgets.values():
            axis_data["image_label"].setPixmap(QPixmap())
            axis_data["image_label"].setText("Slice Viewer needs a volume-backed scan.")
        self.slice_image_meta_label.setText("Slice: unavailable")

    def set_error_message(self, message: str):
        for axis_data in self._axis_widgets.values():
            axis_data["image_label"].setPixmap(QPixmap())
            axis_data["image_label"].setText(f"Slice error: {message}")
        self.slice_image_meta_label.setText("Slice: error")

    def clear_volume(self):
        self._volume_xyz = None
        self._slice_indices = {0: 0, 1: 0, 2: 0}
        for nav_data in self._axis_nav_widgets.values():
            slider = nav_data["slider"]
            slider.blockSignals(True)
            slider.setRange(0, 0)
            slider.setValue(0)
            slider.blockSignals(False)
            nav_data["label"].setText("0/0")
        for axis_data in self._axis_widgets.values():
            slider = axis_data["slider"]
            slider.blockSignals(True)
            slider.setRange(0, 0)
            slider.setValue(0)
            slider.blockSignals(False)
            axis_data["index_label"].setText("0 / 0")
        self._emit_slice_changed()

    def set_volume(self, volume_xyz):
        self._volume_xyz = volume_xyz
        self._setup_slice_controls_for_volume(volume_xyz.shape)
        self._render_all_slices()
        self._emit_slice_changed()

    def step_slice(self, delta: int):
        if not self._active:
            return
        nav_data = self._axis_nav_widgets.get(int(self._active_axis))
        if nav_data is None:
            return
        slider = nav_data["slider"]
        if not slider.isEnabled():
            return
        next_value = int(slider.value()) + int(delta)
        next_value = max(slider.minimum(), min(slider.maximum(), next_value))
        if next_value != slider.value():
            slider.setValue(next_value)

    def refresh(self):
        if self._active and self._volume_xyz is not None:
            self._render_all_slices()

    def get_slice_index(self):
        return int(self._slice_indices.get(int(self._active_axis), 0))

    def get_slice_count(self):
        nav_data = self._axis_nav_widgets.get(int(self._active_axis))
        if nav_data is None:
            return 0
        slider = nav_data["slider"]
        if slider.maximum() < slider.minimum():
            return 0
        return int(slider.maximum()) + 1

    def get_slice_axis(self):
        return int(self._active_axis)

    def get_all_slice_positions(self):
        """Return all axis slice positions as {axis: (index, count)}."""
        result = {}
        for axis, axis_data in self._axis_widgets.items():
            slider = axis_data["slider"]
            count = 0 if slider.maximum() < slider.minimum() else int(slider.maximum()) + 1
            result[int(axis)] = (int(self._slice_indices[int(axis)]), int(count))
        return result

    def get_enhancement_settings(self):
        return {
            "gamma": float(self._gamma),
            "contrast": float(self._contrast),
        }

    def _setup_slice_controls_for_volume(self, shape_xyz):
        for axis, axis_data in self._axis_widgets.items():
            depth = max(1, int(shape_xyz[int(axis)]))
            max_index = depth - 1

            nav_slider = self._axis_nav_widgets[int(axis)]["slider"]
            nav_slider.blockSignals(True)
            nav_slider.setRange(0, max_index)
            nav_slider.setValue(int(self._slice_indices[int(axis)]))
            nav_slider.blockSignals(False)
            nav_slider.setEnabled(True)

            slider = axis_data["slider"]
            slider.blockSignals(True)
            slider.setRange(0, max_index)
            current_index = max(0, min(max_index, int(self._slice_indices[int(axis)])))
            self._slice_indices[int(axis)] = current_index
            slider.setValue(current_index)
            nav_slider.blockSignals(True)
            nav_slider.setValue(current_index)
            nav_slider.blockSignals(False)
            slider.blockSignals(False)
            slider.setEnabled(True)
            self._update_slice_index_label(int(axis))
        self._update_active_axis_label()

    def _on_axis_slider_changed(self, axis, index, source="panel"):
        axis = int(axis)
        self._set_active_axis(axis)
        self._slice_indices[axis] = int(index)

        # Keep 2D panel slider and 3D nav slider synchronized.
        panel_slider = self._axis_widgets[axis]["slider"]
        nav_slider = self._axis_nav_widgets[axis]["slider"]
        if source != "panel" and int(panel_slider.value()) != int(index):
            panel_slider.blockSignals(True)
            panel_slider.setValue(int(index))
            panel_slider.blockSignals(False)
        if source != "nav" and int(nav_slider.value()) != int(index):
            nav_slider.blockSignals(True)
            nav_slider.setValue(int(index))
            nav_slider.blockSignals(False)

        self._render_axis_slice(axis)
        self._update_slice_index_label(axis)
        self._emit_slice_changed()

    def _set_active_axis(self, axis):
        self._active_axis = int(axis)
        self._update_active_axis_label()

    def _update_active_axis_label(self):
        self.active_axis_label.setText(f"Arrow-key axis: {self._axis_name(self._active_axis)}")

    def _extract_slice_uint8(self, volume_xyz, axis, slice_index):
        if int(axis) == 0:
            # YZ plane sampled at X
            plane = np.asarray(volume_xyz[int(slice_index), :, :], dtype=np.uint8)
        elif int(axis) == 1:
            # XZ plane sampled at Y
            plane = np.asarray(volume_xyz[:, int(slice_index), :], dtype=np.uint8)
        else:
            # XY plane sampled at Z
            plane = np.asarray(volume_xyz[:, :, int(slice_index)], dtype=np.uint8)
        raw = np.ascontiguousarray(np.flipud(plane.T))
        return apply_gamma_contrast_uint8(raw, gamma=self._gamma, contrast=self._contrast)

    def _on_gamma_changed(self, value):
        self._gamma = max(float(value) / 100.0, 0.01)
        self.gamma_label.setText(f"Gamma {self._gamma:.2f}")
        self._render_all_slices()

    def _on_contrast_changed(self, value):
        self._contrast = max(float(value) / 100.0, 0.01)
        self.contrast_label.setText(f"Contrast {self._contrast:.2f}")
        self._render_all_slices()

    def _render_axis_slice(self, axis):
        if not self._active or self._volume_xyz is None:
            return

        axis = int(axis)
        axis_data = self._axis_widgets.get(axis)
        if axis_data is None:
            return

        max_index = max(0, int(self._volume_xyz.shape[axis]) - 1)
        self._slice_indices[axis] = max(0, min(max_index, int(self._slice_indices[axis])))

        slice_2d = self._extract_slice_uint8(self._volume_xyz, axis, self._slice_indices[axis])
        h, w = slice_2d.shape
        image = QImage(slice_2d.data, w, h, slice_2d.strides[0], QImage.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(image)

        if not pixmap.isNull():
            target = axis_data["image_label"].size()
            if target.width() > 8 and target.height() > 8:
                pixmap = pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            axis_data["image_label"].setPixmap(pixmap)
            axis_data["image_label"].setText("")

    def _render_all_slices(self):
        for axis in (0, 1, 2):
            self._render_axis_slice(axis)
            self._update_slice_index_label(axis)

    def _update_slice_index_label(self, axis):
        axis = int(axis)
        axis_data = self._axis_widgets.get(axis)
        if axis_data is None:
            return

        slider = axis_data["slider"]
        if slider.maximum() < slider.minimum():
            axis_data["index_label"].setText("0 / 0")
            self.slice_image_meta_label.setText("Slice: --")
            return

        current = int(self._slice_indices[axis]) + 1
        total = int(slider.maximum()) + 1
        axis_data["index_label"].setText(f"{current} / {total}")
        self._axis_nav_widgets[axis]["label"].setText(f"{current}/{total}")
        self.slice_image_meta_label.setText(
            f"Active axis {self._axis_name(self._active_axis)} index: {self._slice_indices[self._active_axis]} | Gamma {self._gamma:.2f} | Contrast {self._contrast:.2f}"
        )

    def _emit_slice_changed(self):
        if self._on_slice_changed is None:
            return
        self._on_slice_changed(self.get_slice_index(), self.get_slice_count(), self.get_slice_axis())

    @staticmethod
    def _axis_name(axis):
        return "XYZ"[int(axis)]
