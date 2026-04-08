# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'xray_file_import_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QAbstractSpinBox, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QSizePolicy, QSpinBox, QVBoxLayout)


class Ui_XRayFileImportDialog(object):
    def setupUi(self, XRayFileImportDialog):
        if not XRayFileImportDialog.objectName():
            XRayFileImportDialog.setObjectName(u"XRayFileImportDialog")
        XRayFileImportDialog.resize(460, 360)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(XRayFileImportDialog.sizePolicy().hasHeightForWidth())
        XRayFileImportDialog.setSizePolicy(sizePolicy)
        XRayFileImportDialog.setStyleSheet(u"background-color: #d3d3d3;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.verticalLayout = QVBoxLayout(XRayFileImportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.group_file = QGroupBox(XRayFileImportDialog)
        self.group_file.setObjectName(u"group_file")
        self.formLayout_file = QFormLayout(self.group_file)
        self.formLayout_file.setObjectName(u"formLayout_file")
        self.formLayout_file.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.formLayout_file.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_path = QLabel(self.group_file)
        self.label_path.setObjectName(u"label_path")
        self.formLayout_file.setWidget(0, QFormLayout.LabelRole, self.label_path)
        self.line_path = QLineEdit(self.group_file)
        self.line_path.setObjectName(u"line_path")
        self.line_path.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.line_path.setReadOnly(True)
        self.formLayout_file.setWidget(0, QFormLayout.FieldRole, self.line_path)
        self.label_dataset = QLabel(self.group_file)
        self.label_dataset.setObjectName(u"label_dataset")
        self.formLayout_file.setWidget(1, QFormLayout.LabelRole, self.label_dataset)
        self.combo_dataset = QComboBox(self.group_file)
        self.combo_dataset.setObjectName(u"combo_dataset")
        self.combo_dataset.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.formLayout_file.setWidget(1, QFormLayout.FieldRole, self.combo_dataset)
        self.label_detected_title = QLabel(self.group_file)
        self.label_detected_title.setObjectName(u"label_detected_title")
        self.formLayout_file.setWidget(2, QFormLayout.LabelRole, self.label_detected_title)
        self.label_volume_info = QLabel(self.group_file)
        self.label_volume_info.setObjectName(u"label_volume_info")
        self.label_volume_info.setWordWrap(True)
        self.label_volume_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.formLayout_file.setWidget(2, QFormLayout.FieldRole, self.label_volume_info)

        self.verticalLayout.addWidget(self.group_file)

        self.group_settings = QGroupBox(XRayFileImportDialog)
        self.group_settings.setObjectName(u"group_settings")
        self.formLayout_settings = QFormLayout(self.group_settings)
        self.formLayout_settings.setObjectName(u"formLayout_settings")
        self.formLayout_settings.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.formLayout_settings.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_voxel_size = QLabel(self.group_settings)
        self.label_voxel_size.setObjectName(u"label_voxel_size")
        self.formLayout_settings.setWidget(0, QFormLayout.LabelRole, self.label_voxel_size)
        self.line_voxel_size = QLineEdit(self.group_settings)
        self.line_voxel_size.setObjectName(u"line_voxel_size")
        self.line_voxel_size.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.formLayout_settings.setWidget(0, QFormLayout.FieldRole, self.line_voxel_size)
        self.label_roi = QLabel(self.group_settings)
        self.label_roi.setObjectName(u"label_roi")
        self.formLayout_settings.setWidget(1, QFormLayout.LabelRole, self.label_roi)
        self.horizontalLayout_roi = QHBoxLayout()
        self.horizontalLayout_roi.setObjectName(u"horizontalLayout_roi")
        self.spin_roi_x = QSpinBox(self.group_settings)
        self.spin_roi_x.setObjectName(u"spin_roi_x")
        self.spin_roi_x.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_x.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_x.setMinimum(1)
        self.spin_roi_x.setMaximum(65535)
        self.spin_roi_x.setValue(512)
        self.horizontalLayout_roi.addWidget(self.spin_roi_x)
        self.spin_roi_y = QSpinBox(self.group_settings)
        self.spin_roi_y.setObjectName(u"spin_roi_y")
        self.spin_roi_y.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_y.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_y.setMinimum(1)
        self.spin_roi_y.setMaximum(65535)
        self.spin_roi_y.setValue(512)
        self.horizontalLayout_roi.addWidget(self.spin_roi_y)
        self.spin_roi_z = QSpinBox(self.group_settings)
        self.spin_roi_z.setObjectName(u"spin_roi_z")
        self.spin_roi_z.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_z.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_roi_z.setMinimum(1)
        self.spin_roi_z.setMaximum(65535)
        self.spin_roi_z.setValue(512)
        self.horizontalLayout_roi.addWidget(self.spin_roi_z)
        self.formLayout_settings.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout_roi)
        self.label_downsampling = QLabel(self.group_settings)
        self.label_downsampling.setObjectName(u"label_downsampling")
        self.formLayout_settings.setWidget(2, QFormLayout.LabelRole, self.label_downsampling)
        self.spin_downsampling = QSpinBox(self.group_settings)
        self.spin_downsampling.setObjectName(u"spin_downsampling")
        self.spin_downsampling.setMinimumSize(150, 34)
        self.spin_downsampling.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding-left: 4px;\n"
