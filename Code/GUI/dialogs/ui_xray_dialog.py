# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'xray_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QComboBox,
    QDialog, QDialogButtonBox, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpinBox, QWidget)

class Ui_XRayDialog(object):
    def setupUi(self, XRayDialog):
        if not XRayDialog.objectName():
            XRayDialog.setObjectName(u"XRayDialog")
        XRayDialog.resize(403, 328)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(XRayDialog.sizePolicy().hasHeightForWidth())
        XRayDialog.setSizePolicy(sizePolicy)
        XRayDialog.setAutoFillBackground(False)
        XRayDialog.setStyleSheet(u"background-color: #d3d3d3;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.buttonBox = QDialogButtonBox(XRayDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(300, 280, 91, 41))
        self.buttonBox.setAutoFillBackground(False)
        self.buttonBox.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(True)
        self.line_path = QLineEdit(XRayDialog)
        self.line_path.setObjectName(u"line_path")
        self.line_path.setGeometry(QRect(140, 60, 181, 31))
        self.line_path.setAutoFillBackground(False)
        self.line_path.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.combo_import_type = QComboBox(XRayDialog)
        self.combo_import_type.addItem("")
        self.combo_import_type.addItem("")
        self.combo_import_type.addItem("")
        self.combo_import_type.setObjectName(u"combo_import_type")
        self.combo_import_type.setGeometry(QRect(140, 20, 221, 31))
        self.combo_import_type.setAutoFillBackground(True)
        self.combo_import_type.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.btn_browse = QPushButton(XRayDialog)
        self.btn_browse.setObjectName(u"btn_browse")
        self.btn_browse.setGeometry(QRect(330, 60, 31, 31))
        self.btn_browse.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_x = QSpinBox(XRayDialog)
        self.spin_roi_x.setObjectName(u"spin_roi_x")
        self.spin_roi_x.setGeometry(QRect(140, 160, 81, 31))
        self.spin_roi_x.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_x.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_x.setProperty(u"showGroupSeparator", False)
        self.spin_roi_x.setMaximum(65535)
        self.spin_roi_x.setValue(512)
        self.spin_roi_y = QSpinBox(XRayDialog)
        self.spin_roi_y.setObjectName(u"spin_roi_y")
        self.spin_roi_y.setGeometry(QRect(230, 160, 81, 31))
        self.spin_roi_y.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_y.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_y.setMaximum(65535)
        self.spin_roi_y.setValue(512)
        self.spin_roi_z = QSpinBox(XRayDialog)
        self.spin_roi_z.setObjectName(u"spin_roi_z")
        self.spin_roi_z.setGeometry(QRect(320, 160, 81, 31))
        self.spin_roi_z.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_z.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_z.setMaximum(65535)
        self.spin_roi_z.setValue(512)
        self.spin_downsampling = QSpinBox(XRayDialog)
        self.spin_downsampling.setObjectName(u"spin_downsampling")
        self.spin_downsampling.setGeometry(QRect(140, 200, 81, 31))
        self.spin_downsampling.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_downsampling.setValue(4)
        self.spin_pcd_pts = QSpinBox(XRayDialog)
        self.spin_pcd_pts.setObjectName(u"spin_pcd_pts")
        self.spin_pcd_pts.setGeometry(QRect(140, 240, 81, 31))
        self.spin_pcd_pts.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_pcd_pts.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_pcd_pts.setMaximum(65535)
        self.spin_pcd_pts.setValue(2500)
        self.line_voxel_size = QLineEdit(XRayDialog)
        self.line_voxel_size.setObjectName(u"line_voxel_size")
        self.line_voxel_size.setGeometry(QRect(140, 120, 221, 31))
        self.line_voxel_size.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.line_voxel_size.setMaxLength(30)
        self.line_voxel_size.setClearButtonEnabled(True)
        self.label_import_type = QLabel(XRayDialog)
        self.label_import_type.setObjectName(u"label_import_type")
        self.label_import_type.setGeometry(QRect(20, 20, 111, 31))
        self.label_import_type.setAutoFillBackground(False)
        self.label_import_type.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.label_file_folder = QLabel(XRayDialog)
        self.label_file_folder.setObjectName(u"label_file_folder")
        self.label_file_folder.setGeometry(QRect(20, 60, 111, 31))
        self.label_file_folder.setAutoFillBackground(False)
        self.label_file_folder.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.label_voxel_size = QLabel(XRayDialog)
        self.label_voxel_size.setObjectName(u"label_voxel_size")
        self.label_voxel_size.setGeometry(QRect(20, 120, 111, 31))
        self.label_voxel_size.setAutoFillBackground(False)
        self.label_voxel_size.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.label_roi_xyz = QLabel(XRayDialog)
        self.label_roi_xyz.setObjectName(u"label_roi_xyz")
        self.label_roi_xyz.setGeometry(QRect(20, 160, 111, 31))
        self.label_roi_xyz.setAutoFillBackground(False)
        self.label_roi_xyz.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.label_downsampling = QLabel(XRayDialog)
        self.label_downsampling.setObjectName(u"label_downsampling")
        self.label_downsampling.setGeometry(QRect(20, 200, 111, 31))
        self.label_downsampling.setAutoFillBackground(False)
        self.label_downsampling.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.label_point_cloud_points = QLabel(XRayDialog)
        self.label_point_cloud_points.setObjectName(u"label_point_cloud_points")
        self.label_point_cloud_points.setGeometry(QRect(20, 240, 111, 31))
        self.label_point_cloud_points.setAutoFillBackground(False)
        self.label_point_cloud_points.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")

        self.retranslateUi(XRayDialog)
        self.buttonBox.accepted.connect(XRayDialog.accept)
        self.buttonBox.rejected.connect(XRayDialog.reject)

        QMetaObject.connectSlotsByName(XRayDialog)
    # setupUi

    def retranslateUi(self, XRayDialog):
        XRayDialog.setWindowTitle(QCoreApplication.translate("XRayDialog", u"Dialog", None))
        self.combo_import_type.setItemText(0, QCoreApplication.translate("XRayDialog", u"TIFF Stack Folder", None))
        self.combo_import_type.setItemText(1, QCoreApplication.translate("XRayDialog", u"H5", None))
        self.combo_import_type.setItemText(2, QCoreApplication.translate("XRayDialog", u"NPY", None))

        self.btn_browse.setText(QCoreApplication.translate("XRayDialog", u"...", None))
#if QT_CONFIG(tooltip)
        self.line_voxel_size.setToolTip(QCoreApplication.translate("XRayDialog", u"Voxel size in millimeters (example: 0.0004631795)", None))
#endif // QT_CONFIG(tooltip)
        self.line_voxel_size.setText(QCoreApplication.translate("XRayDialog", u"0.006937965888099794", None))
        self.line_voxel_size.setPlaceholderText(QCoreApplication.translate("XRayDialog", u"Voxel size in mm", None))
        self.label_import_type.setText(QCoreApplication.translate("XRayDialog", u"Import Type", None))
        self.label_file_folder.setText(QCoreApplication.translate("XRayDialog", u"File / Folder", None))
        self.label_voxel_size.setText(QCoreApplication.translate("XRayDialog", u"Voxel Size (mm)", None))
        self.label_roi_xyz.setText(QCoreApplication.translate("XRayDialog", u"ROI", None))
        self.label_downsampling.setText(QCoreApplication.translate("XRayDialog", u"Downsampling", None))
        self.label_point_cloud_points.setText(QCoreApplication.translate("XRayDialog", u"Point Cloud Points", None))
    # retranslateUi

