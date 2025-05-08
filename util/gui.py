# ------------------------------IMPORTS------------------------------


from . import nyaa

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog, QInputDialog, QLineEdit
from PyQt5.QtCore import Qt, QThread, QStandardPaths, pyqtSignal
from shutil import move

import platform
import configparser
import textwrap
import os
import webbrowser as wb
import urllib


# ------------------------------GLOBAL VARIABLES------------------------------


unhandled_characters = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
ICON_PATH = os.path.join("ico", "nyaa.ico")


# ------------------------------CLASSES AND METHODS------------------------------


def update_config(key: str, value: str) -> None:
    """Update the config.ini file
    Args:
        key (str): Key to update
        value (str): Value to set for the key
    """
    config_filename = "config.ini"
    config_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, config_filename)

    config = configparser.ConfigParser()
    config.read(config_path)

    if not config.has_section("Settings"):
        config.add_section("Settings")

    config.set("Settings", key, value)

    with open(config_path, "w") as configfile:
        config.write(configfile)
            
# Generated with Qt Designer (first time using this one)
class Ui_MainWindow(QDialog):
    def setupUi(self, MainWindow: QtWidgets.QMainWindow) -> None:
        """Build skeleton of the GUI

        Args:
            MainWindow (QMainWindow): Main window of the GUI
        """

        MainWindow.setObjectName("NyaaDownloader")
        MainWindow.setWindowIcon(QtGui.QIcon(ICON_PATH))
        MainWindow.resize(800, 341)
        MainWindow.setMinimumSize(QtCore.QSize(800, 341))
        MainWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        main_layout = QtWidgets.QHBoxLayout(self.centralwidget)

        left_layout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        left_layout.addWidget(self.label)

        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        left_layout.addWidget(self.lineEdit)

        self.label_2 = QtWidgets.QLabel(self.centralwidget)  
        self.label_2.setObjectName("label_2")
        left_layout.addWidget(self.label_2)

        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setObjectName("lineEdit_2")
        left_layout.addWidget(self.lineEdit_2)

        mid_layout = QtWidgets.QHBoxLayout()
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3") 
        mid_layout.addWidget(self.label_3)

        self.spinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(10000) 
        self.spinBox.setObjectName("spinBox")
        mid_layout.addWidget(self.spinBox)

        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        mid_layout.addWidget(self.label_4)  

        self.spinBox_2 = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_2.setMinimum(1)
        self.spinBox_2.setMaximum(10000)
        self.spinBox_2.setObjectName("spinBox_2")
        mid_layout.addWidget(self.spinBox_2)

        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setObjectName("checkBox")  
        mid_layout.addWidget(self.checkBox)

        left_layout.addLayout(mid_layout)

        bottom_left_layout = QtWidgets.QVBoxLayout()

        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")
        bottom_left_layout.addWidget(self.label_5)

        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItems(["2160p", "1080p", "720p", "480p"])
        self.comboBox.setCurrentIndex(1)  
        bottom_left_layout.addWidget(self.comboBox)
        
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(30, 310, 361, 16))
        self.label_6.setObjectName("label_6")
        bottom_left_layout.addWidget(self.label_6)

        self.radioButton = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton") 
        bottom_left_layout.addWidget(self.radioButton)

        self.radioButton_2 = QtWidgets.QRadioButton(self.centralwidget)  
        self.radioButton_2.setObjectName("radioButton_2")
        bottom_left_layout.addWidget(self.radioButton_2)

        btn_layout = QtWidgets.QHBoxLayout()
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setMinimumSize(QtCore.QSize(70, 30))
        self.pushButton.setObjectName("pushButton")
        btn_layout.addWidget(self.pushButton)

        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setMinimumSize(QtCore.QSize(70, 30)) 
        self.pushButton_4.setVisible(False)
        self.pushButton_4.setObjectName("pushButton_4")
        btn_layout.addWidget(self.pushButton_4)  

        bottom_left_layout.addLayout(btn_layout)

        self.checkBox_2 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_2.setObjectName("checkBox_2")
        bottom_left_layout.addWidget(self.checkBox_2)

        left_layout.addLayout(bottom_left_layout)
        main_layout.addLayout(left_layout)

        right_layout = QtWidgets.QVBoxLayout() 
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setObjectName("label_7")
        right_layout.addWidget(self.label_7)

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)  
        self.textBrowser.setObjectName("textBrowser")
        right_layout.addWidget(self.textBrowser)

        btn_layout_2 = QtWidgets.QHBoxLayout()
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setMinimumSize(QtCore.QSize(100, 30))
        self.pushButton_2.setObjectName("pushButton_2")
        btn_layout_2.addWidget(self.pushButton_2)

        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setMinimumSize(QtCore.QSize(100, 30))
        self.pushButton_3.setObjectName("pushButton_3")  
        btn_layout_2.addWidget(self.pushButton_3)

        right_layout.addLayout(btn_layout_2)
        main_layout.addLayout(right_layout)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")  
        self.menuTranslator = QtWidgets.QMenu(self.menubar)
        self.menuTranslator.setObjectName("menuTranslator")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.actionGet_translation_of_an_anime_title = QtWidgets.QAction(MainWindow)
        self.actionGet_translation_of_an_anime_title.setObjectName("actionGet_translation_of_an_anime_title")
        self.menuTranslator.addAction(self.actionGet_translation_of_an_anime_title)
        self.menubar.addAction(self.menuTranslator.menuAction())  

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # We will need to use it later for saving file as .txt
        global mainWindow  
        mainWindow = MainWindow

    def retranslateUi(self, MainWindow) -> None:
        """Setting properties and text of widgets

        Args:
            MainWindow (QMainWindow): Main window of the GUI
        """
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "NyaaDownloader"))
        self.label.setText(_translate("MainWindow", "Uploaders:"))
        self.lineEdit.setPlaceholderText(
            _translate(
                "MainWindow", "Empty=all, else use semicolon like Erai-raws;SubsPlease"
            )
        )
        self.label_2.setText(_translate("MainWindow", "Anime Title:"))
        self.lineEdit_2.setPlaceholderText(
            _translate("MainWindow", "Input your anime title here")
        )
        self.label_3.setText(_translate("MainWindow", "Starting from:"))
        self.label_4.setText(_translate("MainWindow", "Until episode:"))
        self.label_5.setText(_translate("MainWindow", "Quality:"))
        self.comboBox.setItemText(0, _translate("MainWindow", "2160p"))
        self.comboBox.setItemText(1, _translate("MainWindow", "1080p"))
        self.comboBox.setItemText(2, _translate("MainWindow", "720p"))
        self.comboBox.setItemText(3, _translate("MainWindow", "480p"))
        self.comboBox.setCurrentIndex(1)
        self.label_6.setText(
            _translate(
                "MainWindow",
                "Download .torrent files or open magnet links directly in your torrent client?",
            )
        )
        self.radioButton.setText(_translate("MainWindow", "Torrent"))
        self.radioButton_2.setText(_translate("MainWindow", "Magnet"))
        self.checkBox.setText(_translate("MainWindow", "Until last released one"))
        self.pushButton.setText(_translate("MainWindow", "Check"))
        self.label_7.setText(_translate("MainWindow", "Logs:"))
        self.pushButton_2.setText(_translate("MainWindow", "Open folder"))
        self.pushButton_3.setText(_translate("MainWindow", "Save logs as .txt"))
        self.pushButton_4.setText(_translate("MainWindow", "Stop"))
        self.checkBox_2.setText(_translate("MainWindow", "Allow untrusted"))
        self.menuTranslator.setTitle(_translate("MainWindow", "Translator"))
        self.actionGet_translation_of_an_anime_title.setText(
            _translate("MainWindow", "Get translation of an anime title")
        )

        # Linking widgets and methods (callbacks)
        self.checkBox.clicked.connect(
            lambda: self.check_whole_show(self.checkBox.isChecked())
        )
        self.pushButton.clicked.connect(self.is_everything_good)
        self.pushButton_2.clicked.connect(self.open_download_folder)
        self.pushButton_3.clicked.connect(self.save_logs)
        self.pushButton_4.clicked.connect(self.cancel_process)
        self.actionGet_translation_of_an_anime_title.triggered.connect(
            self.ask_anime_to_translate
        )

        # Disabling buttons that doesn't have to be pressed atm
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setVisible(False)

    def ask_anime_to_translate(self) -> None:
        """Asking anime title to translate by opening a link to MyAnimeList"""
        text, okPressed = QInputDialog.getText(
            self, "Search in MyAnimeList", "Anime title to find in MyAnimeList:", QLineEdit.Normal
        )
        if okPressed and text != "":
            text = urllib.quote(text)
            wb.open(f"https://myanimelist.net/anime.php?q={text}&cat=anime")

    def cancel_process(self) -> None:
        """Cancel the check process by using a specific variable"""

        global unexpected_end
        unexpected_end = True

    def check_whole_show(self, is_checked) -> None:
        """Enable/disable widgets when checkBox is checked/unchecked

        Args:
            is_checked (bool): Is the checkBox checked/unchecked?
        """

        if is_checked:
            self.spinBox_2.setEnabled(False)
        else:
            self.spinBox_2.setEnabled(True)

    def show_error_popup(self, error_message: Exception) -> None:
        """Show an error popup message

        Args:
            error_message (str): Message to display with the popup
        """

        error_message = "\n".join(textwrap.wrap(str(error_message), width=100))
        msg = QMessageBox()
        msg.resize(500, 200)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_message)
        msg.setWindowTitle("NyaaDownloader")
        msg.setWindowIcon(QtGui.QIcon(ICON_PATH))
        msg.exec_()

    def show_info_popup(self, info_message: str, never_show_again: bool = True) -> None:
        """Show an info popup message
        Args:
            info_message (str): Message to display with the popup
        """
        msg = QMessageBox()
        msg.setTextFormat(Qt.RichText)
        msg.resize(500, 200)
        msg.setIcon(QMessageBox.Information)
        msg.setText(info_message)
        msg.setWindowTitle("NyaaDownloader")
        msg.setWindowIcon(QtGui.QIcon(ICON_PATH))

        if never_show_again:
            checkbox = QtWidgets.QCheckBox("Never show this popup again")
            msg.setCheckBox(checkbox)

        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        if msg.exec_() == QtWidgets.QMessageBox.Ok and checkbox.isChecked():
            update_config("ShowPopup", "False")

    def set_widget_while_check(self) -> None:
        """Disable all widgets in the GUI."""

        self.menubar.setEnabled(False)
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.spinBox.setEnabled(False)
        self.spinBox_2.setEnabled(False)
        self.checkBox.setEnabled(False)
        self.radioButton.setEnabled(False)
        self.radioButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)

        self.pushButton_4.setVisible(True)

    def set_widget_after_check(self) -> None:
        """Enable all widgets in the GUI (and reset checkbox)."""

        self.menubar.setEnabled(True)
        self.pushButton.setEnabled(True)
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.comboBox.setEnabled(True)
        self.spinBox.setEnabled(True)
        self.spinBox_2.setEnabled(True)
        self.checkBox.setEnabled(True)
        self.radioButton.setEnabled(True)
        self.radioButton_2.setEnabled(True)

        self.checkBox.setChecked(False)  # Reseting checkbox
        self.pushButton_2.setEnabled(True)  # Enabling Open Folder button
        self.pushButton_4.setVisible(False)  # Disabling Stop button
        self.pushButton_3.setEnabled(True)  # Enabling Save logs button

    @staticmethod
    def get_download_folder(anime_name: str) -> str:
        anime_name = " ".join(anime_name.strip().split())

        for s in unhandled_characters:
            anime_name = anime_name.replace(s, "")

        downloads = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        return os.path.join(downloads, "DownloadedTorrents", anime_name)

    @classmethod
    def generate_download_folder(cls, anime_name: str) -> None:
        """Generates a folder name for the .torrents download.

        Args:
            anime_name (str): Name of the anime.
        """
        try:
            os.makedirs(cls.get_download_folder(anime_name), exist_ok=True)

        except FileExistsError:
            pass

    def open_download_folder(self) -> None:
        """Open the DownloadedTorrents folder"""
        try:
            global anime_name
            path = None
            if anime_name is not None and len(anime_name) > 0:
                path = self.get_download_folder(anime_name)
            if path is None or not os.path.exists(path):
                path = self.get_download_folder("")
            if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)):
                self.show_error_popup("Failed opening: " + path)

        except Exception as e:
            self.show_error_popup("DownloadedTorrents folder not found because: " + str(e))

    def notify(self, message: str) -> None:
        """Generate a notifcation with a message

        Args:
            message (str): Message to be displayed
        """

        system = platform.system()
        if system == "Linux":
            import gi
            gi.require_version("Notify", "0.7")
            from gi.repository import Notify
            Notify.init("NyaaDownloader")
            Notify.Notification.new("NyaaDownloader", message).show()
        elif system == "Windows":
            from winotify import Notification, audio
            toast = Notification(
                app_id="NyaaDownloader",
                title="NyaaDownloader",
                msg=message,
            )
            toast.set_audio(audio.Default, loop=False)
            toast.build().show()
        elif system == "Darwin":
            from Foundation import NSUserNotification, NSUserNotificationCenter
            notification = NSUserNotification.alloc().init()
            notification.setTitle("NyaaDownloader")
            notification.setInformativeText(message)
            NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification(notification)


    def save_logs(self) -> None:
        """Saves the logs to a .txt file."""

        name = QtWidgets.QFileDialog.getSaveFileName(
            mainWindow, "Save File", ".", ".txt"
        )[0]
        try:
            # If cancel is clicked, do nothing
            if name != "":
                with open(f"{name}.txt", "w") as f:
                    f.write(self.textBrowser.toPlainText())
        except Exception:
            pass

    def is_everything_good(self) -> None:
        """Check if every input values are correct and if yes, will call the start_checking method"""

        everything_good = True
        self.pushButton.setEnabled(False)

        if self.lineEdit_2.text() == "":
            self.show_error_popup("You need to input your anime title.")
            everything_good = False

        elif len(self.lineEdit_2.text()) <= 2:
            self.show_error_popup(
                "Your anime title needs to be more than 2 characters long."
            )
            everything_good = False

        try:
            if not nyaa.is_in_database(self.lineEdit_2.text()):
                self.show_error_popup("This anime is not in Nyaa database.")
                everything_good = False

        except Exception as e:
            self.show_error_popup(e)
            everything_good = False

        # Setting proper values
        if everything_good:

            global uploaders, anime_name, start_end, quality, option, untrusted_option, path

            uploaders = [
                u.strip() for u in self.lineEdit.text().strip().split(";") if u != ""
            ]
            
            if not uploaders:
                uploaders = [""]
            
            anime_name = " ".join(self.lineEdit_2.text().strip().split())
            start_end = (
                (int(self.spinBox.text()), 10000)
                if self.checkBox.isChecked()
                else (int(self.spinBox.text()), int(self.spinBox_2.text()))
            )
            quality = int(self.comboBox.currentText()[:-1])
            option = 1 if self.radioButton.isChecked() else 2
            untrusted_option = True if self.radioButton_2.isChecked() else False
            
            path = self.get_download_folder(anime_name)
            self.start_checking()

        else:
            self.pushButton.setEnabled(True)

    def start_checking(self) -> None:
        """Will setup the GUI and call the thread to handle the download/transfer of torrent."""

        self.set_widget_while_check()

        # I had to put that thread because if I didn't, the app would freeze when it tried to download the torrents (see below)
        self.worker = WorkerThread()
        self.worker.start()

        # Connecting events to the worker thread
        self.worker.finished.connect(lambda: self.worker_finished())
        self.worker.update_logs.connect(self.append_to_logs)
        self.worker.error_popup.connect(self.show_error_popup)

    def worker_finished(self) -> None:
        """When the thread has finished processing, enable all widgets again and notify the user

        Args:
            anime_name (str): [description]
            verbal_base (str): [description]
        """

        self.set_widget_after_check()
        self.notify(f"The anime {anime_name} has been fully checked!")

    def append_to_logs(self, text: str) -> None:
        """Appends a text to the logs widget

        Args:
            text (str): Text to append to logs
        """

        self.textBrowser.append(text)


