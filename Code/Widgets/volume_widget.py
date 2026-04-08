import numpy as np

from PySide6.QtGui import QVector3D
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    import pyqtgraph.opengl as gl
except ImportError:
    gl = None


class VolumeRenderWidget(QWidget):
    """Unified pyqtgraph GL viewer for point clouds, meshes, and volume previews."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._volume_item = None
        self._grid_item = None
        self._axes_item = None
        self._volume_loaded = False
        self._volume_mode = False

        self.point_clouds = {}
        self.meshes = {}
        self.show_pointcloud = True
        self.show_mesh = False
        self._overlay_text = ""

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
        self._axes_item = gl.GLAxisItem()
        self._view.addItem(self._axes_item)

        empty = np.zeros((1, 1, 1, 4), dtype=np.ubyte)
        self._volume_item = gl.GLVolumeItem(empty)
        self._view.addItem(self._volume_item)
        self._volume_item.setVisible(False)

        self._overlay_label = QLabel(self)
        self._overlay_label.setStyleSheet("color: white; background: transparent;")
        self._overlay_label.move(10, 10)
        self._overlay_label.hide()

        self._update_reference_items()

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
        self._volume_loaded = True

        max_dim = max(data.shape) if data.size else 1
        self._view.setCameraPosition(distance=max(25, max_dim * 2))

        self._apply_visibility()

    def add_point_cloud(self, name, pcd, color=None):
        if not self.is_available():
            return

        points = np.asarray(pcd.points, dtype=np.float32)
        if points.size == 0:
            return

        if color is not None:
            colors = np.full((len(points), 4), [color[0], color[1], color[2], 1.0], dtype=np.float32)
        elif pcd.has_colors():
            c = np.asarray(pcd.colors, dtype=np.float32)
            colors = np.concatenate([c, np.ones((len(c), 1), dtype=np.float32)], axis=1)
        else:
            colors = np.ones((len(points), 4), dtype=np.float32)

        # Use pixel-sized markers so points keep a consistent on-screen size
        # and do not appear as large world-space spheres when zooming/panning.
        item = gl.GLScatterPlotItem(pos=points, color=colors, size=2.0, pxMode=True)
        self._view.addItem(item)
        self.point_clouds[name] = {"points": points, "item": item}
        self._update_reference_items()
        self._apply_visibility()

    def add_mesh(self, name, mesh, color=None):
        if not self.is_available():
            return

        vertices = np.asarray(mesh.vertices, dtype=np.float32)
        faces = np.asarray(mesh.triangles, dtype=np.int32)
        if vertices.size == 0 or faces.size == 0:
            return

        mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
        rgba = (0.55, 0.75, 1.0, 1.0) if color is None else (color[0], color[1], color[2], 1.0)
        item = gl.GLMeshItem(
            meshdata=mesh_data,
            smooth=True,
            drawFaces=True,
            drawEdges=False,
            color=rgba,
            shader="shaded",
        )
        self._view.addItem(item)
        self.meshes[name] = {"vertices": vertices, "item": item}
        self._update_reference_items()
        self._apply_visibility()

    def clear_point_clouds(self):
        if not self.is_available():
            self.point_clouds.clear()
            return
        for data in self.point_clouds.values():
            self._view.removeItem(data["item"])
        self.point_clouds.clear()
        self._update_reference_items()

    def clear_meshes(self):
        if not self.is_available():
            self.meshes.clear()
            return
        for data in self.meshes.values():
            self._view.removeItem(data["item"])
        self.meshes.clear()
        self._update_reference_items()

    def toggle_pointcloud_mesh_view(self):
        self.show_pointcloud = not self.show_pointcloud
        self.show_mesh = not self.show_mesh
        self._apply_visibility()

    def set_volume_mode(self, enabled):
        self._volume_mode = bool(enabled)
        self._apply_visibility()

    def _apply_visibility(self):
        if not self.is_available():
            return

        show_geom = not self._volume_mode
        for data in self.point_clouds.values():
            data["item"].setVisible(show_geom and self.show_pointcloud)
        for data in self.meshes.values():
            data["item"].setVisible(show_geom and self.show_mesh)

        if self._volume_item is not None:
            self._volume_item.setVisible(self._volume_mode and self._volume_loaded)

    def get_scene_bounds(self):
        blocks = [d["points"] for d in self.point_clouds.values() if len(d["points"]) > 0]
        blocks += [d["vertices"] for d in self.meshes.values() if len(d["vertices"]) > 0]
        if not blocks:
            return None
        pts = np.concatenate(blocks, axis=0)
        minp = pts.min(axis=0)
        maxp = pts.max(axis=0)
        return (
            (float(minp[0]), float(minp[1]), float(minp[2])),
            (float(maxp[0]), float(maxp[1]), float(maxp[2])),
        )

    def get_camera_state(self):
        if not self.is_available():
            return None

        distance = float(self._view.opts.get("distance", 200.0))
        pitch = float(self._view.opts.get("elevation", 30.0))
        azimuth = float(self._view.opts.get("azimuth", 45.0))
        center = self._view.opts.get("center", QVector3D(0.0, 0.0, 0.0))
        yaw = 90.0 - azimuth

        return {
            "distance": distance,
            "pitch_deg": pitch,
            "yaw_deg": yaw,
            "origin_xyz": (float(center.x()), float(center.y()), float(center.z())),
        }

    def set_overlay_text(self, text: str):
        self._overlay_text = text or ""
        if not hasattr(self, "_overlay_label"):
            return
        self._overlay_label.setText(self._overlay_text)
        self._overlay_label.setVisible(bool(self._overlay_text))

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
        self._update_reference_items((bounds_min_xyz, bounds_max_xyz))

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_overlay_label"):
            self._overlay_label.adjustSize()

    def _update_reference_items(self, bounds=None):
        """Resize and position the grid/axes to match the current scene."""
        if not self.is_available():
            return

        if bounds is None:
            bounds = self.get_scene_bounds()

        if bounds is None:
            minx = miny = minz = -10.0
            maxx = maxy = maxz = 10.0
        else:
            (minx, miny, minz), (maxx, maxy, maxz) = bounds

        sizex = max(float(maxx - minx), 1.0)
        sizey = max(float(maxy - miny), 1.0)
        sizez = max(float(maxz - minz), 1.0)
        extent = max(sizex, sizey, sizez, 20.0)
        spacing = max(extent / 20.0, 0.1)
        centerx = (float(minx) + float(maxx)) * 0.5
        centery = (float(miny) + float(maxy)) * 0.5
        plane_z = min(float(minz), 0.0)

        if self._grid_item is not None:
            self._grid_item.setSpacing(spacing, spacing, 1.0)
            self._grid_item.setSize(extent * 2.0, extent * 2.0, 1.0)
            self._grid_item.resetTransform()
            self._grid_item.translate(centerx, centery, plane_z)

        if self._axes_item is not None:
            self._axes_item.setSize(extent * 0.25, extent * 0.25, extent * 0.25)
