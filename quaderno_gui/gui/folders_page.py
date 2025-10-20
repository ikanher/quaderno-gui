"""
Folders page UI for QuadernoGUI.
"""

import os

from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quaderno_gui.gui.upload_area import UploadArea


class FoldersPage(QWidget):
    """
    Page for managing folders and files within folders on the device.
    """

    def __init__(self):
        super().__init__()
        self.dp = None

        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.refresh_folders_button = QPushButton("Refresh Folders")
        self.refresh_folders_button.clicked.connect(self.refresh_folders)
        top_layout.addWidget(self.refresh_folders_button)
        self.create_folder_button = QPushButton("Create Folder")
        self.create_folder_button.clicked.connect(self.create_folder)
        top_layout.addWidget(self.create_folder_button)
        self.delete_folder_button = QPushButton("Delete Folder")
        self.delete_folder_button.clicked.connect(self.delete_folder)
        top_layout.addWidget(self.delete_folder_button)
        layout.addLayout(top_layout)

        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.folder_list.itemDoubleClicked.connect(self.folder_selected)
        layout.addWidget(QLabel("Folders (sorted):"))
        layout.addWidget(self.folder_list)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.itemDoubleClicked.connect(self.download_file)
        layout.addWidget(QLabel("Files in Selected Folder:"))
        layout.addWidget(self.file_list)

        file_btn_layout = QHBoxLayout()
        self.download_button = QPushButton("Download Selected")
        self.download_button.clicked.connect(self.download_file)
        file_btn_layout.addWidget(self.download_button)
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_file)
        file_btn_layout.addWidget(self.delete_button)
        layout.addLayout(file_btn_layout)

        self.upload_area = UploadArea(self, target="folder")
        self.upload_area.setFixedHeight(100)
        layout.addWidget(
            QLabel("Drag and drop PDF files here to upload to selected folder:")
        )
        layout.addWidget(self.upload_area)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(QLabel("Folders Log:"))
        layout.addWidget(self.log)

        self.folder_list.itemSelectionChanged.connect(self.folder_selected)

    def set_digital_paper(self, dp):
        """
        Set the DigitalPaper instance and refresh folders.
        """
        self.dp = dp
        self.refresh_folders()

    def log_message(self, message):
        """
        Log a message to the folder log.
        """
        self.log.append(message)

    def refresh_folders(self):
        """
        Retrieve and display the list of folders from the device.
        """
        if not self.dp:
            return

        self.folder_list.clear()

        try:
            all_entries = self.dp.list_all()
            folders = [
                entry.get("entry_path", "")
                for entry in all_entries
                if entry.get("entry_type") == "folder"
            ]
            # Remove the prefix if needed
            folders = [
                f[len("Document/") :] if f.startswith("Document/") else f
                for f in folders
            ]
            folders.sort()
            for folder in folders:
                self.folder_list.addItem(folder)
            self.log_message("Folders refreshed.")

        except Exception as e:
            QMessageBox.warning(self, "Error", "Failed to retrieve folders: " + str(e))

    def folder_selected(self, _item=None):
        """
        Called when a folder is selected; refresh its file list.
        """
        selected_items = self.folder_list.selectedItems()

        if selected_items:
            folder = selected_items[0].text()
            self.refresh_files_in_folder(folder)

    def refresh_files_in_folder(self, folder):
        """
        Retrieve and display files within the selected folder.
        """
        if not self.dp:
            return

        self.file_list.clear()

        try:
            entries = self.dp.list_objects_in_folder("Document/" + folder)
            files = [
                entry.get("entry_path", "")
                for entry in entries
                if entry.get("entry_type") == "document"
            ]
            prefix = "Document/" + folder + "/"
            display_files = []

            for f in files:
                display_files.append(f[len(prefix) :] if f.startswith(prefix) else f)

            display_files.sort()

            for f in display_files:
                self.file_list.addItem(f)

            self.log_message("Files refreshed for folder: " + folder)

        except Exception as e:
            QMessageBox.warning(self, "Error", "Failed to retrieve files: " + str(e))

    def download_file(self, _item=None):
        """
        Download the selected file from the current folder.
        """
        if not self.dp:
            return

        items = self.file_list.selectedItems()

        if not items:
            return

        filename = items[0].text()

        selected_folder_items = self.folder_list.selectedItems()

        if not selected_folder_items:
            return

        folder = selected_folder_items[0].text()
        full_remote = "Document/" + folder + "/" + filename

        local_file, _ = QFileDialog.getSaveFileName(self, "Save File", filename)

        if local_file:
            try:
                data = self.dp.download(full_remote)
                with open(local_file, "wb") as f:
                    f.write(data)

                QMessageBox.information(
                    self, "Download", "File downloaded successfully."
                )

                self.refresh_files_in_folder(folder)

            except Exception as e:
                QMessageBox.warning(self, "Error", "Failed to download file: " + str(e))

    def delete_file(self):
        """
        Delete the selected file from the current folder.
        """
        if not self.dp:
            return

        items = self.file_list.selectedItems()

        if not items:
            return

        selected_folder_items = self.folder_list.selectedItems()

        if not selected_folder_items:
            return

        folder = selected_folder_items[0].text()

        for item in items:
            filename = item.text()
            full_remote = "Document/" + folder + "/" + filename

            reply = QMessageBox.question(
                self, "Delete", f"Delete {filename}?", QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    self.dp.delete_document(full_remote)
                    self.log_message("Deleted: " + filename)
                except Exception as e:
                    QMessageBox.warning(
                        self, "Error", "Failed to delete file: " + str(e)
                    )

        self.refresh_files_in_folder(folder)

    def create_folder(self):
        """
        Create a new folder, optionally within a selected folder.
        """
        if not self.dp:
            return

        base_folder = "Document/"

        selected = self.folder_list.selectedItems()

        if selected:
            base_folder += selected[0].text() + "/"

        folder_name, ok = QInputDialog.getText(
            self, "Create Folder", "Enter new folder name:"
        )

        if ok and folder_name:
            new_folder = base_folder + folder_name
            try:
                self.dp.new_folder(new_folder)
                self.log_message("Created folder: " + new_folder[len("Document/") :])
                self.refresh_folders()
            except Exception as e:
                QMessageBox.warning(self, "Error", "Failed to create folder: " + str(e))

    def delete_folder(self):
        """
        Delete the selected folder.
        """
        if not self.dp:
            return

        selected = self.folder_list.selectedItems()

        if not selected:
            return

        folder = "Document/" + selected[0].text()

        reply = QMessageBox.question(
            self,
            "Delete Folder",
            f"Delete folder {selected[0].text()}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                self.dp.delete_folder(folder)
                self.log_message("Deleted folder: " + selected[0].text())
                self.refresh_folders()
                self.file_list.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", "Failed to delete folder: " + str(e))
