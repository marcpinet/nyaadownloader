# ------------------------------IMPORTS------------------------------


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from . import nyaa
from winotify import Notification, audio
from shutil import move

import textwrap
import os


# ------------------------------GLOBAL VARIABLES------------------------------


# So the thread can access them (didn't found a better way to do it, I'm still learning paralel programming)
# and because PyQt classes uses self keyword, I couldn't just use static methods so I just simply make those variables global
uploaders = []
anime_name= ''
start_end = ()
quality = -1
option = -1
path = ''
verbal_base = ''


# ------------------------------CLASSES AND METHODS------------------------------


# Generated with Qt Designer (first time using this one)
class Ui_MainWindow(QDialog):
    
    def setupUi(self, MainWindow):
        """Build skeleton of the GUI

        Args:
            MainWindow (QMainWindow): Main window of the GUI
        """
        MainWindow.setObjectName('NyaaDownloader')
        MainWindow.setWindowIcon(QtGui.QIcon('ico/nyaa.ico'))
        MainWindow.resize(800, 440)
        MainWindow.setMinimumSize(QtCore.QSize(800, 440))
        MainWindow.setMaximumSize(QtCore.QSize(800, 440))
        MainWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName('centralwidget')
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 30, 51, 16))
        self.label.setObjectName('label')
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(30, 50, 291, 20))
        self.lineEdit.setObjectName('lineEdit')
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(30, 100, 51, 16))
        self.label_2.setObjectName('label_2')
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setGeometry(QtCore.QRect(30, 120, 291, 20))
        self.lineEdit_2.setObjectName('lineEdit_2')
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(30, 170, 81, 16))
        self.label_3.setObjectName('label_3')
        self.spinBox = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox.setGeometry(QtCore.QRect(30, 190, 71, 22))
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(10000)
        self.spinBox.setObjectName('spinBox')
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(150, 170, 71, 16))
        self.label_4.setObjectName('label_4')
        self.spinBox_2 = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_2.setGeometry(QtCore.QRect(150, 190, 71, 22))
        self.spinBox_2.setMinimum(1)
        self.spinBox_2.setMaximum(10000)
        self.spinBox_2.setObjectName('spinBox_2')
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(30, 240, 41, 16))
        self.label_5.setObjectName('label_5')
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(30, 260, 69, 22))
        self.comboBox.setObjectName('comboBox')
        self.comboBox.addItem('')
        self.comboBox.addItem('')
        self.comboBox.addItem('')
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(30, 310, 361, 16))
        self.label_6.setObjectName('label_6')
        self.radioButton = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButton.setGeometry(QtCore.QRect(30, 330, 82, 17))
        self.radioButton.setChecked(True)
        self.radioButton.setAutoExclusive(True)
        self.radioButton.setObjectName('radioButton')
        self.buttonGroup = QtWidgets.QButtonGroup(MainWindow)
        self.buttonGroup.setObjectName('buttonGroup')
        self.buttonGroup.addButton(self.radioButton)
        self.radioButton_2 = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButton_2.setGeometry(QtCore.QRect(130, 330, 82, 17))
        self.radioButton_2.setObjectName('radioButton_2')
        self.buttonGroup.addButton(self.radioButton_2)
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setGeometry(QtCore.QRect(270, 190, 181, 17))
        self.checkBox.setObjectName('checkBox')
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(30, 370, 75, 23))
        self.pushButton.setObjectName('pushButton')
        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(460, 50, 311, 291))
        self.textBrowser.setObjectName("textBrowser")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(460, 30, 31, 16))
        self.label_7.setObjectName('label_7')
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(460, 370, 75, 23))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(550, 370, 91, 23))
        self.pushButton_3.setObjectName("pushButton_3")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        global mainWindow
        mainWindow = MainWindow


    def retranslateUi(self, MainWindow):
        """Setting properties and text of widgets

        Args:
            MainWindow (QMainWindow): Main window of the GUI
        """
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate('MainWindow', 'NyaaDownloader'))
        self.label.setText(_translate('MainWindow', 'Uploaders'))
        self.lineEdit.setText(_translate('MainWindow', 'Erai-raws;SubsPlease'))
        self.lineEdit.setPlaceholderText(_translate('MainWindow', 'Separate them with semicolon (e.g Erai-raws;SubsPlease)'))
        self.label_2.setText(_translate('MainWindow', 'Anime Title'))
        self.lineEdit_2.setPlaceholderText(_translate('MainWindow', 'Input your anime title here'))
        self.label_3.setText(_translate('MainWindow', 'Starting from...'))
        self.label_4.setText(_translate('MainWindow', 'Until episode...'))
        self.label_5.setText(_translate('MainWindow', 'Quality'))
        self.comboBox.setItemText(0, _translate('MainWindow', '1080p'))
        self.comboBox.setItemText(1, _translate('MainWindow', '720p'))
        self.comboBox.setItemText(2, _translate('MainWindow', '480p'))
        self.label_6.setText(_translate('MainWindow', 'Download .torrent files or open magnet links directly in your torrent client?'))
        self.radioButton.setText(_translate('MainWindow', 'Torrent'))
        self.radioButton_2.setText(_translate('MainWindow', 'Magnet'))
        self.checkBox.setText(_translate('MainWindow', 'Until last released one'))
        self.pushButton.setText(_translate('MainWindow', 'Check'))
        self.label_7.setText(_translate('MainWindow', 'Logs'))
        self.pushButton_2.setText(_translate("MainWindow", "Open folder"))
        self.pushButton_3.setText(_translate("MainWindow", "Save logs as .txt"))
        
        # Linking widgets and methods (callbacks)
        self.checkBox.clicked.connect(lambda: self.check_whole_show(self.checkBox.isChecked()))
        self.pushButton.clicked.connect(self.is_everything_good)
        self.pushButton_2.clicked.connect(lambda: os.startfile("DownloadedTorrents"))
        self.pushButton_3.clicked.connect(self.save_logs)
        
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        
        
    def check_whole_show(self, is_checked):
        """Enable/disable widgets when checkBox is checked/unchecked

        Args:
            is_checked (bool): Is the checkBox checked/unchecked?
        """
        if is_checked:
            self.spinBox_2.setEnabled(False)
        else:
            self.spinBox_2.setEnabled(True)
    
    
    def show_error_popup(self, error_message: str):
        """Show an error popup message

        Args:
            error_message (str): Message to display with the popup
        """
        error_message = '\n'.join(textwrap.wrap(error_message, width=100))
        msg = QMessageBox()
        msg.resize(500, 200)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_message)
        msg.setWindowTitle('NyaaDownloader')
        msg.exec_()
       
        
    def show_info_popup(self, info_message: str):
        """Show an info popup message

        Args:
            info_message (str): Message to display with the popup
        """
        msg = QMessageBox()
        msg.setTextFormat(Qt.RichText)
        msg.resize(500, 200)
        msg.setIcon(QMessageBox.Information)
        msg.setText(info_message)
        msg.setWindowTitle('NyaaDownloader')
        msg.exec_()
        
        
    def disable_all_widgets(self):
        """Disable all widgets in the GUI."""
        self.lineEdit.setEnabled(False)
        self.lineEdit_2.setEnabled(False)
        self.comboBox.setEnabled(False)
        self.spinBox.setEnabled(False)
        self.spinBox_2.setEnabled(False)
        self.checkBox.setEnabled(False)
        self.radioButton.setEnabled(False)
        self.radioButton_2.setEnabled(False)
        
    def enable_all_widgets(self):
        """Enable all widgets in the GUI (and reset checkbox)."""
        self.lineEdit.setEnabled(True)
        self.lineEdit_2.setEnabled(True)
        self.comboBox.setEnabled(True)
        self.spinBox.setEnabled(True)
        self.spinBox_2.setEnabled(True)
        self.checkBox.setEnabled(True)
        self.radioButton.setEnabled(True)
        self.radioButton_2.setEnabled(True)
        
        self.checkBox.setChecked(False)
        
    
    def generate_download_folder(self, anime_name: str):
        """Generates a folder name for the .torrents download.

        Args:
            anime_name (str): Name of the anime.
        
        Returns:
            path (str): Path of the folder.
        """
        for s in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            anime_name = anime_name.replace(s, ' ')
        
        try:
            os.makedirs(f'DownloadedTorrents\\{anime_name}')
        except FileExistsError:
            pass
        
        return f'DownloadedTorrents\\{anime_name}'
    

    def notify(self, message: str):
        """Generate a windows 10 notifcation with a message

        Args:
            message (str): Message to be displayed
        """
        toast = Notification(
        app_id='NyaaDownloader',
        title='NyaaDownloader',
        msg=message,
        )
        toast.set_audio(audio.Default, loop=False)
        toast.build().show()
    
    
    def save_logs(self):
        """Saves the logs to a .txt file."""
        name = QtWidgets.QFileDialog.getSaveFileName(mainWindow, "Save File", '.', '.txt')[0]
        try:
            # If cancel is clicked, do nothing
            if name != '':
                with open(f'{name}.txt', 'w') as f:
                    f.write(self.textBrowser.toPlainText())
        except:
            pass


    def is_everything_good(self):
        """Check if every input values are correct and if yes, will call the start_checking method
        """
        everything_good = True
        
        if self.lineEdit.text() == '':
            self.show_error_popup('You need to input at least 1 uploader name.')
            everything_good = False
        
        if self.lineEdit_2.text() == '':
            self.show_error_popup('You need to input your anime title.')
            everything_good = False
        
        elif len(self.lineEdit_2.text()) <= 2:
            self.show_error_popup('Your anime title needs to be more than 2 characters long.')
            everything_good = False
        
        try:
            if not nyaa.is_in_database(self.lineEdit_2.text()):
                self.show_error_popup('This anime is not in Nyaa database.')
                everything_good = False
        except Exception as e:
            self.show_error_popup(e)
            everything_good = False
        
        # Setting proper values
        if everything_good:
            
            global uploaders
            global anime_name
            global start_end
            global quality
            global option
            global path
            global verbal_base
            
            uploaders = [u.strip() for u in self.lineEdit.text().strip().split(';') if u != '']
            anime_name = self.lineEdit_2.text()
            start_end = (int(self.spinBox.text()), 10000) if self.checkBox.isChecked() else (int(self.spinBox.text()), int(self.spinBox_2.text()))
            quality = int(self.comboBox.currentText()[:-1])
            option = 1 if self.radioButton.isChecked() else 2
            path = self.generate_download_folder(anime_name)
            verbal_base = 'Downloaded' if option == 1 else 'Transfered'

            
            self.start_checking()
    
    
    def start_checking(self):
        """Will setup the GUI and call the thread to handle the download/transfer of torrent.
        """
        
        self.disable_all_widgets()
        self.pushButton_2.setEnabled(True) if option == 1 else None  # A folder can now be created to store the .torrent files (only if the option is 1)
        
        # I had to put that thread because if I didn't, the app would freeze when it tried to download the torrents (see below)
        self.worker = WorkerThread()
        self.worker.start()
        
        # Connecting events to the worker thread
        self.worker.finished.connect(lambda: self.worker_finished(anime_name, verbal_base))
        self.worker.update_logs.connect(self.append_to_logs) # text paramter will be passed through signal
        self.worker.error_popup.connect(self.show_error_popup) # text paramter will be passed through signal
        self.worker.gen_folder.connect(self.generate_download_folder) # text paramter will be passed through signal
    
    
    def worker_finished(self, anime_name: str, verbal_base: str):
        """When the thread has finished processing, enable all widgets again and notify the user

        Args:
            anime_name (str): [description]
            verbal_base (str): [description]
        """
        self.notify(f"The anime {anime_name} has been fully {verbal_base.lower()}!")
        self.pushButton_3.setEnabled(True)
        self.enable_all_widgets()
        
        
    def append_to_logs(self, text: str):
        """Appends a text to the logs widget

        Args:
            text (str): Text to append to logs
        """
        self.textBrowser.append(text)
    

