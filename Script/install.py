import subprocess
import os

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

if __name__ == '__main__':
    apps = [
        # 'RapidEE',
        # 'PixPin',
        'TotalCommander',
    ]

    for app in apps:
        create_launcher_of(app)
        create_installer_of(app)