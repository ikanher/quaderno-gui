"""
Device connection functionality for QuadernoGUI.
"""

import os
from PyQt5.QtCore import QThread, pyqtSignal
from dptrp1.dptrp1 import DigitalPaper, find_auth_files, get_default_auth_files

class ConnectionWorker(QThread):
    """
    Worker thread to handle connecting and authenticating with a DigitalPaper device.
    """
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(object)

    def __init__(self, address, serial, parent=None):
        super().__init__(parent)

        self.address = address
        self.serial = serial

    def run(self):
        try:
            self.log_signal.emit(f'Connecting to device at {self.address}...')

            dp = DigitalPaper(addr=self.address, id=self.serial, quiet=True)

            found_client, found_key = find_auth_files()

            if os.path.exists(found_client) and os.path.exists(found_key):
                with open(found_client) as fh:
                    client_id = fh.readline().strip()
                with open(found_key, 'rb') as fh:
                    key = fh.read()
                try:
                    dp.authenticate(client_id, key)
                    self.log_signal.emit('Authenticated successfully.')
                except Exception as e:
                    self.log_signal.emit('Authentication failed: ' + str(e))
            else:
                self.log_signal.emit('Auth files not found. Please register first.')

            info = dp.get_info()
            serial_number = info.get('serial_number', 'unknown')
            self.log_signal.emit('Connected (internal serial: ' + serial_number + ').')
            self.finished_signal.emit(dp)
        except Exception as e:
            self.log_signal.emit('Connection error: ' + str(e))
            self.finished_signal.emit(None)
