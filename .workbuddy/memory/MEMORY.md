# PortableApps 项目长期约定

## 仓库性质与用途
个人自用 PA.c 格式仓库，`D:\Code\xkyii\PortableApps`，git 管理、无远程。
用户实际用 **PortableApps.com Platform** 当启动菜单 —— 全仓库走 PA.c 格式是为了菜单 /
splash 统一，**别因为"某软件本来就能便携"就建议去掉 PA.c 包装**。

## 入库策略
- 只存配置/元数据/模板；真实二进制不入库。`.gitignore` 忽略 `Apps/**/App/AppFile`
  与 `Apps/**/App/AppFile32`（双架构 app 用，2026-09 新增）。
- 因此**不为 installer.ini 填下载源**：换机器靠用户本地放二进制，不靠在线重建。
- **git 卫生**：`.gitignore` 只对**未跟踪**文件生效，**已跟踪文件不会被新规则自动忽略**。
  每次加忽略规则后必扫一遍：`git ls-files . | grep -iE "AppFile|Portable\.exe|\.paf\.exe"`
  （实测抓到 `Apps/XYplorer/XYplorerPortable.exe` 自 `22180de` 起误入库，已 `git rm --cached`
  移出并提交 `344afd8`）。⚠️ `Template/AppNamePortable.exe` 是**有意保留**的模板示例，别误删。
  `.gitignore` 另含 `__pycache__/`、`*.pyc`（py_compile 产生）。

## 工具与构建
- 基线 Format 3.9；构建工具在用户本机 **`D:\Soft\PortableApps`**（不是 `D:\Other\Soft\...`），
  非仓库内容，需手动更新（官方 Installer 3.9.18 / Launcher 2.2.9）。
- 跑 `install.py` 必须设 `PORTABLEAPPS_PAF_DIR`，**用 Windows 风格路径**（`D:/Soft/PortableApps`）；
  传 Git Bash 的 `/d/Soft/...` 会被 pathlib 解析成 `D:\d\...`。
- 入口 `Script/install.py`：`--list` / `--all` / 指定 app 名 / `--rename-paf` / `--keep-portable`；
  多启动器按 `appinfo{i}.ini` 数量自动探测。
- **paf 产物落点**：`Apps/`（app 目录的父级），不是仓库根。

### paf.exe 命名（本仓库约定：短名）
Installer 硬编码 `<AppID>_<DisplayVersion>.paf.exe`（`InstallerWizard.nsi:744-782`），
**无配置可覆盖**；AppID 又不能动（它还决定 launcher 名、`Data\settings\<AppID>Settings.ini`、
Platform 标识与注册表键）。故 `create_installer()` 在 Installer 退出后用 `rename_paf()`
去掉 AppID 结尾的 `Portable`：`BeyondComparePortable_5.2.5.paf.exe` →
`BeyondCompare_5.2.5.paf.exe`（目标已存在则覆盖，幂等）。
改名零风险 —— 那个"须以 `_online.paf.exe` 结尾"的自检整段被 `!ifdef DownloadURL` 包裹，
本仓库不填下载源。注意 AppID ≠ 目录名：`Apps/XShellPlus` 的 AppID 是 `XShellPortable`
→ 安装包名 `XShell_*.paf.exe`。

### 三个已知坑（细节见 skill `portableapps-package`）
1. **所有 .ini 必须 CRLF**：PA.c 用 Win32 `GetPrivateProfileString`，LF-only 会被当成一整行，
   键全读不到 → Generator 报「appinfo 找不到」。写完必转 CRLF
   （`raw.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')`）。
2. **Launcher Generator 只在 app 目录位于 `%TEMP%` 下才能工作**：任何其它绝对路径（工作区内、
   `D:\Temp`、`C:\PA_Test`、家目录、官方原包）一律失败，日志只留**误导性**的
   `ERROR: ... not found in appinfo.ini files`。与沙箱 / appinfo 内容 / 盘符均无关，既有 app
   （DOpus 等）同样失败 → 工具/环境层面问题。`create_launcher()` 已内置规避（把 `App/AppInfo`
   暂存到 `%TEMP%/PortableAppsLauncherBuild/` 编译，再把 `*Portable.exe` 拷回）。
   - 日志编码：Launcher Generator = **UTF-8**；Installer = **UTF-16LE**，且只在主动报错时才写。
   - 验证产物必须用**新建干净目录**，否则预先存在的 exe 会造成假阳性。
3. **Installer 必须带 app 路径参数**：`PortableApps.comInstaller.exe "<APPS_DIR>\<AppName>"`；
   漏传 → rc=1、约 30s 退出、**无日志无产物**。**向导中断会留"残包"**（BC 5.2.5 真包
   27.0 MB / 67 文件 / 压缩前 104 MB / 36s；残包仅 7.1 MB 且 `7z l` 报 `Cannot open`）。
   成功判定三件套：进程退出且 rc=0 → `7z.exe l <paf>` 能列清单 → 压缩前总字节 ≈ `App/` 体积。
   - 已知坏包：`Apps/DirectoryOpus_13.24.paf.exe`（551KB，无 AppFile 二进制，8-19 产物），重发需重建。

