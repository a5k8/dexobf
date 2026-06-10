## dexobf
DEX class name obfuscator (Python)

## Description
Move all classes in DEX files to the designated package for obfuscation and rename all class names. All generated files will be stored in the `/run` directory.

## Environment Setup
This tool requires Python and Git. Run the commands below if they are not installed:
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
## Usage
Put classes.dex into the project root directory first, then run the commands below:
```bash
git clone https://github.com/a5k8/dexobf.git
cd dexobf
python3 dexobf.py  # Linux / macOS |such as python3 dexobf.py app.package
or
python dexobf.py  # Windows / Termux |such as python dexobf.py app.package
```
## Directory Structure
dexobf/
├── dexobf.py
├── dictionary.txt
├── classes.dex
├── .gitignore
└── README.md
## Notice
This project is for learning purposes only. Do not use it for illegal activities.
