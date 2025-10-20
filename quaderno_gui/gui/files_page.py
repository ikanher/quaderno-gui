"""
Files page UI for QuadernoGUI.
"""

import os

from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quaderno_gui.gui.upload_area import UploadArea


class FilesPage(QWidget):
    """
    Page for managing files on the DigitalPaper device.
    """

    def __init__(self):
        super().__init__()
        self.dp = None

        layout = QVBoxLayout(self)

        top_btn_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh File List")
        self.refresh_button.clicked.connect(self.refresh_files)
        top_btn_layout.addWidget(self.refresh_button)
        layout.addLayout(top_btn_layout)

        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.files_list.itemDoubleClicked.connect(self.download_file)
        layout.addWidget(self.files_list)

        btn_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_file)
        btn_layout.addWidget(self.download_button)
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_file)
        btn_layout.addWidget(self.delete_button)
        layout.addLayout(btn_layout)

        layout.addWidget(QLabel("Drag and drop PDF files here to upload to device:"))
        self.upload_area = UploadArea(self, target="default")
        self.upload_area.setFixedHeight(100)
        layout.addWidget(self.upload_area)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("Files Log:"))
        layout.addWidget(self.log)

    def set_digital_paper(self, dp):
        """
        Set the DigitalPaper instance and refresh file list.
        """
        self.dp = dp
        self.refresh_files()

    def refresh_files(self):
        """
        Retrieve and display the list of files from the device.
        """
        if not self.dp:
            return

        self.files_list.clear()

        try:
            docs = self.dp.list_documents()

            for doc in docs:
                path = doc.get("entry_path", "Unknown")
                if path.startswith("Document/"):
                    path = path[len("Document/") :]
                self.files_list.addItem(path)

            self.log.append("File list refreshed.")

        except Exception as e:
            QMessageBox.warning(
                self, "Error", "Failed to retrieve file list: " + str(e)
            )

    def download_file(self, _item=None):
        """
        Download the selected file from the device.
        """
        if not self.dp:
            return

        items = self.files_list.selectedItems()

        if not items:
            return

        remote_path = items[0].text()
        full_remote = "Document/" + remote_path

        local_file, _ = QFileDialog.getSaveFileName(
            self, "Save File", os.path.basename(remote_path)
        )

        if local_file:
            try:
                data = self.dp.download(full_remote)
                with open(local_file, "wb") as f:
                    f.write(data)
                QMessageBox.information(
                    self, "Download", "File downloaded successfully."
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", "Failed to download file: " + str(e))

    def delete_file(self):
        """
        Delete the selected file from the device.
        """
        if not self.dp:
            return

        items = self.files_list.selectedItems()

        if not items:
            return

        for item in items:
            remote_path = item.text()
            full_remote = "Document/" + remote_path

            reply = QMessageBox.question(
                self,
                "Delete",
                f"Delete {remote_path}?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                try:
                    self.dp.delete_document(full_remote)
                    self.log.append("Deleted: " + remote_path)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", "Failed to delete file: " + str(e)
                    )

        self.refresh_files()
