
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
    - TotalCommander   11.51.0.0
    - XShellPlus       8.0.0.9

- Template
    - [Template_3.9.0](https://downloads.sourceforge.net/portableapps/PortableApps.com_Application_Template_3.9.0.zip)


### 命令行
```cmd
cmd /c .\PortableApps.comLauncherGenerator.exe E:\xk\Code\xkyii\PortableApps\Apps\RapidEE
cmd /c .\PortableApps.comInstaller.exe E:\xk\Code\xkyii\PortableApps\Apps\RapidEE
```

### 计算SHA256
```cmd
certutil -hashfile filename SHA256
```

## 多启动器
- [Using the launcher generator to generate multiple app launchers](https://portableapps.com/node/65720)

这里提到, `PA.c Launcher`只支持单`Launcher`, 只有`LibreOffice`和`OpenOffice`是例外.