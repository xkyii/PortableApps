import subprocess
import os
import configparser

APPS_DIR = 'D:\\Code\\xkyii\\PortableApps\\Apps\\'
PAF_DIR = 'D:\\Soft\\PortableApps\\'
LAUNCHER_EXE = PAF_DIR + 'PortableApps.comLauncher\\PortableApps.comLauncherGenerator.exe'
INSTALLER_EXE = PAF_DIR + 'PortableApps.comInstaller\\PortableApps.comInstaller.exe'


def create_launcher_of(app_name):
    cmd = LAUNCHER_EXE + " " + APPS_DIR + app_name
    print(cmd)
    subprocess.run(cmd, shell=True)


def create_installer_of(app_name):
    cmd = INSTALLER_EXE + " " + APPS_DIR + app_name
    print(cmd)
    subprocess.run(cmd, shell=True)


def read_ini(app_name, ini_file):
    ini_file_path = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', ini_file)

    # 检查文件是否存在
    if not os.path.exists(ini_file_path):
        print(f"Error: The file {ini_file_path} does not exist.")
        return None

    # 创建ConfigParser对象
    config = configparser.ConfigParser()

    # 读取ini文件
    config.read(ini_file_path)

    # 将配置项存储到字典中
    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        for key, value in config.items(section):
            config_dict[section][key] = value

    return config_dict


def write_ini(app_name, ini_file, config_dict):
    # 构造appinfo.ini文件的完整路径
    ini_file_path = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', ini_file)

    # 创建ConfigParser对象
    config = configparser.ConfigParser()

    # 将字典中的配置项写入ConfigParser对象
    for section, items in config_dict.items():
        config[section] = items

    # 写回appinfo.ini文件
    with open(ini_file_path, 'w') as configfile:
        config.write(configfile)


def rewrite(app_name, i):
    f = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', 'appinfo.ini')

    # 检查文件是否存在
    if not os.path.exists(f):
        print(f"Error: The file {f} does not exist.")
        return None

    # 创建ConfigParser对象
    config = configparser.ConfigParser()

    # 读取ini文件
    config.read(f)

    # 检查appinfo.ini文件是否存在
    fn = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', 'appinfo' + i + '.ini')
    if os.path.exists(fn):
        # 读取appinfo1.ini文件
        config.read(fn)

    # 将配置项存储到字典中
    config_dict = {}
    for section in config.sections():
        config_dict[section] = {}
        for key, value in config.items(section):
            config_dict[section][key] = value

    return config_dict


if __name__ == '__main__':
    apps = [
        # 'RapidEE',
        # 'PixPin',
        # 'TotalCommander',
        'XShellPlus',
    ]

    appinfo_ini = "appinfo.ini"

    for app in apps:
        # create_launcher_of(app)
        # create_installer_of(app)
        for i in range(1, 10):
            c = read_ini(app, i)
            print(c)