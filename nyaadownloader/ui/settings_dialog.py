from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from nyaadownloader.core.models import Category
from nyaadownloader.core.nyaa import DEFAULT_BASE_URL
from nyaadownloader.core.settings import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self._settings = settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self.folder = QLineEdit(settings.download_dir)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row = QHBoxLayout()
        row.addWidget(self.folder, 1)
        row.addWidget(browse)
        form.addRow("Save .torrent files to", row)

        self.subfolder = QCheckBox("Create one sub-folder per anime")
        self.subfolder.setChecked(settings.subfolder_per_anime)
        form.addRow("", self.subfolder)
        self.open_after = QCheckBox("Open downloaded .torrent files with my torrent client")
        self.open_after.setChecked(settings.open_torrents_after_download)
        form.addRow("", self.open_after)

        self.category = QComboBox()
        for category in Category:
            self.category.addItem(category.label, category.value)
        self.category.setCurrentIndex(max(0, self.category.findData(settings.category)))
        form.addRow("Nyaa category", self.category)

        self.base_url = QLineEdit(settings.base_url)
        self.base_url.setPlaceholderText(DEFAULT_BASE_URL)
        self.base_url.setToolTip("Change this if nyaa.si is blocked by your provider and you use a mirror.")
        form.addRow("Nyaa address", self.base_url)

        self.theme = QComboBox()
        for label, value in (("Follow system", "system"), ("Dark", "dark"), ("Light", "light")):
            self.theme.addItem(label, value)
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.theme)))
        form.addRow("Theme", self.theme)

        self.notifications = QCheckBox("Notify me when a long search or download finishes")
        self.notifications.setChecked(settings.notifications)
        form.addRow("", self.notifications)
        layout.addLayout(form)

        hint = QLabel("Search filters (uploaders, quality, episodes…) are remembered automatically.",
                      objectName="muted", wordWrap=True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Save .torrent files to", self.folder.text())
        if folder:
            self.folder.setText(folder)

    def apply(self) -> None:
        s = self._settings
        s.download_dir = self.folder.text().strip() or Settings().download_dir
        s.subfolder_per_anime = self.subfolder.isChecked()
        s.open_torrents_after_download = self.open_after.isChecked()
        s.category = self.category.currentData()
        url = self.base_url.text().strip().rstrip("/")
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        s.base_url = url or DEFAULT_BASE_URL
        s.theme = self.theme.currentData()
        s.notifications = self.notifications.isChecked()
