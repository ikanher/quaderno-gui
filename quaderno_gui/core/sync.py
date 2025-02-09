"""
Sync functionality for QuadernoGUI.
"""

from PyQt5.QtCore import QThread, pyqtSignal

from quaderno_gui.core.zotero import build_zotero_file_mapping, build_zotero_folder_set


class SyncWorker(QThread):
    """
    Worker thread to synchronize Zotero files with the DigitalPaper device.
    """
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)

    def __init__(self, dp, simulate, remote_base, parent=None):
        super().__init__(parent)

        self.dp = dp
        self.simulate = simulate
        self.remote_base = remote_base

    def run(self):
        self.log_signal.emit('Starting Zotero sync...' + (' (Simulation)' if self.simulate else ''))
        zotero_files = build_zotero_file_mapping()
        zotero_folders = build_zotero_folder_set()

        # List what's on the device within remote_base.
        device_items = self.dp.list_all()
        device_files = {}
        device_folders = set()

        for entry in device_items:
            path = entry.get('entry_path', '')
            entry_type = entry.get('entry_type')

            if not path.startswith(self.remote_base):
                continue

            relative_path = path[len(self.remote_base):].lstrip('/')

            if entry_type == 'document':
                device_files[relative_path] = 0
            elif entry_type == 'folder':
                device_folders.add(relative_path)

        # Ensure new Zotero folders exist on the device.
        for folder in sorted(zotero_folders):
            device_path = folder.replace('\\', '/')

            if device_path not in device_folders:
                if self.simulate:
                    self.log_signal.emit('Simulate: Would create folder: ' + self.remote_base + '/' + device_path)
                else:
                    try:
                        self.dp.new_folder(self.remote_base + '/' + device_path)
                        self.log_signal.emit('Created folder: ' + self.remote_base + '/' + device_path)
                    except Exception as e:
                        self.log_signal.emit('Folder creation failed (' + device_path + '): ' + str(e))

        # Remove folders that no longer exist in Zotero.
        for folder in sorted(device_folders, reverse=True):
            if folder not in zotero_folders and folder != '':
                remote_folder = self.remote_base + '/' + folder

                if self.simulate:
                    self.log_signal.emit('Simulate: Would delete folder: ' + remote_folder)
                else:
                    try:
                        self.dp.delete_folder(remote_folder)
                        self.log_signal.emit('Deleted folder: ' + remote_folder)
                    except Exception as e:
                        self.log_signal.emit('Folder deletion failed (' + remote_folder + '): ' + str(e))

        # Compare files that exist in Zotero vs device.
        zotero_rel_paths = set(zotero_files.keys())
        device_rel_paths = set(device_files.keys())

        # Delete files on device that are not in Zotero.
        for rel in sorted(device_rel_paths - zotero_rel_paths):
            remote_path = self.remote_base + '/' + rel

            if self.simulate:
                self.log_signal.emit('Simulate: Would delete file: ' + remote_path)
            else:
                try:
                    self.dp.delete_document(remote_path)
                    self.log_signal.emit('Deleted file: ' + remote_path)
                    if self.dp.path_exists(remote_path):
                        self.log_signal.emit('Warning: File still exists after deletion attempt: ' + remote_path)
                except Exception as e:
                    self.log_signal.emit('File deletion failed (' + remote_path + '): ' + str(e))

        # Upload files that are in Zotero but not on device.
        for rel in sorted(zotero_rel_paths):
            remote_path = self.remote_base + '/' + rel
            local_info = zotero_files[rel]

            if rel not in device_rel_paths:
                if self.simulate:
                    self.log_signal.emit('Simulate: Would upload file: ' + remote_path)
                else:
                    try:
                        self.dp.upload_file(local_info['abs_path'], remote_path)
                        self.log_signal.emit('Uploaded: ' + remote_path)
                    except Exception as e:
                        self.log_signal.emit('File upload failed (' + remote_path + '): ' + str(e))
            else:
                pass

        self.log_signal.emit('Zotero sync ' + ('simulation' if self.simulate else 'complete') + '.')
        self.finished_signal.emit({})
