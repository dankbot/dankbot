import asyncio
import logging
import shutil

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QWidget, \
    QLabel, QLineEdit, QGridLayout, QCheckBox, QMessageBox, QInputDialog, QPlainTextEdit
import sys
import os
import json
import re

from threading import Thread

import webdriver_downloader
from bot import TheBot
from config_base import config, cooldown_donator, cooldown_normal


logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s', stream=sys.stdout)
logging.getLogger("bot").setLevel(logging.DEBUG)


class ProfileManager:
    P_ALLOWED_CHARS = re.compile("^[a-zA-Z0-9 ]+$")

    def __init__(self):
        self.profiles = []
        self.load()

    def load(self):
        if not os.path.isdir("profiles/"):
            return
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
        if not os.path.isdir("profiles/"):
            os.mkdir("profiles/")
        with open("profiles/" + p["name"] + ".json", "w") as f:
            json.dump(p, f)

    def delete_profile(self, p):
        if not os.path.isdir("profiles/"):
            return
        self.profiles.remove(p)
        if os.path.isdir("profiles/" + p["name"]):
            shutil.rmtree("profiles/" + p["name"])
        if os.path.exists("profiles/" + p["name"] + ".json"):
            os.remove("profiles/" + p["name"] + ".json")

    def check_new_profile_name(self, name):
        for p in self.profiles:
            if p["name"] == name:
                return False
        return ProfileManager.P_ALLOWED_CHARS.match(name) is not None

    def create_new_profile(self, name):
        p = {"name": name}
        self.profiles.append(p)
        return p


class QLogHandler(QObject, logging.Handler):
    emitted = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

    def emit(self, record):
        self.emitted.emit(self.format(record))


log_handler = QLogHandler(None)
log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s"))
logging.root.addHandler(log_handler)


class QLogTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        log_handler.emitted.connect(self.on_emitted)

    def on_emitted(self, msg):
        s = self.verticalScrollBar().value() >= self.verticalScrollBar().maximum() - 10
        self.appendPlainText(msg)
        if s:
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DankBot")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.resize(400, 1)

        self.profile_manager = ProfileManager()
        self.current_profile = None

        self.log_text = QLogTextEdit()
        self.bot = None
        self.thread_timer = None

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
        del_btn = QPushButton("Del")
        del_btn.clicked.connect(self.delete_current_profile)
        del_btn.setFixedWidth(50)
        hbox.addWidget(del_btn)
        vbox.addLayout(hbox)

        self.setting_disable_widgets = []
        self.setting_disable_widgets.append(copy_btn)
        self.setting_disable_widgets.append(del_btn)
        self.setting_load_functions = []
        self.setting_save_functions = []
        self.grid = QGridLayout()
        self.grid_row = 0
        self._create_text_option("token", "Bot Token")
        self._create_int_option("type_channel_id", "Type Channel ID")
        self._create_int_option("notify_channel_id", "Notify Channel ID")
        self._create_int_option("owner_id", "Owner Account ID")
        self._create_bool_option("donator", "Donator", "Use Donator Cooldowns")
        self._create_module_list_option("Basic Modules", [("Beg", "beg"), ("Search", "search"), ("Meme", "pm"), ("Fish", "fish"), ("Hunt", "hunt")])
        self._create_module_list_option("Gambling Modules", [("Gamble", "gamble"), ("Blackjack", "blackjack")])
        self._create_module_list_option("Other Modules", [("Trivia", "trivia"), ("Fidget", "fidget"), ("Depwit", "depwit")])
        self._create_drop_down_option("autodep_mode", "Auto-Dep Mode", [("Off", "off"), ("Deposit", "dep"), ("Give", "give")])
        self._create_range_option("autodep_threshold", "Auto-Dep Threshold")
        self._create_range_option("autodep_result", "Auto-Dep Result")
        self._create_int_option("autodep_account_id", "Auto-Dep Account ID")
        vbox.addLayout(self.grid)

        show_advanced = QCheckBox("Show advanced")
        vbox.addWidget(show_advanced)
        show_advanced.stateChanged.connect(self.on_show_advanced_clicked)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self._create_text_option("chrome_path", "Chrome Path")
        self._create_text_option("driver_path", "WebDriver Path")
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
        start_btn.clicked.connect(self.run)
        hbox.addWidget(start_btn, 2)
        vbox.addLayout(hbox)
        self.setting_disable_widgets.append(save_btn)
        self.setting_disable_widgets.append(start_btn)

        w = QWidget()
        w.setLayout(vbox)
        self.setCentralWidget(w)

        self.update_profile_list_combo()

    def on_show_advanced_clicked(self, state):
        if state:
            self.advanced_widget.setVisible(True)
        else:
            self.advanced_widget.setVisible(False)

    def run(self):
        if self.current_profile is None:
            return

        self.save_current_profile()

        bot_cfg = dict(config)
        bot_cfg.update(self.current_profile)
        bot_cfg["profile_id"] = bot_cfg["name"]
        bot_cfg["cooldown"] = cooldown_donator if bot_cfg["donator"] else cooldown_normal

        if "token" not in bot_cfg or len(bot_cfg["token"]) == 0:
            QMessageBox.information(self, "DankBot", f"Must set the bot token!")
            return
        if "type_channel_id" not in bot_cfg:
            QMessageBox.information(self, "DankBot", f"Must set the message type channel!")
            return
        if "notify_channel_id" not in bot_cfg:
            QMessageBox.information(self, "DankBot", f"Must set a notification channel!")
            return

        if "driver_path" not in bot_cfg or len(bot_cfg["driver_path"]) == 0:
            if "chrome_path" not in bot_cfg or len(bot_cfg["chrome_path"]) == 0:
                bot_cfg["chrome_path"] = webdriver_downloader.find_chrome()
            chrome = bot_cfg["chrome_path"]
            chrome_ver = webdriver_downloader.get_chrome_version(chrome)
            if not chrome or not chrome_ver:
                QMessageBox.information(self, "DankBot", f"Couldn't find a Chrome installation, select chrome.exe manually")
                return
            if not webdriver_downloader.check_webdriver_version(chrome_ver):
                dler = webdriver_downloader.QWebDriverDownloader(self, chrome)
                def on_web_driver_dled():
                    if dler.success:
                        self.run()
                dler.completed.connect(on_web_driver_dled)
                return

            bot_cfg["driver_path"] = webdriver_downloader.get_webdriver_path(chrome_ver)

        if self.width() < 600:
            self.resize(600, self.height())

        loop = asyncio.new_event_loop()

        thread = Thread(target=self.bot_thread, args=(loop, bot_cfg))
        self.thread_timer = QTimer()

        vbox = QVBoxLayout()
        lbl = QLabel("The bot has been started, have fun.")
        vbox.addWidget(lbl)
        vbox.addWidget(self.log_text, 1)

        stop_btn = QPushButton("Stop the bot")

        def do_stop():
            asyncio.create_task(self.bot.close())
        def stop():
            if thread.is_alive():
                stop_btn.setEnabled(False)
                stop_btn.setText("Stopping the bot...")
                loop.call_soon_threadsafe(do_stop)

        stop_btn.clicked.connect(stop)
        vbox.addWidget(stop_btn)

        w = QWidget()
        w.setLayout(vbox)
        self.setCentralWidget(w)

        def check_stopped():
            if not thread.is_alive():
                lbl.setText("The bot has been stopped, feel free to close the program.")
                stop_btn.setText("Stopped the bot")

        thread.start()
        self.thread_timer.setInterval(100)
        self.thread_timer.timeout.connect(check_stopped)
        self.thread_timer.start()

    def bot_thread(self, loop, cfg):
        asyncio.set_event_loop(loop)
        bot = self.bot = TheBot(cfg)
        try:
            loop.run_until_complete(bot.start(cfg["token"]))
        except Exception as e:
            logging.getLogger("bot").exception("Run failed")
        bot.stop()

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
        self.on_current_profile_changed(ci)

    def on_current_profile_changed(self, index):
        if len(self.profile_manager.profiles) > 0:
            self.current_profile = self.profile_manager.profiles[index]
            for w in self.setting_disable_widgets:
                w.setEnabled(True)
            # load based on default cfg
            p_with_defaults = dict(config)
            p_with_defaults.update(self.current_profile)
            for l in self.setting_load_functions:
                l(p_with_defaults)
        else:
            for w in self.setting_disable_widgets:
                w.setEnabled(False)

    def create_new_profile(self, clone=False):
        name, ok = QInputDialog.getText(self, "DankBot", "Enter profile name")
        if not ok:
            return False
        if len(name) == 0 or not self.profile_manager.check_new_profile_name(name):
            QMessageBox.information(self, "DankBot", f"The profile name is not valid")
            return False

        old_current = dict(self.current_profile)
        self.current_profile = self.profile_manager.create_new_profile(name)
        if clone:
            del old_current["name"]
            self.current_profile.update(old_current)
        self.update_profile_list_combo()
        return True

    def clone_current_profile(self):
        return self.create_new_profile(True)

    def delete_current_profile(self):
        if self.current_profile is not None:
            self.profile_manager.delete_profile(self.current_profile)
        self.update_profile_list_combo()

    def save_current_profile(self):
        for f in self.setting_save_functions:
            if not f(self.current_profile):
                return False
        self.profile_manager.save_profile(self.current_profile)
        return True

    def _create_text_option(self, pref_id, name):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        txt = QLineEdit()
        self.grid.addWidget(txt, self.grid_row, 1)
        self.grid_row += 1

        def load(profile):
            txt.setText(profile[pref_id] if pref_id in profile else "")
        def save(profile):
            profile[pref_id] = txt.text()
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)

    def _create_int_option(self, pref_id, name):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        txt = QLineEdit()
        self.grid.addWidget(txt, self.grid_row, 1)
        self.grid_row += 1

        def load(profile):
            try:
                txt.setText(str(profile[pref_id]) if pref_id in profile else "")
            except ValueError:
                txt.setText("")
        def save(profile):
            try:
                profile[pref_id] = int(txt.text())
            except ValueError:
                if txt.text() != "":
                    QMessageBox.information(self, "DankBot", f"The value for {name} is not a valid integer")
                    return False
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)

    def _create_range_option(self, pref_id, name):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        l = QHBoxLayout()
        txt = QLineEdit()
        lbl2 = QLabel(" - ")
        txt2 = QLineEdit()
        l.addWidget(txt)
        l.addWidget(lbl2)
        l.addWidget(txt2)
        self.grid.addItem(l, self.grid_row, 1)
        self.grid_row += 1

        def load(profile):
            try:
                txt.setText(str(profile[pref_id][0]))
                txt2.setText(str(profile[pref_id][1]))
            except (ValueError, KeyError):
                txt.setText("")
                txt2.setText("")
        def save(profile):
            try:
                profile[pref_id] = (int(txt.text()), int(txt2.text()))
            except ValueError:
                if txt.text() != "":
                    QMessageBox.information(self, "DankBot", f"The values for {name} are not valid integers")
                    return False
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)

    def _create_bool_option(self, pref_id, name, name2):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        txt = QCheckBox(name2)
        self.grid.addWidget(txt, self.grid_row, 1)
        self.grid_row += 1

        def load(profile):
            try:
                txt.setChecked(bool(profile[pref_id]) if pref_id in profile else False)
            except ValueError:
                txt.setChecked(False)
        def save(profile):
            profile[pref_id] = txt.isChecked()
            return True
        self.setting_disable_widgets.append(txt)
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)

    def _create_drop_down_option(self, pref_id, name, opts):
        lbl = QLabel(name)
        self.grid.addWidget(lbl, self.grid_row, 0)
        cb = QComboBox()
        for opt_disp, _ in opts:
            cb.addItem(opt_disp)
        self.grid.addWidget(cb, self.grid_row, 1)
        self.grid_row += 1

        def load(profile):
            if pref_id in profile:
                for i, (opt_disp, opt_int) in enumerate(opts):
                    if opt_int == profile[pref_id]:
                        cb.setCurrentIndex(i)
                        return
            cb.setCurrentIndex(-1)
        def save(profile):
            if cb.currentIndex() != -1:
                profile[pref_id] = opts[cb.currentIndex()][1]
            return True
        self.setting_disable_widgets.append(cb)
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)

    def _create_module_list_option(self, lbl, modules):
        lbl = QLabel(lbl)
        self.grid.addWidget(lbl, self.grid_row, 0)
        w = QWidget()
        f = QHBoxLayout()
        f.setContentsMargins(0, 0, 0, 0)
        w.setLayout(f)
        self.grid.addWidget(w, self.grid_row, 1)
        self.grid_row += 1

        cbs = []
        for md, mi in modules:
            c = QCheckBox(md)
            f.addWidget(c)
            self.setting_disable_widgets.append(c)
            cbs.append(c)
        f.addStretch(1)

        def load(profile):
            enabled = set(profile["modules"] if "modules" in profile else [])
            for i, (_, mi) in enumerate(modules):
                cbs[i].setChecked((mi in enabled))
        def save(profile):
            enabled = set(profile["modules"] if "modules" in profile else [])
            for i, (_, mi) in enumerate(modules):
                if cbs[i].isChecked():
                    enabled.add(mi)
                else:
                    enabled.discard(mi)
            profile["modules"] = list(enabled)
            return True
        self.setting_load_functions.append(load)
        self.setting_save_functions.append(save)




app = QApplication([])
w = MainWindow()
w.show()
sys.exit(app.exec_())