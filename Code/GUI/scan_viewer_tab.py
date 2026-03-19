from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from Widgets.pointcloud_widget import PointCloudWidget


class ScanViewerTab(QWidget):
    """Small container for one scan/result viewer and its summary text."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.info_label = QLabel("No scan loaded")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.viewer = PointCloudWidget(self)
        layout.addWidget(self.viewer, 1)

    def set_info_text(self, text):
        self.info_label.setText(text)

    def set_point_clouds(self, clouds):
        """Replace the displayed point clouds with ``clouds``.

        ``clouds`` is an iterable of ``(name, pcd, color)`` tuples.
        """
        self.viewer.clear_point_clouds()
        for name, pcd, color in clouds:
            self.viewer.add_point_cloud(name, pcd, color=color)
        self.viewer.update()
