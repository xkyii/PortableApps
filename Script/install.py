import subprocess
import os
import configparser

APPS_DIR = 'D:\\Code\\xkyii\\PortableApps\\Apps\\'
PAF_DIR = 'D:\\Other\\Soft\\PortableApps\\'
LAUNCHER_EXE = PAF_DIR + 'PortableApps.comLauncher\\PortableApps.comLauncherGenerator.exe'
INSTALLER_EXE = PAF_DIR + 'PortableApps.comInstaller\\PortableApps.comInstaller.exe'

class IniParser(configparser.ConfigParser):
    def optionxform(self, option_str):
        return option_str


def create_installer_cmd(app_name):
    cmd = INSTALLER_EXE + " " + APPS_DIR + app_name
    print(cmd)
    subprocess.run(cmd, shell=True)


def create_installer_of(app_name):
    create_installer_cmd(app_name)


def create_launcher_cmd(app_name):
    cmd = LAUNCHER_EXE + " " + APPS_DIR + app_name
    print(cmd)
    subprocess.run(cmd, shell=True)


def create_launcher_of(app_name, n=1):
    if n == 1:
        create_launcher_cmd(app_name)
        return

    f = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', 'appinfo.ini')

    # 检查文件是否存在
    if not os.path.exists(f):
        print(f"Error: The file {f} does not exist.")
        return

    # 创建[IniParser]对象
    config = IniParser()

    # 读取读取appinfo.ini文件
    config.read(f)

    # 备份原文件
    os.replace(f, f + '.bak')

    for i in range(1, n+1):
        # 检查appinfo.ini文件是否存在
        fi = os.path.join(APPS_DIR, app_name, 'App', 'AppInfo', 'appinfo' + str(i) + '.ini')
        print(fi)
        if not os.path.exists(fi):
            # print(fi + ' not exist.')
            break

        c = IniParser()
        # 复制config
        for section in config.sections():
            if section not in c:
                c.add_section(section)
            for key, value in config.items(section):
                c.set(section, key, value)

        # 读取appinfox.ini文件 (覆盖部分配置)
        c.read(fi)

        # 写回appinfo.ini文件
        with open(f, 'w') as cf:
            c.write(cf)

        print(f'create_launcher_of: {c['Details']['AppId']}')
        create_launcher_of(app_name)

    # 恢复文件
    os.replace(f + '.bak', f)


if __name__ == '__main__':
    apps = [
        # 'RapidEE',
        # 'PixPin',
        # 'TotalCommander',
        # ['XShellPlus', 2],
        # 'FreeFileSync',
        # 'LinqPad',
        # 'FsCapture',
        'XYplorer',
    ]

    for app in apps:
        if isinstance(app, str):
            create_launcher_of(app)
            create_installer_of(app)
        elif isinstance(app, list):
            create_launcher_of(app[0], app[1])
            create_installer_of(app[0])
