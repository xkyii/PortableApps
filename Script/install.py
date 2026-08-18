#!/usr/bin/env python3
"""PortableApps.com 构建辅助脚本（去硬编码版）。

封装 PortableApps.com 的 Launcher Generator 与 Installer：
先为每个 app 生成启动器（*Portable.exe），再生成安装包（*.paf.exe）。

用法:
    python install.py --list                列出所有可用 app 及其启动器数量
    python install.py Thunder               构建单个 app（先 launcher 后 installer）
    python install.py Thunder XYplorer      构建多个 app
    python install.py --all                 构建全部 app

多启动器:
    若某 app 的 App/AppInfo 下存在 appinfo1.ini、appinfo2.ini ...，
    脚本会自动探测数量并逐个合并生成（PA.c 单 Launcher 限制的官方 workaround）。

环境变量:
    PORTABLEAPPS_APPS_DIR    Apps 目录（默认: 本脚本所在仓库的 Apps/）
    PORTABLEAPPS_PAF_DIR    PortableApps.com 工具目录，需含
                            PortableApps.comLauncher/ 与 PortableApps.comInstaller/ 子目录
                            （默认回退: D:\\Other\\Soft\\PortableApps，建议用环境变量覆盖）
"""
import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path

# --- 路径解析（去硬编码）---
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_APPS_DIR = SCRIPT_DIR.parent / 'Apps'
DEFAULT_PAF_DIR = Path(r'D:\Other\Soft\PortableApps')  # 仅作回退，请用环境变量覆盖

APPS_DIR = Path(os.environ.get('PORTABLEAPPS_APPS_DIR', DEFAULT_APPS_DIR)).resolve()
PAF_DIR = Path(os.environ.get('PORTABLEAPPS_PAF_DIR', DEFAULT_PAF_DIR)).resolve()
LAUNCHER_EXE = PAF_DIR / 'PortableApps.comLauncher' / 'PortableApps.comLauncherGenerator.exe'
INSTALLER_EXE = PAF_DIR / 'PortableApps.comInstaller' / 'PortableApps.comInstaller.exe'


class IniParser(configparser.ConfigParser):
    def optionxform(self, option_str):
        return option_str


def list_apps():
    """返回所有含 appinfo.ini 的 app 目录名（已排序）。"""
    if not APPS_DIR.is_dir():
        print(f"Apps 目录不存在: {APPS_DIR}")
        return []
    return sorted(
        p.name for p in APPS_DIR.iterdir()
        if p.is_dir() and (p / 'App' / 'AppInfo' / 'appinfo.ini').is_file()
    )


def detect_launcher_count(app_name):
    """根据 appinfo{i}.ini 自动探测需要的启动器数量（默认 1）。"""
    info_dir = APPS_DIR / app_name / 'App' / 'AppInfo'
    n = 1
    while (info_dir / f'appinfo{n + 1}.ini').is_file():
        n += 1
    return n


def run(cmd):
    print('> ' + cmd)
    subprocess.run(cmd, shell=True)


def create_launcher(app_name):
    run(f'"{LAUNCHER_EXE}" "{APPS_DIR / app_name}"')


def create_installer(app_name):
    run(f'"{INSTALLER_EXE}" "{APPS_DIR / app_name}"')


def build_multi_launcher(app_name, n):
    """多启动器 hack：临时合并 appinfo{i}.ini 后逐个生成，最后还原。"""
    f = APPS_DIR / app_name / 'App' / 'AppInfo' / 'appinfo.ini'
    if not f.is_file():
        print(f"Error: {f} 不存在。")
        return
    config = IniParser()
    config.read(f)
    backup = f.with_suffix('.ini.bak')
    os.replace(f, backup)
    try:
        for i in range(1, n + 1):
            fi = APPS_DIR / app_name / 'App' / 'AppInfo' / f'appinfo{i}.ini'
            if not fi.is_file():
                break
            c = IniParser()
            for section in config.sections():
                if section not in c:
                    c.add_section(section)
                for key, value in config.items(section):
                    c.set(section, key, value)
            c.read(fi)
            with open(f, 'w', encoding='utf-8') as cf:
                c.write(cf)
            app_id = c['Details']['AppId']
            print(f"    生成启动器: {app_id}")
            create_launcher(app_name)
    finally:
        os.replace(backup, f)


def build_app(app_name):
    app_path = APPS_DIR / app_name
    if not app_path.is_dir():
        print(f"[跳过] 找不到 app: {app_name}")
        return
    n = detect_launcher_count(app_name)
    if n > 1:
        print(f"==> {app_name}: 检测到 {n} 个启动器配置")
        build_multi_launcher(app_name, n)
    else:
        create_launcher(app_name)
    create_installer(app_name)
    print(f"[完成] {app_name}\n")


def check_tools():
    missing = [p for p in (LAUNCHER_EXE, INSTALLER_EXE) if not p.is_file()]
    if missing:
        print("错误：找不到 PortableApps.com 工具，请设置环境变量 PORTABLEAPPS_PAF_DIR。")
        print(f"  当前解析: {PAF_DIR}")
        for p in missing:
            print(f"  缺失: {p}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='PortableApps.com 构建辅助脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('apps', nargs='*', help='要构建的 app 名（可多个）')
    parser.add_argument('--list', action='store_true', help='列出所有可用 app')
    parser.add_argument('--all', action='store_true', help='构建全部 app')
    args = parser.parse_args()

    if args.list:
        apps = list_apps()
        print("可用 app:")
        for a in apps:
            n = detect_launcher_count(a)
            mark = f" (x{n} 启动器)" if n > 1 else ""
            print(f"  - {a}{mark}")
        return

    if args.all:
        targets = list_apps()
    elif args.apps:
        targets = args.apps
    else:
        parser.print_help()
        return

    if not targets:
        print("没有可构建的 app。")
        return

    check_tools()
    print(f"将构建 {len(targets)} 个 app: {', '.join(targets)}\n")
    for app in targets:
        build_app(app)


if __name__ == '__main__':
    main()
