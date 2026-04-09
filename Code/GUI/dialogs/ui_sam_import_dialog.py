# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sam_import_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget)

class Ui_SAMImportDialog(object):
    def setupUi(self, SAMImportDialog):
        if not SAMImportDialog.objectName():
            SAMImportDialog.setObjectName(u"SAMImportDialog")
        SAMImportDialog.resize(460, 360)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SAMImportDialog.sizePolicy().hasHeightForWidth())
        SAMImportDialog.setSizePolicy(sizePolicy)
        SAMImportDialog.setStyleSheet(u"background-color: #d3d3d3;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.verticalLayout = QVBoxLayout(SAMImportDialog)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.group_stack = QGroupBox(SAMImportDialog)
        self.group_stack.setObjectName(u"group_stack")
        self.formLayout_stack = QFormLayout(self.group_stack)
        self.formLayout_stack.setObjectName(u"formLayout_stack")
        self.formLayout_stack.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.formLayout_stack.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_folder = QLabel(self.group_stack)
        self.label_folder.setObjectName(u"label_folder")

        self.formLayout_stack.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_folder)

        self.horizontalLayout_path = QHBoxLayout()
        self.horizontalLayout_path.setSpacing(6)
        self.horizontalLayout_path.setObjectName(u"horizontalLayout_path")
        self.line_path = QLineEdit(self.group_stack)
        self.line_path.setObjectName(u"line_path")
        self.line_path.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")

        self.horizontalLayout_path.addWidget(self.line_path)

        self.btn_browse = QPushButton(self.group_stack)
        self.btn_browse.setObjectName(u"btn_browse")
        self.btn_browse.setMinimumSize(QSize(32, 0))
        self.btn_browse.setMaximumSize(QSize(32, 16777215))
        self.btn_browse.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")

        self.horizontalLayout_path.addWidget(self.btn_browse)


        self.formLayout_stack.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_path)

        self.label_detected_title = QLabel(self.group_stack)
        self.label_detected_title.setObjectName(u"label_detected_title")

        self.formLayout_stack.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_detected_title)

        self.label_detected = QLabel(self.group_stack)
        self.label_detected.setObjectName(u"label_detected")
        self.label_detected.setWordWrap(True)
        self.label_detected.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.formLayout_stack.setWidget(1, QFormLayout.ItemRole.FieldRole, self.label_detected)


        self.verticalLayout.addWidget(self.group_stack)

        self.group_settings = QGroupBox(SAMImportDialog)
        self.group_settings.setObjectName(u"group_settings")
        self.formLayout_settings = QFormLayout(self.group_settings)
        self.formLayout_settings.setObjectName(u"formLayout_settings")
        self.formLayout_settings.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.formLayout_settings.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_voxel_size = QLabel(self.group_settings)
        self.label_voxel_size.setObjectName(u"label_voxel_size")

        self.formLayout_settings.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_voxel_size)

        self.line_voxel_size = QLineEdit(self.group_settings)
        self.line_voxel_size.setObjectName(u"line_voxel_size")
        self.line_voxel_size.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")

        self.formLayout_settings.setWidget(0, QFormLayout.ItemRole.FieldRole, self.line_voxel_size)

        self.label_roi = QLabel(self.group_settings)
        self.label_roi.setObjectName(u"label_roi")

        self.formLayout_settings.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_roi)

        self.horizontalLayout_roi = QHBoxLayout()
        self.horizontalLayout_roi.setSpacing(6)
        self.horizontalLayout_roi.setObjectName(u"horizontalLayout_roi")
        self.spin_roi_x = QSpinBox(self.group_settings)
        self.spin_roi_x.setObjectName(u"spin_roi_x")
        self.spin_roi_x.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_x.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_roi_x.setMinimum(1)
        self.spin_roi_x.setMaximum(65535)
        self.spin_roi_x.setValue(512)

        self.horizontalLayout_roi.addWidget(self.spin_roi_x)

        self.spin_roi_y = QSpinBox(self.group_settings)
        self.spin_roi_y.setObjectName(u"spin_roi_y")
        self.spin_roi_y.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_y.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_roi_y.setMinimum(1)
        self.spin_roi_y.setMaximum(65535)
        self.spin_roi_y.setValue(512)

        self.horizontalLayout_roi.addWidget(self.spin_roi_y)

        self.spin_roi_z = QSpinBox(self.group_settings)
        self.spin_roi_z.setObjectName(u"spin_roi_z")
        self.spin_roi_z.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_roi_z.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_roi_z.setMinimum(1)
        self.spin_roi_z.setMaximum(65535)
        self.spin_roi_z.setValue(512)

        self.horizontalLayout_roi.addWidget(self.spin_roi_z)


        self.formLayout_settings.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_roi)

        self.label_downsampling = QLabel(self.group_settings)
        self.label_downsampling.setObjectName(u"label_downsampling")

        self.formLayout_settings.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_downsampling)

        self.spin_downsampling = QSpinBox(self.group_settings)
        self.spin_downsampling.setObjectName(u"spin_downsampling")
        self.spin_downsampling.setMinimumSize(QSize(150, 34))
        self.spin_downsampling.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding-left: 4px;\n"