class WorkerThread(QThread):
    """This class was necessary because I PyQt doesn't well supports loop (see: https://stackoverflow.com/questions/50851966/pyqt5-window-crashes-when-socket-is-continue-running-in-background#comment88740648_50864417)
    """
    update_logs = pyqtSignal(str)
    error_popup = pyqtSignal(str)
    gen_folder = pyqtSignal(str)

    def run(self):
        """The "almost main" function of that program. Will download/transfer every found torrent. Will also handle logs update, etc.
        """
        
        fails_in_a_row = 0
        unexpected_end = False
        
        # Will break if "END" found in title (Erai-raws)
        for episode in range(start_end[0], start_end[1] + 1):
            
            if unexpected_end:
                break
            
            # Will break if found (so we don't check uselessly the same found torrent with different uploaders)
            for uploader in uploaders:
                
                torrent = nyaa.find_torrent(uploader, anime_name, episode, quality)
                
                if torrent is not None:
                    fails_in_a_row = 0
                        
                    if option == 1:
                        self.gen_folder.emit(anime_name)  # In case the user tries to delete it while the program is running
                        if nyaa.download(torrent):  # Will download the .torrent file along the condition check
                            move(f"{torrent['name']}.torrent", f"{path}\\{torrent['name']}.torrent")
                        else:
                            self.error_popup.emit('No Internet connection available')
                            unexpected_end = True
                            break
                    
                    elif option == 2:
                        if not nyaa.transfer(torrent):  # Will transfer the torrent link along the condition check
                            self.error_popup.emit('No bittorrent client or web browser (that supports magnet links) found.')
                            unexpected_end = True
                            break
                    
                    self.update_logs.emit(f'{verbal_base}: {anime_name} - Episode {episode}')
                    
                    # Erai-raws uses a special notation (they just add "END" in the torrent name when an anime has finished airing)
                    if uploader == 'Erai-raws' and torrent['name'].find(' END [') != -1:
                        self.update_logs.emit(f'Note: {anime_name} has no more than {episode} episodes')
                        unexpected_end = True
                    
                    # We skip the next uploaders because we don't need to check them since we found what we were looking for (lol)
                    break
                        
                else:
                    if uploader == uploaders[-1]:
                        self.update_logs.emit(f'Failed: {anime_name} - Episode {episode}')
                        
                        fails_in_a_row += 1
            
            if fails_in_a_row >= 10:
                self.update_logs.emit(f'Note: {anime_name} seems to only have {episode - 10} episodes')
                break