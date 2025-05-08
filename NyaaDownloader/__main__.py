# ------------------------------IMPORTS------------------------------


from . import gui

from PyQt6 import QtWidgets
from PyQt6.QtCore import QStandardPaths

import sys
import configparser
import os


# ------------------------------MAIN FUNCTION------------------------------


def main() -> None:

    message = """<p>Welcome to my batch downloader for Nyaa.si!<br><br><br>
    

    Make sure to write the title in Japanese.<br>
    (e.g, instead of writing My Hero Academia, write Boku no Hero Academia).<br>
    Uploaders often use the Japanese title, you won't find your anime otherwise.<br>
    You may refer to MyAnimeList.net so you can get both translations.<br>
    Don't worry, there is no case sensitivity.<br><br>

    The uploader Erai-Raws specifies the season number for the title<br>
    (e.g Boku no Hero Academia 5th Season).<br><br>

    SubsPlease increases the episode number without using the season number<br>
    (e.g Boku no Hero Academia - 103).<br><br>

    Erai-Raws would be better for downloading one season,<br>
    SubsPlease might be better for downloading many seasons at once.<br><br>

    This program isn't made for downloading huge and old things Dragon Ball Z.<br>
    Indeed, there are already multiple torrents that contains every single episodes.<br>
    However, you can still download the latest episodes of things like One Piece.<br>
    Only depends if the uploaders uploaded them episode by episode or not.<br><br>

    If you find any bug, please let me know on my GitHub:<br>
    <a href="https://github.com/marcpinet/nyaadownloader">https://github.com/marcpinet/nyaadownloader</a>.</p>"""

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("NyaaDownloader")
    app.setDesktopFileName("NyaaDownloader")
    MainWindow = QtWidgets.QMainWindow()
    ui = gui.Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    config_filename = "config.ini"
    config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    config_path = os.path.join(config_dir, config_filename)

    config = configparser.ConfigParser()
    config.read(config_path)

    if not config.has_option("Settings", "ShowPopup") or config.getboolean("Settings", "ShowPopup"):
        gui.Ui_MainWindow.show_info_popup(MainWindow, message, never_show_again=True)

    sys.exit(app.exec())


# ------------------------------MAIN CALL------------------------------


if __name__ == "__main__":
    main()
