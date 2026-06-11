## dex混淆
dex类名混淆工具（Python）
[English](https://github.com/a5k8/dexobf/blob/master/README_en.md)
## 说明
把dex中的所有类都放到指定包名下以混淆，同时进行类名混淆，运行产生的文件统一存放至 `dexobf/run/` 目录。
## 环境部署
本工具依赖 **Python、Git、Java 8+**，未安装请根据对应系统执行以下命令：
```bash
# Debian / Ubuntu
sudo apt update && sudo apt install python3 git openjdk-8-jdk -y
# CentOS / RHEL
sudo yum install python3 git java-1.8.0-openjdk -y
# Windows（PowerShell，需管理员）
winget install Python.Python.3 Git.Git AdoptOpenJDK.AdoptOpenJDK.8
# macOS
brew install python3 git adoptopenjdk8
# Termux（Android）
pkg update && pkg install python git openjdk-17
```
## 使用方法
请先将 `classes.dex` 放置到 `dexobf/` ，再执行以下命令：
```bash
git clone https://github.com/a5k8/dexobf.git
cd dexobf
# Linux / macOS
python3 dexobf.py 指定包名 # 如 python3 dexobf.py app.package
# Windows / Termux
python dexobf.py 指定包名 # 如 python dexobf.py app.package
```
混淆完成后，需同步替换 `AndroidManifest.xml` 中的类名，新旧类名对应关系可在 `dexobf/run/mapping.txt` 中查看检索。
## 目录结构
```
dexobf/
├── dexobf.py
├── dictionary.txt
├── baksmali-2.5.2.jar
├── smali-2.5.2.jar
├── .gitignore
├── README.md
└── README_en.md
```
## 声明
本项目仅供学习交流，请勿用于非法用途。