class WorkerThread(QThread):
    """This class was necessary because I PyQt doesn't well supports loop (see: https://stackoverflow.com/questions/50851966/pyqt5-window-crashes-when-socket-is-continue-running-in-background#comment88740648_50864417)"""

    update_logs = pyqtSignal(str)
    error_popup = pyqtSignal(str)

    def run(self) -> None:
        """The "almost main" function of that program. Will download/transfer every found torrent. Will also handle logs update, etc."""

        episode = start_end[0]
        fails_in_a_row = 0

        # Call it as global (cuz the stop button uses it) and reset it to False
        global unexpected_end
        unexpected_end = False

        # Will break if "END" found in title (Erai-raws)
        while not unexpected_end and episode <= start_end[1] and fails_in_a_row < 10:
            for uploader in uploaders:
                torrent = nyaa.find_torrent(uploader, anime_name, episode, quality, untrusted_option)

                if torrent:
                    fails_in_a_row = 0

                    if option == 1:

                        if nyaa.download(torrent):
                            Ui_MainWindow.generate_download_folder(anime_name)
                            move(
                                f"{torrent.name}.torrent",
                                os.path.join(path, f"{torrent.name}.torrent"),
                            )

                        else:
                            self.error_popup.emit(f"Failed downloading: {torrent.name}")
                            unexpected_end = True
                            break

                    # I prefer this rather than a simple else because it's cleaner
                    elif option == 2 and not nyaa.transfer(torrent):
                        self.error_popup.emit(
                            "No bittorrent client or web browser (that supports magnet links) found."
                        )
                        unexpected_end = True
                        break

                    self.update_logs.emit(f"Found: {anime_name} - Episode {episode}")

                    # Erai-raws add "END" in the torrent name when an anime has finished airing
                    if uploader == "Erai-raws" and torrent.name.find(" END [") != -1:
                        self.update_logs.emit(
                            f"Note: {anime_name} has no more than {episode} episodes"
                        )
                        unexpected_end = True

                    # Skip other uploaders, don't need to check for them since torrent was found
                    break

                else:
                    if uploader == uploaders[-1]:
                        self.update_logs.emit(
                            f"Failed finding: {anime_name} - Episode {episode}"
                        )

                        fails_in_a_row += 1

            episode += 1

        if fails_in_a_row >= 10:
            self.update_logs.emit(
                f"Note: {anime_name} seems to only have {episode - 11} episodes"
            )
