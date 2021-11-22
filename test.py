#%% Imports
try:
    from PyQt5.QtCore import QSettings
    from PyQt5 import uic,QtCore
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QMessageBox
except:
    print("error QT5 import")

import ctypes
import os

msg = QMessageBox()
msg.setIcon(QMessageBox.Critical)
msg.setText("Controler Smartact pb !")
msg.setInformativeText("All smart controller are not connected, please reboot... !")
msg.setWindowTitle("Warning ...")
msg.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
msg.exec_()