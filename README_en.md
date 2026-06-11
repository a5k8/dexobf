## dexobf
DEX class name obfuscator (Python)
[简体中文](https://github.com/a5k8/dexobf/blob/8c9fbce6cf0be9d165e5c8749620c84e2299a2c7/README.md)
## Description
Move all classes in DEX files to the designated package for obfuscation and rename all class names. All generated files will be stored in the `/dexobf` directory.
## Environment Setup
This tool requires **Python, Git, Java 8+**. Run the commands below if they are not installed:
```bash
# Debian / Ubuntu
 sudo apt update && sudo apt install python3 git openjdk-8-jdk -y
 # CentOS / RHEL
 sudo yum install python3 git java-1.8.0-openjdk -y
 # Windows (PowerShell, admin)
 winget install Python.Python.3 Git.Git AdoptOpenJDK.AdoptOpenJDK.8
 # macOS
 brew install python3 git adoptopenjdk8
 # Termux (Android)
 pkg update && pkg install python git openjdk-17
```
## Usage
Put `classes.dex` into the project root directory first, then run the commands below:
```bash
git clone https://github.com/a5k8/dexobf.git
cd dexobf
# Linux / macOS
python3 dexobf.py #Example: python3 dexobf.py app.package
# Windows / Termux
python dexobf.py #Example: python dexobf.py app.package
```
After obfuscation, please update class names in `AndroidManifest.xml`. You can find the original and new class name mappings in `dexobf/mapping.txt`.
## Directory Structure
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
## Notice
This project is for learning purposes only. Do not use it for illegal activities.
