"""
Sync functionality for QuadernoGUI.
"""

from pathlib import PurePosixPath

from PyQt5.QtCore import QThread, pyqtSignal

from quaderno_gui.core.zotero import build_zotero_file_mapping, build_zotero_folder_set


def _normalize_relative_path(full_path, remote_base):
    """Return a normalized relative path (POSIX style) or None if outside the base."""
    normalized_full = full_path.replace('\\', '/')
    normalized_base = remote_base.replace('\\', '/')

    full_posix = PurePosixPath(normalized_full)
    base_posix = PurePosixPath(normalized_base)

    try:
        relative = full_posix.relative_to(base_posix)
    except ValueError:
        return None

    rel_posix = relative.as_posix()
    return '' if rel_posix == '.' else rel_posix


class SyncWorker(QThread):
    """
    Worker thread to synchronize Zotero files with the DigitalPaper device.
    """
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(dict)

    def __init__(self, dp, simulate, remote_base, storage_path=None, db_path=None, parent=None):
        super().__init__(parent)

        self.dp = dp
        self.simulate = simulate
        self.remote_base = remote_base
        self.storage_path = storage_path
        self.db_path = db_path

    def run(self):
        self.log_signal.emit('Starting Zotero sync...' + (' (Simulation)' if self.simulate else ''))

        try:
            zotero_files = build_zotero_file_mapping(self.storage_path, self.db_path)
            zotero_folders = build_zotero_folder_set(self.db_path)
        except FileNotFoundError as exc:
            self.log_signal.emit(str(exc))
            self.log_signal.emit('Zotero sync aborted.')
            self.finished_signal.emit({})
            return
        except Exception as exc:
            self.log_signal.emit('Unexpected error while reading Zotero data: ' + str(exc))
            self.log_signal.emit('Zotero sync aborted.')
            self.finished_signal.emit({})
            return

        # List what's on the device within remote_base.
        device_items = self.dp.list_all()
        device_files = {}
        device_folders = set()

        for entry in device_items:
            path = entry.get('entry_path', '')
            entry_type = entry.get('entry_type')

            relative_path = _normalize_relative_path(path, self.remote_base)

            if relative_path is None:
                continue

            if entry_type == 'document':
                if relative_path:
                    device_files[relative_path] = 0
            elif entry_type == 'folder':
                if relative_path:
                    device_folders.add(relative_path)

        # Ensure new Zotero folders exist on the device.
        for folder in sorted(zotero_folders):
            normalized_folder = folder.replace('\\', '/')
            target_path = self.remote_base if not normalized_folder else self.remote_base + '/' + normalized_folder

            if normalized_folder not in device_folders:
                if self.simulate:
                    self.log_signal.emit('Simulate: Would create folder: ' + target_path)
                else:
                    try:
                        self.dp.new_folder(target_path)
                        self.log_signal.emit('Created folder: ' + target_path)
                    except Exception as e:
                        self.log_signal.emit('Folder creation failed (' + target_path + '): ' + str(e))

        # Remove folders that no longer exist in Zotero.
        for folder in sorted(device_folders, reverse=True):
            if folder not in zotero_folders and folder != '':
                remote_folder = self.remote_base + '/' + folder.replace('\\', '/')

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
