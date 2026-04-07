import numpy as np

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    import pyqtgraph.opengl as gl
except ImportError:
    gl = None


class VolumeRenderWidget(QWidget):
    """Render uint8 XYZ volume previews using pyqtgraph's GLVolumeItem."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._volume_item = None
        self._grid_item = None

        if gl is None:
            label = QLabel(
                "3D volume view requires pyqtgraph.\n"
                "Install it with: pip install pyqtgraph"
            )
            label.setWordWrap(True)
            layout.addWidget(label)
            self._view = None
            return

        self._view = gl.GLViewWidget()
        self._view.opts["distance"] = 200
        self._view.setBackgroundColor("k")
        layout.addWidget(self._view, 1)

        self._grid_item = gl.GLGridItem()
        self._view.addItem(self._grid_item)
        self._view.addItem(gl.GLAxisItem())

        empty = np.zeros((1, 1, 1, 4), dtype=np.ubyte)
        self._volume_item = gl.GLVolumeItem(empty)
        self._view.addItem(self._volume_item)

    def is_available(self):
        return self._view is not None

    def set_volume(self, data_xyz, transparency_factor=3.0):
        """Upload an XYZ uint8 volume to the OpenGL volume item."""
        if not self.is_available():
            return

        data = np.ascontiguousarray(data_xyz, dtype=np.uint8)
        rgba = np.empty(data.shape + (4,), dtype=np.ubyte)
        rgba[..., 0:3] = data[..., None]

        alpha = ((data.astype(np.float32) * 0.6) / 255.0) ** float(transparency_factor)
        rgba[..., 3] = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.ubyte)

        if data.shape[0] > 0:
            rgba[:, 0, 0] = [255, 0, 0, 140]
        if data.shape[1] > 0:
            rgba[0, :, 0] = [0, 255, 0, 140]
        if data.shape[2] > 0:
            rgba[0, 0, :] = [0, 0, 255, 140]

        self._volume_item.setData(rgba)

        max_dim = max(data.shape) if data.size else 1
        self._view.setCameraPosition(distance=max(25, max_dim * 2))

        if self._grid_item is not None:
            self._grid_item.resetTransform()
            self._grid_item.scale(max(data.shape[0], 1), max(data.shape[1], 1), 1)
