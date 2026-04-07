import numpy as np

from PySide6.QtGui import QVector3D
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

    def align_volume_to_world_bounds(self, volume_shape_xyz, bounds_min_xyz, bounds_max_xyz):
        """Scale/translate volume item so [0..Nx,0..Ny,0..Nz] maps into world bounds."""
        if not self.is_available() or self._volume_item is None:
            return

        nx, ny, nz = [max(int(v), 1) for v in volume_shape_xyz]
        minx, miny, minz = [float(v) for v in bounds_min_xyz]
        maxx, maxy, maxz = [float(v) for v in bounds_max_xyz]

        sx = (maxx - minx) / float(max(nx - 1, 1))
        sy = (maxy - miny) / float(max(ny - 1, 1))
        sz = (maxz - minz) / float(max(nz - 1, 1))

        self._volume_item.resetTransform()
        # Translate first so translation is not scaled by the subsequent scale.
        self._volume_item.translate(minx, miny, minz)
        self._volume_item.scale(sx, sy, sz)

    def set_camera_from_geometry_state(self, camera_state):
        """Apply geometry viewer camera state to the pyqtgraph camera."""
        if not self.is_available() or camera_state is None:
            return

        distance = float(camera_state.get("distance", 200.0))
        pitch = float(camera_state.get("pitch_deg", 30.0))
        yaw = float(camera_state.get("yaw_deg", 45.0))
        origin = camera_state.get("origin_xyz", (0.0, 0.0, 0.0))

        # PointCloudWidget yaw 0deg looks along +Y. pyqtgraph azimuth 0deg looks along +X.
        azimuth = 90.0 - yaw

        self._view.opts["center"] = QVector3D(float(origin[0]), float(origin[1]), float(origin[2]))
        self._view.setCameraPosition(distance=max(distance, 1.0), elevation=pitch, azimuth=azimuth)
