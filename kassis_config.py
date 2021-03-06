import os.path
import re
import platform
import configparser
import sys
try:
    from win32com.shell import shell, shellcon
except ModuleNotFoundError:
    pass

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
        sys.stderr.write("kassis.iniが見つかりません\n")
        sys.exit(2)

    config = configparser.ConfigParser()
    if os.path.exists(ini_fileepath):
        config.read(ini_fileepath, encoding='utf8')
    else:
        sys.stderr.write(ini_fileepath + " が見つかりません\n")
        sys.exit(2)

    for s in config.sections():
        for i in config[s]:

            for m in re.finditer(r"(\$)(\w+)", config[s][i]):
                if os.environ[m.group(2)] is not None:
                    config[s][i] = re.sub(r"(\$)(\w+)", os.environ[m.group(2)], config[s][i])

    return config
