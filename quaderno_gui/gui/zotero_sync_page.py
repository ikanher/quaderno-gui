"""
Zotero sync page UI for QuadernoGUI.
"""

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quaderno_gui.core.sync import SyncWorker
from quaderno_gui.core.zotero import resolve_zotero_paths


class ZoteroSyncPage(QWidget):
    """
    Page for synchronizing Zotero files with the DigitalPaper device.
    """

    def __init__(self):
        super().__init__()
        self.dp = None
        self.worker = None
        self.settings = QSettings('QuadernoGUI', 'ZoteroSync')

        default_storage, default_db = resolve_zotero_paths()
        default_storage = str(default_storage)
        default_db = str(default_db)
        saved_storage = self.settings.value('storage_path', '', type=str)
        saved_db = self.settings.value('db_path', '', type=str)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Zotero storage folder:"))
        storage_row = QHBoxLayout()
        self.storage_path_edit = QLineEdit(saved_storage)
        self.storage_path_edit.setPlaceholderText(default_storage)
        storage_row.addWidget(self.storage_path_edit)
        storage_browse = QPushButton("Browse...")
        storage_browse.clicked.connect(self.browse_storage_path)
        storage_row.addWidget(storage_browse)
        layout.addLayout(storage_row)

        layout.addWidget(QLabel("Zotero database file:"))
        db_row = QHBoxLayout()
        self.db_path_edit = QLineEdit(saved_db)
        self.db_path_edit.setPlaceholderText(default_db)
        db_row.addWidget(self.db_path_edit)
        db_browse = QPushButton("Browse...")
        db_browse.clicked.connect(self.browse_db_path)
        db_row.addWidget(db_browse)
        layout.addLayout(db_row)

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
        storage_path = self.storage_path_edit.text().strip() or None
        db_path = self.db_path_edit.text().strip() or None
        self.settings.setValue('storage_path', self.storage_path_edit.text().strip())
        self.settings.setValue('db_path', self.db_path_edit.text().strip())
        self.worker = SyncWorker(self.dp, simulate, remote_base, storage_path=storage_path, db_path=db_path)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(self.sync_finished)
        self.worker.start()

    def sync_finished(self, checkpoint):
        """
        Callback after sync is complete.
        """
        self.log_message("Sync operation finished.")

    def browse_storage_path(self):
        current = self.storage_path_edit.text().strip() or self.storage_path_edit.placeholderText()
        directory = QFileDialog.getExistingDirectory(self, "Select Zotero Storage Folder", current)
        if directory:
            self.storage_path_edit.setText(directory)

    def browse_db_path(self):
        current = self.db_path_edit.text().strip() or self.db_path_edit.placeholderText()
        db_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Zotero Database File",
            current,
            "SQLite Database (*.sqlite *.db);;All Files (*)",
        )
        if db_file:
            self.db_path_edit.setText(db_file)
