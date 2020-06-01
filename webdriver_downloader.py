import os
import platform
import subprocess


def get_dirs():
    ret = []
    if platform.system() == "Windows":
        local_app_data = os.getenv('LOCALAPPDATA')
        program_files = os.getenv('%ProgramW6432%')
        program_files_x86 = os.getenv('%ProgramFiles(x86)%')

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


def get_chrome_version():
    c = find_chrome()
    if c is None:
        return None
    if platform.system() == "Windows":
        return subprocess.check_output(["wmic", "datafile", "where", "name=" + c, "get", "Version", "/value"]).decode().strip()
    else:
        return subprocess.check_output([c, "--product-version"]).decode().strip()


print(get_chrome_version())