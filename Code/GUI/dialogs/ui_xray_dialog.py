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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QLineEdit, QPlainTextEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_XRayDialog(object):
    def setupUi(self, XRayDialog):
        if not XRayDialog.objectName():
            XRayDialog.setObjectName(u"XRayDialog")
        XRayDialog.resize(378, 273)
        self.buttonBox = QDialogButtonBox(XRayDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.line_path = QLineEdit(XRayDialog)
        self.line_path.setObjectName(u"line_path")
        self.line_path.setGeometry(QRect(140, 60, 181, 31))
        self.combo_import_type = QComboBox(XRayDialog)
        self.combo_import_type.addItem("")
        self.combo_import_type.addItem("")
        self.combo_import_type.addItem("")
        self.combo_import_type.setObjectName(u"combo_import_type")
        self.combo_import_type.setGeometry(QRect(140, 20, 181, 31))
        self.plainTextEdit = QPlainTextEdit(XRayDialog)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        self.plainTextEdit.setGeometry(QRect(10, 20, 111, 31))
        self.plainTextEdit_2 = QPlainTextEdit(XRayDialog)
        self.plainTextEdit_2.setObjectName(u"plainTextEdit_2")
        self.plainTextEdit_2.setGeometry(QRect(10, 60, 111, 31))
        self.btn_browse = QPushButton(XRayDialog)
        self.btn_browse.setObjectName(u"btn_browse")
        self.btn_browse.setGeometry(QRect(330, 60, 31, 31))

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

        self.plainTextEdit.setPlainText(QCoreApplication.translate("XRayDialog", u"Data Type", None))
        self.plainTextEdit_2.setPlainText(QCoreApplication.translate("XRayDialog", u"File/Folder Path", None))
        self.btn_browse.setText(QCoreApplication.translate("XRayDialog", u"...", None))
    # retranslateUi