"padding-right: 22px;\n"
"border-radius: 3px;")
        self.spin_downsampling.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.spin_downsampling.setMinimum(1)
        self.spin_downsampling.setMaximum(128)
        self.spin_downsampling.setValue(4)

        self.formLayout_settings.setWidget(2, QFormLayout.ItemRole.FieldRole, self.spin_downsampling)

        self.label_pcd_points = QLabel(self.group_settings)
        self.label_pcd_points.setObjectName(u"label_pcd_points")

        self.formLayout_settings.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_pcd_points)

        self.spin_pcd_pts = QSpinBox(self.group_settings)
        self.spin_pcd_pts.setObjectName(u"spin_pcd_pts")
        self.spin_pcd_pts.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_pcd_pts.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_pcd_pts.setMinimum(1)
        self.spin_pcd_pts.setMaximum(500000)
        self.spin_pcd_pts.setValue(2500)

        self.formLayout_settings.setWidget(3, QFormLayout.ItemRole.FieldRole, self.spin_pcd_pts)

        self.label_marching_cubes = QLabel(self.group_settings)
        self.label_marching_cubes.setObjectName(u"label_marching_cubes")

        self.formLayout_settings.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_marching_cubes)

        self.spin_marching_cubes = QSpinBox(self.group_settings)
        self.spin_marching_cubes.setObjectName(u"spin_marching_cubes")
        self.spin_marching_cubes.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.spin_marching_cubes.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_marching_cubes.setMinimum(1)
        self.spin_marching_cubes.setMaximum(262143)
        self.spin_marching_cubes.setValue(128)

        self.formLayout_settings.setWidget(4, QFormLayout.ItemRole.FieldRole, self.spin_marching_cubes)


        self.verticalLayout.addWidget(self.group_settings)

        self.button_box = QDialogButtonBox(SAMImportDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStyleSheet(u"background-color: #f0f0f0;\n"
"padding: 3px;\n"
"border-radius: 3px;")
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(SAMImportDialog)

        QMetaObject.connectSlotsByName(SAMImportDialog)
    # setupUi

    def retranslateUi(self, SAMImportDialog):
        SAMImportDialog.setWindowTitle(QCoreApplication.translate("SAMImportDialog", u"SAM Import", None))
        self.group_stack.setTitle(QCoreApplication.translate("SAMImportDialog", u"SAM PNG Stack", None))
        self.label_folder.setText(QCoreApplication.translate("SAMImportDialog", u"Folder", None))
        self.btn_browse.setText(QCoreApplication.translate("SAMImportDialog", u"...", None))
        self.label_detected_title.setText(QCoreApplication.translate("SAMImportDialog", u"Detected (XYZ)", None))
        self.label_detected.setText("")
        self.group_settings.setTitle(QCoreApplication.translate("SAMImportDialog", u"Import Settings", None))
        self.label_voxel_size.setText(QCoreApplication.translate("SAMImportDialog", u"Voxel Size (mm)", None))
        self.label_roi.setText(QCoreApplication.translate("SAMImportDialog", u"ROI (X,Y,Z)", None))
        self.label_downsampling.setText(QCoreApplication.translate("SAMImportDialog", u"Downsampling", None))
        self.label_pcd_points.setText(QCoreApplication.translate("SAMImportDialog", u"Point Cloud Points", None))
        self.label_marching_cubes.setText(QCoreApplication.translate("SAMImportDialog", u"Marching Cubes", None))
    # retranslateUi

