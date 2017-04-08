import os.path
import platform
import configparser
import sys
from win32com.shell import shell, shellcon

def get():

    folders = []
    ext_name = ".ini"

    folders.append(os.path.dirname(os.path.abspath(__file__)))
    folders.append(os.path.expanduser("~"))
    if platform.system() == "Windows":
        folders.append(shell.SHGetFolderPath(0, shellcon.CSIDL_LOCAL_APPDATA, None, 0))
    else:
        folders.append("/etc")

    ini_fileepath = None
    for f in folders:
        inifile = os.path.join(f, f"kassis{ext_name}")
        #print(inifile)
        if os.path.isfile(inifile):
            ini_fileepath = inifile
            break

    if ini_fileepath is None:
        sys.stderr.write("INIFILE/CONFFILEが見つかりません\n")
        sys.exit(2)

    config = configparser.ConfigParser()
    if os.path.exists(ini_fileepath):
        config.read(ini_fileepath, encoding='utf8')
    else:
        sys.stderr.write(ini_fileepath + " が見つかりません\n")
        sys.exit(2)

    return config