"padding-right: 22px;\n"
"border-radius: 3px;")
        self.spin_downsampling.setMinimum(1)
        self.spin_downsampling.setMaximum(128)
        self.spin_downsampling.setValue(4)
        self.formLayout_settings.setWidget(2, QFormLayout.FieldRole, self.spin_downsampling)
        self.label_pcd_points = QLabel(self.group_settings)
        self.label_pcd_points.setObjectName(u"label_pcd_points")
        self.formLayout_settings.setWidget(3, QFormLayout.LabelRole, self.label_pcd_points)
        self.spin_pcd_pts = QSpinBox(self.group_settings)
        self.spin_pcd_pts.setObjectName(u"spin_pcd_pts")
        self.spin_pcd_pts.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_pcd_pts.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_pcd_pts.setMinimum(1)
        self.spin_pcd_pts.setMaximum(500000)
        self.spin_pcd_pts.setValue(2500)
        self.formLayout_settings.setWidget(3, QFormLayout.FieldRole, self.spin_pcd_pts)
        self.label_marching_cubes = QLabel(self.group_settings)
        self.label_marching_cubes.setObjectName(u"label_marching_cubes")
        self.formLayout_settings.setWidget(4, QFormLayout.LabelRole, self.label_marching_cubes)
        self.spin_marching_cubes = QSpinBox(self.group_settings)
        self.spin_marching_cubes.setObjectName(u"spin_marching_cubes")
        self.spin_marching_cubes.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_marching_cubes.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_marching_cubes.setMinimum(1)
        self.spin_marching_cubes.setMaximum(262143)
        self.spin_marching_cubes.setValue(42000)
        self.formLayout_settings.setWidget(4, QFormLayout.FieldRole, self.spin_marching_cubes)

        self.verticalLayout.addWidget(self.group_settings)

        self.button_box = QDialogButtonBox(XRayFileImportDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.button_box.setOrientation(Qt.Orientation.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.button_box)

        self.retranslateUi(XRayFileImportDialog)
        self.button_box.accepted.connect(XRayFileImportDialog.accept)
        self.button_box.rejected.connect(XRayFileImportDialog.reject)

        QMetaObject.connectSlotsByName(XRayFileImportDialog)
    # setupUi

    def retranslateUi(self, XRayFileImportDialog):
        XRayFileImportDialog.setWindowTitle(QCoreApplication.translate("XRayFileImportDialog", u"X-Ray File Import", None))
        self.group_file.setTitle(QCoreApplication.translate("XRayFileImportDialog", u"File", None))
        self.label_path.setText(QCoreApplication.translate("XRayFileImportDialog", u"Path", None))
        self.label_dataset.setText(QCoreApplication.translate("XRayFileImportDialog", u"H5 Dataset", None))
        self.label_detected_title.setText(QCoreApplication.translate("XRayFileImportDialog", u"Detected", None))
        self.label_volume_info.setText("")
        self.group_settings.setTitle(QCoreApplication.translate("XRayFileImportDialog", u"Import Settings", None))
        self.label_voxel_size.setText(QCoreApplication.translate("XRayFileImportDialog", u"Voxel Size (mm)", None))
        self.label_roi.setText(QCoreApplication.translate("XRayFileImportDialog", u"ROI (X,Y,Z)", None))
        self.label_downsampling.setText(QCoreApplication.translate("XRayFileImportDialog", u"Downsampling", None))
        self.label_pcd_points.setText(QCoreApplication.translate("XRayFileImportDialog", u"Point Cloud Points", None))
        self.label_marching_cubes.setText(QCoreApplication.translate("XRayFileImportDialog", u"Marching Cubes", None))
    # retranslateUi
