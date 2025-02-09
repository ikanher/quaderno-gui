"""
Connect page UI for QuadernoGUI.
"""

import os

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quaderno_gui.core.connection import ConnectionWorker


class ConnectPage(QWidget):
    """
    Page for connecting to a DigitalPaper device.
    """

    def __init__(self, parent_window):
        super().__init__()

        self.parent_window = parent_window
        self.settings = QSettings("MyCompany", "QuadernoGUI")
        self.worker = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Device Address:"))
        self.addr_edit = QLineEdit()
        self.addr_edit.setPlaceholderText("e.g., 192.168.0.13")
        self.addr_edit.setText(self.settings.value("device/address", ""))
        layout.addWidget(self.addr_edit)

        layout.addWidget(QLabel("Serial Number (optional):"))
        self.serial_edit = QLineEdit()
        self.serial_edit.setText(self.settings.value("device/serial", ""))
        layout.addWidget(self.serial_edit)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)
        layout.addWidget(self.connect_button)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def connect_device(self):
        """
        Initiates connection to the DigitalPaper device.
        """
        addr = self.addr_edit.text().strip()
        serial = self.serial_edit.text().strip() or None

        if not addr:
            self.log.append("Please enter a device address.")
            return

        self.settings.setValue("device/address", addr)
        self.settings.setValue("device/serial", serial if serial else "")
        self.connect_button.setEnabled(False)
        self.log.clear()
        self.log.append("Starting connection...")
        self.worker = ConnectionWorker(addr, serial)
        self.worker.log_signal.connect(self.log.append)
        self.worker.finished_signal.connect(self.connection_finished)
        self.worker.start()

    def connection_finished(self, dp):
        """
        Callback when connection attempt finishes.
        """
        if dp is not None:
            self.parent_window.set_digital_paper(dp)
        else:
            self.log.append("Connection failed.")

        self.connect_button.setEnabled(True)

    def set_connected(self, dp):
        """
        Update UI after successful connection.
        """
        pass
