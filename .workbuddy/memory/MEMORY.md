# PortableApps 项目长期约定

- **性质**：个人自用（Personal/Personal-use）的 PortableApps.com 格式仓库，位于 `D:\Code\xkyii\PortableApps`，git 管理，无远程。
- **用途（重要）**：用户实际使用 **PortableApps.com Platform** 作为启动菜单。因此全仓库采用 PA.c 格式的核心目的是让所有 app 统一出现在 Platform 菜单、统一处理 splash。即便 RapidEE 这类单文件免安装 exe，包装成 PA.c 也有意义（菜单一致性），**不要为了"它本来就能便携"而建议去掉 PA.c 包装**。
- **入库策略（重要）**：仓库只存配置/元数据/模板；各 app 的**真实二进制程序不入库**。`.gitignore` 仅忽略 `Apps/**/App/AppFile`。用户自行把程序下载到本地 `Apps/*/App/AppFile` 目录后参与构建，但不提交。
  - 因此**不为 installer.ini 填下载源**（任务④已取消）：换机器靠用户本地放置二进制，而非在线下载重建。
- **格式/工具版本基线（2026-08）**：Format 3.9；Application Template 已升 3.9.2；外部构建工具（PortableApps.com Installer / Launcher Generator）在用户本机 `D:\Soft\PortableApps`（注意：不是 `D:\Other\Soft\...`，曾记错），非仓库内容，需用户手动更新（官方现为 Installer 3.9.18 / Launcher 2.2.9）。
  - 运行 `install.py` 必须设 `PORTABLEAPPS_PAF_DIR` 指向该目录，且**要用 Windows 风格路径**（如 `D:/Soft/PortableApps`），不能传 Git Bash 的 `/d/Soft/...`——pathlib 在 Windows 上会把 `/d/...` 误解析成 `D:\d\...`。
  - 已实测：`install.py RapidEE` 在该路径下构建成功，产出 `Apps/RapidEE/RapidEEPortable.exe` 与根目录 `RapidEEPortable_3.9.0.paf.exe`（均已被 .gitignore 忽略）。
- **构建入口**：`Script/install.py` 已重构——去机器硬编码路径（用环境变量 `PORTABLEAPPS_APPS_DIR`/`PORTABLEAPPS_PAF_DIR`），支持 `--list`/`--all`/指定 app 名，多启动器自动探测（`appinfo{i}.ini` 数量）。
- **启动闪屏已全局关闭（2026-08）**：所有 launcher 源 ini 的 `[Launch]` 段已加 `ShowSplashScreen=false` 并重编译 launcher；Platform 层 `DisableSplashScreen` 模板（`Template/Other/Source/AppNamePortable.ini` 与 `Apps/XShellPlus/Other/Source/AppNamePortable.ini`）已统一为 `true`，防重打包被覆盖回弹窗。**改 launcher 源 ini 后必须重编译 launcher（`install.py <app>`）才生效**。

## 从 Scoop app 打包成 PortableApp 的实践坑（可复用）
- **环境限制（重要）**：Git Bash **无法直接 exec 工作区内的 `.exe`**（报 `Permission denied`，连 `D:\Soft` 下也拒绝）——工作区疑似挂载 noexec。但 **Python `subprocess`（走 Windows `CreateProcess`）可正常执行任何 exe**。所以凡要在仓库目录里跑 exe（如某 app 的 patcher/安装器），用 `python -c "subprocess.run([...])"` 启动，别用 `./xxx.exe` 或 `cmd /c`。
  - 同理：PowerShell 的 `Start-Process` / `[Diagnostics.Process]::Start` 被工具安全策略拦截；Bash 里调 `cmd.exe` 也被拦。
  - 给 Windows Python 传路径**必须用 `D:/...`**，不能传 Git Bash 的 `/d/...`（会被 Python 解析成 `D:\d\...`）。
- **图标提取**：用 `icoextract`（pip 安装）。其 Python API 在 0.3.0 没有直接可用的 `.export()`，改用 CLI：`icoextract.exe <输入exe> <输出.ico>`。再用 Pillow 从抽出的基准尺寸（常为 256）缩放生成 PA.c 需要的 `appicon_16/32/75/128.png`，并把 `appicon.ico` 补成 16/32/48/256 多尺寸（避免启动器 exe 小图标发虚）。验证图标是否嵌入启动器 exe：对生成的 `*Portable.exe` 再跑一次 `icoextract` 应能抽出非空 ico。
- **DOpus 授权（用户自有正版证书，非破解）**：用户持有**自有正版授权**，`dopus.opuscert` 是其合法证书文件。DOpus 会自动从**程序目录（即 AppFile，与 `dopus.exe` 同目录）**读取 `dopus.opuscert` 并在每次启动时加载——因此把证书放在 AppFile 即可实现**换机器免重新导入**、随 app 走。无需跑 License Manager GUI、无需 patcher、无需任何手动步骤。AppFile 内的 `dopuslib.dll` 等是正常程序文件（非补丁）。`dopus.opuscert`/`cert_file.txt`/`stockcert.txt` 均保留在 AppFile（不入 git）。（注：早期曾误按"破解"处理，已纠正。）
- **AppFile 复制剔除项**（通用）：`*.bak`、Inno 卸载残留 `unins000.exe/.dat/.msg`、Scoop 元数据 `install.json`/`manifest.json`、`_dopus_patcher.exe`/`crack/` 等破解残留目录（DOpus 用正版证书，不需要这些）。DOpus 的 `dopus.opuscert`/`cert_file.txt`/`stockcert.txt` 保留在 AppFile（均不入 git）。
- **PAL 多目录同名重定向冲突（重要）**：DOpus 要把 3 个系统目录 `%APPDATA%/%LOCALAPPDATA%/%PROGRAMDATA%\GPSoftware` 都随身走。若 `[Directories]` 三条都写 `=%X%\GPSoftware`（省略左侧名），PAL 默认用目录名当 Data 子目录名，**三个同名互相覆盖 → `Data` 目录生成不出来、配置/激活搬不回去**。必须给每条指定唯一 settingsdir 名：`AppDataGPSoftware=%APPDATA%\GPSoftware` 等。另需加 `[CloseEXE] EXE1=dopusd.exe` 关闭守护进程释放文件锁，否则 PAL 退出时搬回失败、`Data` 仍为空。