## 闪屏
- 已从带图三款（FlyingBird / DOpus / XShellPlus）**删除** `App/AppInfo/Launcher/splash.jpg`
  （commit `6201852`）：`SplashScreen.nsh` 在 splash.jpg 不存在时强制 `DisableSplashScreen=true`，
  首启/之后都不弹，也不依赖根 ini 是否被打包。
- 控制 PAL splash 的键是 `DisableSplashScreen`（launcher 源 `[Launch]` 段，编译时烘焙），
  **不是 `ShowSplashScreen`** —— 后者 PAL 源码里根本不存在，早期给 11 个 launcher 加的全是无效键。
- Platform 层"启动中"窗口另由 app 根 `<AppId>.ini` 的平铺 `DisableSplashScreen=true` 控制，
  与 PAL 自带 splash 是两回事。

## 环境注意
- **Git Bash 无法直接 exec 工作区内的 .exe**（`Permission denied`，工作区疑似 noexec）；改用
  `python -c "subprocess.run([...])"` 走 `CreateProcess`，别用 `./x.exe` 或 `cmd /c`。
  PowerShell 的 `Start-Process` / `[Diagnostics.Process]::Start` 亦被安全策略拦截。
  给 Windows Python 传路径必须用 `D:/...`。
- **环境异常（2026-08-19）**：曾反复出现 `Apps/` 被外部进程删空 + `.git/index.lock` 被重建，
  导致 git 报锁 / 文件消失。应对：先 `rm -f .git/index.lock`；用 `rm` + 只 `git add` 特定路径
  （不用 `git rm -A`）；数据全在 git HEAD，`git checkout HEAD -- Apps/` 可无损恢复。
  疑与沙箱 / IDE 后台 git 轮询有关，未完全定位。
- Installer 是 GUI，会弹到用户交互桌面，需用户点掉才 rc=0；Launcher Generator 可无头。

## app 清单
`Apps/`：BeyondCompare(5.2.5，双架构) / DirectoryOpus / FlyingBird / FreeFileSync / FsCapture /
LinqPad / PixPin / RapidEE / Thunder / TotalCommander / XShellPlus / XYplorer。

## 可复用经验（Scoop → PortableApp）
- **授权随程序目录走**（免重导入、换机器无感）：DOpus 的 `dopus.opuscert`（用户自有正版证书）
  放 AppFile，DOpus 每次启动自动从程序目录读取，无需 patcher / License GUI；
  BeyondCompare 同模式 —— `BC5Key.txt` 放 AppFile，BC 自动读。
  注意 `Patch.exe` 是 GnuWin32 的 GNU patch（BC 自带，非破解）。
- **BeyondCompare 特例**：64 位 `App/AppFile` + 32 位 `App/AppFile32`；去掉上游
  `RunAsAdmin=force`（原为装 Explorer 外壳扩展，代价是每次弹 UAC；副作用是右键菜单集成
  不可用，已在 help.html 说明）；数据重定向 `%APPDATA%\Scooter Software` +
  `HKCU\Software\Scooter Software`。
- **图标**：`icoextract.exe <输入exe> <输出.ico>`（0.3.0 的 Python API 无可用 `.export()`），
  再用 Pillow 从基准尺寸（常 256）生成 `appicon_16/32/75/128.png`，`appicon.ico` 补成
  16/32/48/256。验证：对生成的 `*Portable.exe` 再抽一次应得非空 ico。
- **PAL 多目录同名重定向冲突**：DOpus 要带 `%APPDATA%/%LOCALAPPDATA%/%PROGRAMDATA%\GPSoftware`，
  若 `[Directories]` 三条都省略左侧名，PAL 会用目录名当 Data 子目录名 → 三个同名互相覆盖，
  `Data` 生不出来、配置搬不回去。必须给每条唯一名（`AppDataGPSoftware=%APPDATA%\GPSoftware` 等）；
  另加 `[CloseEXE] EXE1=dopusd.exe` 释放文件锁，否则退出时搬回失败。
- **Installer 硬性预检 `help.html`**：Installer（2026-08-18 更新后）要求 `Apps/<app>/help.html`
  存在于 **app 根目录**，缺失则秒退、不产 paf，日志 `ERROR: No help.html in <appdir>`；
  `Other/Help/help.html` 是给 Platform「帮助」菜单用的，两者并存。
- **AppFile 复制剔除项**：`*.bak`、Inno 残留 `unins000.exe/.dat/.msg`、Scoop 元数据
  `install.json`/`manifest.json`、破解残留（`crack/`、`*patcher.exe`）。
- **FlyingBird 二进制来源**：`D:\Scoop\apps\flyingbird\current`（随 `scoop update` 升级；
  升级时同步改 appinfo 的 `DisplayVersion`/`PackageVersion`，paf 名取 DisplayVersion）。
  只拷程序文件，别拷 `current` 软链本身或 `manifest.json`。
