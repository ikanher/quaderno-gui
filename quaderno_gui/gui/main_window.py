"""
Main window for QuadernoGUI.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QMainWindow, QSplitter, QStackedWidget

from quaderno_gui.gui.connect_page import ConnectPage
from quaderno_gui.gui.files_page import FilesPage
from quaderno_gui.gui.folders_page import FoldersPage
from quaderno_gui.gui.zotero_sync_page import ZoteroSyncPage


class MainWindow(QMainWindow):
    """
    Main window that hosts the sidebar and different pages.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuadernoGUI")
        self.resize(1100, 700)
        self.digital_paper = None

        splitter = QSplitter(Qt.Horizontal)
        self.sidebar = QListWidget()
        self.sidebar.setSelectionMode(QListWidget.SingleSelection)
        self.sidebar.addItem("Connect")
        self.sidebar.addItem("Files")
        self.sidebar.addItem("Folders")
        self.sidebar.addItem("Zotero Sync")
        self.sidebar.currentRowChanged.connect(self.change_page)
        splitter.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.connect_page = ConnectPage(self)
        self.files_page = FilesPage()
        self.folders_page = FoldersPage()
        self.zotero_sync_page = ZoteroSyncPage()
        self.pages.addWidget(self.connect_page)
        self.pages.addWidget(self.files_page)
        self.pages.addWidget(self.folders_page)
        self.pages.addWidget(self.zotero_sync_page)
        splitter.addWidget(self.pages)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def change_page(self, index):
        """
        Change the displayed page based on sidebar selection.
        """
        self.pages.setCurrentIndex(index)

    def set_digital_paper(self, dp):
        """
        Update all pages with the connected DigitalPaper instance.
        """
        self.digital_paper = dp
        self.connect_page.set_connected(dp)
        self.files_page.set_digital_paper(dp)
        self.folders_page.set_digital_paper(dp)
        self.zotero_sync_page.set_digital_paper(dp)
