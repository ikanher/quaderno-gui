#!/usr/bin/env python3
"""
Entry point for the QuadernoGUI application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from quaderno_gui.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
