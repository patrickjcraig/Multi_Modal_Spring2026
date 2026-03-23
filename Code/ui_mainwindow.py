# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_V1.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QStackedWidget, QStatusBar,
    QTabWidget, QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1600, 980)
        self.actionSave_Workspace = QAction(MainWindow)
        self.actionSave_Workspace.setObjectName(u"actionSave_Workspace")
        self.actionLoad_Workspace = QAction(MainWindow)
        self.actionLoad_Workspace.setObjectName(u"actionLoad_Workspace")
        self.actionX_Ray = QAction(MainWindow)
        self.actionX_Ray.setObjectName(u"actionX_Ray")
        self.actionPoint_Cloud = QAction(MainWindow)
        self.actionPoint_Cloud.setObjectName(u"actionPoint_Cloud")
        self.actionImport_XRay = QAction(MainWindow)
        self.actionImport_XRay.setObjectName(u"actionImport_XRay")
        self.actionSet_Source = QAction(MainWindow)
        self.actionSet_Source.setObjectName(u"actionSet_Source")
        self.actionSet_Target = QAction(MainWindow)
        self.actionSet_Target.setObjectName(u"actionSet_Target")
        self.actionSet_Source_2 = QAction(MainWindow)
        self.actionSet_Source_2.setObjectName(u"actionSet_Source_2")
        self.actionParameters = QAction(MainWindow)
        self.actionParameters.setObjectName(u"actionParameters")
        self.actionParameters_2 = QAction(MainWindow)
        self.actionParameters_2.setObjectName(u"actionParameters_2")
        self.actionRegistration_2 = QAction(MainWindow)
        self.actionRegistration_2.setObjectName(u"actionRegistration_2")
        self.actionTransformation = QAction(MainWindow)
        self.actionTransformation.setObjectName(u"actionTransformation")
        self.actionTransformation_2 = QAction(MainWindow)
        self.actionTransformation_2.setObjectName(u"actionTransformation_2")
        self.actionRegistration_3 = QAction(MainWindow)
        self.actionRegistration_3.setObjectName(u"actionRegistration_3")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layout_main = QHBoxLayout(self.centralwidget)
        self.layout_main.setSpacing(16)
        self.layout_main.setObjectName(u"layout_main")
        self.layout_main.setContentsMargins(16, 16, 16, 16)
        self.layout_leftPanel = QVBoxLayout()
        self.layout_leftPanel.setSpacing(12)
        self.layout_leftPanel.setObjectName(u"layout_leftPanel")
        self.layout_leftPanel.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)

        self.layout_leftPanel.addWidget(self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.toolButton = QToolButton(self.centralwidget)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setEnabled(True)

        self.horizontalLayout.addWidget(self.toolButton)

        self.toolButton_3 = QToolButton(self.centralwidget)
        self.toolButton_3.setObjectName(u"toolButton_3")

        self.horizontalLayout.addWidget(self.toolButton_3)

        self.toolButton_2 = QToolButton(self.centralwidget)
        self.toolButton_2.setObjectName(u"toolButton_2")

        self.horizontalLayout.addWidget(self.toolButton_2)

        self.toolButton_4 = QToolButton(self.centralwidget)
        self.toolButton_4.setObjectName(u"toolButton_4")

        self.horizontalLayout.addWidget(self.toolButton_4)

        self.toolButton_5 = QToolButton(self.centralwidget)
        self.toolButton_5.setObjectName(u"toolButton_5")

        self.horizontalLayout.addWidget(self.toolButton_5)


        self.layout_leftPanel.addLayout(self.horizontalLayout)

        self.scanTabs = QTabWidget(self.centralwidget)
        self.scanTabs.setObjectName(u"scanTabs")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.scanTabs.sizePolicy().hasHeightForWidth())
        self.scanTabs.setSizePolicy(sizePolicy)
        self.tab_workspace_placeholder = QWidget()
        self.tab_workspace_placeholder.setObjectName(u"tab_workspace_placeholder")
        self.scanTabs.addTab(self.tab_workspace_placeholder, "")

        self.layout_leftPanel.addWidget(self.scanTabs)

        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.layout_leftPanel.addWidget(self.progressBar)

        self.layout_navigation = QHBoxLayout()
        self.layout_navigation.setSpacing(12)
        self.layout_navigation.setObjectName(u"layout_navigation")
        self.label_step_info = QLabel(self.centralwidget)
        self.label_step_info.setObjectName(u"label_step_info")
        self.label_step_info.setMinimumSize(QSize(240, 0))
        font1 = QFont()
        font1.setBold(True)
        self.label_step_info.setFont(font1)
        self.label_step_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout_navigation.addWidget(self.label_step_info)

        self.btn_prev_step = QPushButton(self.centralwidget)
        self.btn_prev_step.setObjectName(u"btn_prev_step")
        self.btn_prev_step.setEnabled(False)

        self.layout_navigation.addWidget(self.btn_prev_step)

        self.btn_next_step = QPushButton(self.centralwidget)
        self.btn_next_step.setObjectName(u"btn_next_step")
        self.btn_next_step.setEnabled(False)

        self.layout_navigation.addWidget(self.btn_next_step)


        self.layout_leftPanel.addLayout(self.layout_navigation)


        self.layout_main.addLayout(self.layout_leftPanel)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_tools_title = QLabel(self.centralwidget)
        self.label_tools_title.setObjectName(u"label_tools_title")
        self.label_tools_title.setFont(font)

        self.verticalLayout.addWidget(self.label_tools_title)

        self.layout_tool_selector = QHBoxLayout()
        self.layout_tool_selector.setSpacing(4)
        self.layout_tool_selector.setObjectName(u"layout_tool_selector")
        self.btn_show_registration_tools = QToolButton(self.centralwidget)
        self.btn_show_registration_tools.setObjectName(u"btn_show_registration_tools")
        self.btn_show_registration_tools.setCheckable(True)
        self.btn_show_registration_tools.setChecked(True)

        self.layout_tool_selector.addWidget(self.btn_show_registration_tools)

        self.btn_show_transformation_tools = QToolButton(self.centralwidget)
        self.btn_show_transformation_tools.setObjectName(u"btn_show_transformation_tools")
        self.btn_show_transformation_tools.setCheckable(True)

        self.layout_tool_selector.addWidget(self.btn_show_transformation_tools)


        self.verticalLayout.addLayout(self.layout_tool_selector)

        self.toolsStack = QStackedWidget(self.centralwidget)
        self.toolsStack.setObjectName(u"toolsStack")
        self.toolsStack.setMaximumSize(QSize(250, 16777215))
        self.page_registration_tools = QWidget()
        self.page_registration_tools.setObjectName(u"page_registration_tools")
        self.layout_registration_tools = QVBoxLayout(self.page_registration_tools)
        self.layout_registration_tools.setSpacing(5)
        self.layout_registration_tools.setObjectName(u"layout_registration_tools")
        self.label_params_title = QLabel(self.page_registration_tools)
        self.label_params_title.setObjectName(u"label_params_title")
        self.label_params_title.setFont(font)

        self.layout_registration_tools.addWidget(self.label_params_title)

        self.label_voxel_size = QLabel(self.page_registration_tools)
        self.label_voxel_size.setObjectName(u"label_voxel_size")

        self.layout_registration_tools.addWidget(self.label_voxel_size)

        self.spinBox_voxel_size = QDoubleSpinBox(self.page_registration_tools)
        self.spinBox_voxel_size.setObjectName(u"spinBox_voxel_size")
        self.spinBox_voxel_size.setDecimals(2)
        self.spinBox_voxel_size.setMinimum(0.100000000000000)
        self.spinBox_voxel_size.setMaximum(10.000000000000000)
        self.spinBox_voxel_size.setSingleStep(0.500000000000000)
        self.spinBox_voxel_size.setValue(2.000000000000000)

        self.layout_registration_tools.addWidget(self.spinBox_voxel_size)

        self.label_global_transform_model = QLabel(self.page_registration_tools)
        self.label_global_transform_model.setObjectName(u"label_global_transform_model")

        self.layout_registration_tools.addWidget(self.label_global_transform_model)

        self.combo_global_transform_model = QComboBox(self.page_registration_tools)
        self.combo_global_transform_model.addItem("")
        self.combo_global_transform_model.addItem("")
        self.combo_global_transform_model.setObjectName(u"combo_global_transform_model")

        self.layout_registration_tools.addWidget(self.combo_global_transform_model)

        self.line_1 = QFrame(self.page_registration_tools)
        self.line_1.setObjectName(u"line_1")
        self.line_1.setFrameShape(QFrame.Shape.HLine)
        self.line_1.setFrameShadow(QFrame.Shadow.Sunken)

        self.layout_registration_tools.addWidget(self.line_1)

        self.label_ransac_title = QLabel(self.page_registration_tools)
        self.label_ransac_title.setObjectName(u"label_ransac_title")
        self.label_ransac_title.setFont(font1)

        self.layout_registration_tools.addWidget(self.label_ransac_title)

        self.label_ransac_dist = QLabel(self.page_registration_tools)
        self.label_ransac_dist.setObjectName(u"label_ransac_dist")

        self.layout_registration_tools.addWidget(self.label_ransac_dist)

        self.spinBox_ransac_dist = QDoubleSpinBox(self.page_registration_tools)
        self.spinBox_ransac_dist.setObjectName(u"spinBox_ransac_dist")
        self.spinBox_ransac_dist.setDecimals(2)
        self.spinBox_ransac_dist.setMinimum(0.500000000000000)
        self.spinBox_ransac_dist.setMaximum(5.000000000000000)
        self.spinBox_ransac_dist.setSingleStep(0.100000000000000)
        self.spinBox_ransac_dist.setValue(1.500000000000000)

        self.layout_registration_tools.addWidget(self.spinBox_ransac_dist)

        self.label_ransac_max_iter = QLabel(self.page_registration_tools)
        self.label_ransac_max_iter.setObjectName(u"label_ransac_max_iter")

        self.layout_registration_tools.addWidget(self.label_ransac_max_iter)

        self.spinBox_ransac_max_iter = QSpinBox(self.page_registration_tools)
        self.spinBox_ransac_max_iter.setObjectName(u"spinBox_ransac_max_iter")
        self.spinBox_ransac_max_iter.setMinimum(1000)
        self.spinBox_ransac_max_iter.setMaximum(1000000)
        self.spinBox_ransac_max_iter.setSingleStep(10000)
        self.spinBox_ransac_max_iter.setValue(100000)

        self.layout_registration_tools.addWidget(self.spinBox_ransac_max_iter)

        self.label_ransac_validation = QLabel(self.page_registration_tools)
        self.label_ransac_validation.setObjectName(u"label_ransac_validation")

        self.layout_registration_tools.addWidget(self.label_ransac_validation)

        self.spinBox_ransac_validation = QSpinBox(self.page_registration_tools)
        self.spinBox_ransac_validation.setObjectName(u"spinBox_ransac_validation")
        self.spinBox_ransac_validation.setMinimum(100)
        self.spinBox_ransac_validation.setMaximum(10000)
        self.spinBox_ransac_validation.setSingleStep(100)
        self.spinBox_ransac_validation.setValue(1000)

        self.layout_registration_tools.addWidget(self.spinBox_ransac_validation)

        self.line_2 = QFrame(self.page_registration_tools)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.layout_registration_tools.addWidget(self.line_2)

        self.label_icp_title = QLabel(self.page_registration_tools)
        self.label_icp_title.setObjectName(u"label_icp_title")
        self.label_icp_title.setFont(font1)

        self.layout_registration_tools.addWidget(self.label_icp_title)

        self.label_icp_dist = QLabel(self.page_registration_tools)
        self.label_icp_dist.setObjectName(u"label_icp_dist")

        self.layout_registration_tools.addWidget(self.label_icp_dist)

        self.spinBox_icp_dist = QDoubleSpinBox(self.page_registration_tools)
        self.spinBox_icp_dist.setObjectName(u"spinBox_icp_dist")
        self.spinBox_icp_dist.setDecimals(2)
        self.spinBox_icp_dist.setMinimum(0.100000000000000)
        self.spinBox_icp_dist.setMaximum(2.000000000000000)
        self.spinBox_icp_dist.setSingleStep(0.050000000000000)
        self.spinBox_icp_dist.setValue(0.400000000000000)

        self.layout_registration_tools.addWidget(self.spinBox_icp_dist)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_registration_tools.addItem(self.verticalSpacer)

        self.line_3 = QFrame(self.page_registration_tools)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.layout_registration_tools.addWidget(self.line_3)

        self.label_results_title = QLabel(self.page_registration_tools)
        self.label_results_title.setObjectName(u"label_results_title")
        self.label_results_title.setFont(font)

        self.layout_registration_tools.addWidget(self.label_results_title)

        self.label_ransac_results_title = QLabel(self.page_registration_tools)
        self.label_ransac_results_title.setObjectName(u"label_ransac_results_title")
        self.label_ransac_results_title.setFont(font1)

        self.layout_registration_tools.addWidget(self.label_ransac_results_title)

        self.label_ransac_fitness_label = QLabel(self.page_registration_tools)
        self.label_ransac_fitness_label.setObjectName(u"label_ransac_fitness_label")

        self.layout_registration_tools.addWidget(self.label_ransac_fitness_label)

        self.label_ransac_fitness = QLabel(self.page_registration_tools)
        self.label_ransac_fitness.setObjectName(u"label_ransac_fitness")
        self.label_ransac_fitness.setStyleSheet(u"color: rgb(0, 170, 255); font-weight: bold;")

        self.layout_registration_tools.addWidget(self.label_ransac_fitness)

        self.label_ransac_rmse_label = QLabel(self.page_registration_tools)
        self.label_ransac_rmse_label.setObjectName(u"label_ransac_rmse_label")

        self.layout_registration_tools.addWidget(self.label_ransac_rmse_label)

        self.label_ransac_rmse = QLabel(self.page_registration_tools)
        self.label_ransac_rmse.setObjectName(u"label_ransac_rmse")
        self.label_ransac_rmse.setStyleSheet(u"color: rgb(0, 170, 255); font-weight: bold;")

        self.layout_registration_tools.addWidget(self.label_ransac_rmse)

        self.line_4 = QFrame(self.page_registration_tools)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.layout_registration_tools.addWidget(self.line_4)

        self.label_icp_results_title = QLabel(self.page_registration_tools)
        self.label_icp_results_title.setObjectName(u"label_icp_results_title")
        self.label_icp_results_title.setFont(font1)

        self.layout_registration_tools.addWidget(self.label_icp_results_title)

        self.label_icp_fitness_label = QLabel(self.page_registration_tools)
        self.label_icp_fitness_label.setObjectName(u"label_icp_fitness_label")

        self.layout_registration_tools.addWidget(self.label_icp_fitness_label)

        self.label_icp_fitness = QLabel(self.page_registration_tools)
        self.label_icp_fitness.setObjectName(u"label_icp_fitness")
        self.label_icp_fitness.setStyleSheet(u"color: rgb(0, 255, 127); font-weight: bold;")

        self.layout_registration_tools.addWidget(self.label_icp_fitness)

        self.label_icp_rmse_label = QLabel(self.page_registration_tools)
        self.label_icp_rmse_label.setObjectName(u"label_icp_rmse_label")

        self.layout_registration_tools.addWidget(self.label_icp_rmse_label)

        self.label_icp_rmse = QLabel(self.page_registration_tools)
        self.label_icp_rmse.setObjectName(u"label_icp_rmse")
        self.label_icp_rmse.setStyleSheet(u"color: rgb(0, 255, 127); font-weight: bold;")

        self.layout_registration_tools.addWidget(self.label_icp_rmse)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_registration_tools.addItem(self.verticalSpacer_2)

        self.toolsStack.addWidget(self.page_registration_tools)
        self.page_transformation_tools = QWidget()
        self.page_transformation_tools.setObjectName(u"page_transformation_tools")
        self.layout_transformation_tools = QVBoxLayout(self.page_transformation_tools)
        self.layout_transformation_tools.setSpacing(5)
        self.layout_transformation_tools.setObjectName(u"layout_transformation_tools")
        self.label_transform_title = QLabel(self.page_transformation_tools)
        self.label_transform_title.setObjectName(u"label_transform_title")
        self.label_transform_title.setFont(font)

        self.layout_transformation_tools.addWidget(self.label_transform_title)

        self.label_transform_help = QLabel(self.page_transformation_tools)
        self.label_transform_help.setObjectName(u"label_transform_help")
        self.label_transform_help.setWordWrap(True)

        self.layout_transformation_tools.addWidget(self.label_transform_help)

        self.layout_affine_matrix = QGridLayout()
        self.layout_affine_matrix.setObjectName(u"layout_affine_matrix")
        self.layout_affine_matrix.setHorizontalSpacing(3)
        self.layout_affine_matrix.setVerticalSpacing(3)
        self.matrix_00 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_00.setObjectName(u"matrix_00")

        self.layout_affine_matrix.addWidget(self.matrix_00, 0, 0, 1, 1)

        self.matrix_01 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_01.setObjectName(u"matrix_01")

        self.layout_affine_matrix.addWidget(self.matrix_01, 0, 1, 1, 1)

        self.matrix_02 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_02.setObjectName(u"matrix_02")

        self.layout_affine_matrix.addWidget(self.matrix_02, 0, 2, 1, 1)

        self.matrix_03 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_03.setObjectName(u"matrix_03")

        self.layout_affine_matrix.addWidget(self.matrix_03, 0, 3, 1, 1)

        self.matrix_10 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_10.setObjectName(u"matrix_10")

        self.layout_affine_matrix.addWidget(self.matrix_10, 1, 0, 1, 1)

        self.matrix_11 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_11.setObjectName(u"matrix_11")

        self.layout_affine_matrix.addWidget(self.matrix_11, 1, 1, 1, 1)

        self.matrix_12 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_12.setObjectName(u"matrix_12")

        self.layout_affine_matrix.addWidget(self.matrix_12, 1, 2, 1, 1)

        self.matrix_13 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_13.setObjectName(u"matrix_13")

        self.layout_affine_matrix.addWidget(self.matrix_13, 1, 3, 1, 1)

        self.matrix_20 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_20.setObjectName(u"matrix_20")

        self.layout_affine_matrix.addWidget(self.matrix_20, 2, 0, 1, 1)

        self.matrix_21 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_21.setObjectName(u"matrix_21")

        self.layout_affine_matrix.addWidget(self.matrix_21, 2, 1, 1, 1)

        self.matrix_22 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_22.setObjectName(u"matrix_22")

        self.layout_affine_matrix.addWidget(self.matrix_22, 2, 2, 1, 1)

        self.matrix_23 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_23.setObjectName(u"matrix_23")

        self.layout_affine_matrix.addWidget(self.matrix_23, 2, 3, 1, 1)

        self.matrix_30 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_30.setObjectName(u"matrix_30")

        self.layout_affine_matrix.addWidget(self.matrix_30, 3, 0, 1, 1)

        self.matrix_31 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_31.setObjectName(u"matrix_31")

        self.layout_affine_matrix.addWidget(self.matrix_31, 3, 1, 1, 1)

        self.matrix_32 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_32.setObjectName(u"matrix_32")

        self.layout_affine_matrix.addWidget(self.matrix_32, 3, 2, 1, 1)

        self.matrix_33 = QDoubleSpinBox(self.page_transformation_tools)
        self.matrix_33.setObjectName(u"matrix_33")

        self.layout_affine_matrix.addWidget(self.matrix_33, 3, 3, 1, 1)


        self.layout_transformation_tools.addLayout(self.layout_affine_matrix)

        self.layout_transform_buttons_top = QHBoxLayout()
        self.layout_transform_buttons_top.setObjectName(u"layout_transform_buttons_top")
        self.btn_matrix_identity = QPushButton(self.page_transformation_tools)
        self.btn_matrix_identity.setObjectName(u"btn_matrix_identity")

        self.layout_transform_buttons_top.addWidget(self.btn_matrix_identity)

        self.btn_matrix_load_current = QPushButton(self.page_transformation_tools)
        self.btn_matrix_load_current.setObjectName(u"btn_matrix_load_current")

        self.layout_transform_buttons_top.addWidget(self.btn_matrix_load_current)


        self.layout_transformation_tools.addLayout(self.layout_transform_buttons_top)

        self.layout_transform_buttons_bottom = QVBoxLayout()
        self.layout_transform_buttons_bottom.setObjectName(u"layout_transform_buttons_bottom")
        self.btn_transform_apply_current = QPushButton(self.page_transformation_tools)
        self.btn_transform_apply_current.setObjectName(u"btn_transform_apply_current")

        self.layout_transform_buttons_bottom.addWidget(self.btn_transform_apply_current)

        self.btn_transform_duplicate_current = QPushButton(self.page_transformation_tools)
        self.btn_transform_duplicate_current.setObjectName(u"btn_transform_duplicate_current")

        self.layout_transform_buttons_bottom.addWidget(self.btn_transform_duplicate_current)


        self.layout_transformation_tools.addLayout(self.layout_transform_buttons_bottom)

        self.label_transform_status = QLabel(self.page_transformation_tools)
        self.label_transform_status.setObjectName(u"label_transform_status")
        self.label_transform_status.setWordWrap(True)

        self.layout_transformation_tools.addWidget(self.label_transform_status)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout_transformation_tools.addItem(self.verticalSpacer_3)

        self.toolsStack.addWidget(self.page_transformation_tools)

        self.verticalLayout.addWidget(self.toolsStack)


        self.layout_main.addLayout(self.verticalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1600, 33))
        self.menuFiles = QMenu(self.menubar)
        self.menuFiles.setObjectName(u"menuFiles")
        self.menuImport_2 = QMenu(self.menuFiles)
        self.menuImport_2.setObjectName(u"menuImport_2")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFiles.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFiles.addAction(self.actionSave_Workspace)
        self.menuFiles.addAction(self.actionLoad_Workspace)
        self.menuFiles.addAction(self.menuImport_2.menuAction())
        self.menuImport_2.addAction(self.actionImport_XRay)
        self.menuTools.addAction(self.actionTransformation_2)
        self.menuTools.addAction(self.actionRegistration_3)

        self.retranslateUi(MainWindow)

        self.scanTabs.setCurrentIndex(0)
        self.toolsStack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionSave_Workspace.setText(QCoreApplication.translate("MainWindow", u"Save Workspace", None))
        self.actionLoad_Workspace.setText(QCoreApplication.translate("MainWindow", u"Load Workspace", None))
        self.actionX_Ray.setText(QCoreApplication.translate("MainWindow", u"X-Ray", None))
        self.actionPoint_Cloud.setText(QCoreApplication.translate("MainWindow", u"Point Cloud", None))
        self.actionImport_XRay.setText(QCoreApplication.translate("MainWindow", u"X-Ray", None))
        self.actionSet_Source.setText(QCoreApplication.translate("MainWindow", u"Set Source", None))
        self.actionSet_Target.setText(QCoreApplication.translate("MainWindow", u"Set Target", None))
        self.actionSet_Source_2.setText(QCoreApplication.translate("MainWindow", u"Set Source", None))
        self.actionParameters.setText(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.actionParameters_2.setText(QCoreApplication.translate("MainWindow", u"Parameters", None))
        self.actionRegistration_2.setText(QCoreApplication.translate("MainWindow", u"Registration", None))
        self.actionTransformation.setText(QCoreApplication.translate("MainWindow", u"Transformation", None))
        self.actionTransformation_2.setText(QCoreApplication.translate("MainWindow", u"Transformation", None))
        self.actionRegistration_3.setText(QCoreApplication.translate("MainWindow", u"Registration", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Scans Workspace", None))
        self.toolButton.setText(QCoreApplication.translate("MainWindow", u"Run Global + Local Registration", None))
        self.toolButton_3.setText(QCoreApplication.translate("MainWindow", u"Registration (Sample Point Cloud)", None))
        self.toolButton_2.setText(QCoreApplication.translate("MainWindow", u"Save Data", None))
        self.toolButton_4.setText(QCoreApplication.translate("MainWindow", u"Set Current As Source", None))
        self.toolButton_5.setText(QCoreApplication.translate("MainWindow", u"Set Current As Target", None))
        self.scanTabs.setTabText(self.scanTabs.indexOf(self.tab_workspace_placeholder), QCoreApplication.translate("MainWindow", u"Workspace", None))
        self.label_step_info.setText(QCoreApplication.translate("MainWindow", u"---", None))
        self.btn_prev_step.setText(QCoreApplication.translate("MainWindow", u"Previous Step", None))
        self.btn_next_step.setText(QCoreApplication.translate("MainWindow", u"Next Step", None))
        self.label_tools_title.setText(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.btn_show_registration_tools.setText(QCoreApplication.translate("MainWindow", u"Register", None))
        self.btn_show_transformation_tools.setText(QCoreApplication.translate("MainWindow", u"Transform", None))
        self.label_params_title.setText(QCoreApplication.translate("MainWindow", u"Registration Parameters", None))
        self.label_voxel_size.setText(QCoreApplication.translate("MainWindow", u"Voxel Size:", None))
        self.label_global_transform_model.setText(QCoreApplication.translate("MainWindow", u"Global Transform Model:", None))
        self.combo_global_transform_model.setToolTip(QCoreApplication.translate("MainWindow", u"Rigid keeps scale fixed. Similarity lets the global stage estimate one uniform scale factor.", None))
        self.combo_global_transform_model.setItemText(0, QCoreApplication.translate("MainWindow", u"Rigid", None))
        self.combo_global_transform_model.setItemText(1, QCoreApplication.translate("MainWindow", u"Similarity (uniform scale)", None))
        self.label_ransac_title.setText(QCoreApplication.translate("MainWindow", u"Global Registration (RANSAC)", None))
        self.label_ransac_dist.setText(QCoreApplication.translate("MainWindow", u"Distance Multiplier:", None))
        self.label_ransac_max_iter.setText(QCoreApplication.translate("MainWindow", u"Max Iterations:", None))
        self.label_ransac_validation.setText(QCoreApplication.translate("MainWindow", u"Validation Iters:", None))
        self.label_icp_title.setText(QCoreApplication.translate("MainWindow", u"Local Registration (ICP)", None))
        self.label_icp_dist.setText(QCoreApplication.translate("MainWindow", u"Distance Multiplier:", None))
        self.label_results_title.setText(QCoreApplication.translate("MainWindow", u"Registration Results", None))
        self.label_ransac_results_title.setText(QCoreApplication.translate("MainWindow", u"Global Results (RANSAC)", None))
        self.label_ransac_fitness_label.setText(QCoreApplication.translate("MainWindow", u"Fitness:", None))
        self.label_ransac_fitness.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_ransac_rmse_label.setText(QCoreApplication.translate("MainWindow", u"Inlier RMSE:", None))
        self.label_ransac_rmse.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_icp_results_title.setText(QCoreApplication.translate("MainWindow", u"Local Results (ICP)", None))
        self.label_icp_fitness_label.setText(QCoreApplication.translate("MainWindow", u"Fitness:", None))
        self.label_icp_fitness.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_icp_rmse_label.setText(QCoreApplication.translate("MainWindow", u"Inlier RMSE:", None))
        self.label_icp_rmse.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_transform_title.setText(QCoreApplication.translate("MainWindow", u"Transformation Matrix", None))
        self.label_transform_help.setText(QCoreApplication.translate("MainWindow", u"Enter a 4x4 affine matrix for the current scan.", None))
        self.btn_matrix_identity.setText(QCoreApplication.translate("MainWindow", u"Identity", None))
        self.btn_matrix_load_current.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.btn_transform_apply_current.setText(QCoreApplication.translate("MainWindow", u"Apply Current", None))
        self.btn_transform_duplicate_current.setText(QCoreApplication.translate("MainWindow", u"Create Copy", None))
        self.label_transform_status.setText(QCoreApplication.translate("MainWindow", u"Select a scan tab to transform.", None))
        self.menuFiles.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuImport_2.setTitle(QCoreApplication.translate("MainWindow", u"Import", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
    # retranslateUi

