import os
import platform
import shutil
import subprocess
import sys
import zipfile

from PyQt5.QtCore import QUrl, QFile, QIODevice, pyqtSignal, QObject
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QProgressDialog, QApplication, QMessageBox

if platform.system() == "Windows":
    from win32api import GetFileVersionInfo, LOWORD, HIWORD

    # https://stackoverflow.com/questions/16011379/operating-system-specific-requirements-with-pip
    def get_version_number(filename):
        try:
            info = GetFileVersionInfo(filename, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            return [HIWORD(ms), LOWORD(ms), HIWORD(ls), LOWORD(ls)]
        except:
            return None


def get_dirs():
    ret = []
    if platform.system() == "Windows":
        local_app_data = os.getenv('LOCALAPPDATA')
        program_files = os.getenv('ProgramW6432')
        program_files_x86 = os.getenv('ProgramFiles(x86)')

        for cp in ["Google\\Chrome\\Application", "Chromium\\Application"]:
            for d in [local_app_data, program_files, program_files_x86]:
                if d is not None:
                    ret.append(os.path.join(d, cp))
    if platform.system() == "Linux":
        ret += ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"]
        ret += ["/opt/google/chrome", "/opt/chromium.org/chromium"]
    return ret

def get_chrome_exe_names():
    if platform.system() == "Windows":
        return ["chrome.exe", "chromium.exe"]
    else:
        return ["chrome", "chromium"]

def find_chrome():
    names = get_chrome_exe_names()
    for d in get_dirs():
        for n in names:
            if os.path.exists(os.path.join(d, n)):
                return os.path.join(d, n)
    return None

def get_chrome_version(c):
    if c is None:
        return None
    if platform.system() == "Windows":
        return get_version_number(c)
    else:
        return subprocess.check_output([c, "--product-version"]).decode().strip().split(".")

def get_webdriver_path(version):
    v = version[0]
    if platform.system() == "Windows":
        return f"chromedriver_{v}.exe"
    else:
        return f"chromedriver_{v}"

def check_webdriver_version(version):
    p = get_webdriver_path(version)
    return os.path.exists(p)

def get_webdriver_version_url(chrome_version):
    return f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version[0]}"

def get_webdriver_download_url(webdriver_version):
    if platform.system() == "Windows":
        plat = "win32"
    elif platform.system() == "Linux":
        plat = "linux64"
    elif platform.system() == "Darwin":
        plat = "mac64"
    else:
        return None
    return f"https://chromedriver.storage.googleapis.com/{webdriver_version}/chromedriver_{plat}.zip"


class QWebDriverDownloader(QObject):
    completed = pyqtSignal()

    def __init__(self, parent, chrome_path):
        super().__init__(parent)
        self.success = False

        self.net = QNetworkAccessManager()

        self.dialog = QProgressDialog(parent)
        self.dialog.setWindowTitle("Chrome Web Driver Download")
        self.dialog.canceled.disconnect()
        self.dialog.canceled.connect(self.cancel)

        self.dialog.setLabelText("Getting the Web Driver version")
        self.dialog.setMinimum(0)
        self.dialog.setMaximum(0)
        self.dialog.setValue(0)
        self.dialog.show()

        cv = get_chrome_version(chrome_path)
        self.webdriver_path = get_webdriver_path(cv)
        url = get_webdriver_version_url(cv)
        print(f"Getting Web Driver version from: {url}")
        req = QNetworkRequest(QUrl(url))
        self.version_rep = self.net.get(req)
        self.version_rep.finished.connect(self.on_version_fetched)
        self.download_rep = None
        self.download_file = None

    def cancel(self):
        self.version_rep.abort()
        if self.download_rep is not None:
            self.download_rep.abort()

    def report_error(self, req):
        print(f"Download failed")

        if self.download_file is not None:
            self.download_file.close()
            self.download_file.remove()

        QMessageBox.information(self.dialog, "Web Driver Download", f"Failed to download Web Driver: {req.errorString()}")
        self.dialog.close()
        self.completed.emit()

    def on_version_fetched(self):
        if self.version_rep.error() != QNetworkReply.NoError:
            self.report_error(self.version_rep)
            return

        ver = bytes(self.version_rep.readAll()).decode().strip()
        print(f"Web Driver version: {ver}")

        url = get_webdriver_download_url(ver)
        print(f"Getting Web Driver from: {url}")

        req = QNetworkRequest(QUrl(url))
        self.download_file = QFile(self.webdriver_path + ".zip.tmp")
        self.download_file.open(QIODevice.WriteOnly)
        self.download_rep = self.net.get(req)
        self.download_rep.finished.connect(self.on_download_completed)
        self.download_rep.downloadProgress.connect(self.on_download_progress)
        self.download_rep.readyRead.connect(self.on_read_ready)

    def on_download_progress(self, cur, total):
        print(f"Download progress: {cur}/{total}")
        self.dialog.setMaximum(total)
        self.dialog.setValue(cur)

    def on_download_completed(self):
        if self.download_rep.error() != QNetworkReply.NoError:
            self.report_error(self.download_rep)
            return
        print(f"Download completed")
        self.download_file.write(self.download_rep.readAll())
        self.download_file.close()

        print(f"Unzipping")
        with zipfile.ZipFile(self.webdriver_path + ".zip.tmp", 'r') as z:
            chromedriver_exe = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
            with z.open(chromedriver_exe) as src, open(self.webdriver_path, "wb") as dest:
                shutil.copyfileobj(src, dest)
            if platform.system() != "Windows":
                os.chmod(self.webdriver_path, 0o555)
        self.download_file.remove()

        print(f"Everything completed")
        self.success = True
        self.dialog.close()
        self.completed.emit()

    def on_read_ready(self):
        self.download_file.write(self.download_rep.readAll())
