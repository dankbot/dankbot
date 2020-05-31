from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QWidget, \
    QLabel, QLineEdit, QGridLayout, QCheckBox, QMessageBox, QInputDialog
import sys
import os
import json
import re


class ProfileManager:
    P_ALLOWED_CHARS = re.compile("^[a-zA-Z0-9 ]+$")

    def __init__(self):
        self.profiles = []
        self.load()

    def load(self):
        for f in os.listdir("profiles/"):
            if not f.endswith(".json"):
                continue
            try:
                with open("profiles/" + f) as ff:
                    profile = json.load(ff)
                profile["name"] = f[:-5]
                self.profiles.append(profile)
            except Exception as e:
                print("Failed to open profile " + f)
                print(e)

    def save_profile(self, p):
        with open("profiles/" + p["name"] + ".json", "w") as f:
            json.dump(p, f)

    def check_new_profile_name(self, name):
        for p in self.profiles:
            if p["name"] == name:
                return False
        return ProfileManager.P_ALLOWED_CHARS.match(name) is not None

    def create_new_profile(self, name):
        p = {"name": name}
        self.profiles.append(p)
        return p


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DankBot")
        self.setWindowFlags(Qt.Dialog)

        self.profile_manager = ProfileManager()
        self.current_profile = None

        vbox = QVBoxLayout()

        hbox = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.on_current_profile_changed)
        hbox.addWidget(self.profile_combo, stretch=1)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.create_new_profile)
        add_btn.setFixedWidth(50)
        hbox.addWidget(add_btn)
        copy_btn = QPushButton("Copy")
        copy_btn.clicked.connect(self.clone_current_profile)
        copy_btn.setFixedWidth(50)
        hbox.addWidget(copy_btn)
        vbox.addLayout(hbox)

        self.setting_disable_widgets = []
        self.setting_save_functions = []
        self.grid = QGridLayout()
        self.grid_row = 0
        self._create_text_option("token", "Bot Token")
        vbox.addLayout(self.grid)

        show_advanced = QCheckBox("Show advanced")
        vbox.addWidget(show_advanced)
        show_advanced.stateChanged.connect(self.on_show_advanced_clicked)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self._create_text_option("type_url", "Type URL")
        self._create_int_option("user_id", "User Account ID")
        self._create_int_option("owner_id", "Owner Account ID")
        self._create_int_option("notify_channel_id", "Notify Channel ID")
        self.advanced_widget = QWidget()
        self.advanced_widget.setLayout(self.grid)
        self.advanced_widget.setVisible(False)
        vbox.addWidget(self.advanced_widget)

        vbox.addStretch(1)
        hbox = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_current_profile)
        hbox.addWidget(save_btn, 1)
        start_btn = QPushButton("Start the bot")
        hbox.addWidget(start_btn, 2)
        vbox.addLayout(hbox)

        w = QWidget()
        w.setLayout(vbox)
        self.setCentralWidget(w)

        self.update_profile_list_combo()

    def sizeHint(self):
        h = super().sizeHint()
        return QSize(400, h.height())

    def update_profile_list_combo(self):
        profile_name = self.current_profile["name"] if self.current_profile is not None else None
        self.profile_combo.clear()
        for i, p in enumerate(self.profile_manager.profiles):
            self.profile_combo.addItem(p["name"])
        self.set_current_profile_by_name(profile_name)

    def set_current_profile_by_name(self, profile_name):
        ci = 0
        for i, p in enumerate(self.profile_manager.profiles):
            if p["name"] == profile_name:
                ci = i
        self.profile_combo.setCurrentIndex(ci)
        if len(self.profile_manager.profiles) > 0:
            self.current_profile = self.profile_manager.profiles[ci]
            for w in self.setting_disable_widgets:
                w.setEnabled(True)
        else:
            for w in self.setting_disable_widgets:
                w.setEnabled(False)

    def on_current_profile_changed(self, index):
        self.current_profile = self.profile_manager.profiles[index]

    def create_new_profile(self, clone=False):
        name, ok = QInputDialog.getText(self, "DankBot", "Enter profile name")
        if not ok:
            return False
        if len(name) == 0 or not self.profile_manager.check_new_profile_name(name):
            QMessageBox.information(self, "DankBot", f"The profile name is not valid")
            return False

        self.current_profile = self.profile_manager.create_new_profile(name)
        self.update_profile_list_combo()
        return True

    def clone_current_profile(self):
        return self.create_new_profile(True)

    def save_current_profile(self):
        for f in self.setting_save_functions:
            if not f(self.current_profile):
                return False
        self.profile_manager.save_profile(self.current_profile)
        return True

    def on_show_advanced_clicked(self, state):
        if state:
            self.advanced_widget.setVisible(True)
        else:
            self.advanced_widget.setVisible(False)

    def _create_text_option(self, pref_id, name):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        txt = QLineEdit()
        self.grid.addWidget(txt, self.grid_row, 1)
        self.grid_row += 1

        def save(profile):
            profile[pref_id] = txt.text()
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_save_functions.append(save)

    def _create_int_option(self, pref_id, name):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        txt = QLineEdit()
        self.grid.addWidget(txt, self.grid_row, 1)
        self.grid_row += 1

        def save(profile):
            try:
                profile[pref_id] = int(txt.text())
            except ValueError:
                if txt.text() != "":
                    QMessageBox.information(self, "DankBot", f"The value for {name} is not a valid integer")
                    return False
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_save_functions.append(save)



app = QApplication([])
w = MainWindow()
w.show()
sys.exit(app.exec_())