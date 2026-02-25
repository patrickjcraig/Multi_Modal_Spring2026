# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_V1.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QStatusBar, QToolButton, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1089, 711)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QRect(22, 540, 381, 23))
        self.progressBar.setValue(24)
        self.openGLWidget = QOpenGLWidget(self.centralwidget)
        self.openGLWidget.setObjectName(u"openGLWidget")
        self.openGLWidget.setGeometry(QRect(20, 50, 781, 481))
        self.horizontalLayoutWidget_2 = QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(20, 540, 361, 31))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 30, 121, 18))
        self.horizontalLayoutWidget = QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 0, 425, 27))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.toolButton = QToolButton(self.horizontalLayoutWidget)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setEnabled(True)

        self.horizontalLayout.addWidget(self.toolButton)

        self.toolButton_2 = QToolButton(self.horizontalLayoutWidget)
        self.toolButton_2.setObjectName(u"toolButton_2")

        self.horizontalLayout.addWidget(self.toolButton_2)

        self.toolButton_3 = QToolButton(self.horizontalLayoutWidget)
        self.toolButton_3.setObjectName(u"toolButton_3")

        self.horizontalLayout.addWidget(self.toolButton_3)

        self.toolButton_4 = QToolButton(self.horizontalLayoutWidget)
        self.toolButton_4.setObjectName(u"toolButton_4")

        self.horizontalLayout.addWidget(self.toolButton_4)

        self.toolButton_5 = QToolButton(self.horizontalLayoutWidget)
        self.toolButton_5.setObjectName(u"toolButton_5")

        self.horizontalLayout.addWidget(self.toolButton_5)

        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(830, 40, 231, 634))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_params_title = QLabel(self.verticalLayoutWidget)
        self.label_params_title.setObjectName(u"label_params_title")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_params_title.setFont(font)

        self.verticalLayout.addWidget(self.label_params_title)

        self.label_voxel_size = QLabel(self.verticalLayoutWidget)
        self.label_voxel_size.setObjectName(u"label_voxel_size")

        self.verticalLayout.addWidget(self.label_voxel_size)

        self.spinBox_voxel_size = QDoubleSpinBox(self.verticalLayoutWidget)
        self.spinBox_voxel_size.setObjectName(u"spinBox_voxel_size")
        self.spinBox_voxel_size.setDecimals(2)
        self.spinBox_voxel_size.setMinimum(0.100000000000000)
        self.spinBox_voxel_size.setMaximum(10.000000000000000)
        self.spinBox_voxel_size.setSingleStep(0.500000000000000)
        self.spinBox_voxel_size.setValue(2.000000000000000)

        self.verticalLayout.addWidget(self.spinBox_voxel_size)

        self.line_1 = QFrame(self.verticalLayoutWidget)
        self.line_1.setObjectName(u"line_1")
        self.line_1.setFrameShape(QFrame.Shape.HLine)
        self.line_1.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_1)

        self.label_ransac_title = QLabel(self.verticalLayoutWidget)
        self.label_ransac_title.setObjectName(u"label_ransac_title")
        font1 = QFont()
        font1.setBold(True)
        self.label_ransac_title.setFont(font1)

        self.verticalLayout.addWidget(self.label_ransac_title)

        self.label_ransac_dist = QLabel(self.verticalLayoutWidget)
        self.label_ransac_dist.setObjectName(u"label_ransac_dist")

        self.verticalLayout.addWidget(self.label_ransac_dist)

        self.spinBox_ransac_dist = QDoubleSpinBox(self.verticalLayoutWidget)
        self.spinBox_ransac_dist.setObjectName(u"spinBox_ransac_dist")
        self.spinBox_ransac_dist.setDecimals(2)
        self.spinBox_ransac_dist.setMinimum(0.500000000000000)
        self.spinBox_ransac_dist.setMaximum(5.000000000000000)
        self.spinBox_ransac_dist.setSingleStep(0.100000000000000)
        self.spinBox_ransac_dist.setValue(1.500000000000000)

        self.verticalLayout.addWidget(self.spinBox_ransac_dist)

        self.label_ransac_max_iter = QLabel(self.verticalLayoutWidget)
        self.label_ransac_max_iter.setObjectName(u"label_ransac_max_iter")

        self.verticalLayout.addWidget(self.label_ransac_max_iter)

        self.spinBox_ransac_max_iter = QSpinBox(self.verticalLayoutWidget)
        self.spinBox_ransac_max_iter.setObjectName(u"spinBox_ransac_max_iter")
        self.spinBox_ransac_max_iter.setMinimum(1000)
        self.spinBox_ransac_max_iter.setMaximum(1000000)
        self.spinBox_ransac_max_iter.setSingleStep(10000)
        self.spinBox_ransac_max_iter.setValue(100000)

        self.verticalLayout.addWidget(self.spinBox_ransac_max_iter)

        self.label_ransac_validation = QLabel(self.verticalLayoutWidget)
        self.label_ransac_validation.setObjectName(u"label_ransac_validation")

        self.verticalLayout.addWidget(self.label_ransac_validation)

        self.spinBox_ransac_validation = QSpinBox(self.verticalLayoutWidget)
        self.spinBox_ransac_validation.setObjectName(u"spinBox_ransac_validation")
        self.spinBox_ransac_validation.setMinimum(100)
        self.spinBox_ransac_validation.setMaximum(10000)
        self.spinBox_ransac_validation.setSingleStep(100)
        self.spinBox_ransac_validation.setValue(1000)

        self.verticalLayout.addWidget(self.spinBox_ransac_validation)

        self.line_2 = QFrame(self.verticalLayoutWidget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.label_icp_title = QLabel(self.verticalLayoutWidget)
        self.label_icp_title.setObjectName(u"label_icp_title")
        self.label_icp_title.setFont(font1)

        self.verticalLayout.addWidget(self.label_icp_title)

        self.label_icp_dist = QLabel(self.verticalLayoutWidget)
        self.label_icp_dist.setObjectName(u"label_icp_dist")

        self.verticalLayout.addWidget(self.label_icp_dist)

        self.spinBox_icp_dist = QDoubleSpinBox(self.verticalLayoutWidget)
        self.spinBox_icp_dist.setObjectName(u"spinBox_icp_dist")
        self.spinBox_icp_dist.setDecimals(2)
        self.spinBox_icp_dist.setMinimum(0.100000000000000)
        self.spinBox_icp_dist.setMaximum(2.000000000000000)
        self.spinBox_icp_dist.setSingleStep(0.050000000000000)
        self.spinBox_icp_dist.setValue(0.400000000000000)

        self.verticalLayout.addWidget(self.spinBox_icp_dist)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.line_3 = QFrame(self.verticalLayoutWidget)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_3)

        self.label_results_title = QLabel(self.verticalLayoutWidget)
        self.label_results_title.setObjectName(u"label_results_title")
        self.label_results_title.setFont(font)

        self.verticalLayout.addWidget(self.label_results_title)

        self.label_ransac_results_title = QLabel(self.verticalLayoutWidget)
        self.label_ransac_results_title.setObjectName(u"label_ransac_results_title")
        self.label_ransac_results_title.setFont(font1)

        self.verticalLayout.addWidget(self.label_ransac_results_title)

        self.label_ransac_fitness_label = QLabel(self.verticalLayoutWidget)
        self.label_ransac_fitness_label.setObjectName(u"label_ransac_fitness_label")

        self.verticalLayout.addWidget(self.label_ransac_fitness_label)

        self.label_ransac_fitness = QLabel(self.verticalLayoutWidget)
        self.label_ransac_fitness.setObjectName(u"label_ransac_fitness")
        self.label_ransac_fitness.setStyleSheet(u"color: rgb(0, 170, 255); font-weight: bold;")

        self.verticalLayout.addWidget(self.label_ransac_fitness)

        self.label_ransac_rmse_label = QLabel(self.verticalLayoutWidget)
        self.label_ransac_rmse_label.setObjectName(u"label_ransac_rmse_label")

        self.verticalLayout.addWidget(self.label_ransac_rmse_label)

        self.label_ransac_rmse = QLabel(self.verticalLayoutWidget)
        self.label_ransac_rmse.setObjectName(u"label_ransac_rmse")
        self.label_ransac_rmse.setStyleSheet(u"color: rgb(0, 170, 255); font-weight: bold;")

        self.verticalLayout.addWidget(self.label_ransac_rmse)

        self.line_4 = QFrame(self.verticalLayoutWidget)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.HLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_4)

        self.label_icp_results_title = QLabel(self.verticalLayoutWidget)
        self.label_icp_results_title.setObjectName(u"label_icp_results_title")
        self.label_icp_results_title.setFont(font1)

        self.verticalLayout.addWidget(self.label_icp_results_title)

        self.label_icp_fitness_label = QLabel(self.verticalLayoutWidget)
        self.label_icp_fitness_label.setObjectName(u"label_icp_fitness_label")

        self.verticalLayout.addWidget(self.label_icp_fitness_label)

        self.label_icp_fitness = QLabel(self.verticalLayoutWidget)
        self.label_icp_fitness.setObjectName(u"label_icp_fitness")
        self.label_icp_fitness.setStyleSheet(u"color: rgb(0, 255, 127); font-weight: bold;")

        self.verticalLayout.addWidget(self.label_icp_fitness)

        self.label_icp_rmse_label = QLabel(self.verticalLayoutWidget)
        self.label_icp_rmse_label.setObjectName(u"label_icp_rmse_label")

        self.verticalLayout.addWidget(self.label_icp_rmse_label)

        self.label_icp_rmse = QLabel(self.verticalLayoutWidget)
        self.label_icp_rmse.setObjectName(u"label_icp_rmse")
        self.label_icp_rmse.setStyleSheet(u"color: rgb(0, 255, 127); font-weight: bold;")

        self.verticalLayout.addWidget(self.label_icp_rmse)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(410, 0, 201, 18))
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(830, 10, 271, 31))
        self.label_step_info = QLabel(self.centralwidget)
        self.label_step_info.setObjectName(u"label_step_info")
        self.label_step_info.setGeometry(QRect(390, 540, 239, 33))
        self.label_step_info.setFont(font1)
        self.label_step_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_prev_step = QPushButton(self.centralwidget)
        self.btn_prev_step.setObjectName(u"btn_prev_step")
        self.btn_prev_step.setEnabled(False)
        self.btn_prev_step.setGeometry(QRect(22, 570, 362, 26))
        self.btn_next_step = QPushButton(self.centralwidget)
        self.btn_next_step.setObjectName(u"btn_next_step")
        self.btn_next_step.setEnabled(False)
        self.btn_next_step.setGeometry(QRect(390, 570, 361, 21))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1089, 33))
        self.menuFiles = QMenu(self.menubar)
        self.menuFiles.setObjectName(u"menuFiles")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFiles.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"OpenGL Window", None))
        self.toolButton.setText(QCoreApplication.translate("MainWindow", u"Perform Registration", None))
        self.toolButton_2.setText(QCoreApplication.translate("MainWindow", u"Save Data", None))
        self.toolButton_3.setText(QCoreApplication.translate("MainWindow", u"Icon 3", None))
        self.toolButton_4.setText(QCoreApplication.translate("MainWindow", u"Icon 4", None))
        self.toolButton_5.setText(QCoreApplication.translate("MainWindow", u"Icon 5", None))
        self.label_params_title.setText(QCoreApplication.translate("MainWindow", u"Registration Parameters", None))
        self.label_voxel_size.setText(QCoreApplication.translate("MainWindow", u"Voxel Size (Downsampling):", None))
        self.label_ransac_title.setText(QCoreApplication.translate("MainWindow", u"RANSAC Parameters", None))
        self.label_ransac_dist.setText(QCoreApplication.translate("MainWindow", u"Distance Threshold Multiplier:", None))
        self.label_ransac_max_iter.setText(QCoreApplication.translate("MainWindow", u"Max Iterations:", None))
        self.label_ransac_validation.setText(QCoreApplication.translate("MainWindow", u"Validation Iterations:", None))
        self.label_icp_title.setText(QCoreApplication.translate("MainWindow", u"ICP Parameters", None))
        self.label_icp_dist.setText(QCoreApplication.translate("MainWindow", u"Distance Threshold Multiplier:", None))
        self.label_results_title.setText(QCoreApplication.translate("MainWindow", u"Registration Results", None))
        self.label_ransac_results_title.setText(QCoreApplication.translate("MainWindow", u"RANSAC Results", None))
        self.label_ransac_fitness_label.setText(QCoreApplication.translate("MainWindow", u"Fitness:", None))
        self.label_ransac_fitness.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_ransac_rmse_label.setText(QCoreApplication.translate("MainWindow", u"Inlier RMSE:", None))
        self.label_ransac_rmse.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_icp_results_title.setText(QCoreApplication.translate("MainWindow", u"ICP Results", None))
        self.label_icp_fitness_label.setText(QCoreApplication.translate("MainWindow", u"Fitness:", None))
        self.label_icp_fitness.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_icp_rmse_label.setText(QCoreApplication.translate("MainWindow", u"Inlier RMSE:", None))
        self.label_icp_rmse.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Icon Bar (Change as needed)", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Algorithm Parameter Table goes below", None))
        self.label_step_info.setText(QCoreApplication.translate("MainWindow", u"Step 1/3: Original Point Clouds", None))
        self.btn_prev_step.setText(QCoreApplication.translate("MainWindow", u"\u25c0 Previous", None))
        self.btn_next_step.setText(QCoreApplication.translate("MainWindow", u"Next \u25b6", None))
        self.menuFiles.setTitle(QCoreApplication.translate("MainWindow", u"Files", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

