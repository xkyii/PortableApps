#!/usr/bin/env python3
"""PortableApps.com 构建辅助脚本（去硬编码版）。

封装 PortableApps.com 的 Launcher Generator 与 Installer：
先为每个 app 生成启动器（*Portable.exe），再生成安装包（*.paf.exe）。

用法:
    python install.py --list                列出所有可用 app 及其启动器数量
    python install.py Thunder               构建单个 app（先 launcher 后 installer）
    python install.py Thunder XYplorer      构建多个 app
    python install.py --all                 构建全部 app
    python install.py --rename-paf          仅把已存在的 *.paf.exe 改为短名，不构建
    python install.py --all --keep-portable 保留 Installer 原生命名

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
import shutil
import subprocess
import sys
import tempfile
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


# --- paf 安装包命名策略 ---
# Installer 把安装包名硬编码为 "<AppID>_<DisplayVersion>"（再加可选后缀），
# 见 InstallerWizard.nsi:744-782，没有任何配置项能覆盖。
# 但 AppID 在 PA.c 里必须是 <Name>Portable 形式 —— 它还同时决定 launcher
# 文件名、Data\settings\<AppID>Settings.ini、Platform 的应用标识与注册表键，
# 不能为了改名去动它。所以文件名里那个 "Portable" 是冗余的：
# ".paf.exe" 后缀本身已表明这是 Portable 安装包。
# 故构建完成后，把 AppID 结尾的 Portable 从文件名里去掉。
#
# 安全性：生成物只在 installer.ini 设了 [DownloadFiles] DownloadURL 时才会在
# 运行时自检"文件名必须以 _online.paf.exe 结尾"，见
# PortableApps.comInstaller.nsi:440-455（整段被 !ifdef DownloadURL 条件编译包裹）。
# 本仓库不填下载源，因此改名对安装包的运行没有任何影响。
# 需要 Installer 原生名字时传 --keep-portable。
KEEP_PORTABLE_NAME = False
PORTABLE_SUFFIX = 'Portable'


def read_appid(app_name):
    """读 appinfo.ini 的 [Details] AppId（键名大小写不敏感，兼容 AppID/AppId）。"""
    f = APPS_DIR / app_name / 'App' / 'AppInfo' / 'appinfo.ini'
    if not f.is_file():
        return None
    c = configparser.ConfigParser(interpolation=None)
    c.optionxform = str
    try:
        c.read(f, encoding='utf-8')
    except configparser.Error:
        return None
    if 'Details' not in c:
        return None
    for key, value in c['Details'].items():
        if key.lower() == 'appid':
            return value.strip()
    return None


def rename_paf(app_name):
    """把 <AppID>_<ver>.paf.exe 中的 AppID 去掉结尾的 Portable。返回改名个数。

    幂等：目标名已存在时直接覆盖（重建场景下旧文件会残留，正好清掉）。
    """
    appid = read_appid(app_name)
    if not appid:
        print(f"  [警告] {app_name}: 读不到 AppId，跳过重命名")
        return 0
    if not appid.endswith(PORTABLE_SUFFIX) or appid == PORTABLE_SUFFIX:
        return 0  # AppID 本就不带 Portable 结尾，无需处理

    short = appid[:-len(PORTABLE_SUFFIX)]
    renamed = 0
    for src in sorted(APPS_DIR.glob(f'{appid}_*.paf.exe')):
        dst = APPS_DIR / (short + src.name[len(appid):])
        if dst.exists():
            dst.unlink()
        os.replace(src, dst)
        print(f"  -> 重命名 {src.name}  =>  {dst.name}")
        renamed += 1
    return renamed


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
    """编译启动器。

    坑（2026-09 实测）：PortableApps.com Launcher Generator 2.2.9 只有在
    **app 目录位于 %TEMP% 之下**时才能读到 appinfo.ini。传任何其它绝对路径
    （工作区内、D:\\Temp、C:\\PA_Test …）都会失败，日志只留一句误导性的
    "ERROR: [Details]:Name [Details]:AppID or [Version]:PackageVersion not
    found in appinfo.ini files"，且不产出 exe。

    所以这里先把 App\\AppInfo 暂存到 %TEMP% 再编译，最后把生成的
    *Portable.exe 拷回真实 app 目录。生成启动器只需要 App\\AppInfo
    （appinfo.ini / appicon.ico / Launcher\\*.ini），不需要 AppFile 里的二进制。
    """
    src = APPS_DIR / app_name
    stage = Path(tempfile.gettempdir()) / 'PortableAppsLauncherBuild' / app_name
    if stage.exists():
        shutil.rmtree(stage)
    (stage / 'App').mkdir(parents=True)
    shutil.copytree(src / 'App' / 'AppInfo', stage / 'App' / 'AppInfo')

    run(f'"{LAUNCHER_EXE}" "{stage}"')

    produced = sorted(p for p in stage.glob('*.exe'))
    if not produced:
        print(f"  [警告] {app_name}: 启动器未生成，检查 "
              f"{LAUNCHER_EXE.parent / 'Data' / 'PortableApps.comLauncherGeneratorLog.txt'}")
        return
    for p in produced:
        shutil.copy2(p, src / p.name)
        print(f"  -> {src / p.name}")
    shutil.rmtree(stage, ignore_errors=True)


def create_installer(app_name):
    run(f'"{INSTALLER_EXE}" "{APPS_DIR / app_name}"')
    if not KEEP_PORTABLE_NAME:
        rename_paf(app_name)


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
    global KEEP_PORTABLE_NAME
    parser = argparse.ArgumentParser(
        description='PortableApps.com 构建辅助脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('apps', nargs='*', help='要构建的 app 名（可多个）')
    parser.add_argument('--list', action='store_true', help='列出所有可用 app')
    parser.add_argument('--all', action='store_true', help='构建全部 app')
    parser.add_argument('--rename-paf', action='store_true',
                        help='仅重命名已存在的 *.paf.exe（去掉 AppID 结尾的 Portable），不构建')
    parser.add_argument('--keep-portable', action='store_true',
                        help='保留 Installer 的原生命名（<AppID>_<ver>.paf.exe）')
    args = parser.parse_args()

    KEEP_PORTABLE_NAME = args.keep_portable

    if args.list:
        apps = list_apps()
        print("可用 app:")
        for a in apps:
            n = detect_launcher_count(a)
            mark = f" (x{n} 启动器)" if n > 1 else ""
            print(f"  - {a}{mark}")
        return

    if args.rename_paf:
        if args.keep_portable:
            print("--rename-paf 与 --keep-portable 矛盾：前者就是执行改名。")
            return
        total = sum(rename_paf(a) for a in list_apps())
        print(f"共重命名 {total} 个 paf。")
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
