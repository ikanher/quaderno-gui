"""
Zotero sync page UI for QuadernoGUI.
"""

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quaderno_gui.core.sync import SyncWorker


class ZoteroSyncPage(QWidget):
    """
    Page for synchronizing Zotero files with the DigitalPaper device.
    """

    def __init__(self):
        super().__init__()
        self.dp = None
        self.worker = None

        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        self.simulate_button = QPushButton("Simulate Sync")
        self.simulate_button.clicked.connect(lambda: self.start_sync(simulate=True))
        btn_layout.addWidget(self.simulate_button)
        self.sync_button = QPushButton("Perform Sync")
        self.sync_button.clicked.connect(lambda: self.start_sync(simulate=False))
        btn_layout.addWidget(self.sync_button)
        layout.addLayout(btn_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("Zotero Sync Log:"))
        layout.addWidget(self.log)

    def set_digital_paper(self, dp):
        """
        Set the DigitalPaper instance.
        """
        self.dp = dp

    def log_message(self, message):
        """
        Append a message to the sync log.
        """
        self.log.append(message)

    def start_sync(self, simulate=False):
        """
        Start the sync process, either in simulation or live mode.
        """
        if not self.dp:
            QMessageBox.warning(self, "Error", "Device not connected")
            return

        self.log.clear()
        remote_base = "Document/Zotero"
        self.worker = SyncWorker(self.dp, simulate, remote_base)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.sync_finished)
        self.worker.start()

    def sync_finished(self, checkpoint):
        """
        Callback after sync is complete.
        """
        self.log_message("Sync operation finished.")
