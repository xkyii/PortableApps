
## PortableApps

Windows portable apps for personal use.

[PortableApps.com/development](https://portableapps.com/development)
[SourceForge](https://sourceforge.net/projects/portableapps/)


### 目录结构

- Apps
    - FreeFileSync     14.3.0.0
    - FsCapture        11.0.0.0
    - LinqPad          8.9.9.0
    - PixPin           2.0.0.3
    - RapidEE          3.9.0.0
    - Thunder          12.3.0.3340
    - TotalCommander   11.51.0.0
    - XShellPlus       8.0.0.9
    - XYplorer         27.00.600.0

- Template
    - [Template_3.9.2](https://downloads.sourceforge.net/portableapps/PortableApps.com_Application_Template_3.9.2.zip)


### 构建

构建工具（PortableApps.com Launcher Generator / Installer）在本机 `D:\Soft\PortableApps`
（非仓库内容，需自行安装）。通过 `Script/install.py` 封装调用：

```cmd
REM 设置工具目录（必须用 Windows 风格路径，不要写 /d/... 否则会被误解析成 D:\d\...）
set PORTABLEAPPS_PAF_DIR=D:\Soft\PortableApps

REM 列出所有 app 及其启动器数量
python Script/install.py --list

REM 构建单个 app（先生成启动器，再生成安装包）
python Script/install.py RapidEE

REM 构建多个 / 全部
python Script/install.py Thunder XYplorer
python Script/install.py --all
```

> 构建前需先把原始软件放到 `Apps\<AppName>\App\AppFile\`（不入 git）。
> 生成的 `*Portable.exe` 与 `*.paf.exe` 已被 `.gitignore` 忽略，不会提交进仓库。

### 计算SHA256
```cmd
certutil -hashfile filename SHA256
```

## 多启动器
- [Using the launcher generator to generate multiple app launchers](https://portableapps.com/node/65720)

这里提到, `PA.c Launcher`只支持单`Launcher`, 只有`LibreOffice`和`OpenOffice`是例外.