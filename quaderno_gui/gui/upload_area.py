"""
Upload area widget for drag-and-drop PDF uploads.
"""

import os
from PyQt5.QtWidgets import QTextEdit, QMessageBox
from PyQt5.QtCore import Qt


class UploadArea(QTextEdit):
    """
    A QTextEdit subclass that accepts drag-and-drop PDF files.
    """

    def __init__(self, parent_page, target="default"):
        super().__init__()
        self.parent_page = parent_page
        self.target = target
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.setText("Drop PDF files here to upload")
        self.default_style = self.styleSheet()

    def dragEnterEvent(self, event):
        """
        Highlight the widget when a valid PDF is dragged over.
        """
        if event.mimeData().hasUrls():
            valid = any(
                url.toLocalFile().lower().endswith(".pdf")
                for url in event.mimeData().urls()
            )

            if valid:
                self.setStyleSheet("background-color: #cceeff;")
                event.acceptProposedAction()
            else:
                event.ignore()

    def dragLeaveEvent(self, event):
        """
        Reset the widget style when the drag leaves.
        """
        self.setStyleSheet(self.default_style)

    def dropEvent(self, event):
        """
        Handle dropped files and upload them to the device.
        """
        self.setStyleSheet(self.default_style)

        if not self.parent_page.dp:
            return

        if self.target == "folder":
            selected_items = self.parent_page.folder_list.selectedItems()

            if not selected_items:
                QMessageBox.warning(self, "Error", "Please select a folder first.")
                return

            target_folder = "Document/" + selected_items[0].text()
        else:
            target_folder = "Document"
        for url in event.mimeData().urls():
            local_file = url.toLocalFile()

            if os.path.isfile(local_file):
                if not local_file.lower().endswith(".pdf"):
                    QMessageBox.warning(self, "Error", "Only PDF files are allowed.")
                    continue

                remote_path = target_folder + "/" + os.path.basename(local_file)

                try:
                    if self.parent_page.dp.path_exists(remote_path):
                        reply = QMessageBox.question(
                            self,
                            "Duplicate",
                            f"{remote_path} already exists. Overwrite?",
                            QMessageBox.Yes | QMessageBox.No,
                        )

                        if reply != QMessageBox.Yes:
                            continue

                except Exception:
                    pass
                try:
                    self.parent_page.dp.upload_file(local_file, remote_path)
                    QMessageBox.information(
                        self,
                        "Upload",
                        f"{os.path.basename(local_file)} uploaded as {remote_path}.",
                    )

                    if self.target == "folder":
                        folder = self.parent_page.folder_list.selectedItems()[0].text()
                        self.parent_page.refresh_files_in_folder(folder)
                    else:
                        self.parent_page.refresh_files()

                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", f"Failed to upload {local_file}: " + str(e)
                    )
