## dexobf
dex类名混淆工具（Python）
[English](https://github.com/a5k8/dexobf)
## 说明
把dex中的所有类都放到指定包名下以混淆，同时进行类名混淆，运行产生的文件统一存放至 `/run` 目录。
## 环境部署
本工具依赖 Python，若未安装python，根据对应系统执行安装命令：
```bash
# Debian / Ubuntu
sudo apt update && sudo apt install python3 git
# CentOS / RHEL
sudo yum install python3 git
# Windows (PowerShell)
winget install Python.Python.3 Git.Git
# macOS
brew install python3 git
# Termux (Android)
pkg update && pkg install python git
```
## 使用方法
请先将 classes.dex 放置到项目根目录，再执行以下命令：
```bash
git clone https://github.com/a5k8/dexobf.git
cd dexobf
python3 dexobf.py 指定包名 # Linux / macOS 如 python3 dexobf.py app.package
或
python dexobf.py 指定包名 # Windows / Termux 如 python dexobf.py app.package
```
##目录结构
dexobf/
├── dexobf.py
├── dictionary.txt
├── classes.dex
├── .gitignore
└── README.md
## 声明
本项目仅供学习交流，请勿用于非法用途。
