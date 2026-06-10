import sys
import os
import re
import shutil
import subprocess
import urllib.request
BASE_DIR = "run"
SMALI_DIR = "classes_smali"
ORIG_DEX = "classes.dex"
OUT_DEX = "classes.dex"
MAP_FILE = os.path.join(BASE_DIR, "mapping.txt")
TEMP_FILE = os.path.join(BASE_DIR, "temp.txt")
TREE_FILE = os.path.join(BASE_DIR, "tree.txt")
DICT_FILE = "dictionary.txt"
BAKSMALI_JAR = os.path.join(BASE_DIR, "baksmali-2.5.2.jar")
SMALI_JAR = os.path.join(BASE_DIR, "smali-2.5.2.jar")
URL_BAKSMALI = "https://bitbucket.org/JesusFreke/smali/downloads/baksmali-2.5.2.jar"
URL_SMALI = "https://bitbucket.org/JesusFreke/smali/downloads/smali-2.5.2.jar"
def download_jar():
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(BAKSMALI_JAR):
        print(f"下载 baksmali-2.5.2.jar（1.22MB） 到 {BASE_DIR}...")
        urllib.request.urlretrieve(URL_BAKSMALI, BAKSMALI_JAR)
    if not os.path.exists(SMALI_JAR):
        print(f"下载 smali-2.5.2.jar（943.03KB） 到 {BASE_DIR}...")
        urllib.request.urlretrieve(URL_SMALI, SMALI_JAR)
def dex2smali(dex_path, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    print(f"反编译：{dex_path} → {out_dir}")
    subprocess.run(
        ["java", "-jar", BAKSMALI_JAR, "d", dex_path, "-o", out_dir],
        check=True
    )
    print("反编译完成")
def smali2dex(smali_dir, dex_path):
    print(f"编译：{smali_dir} → {dex_path}")
    subprocess.run(
        ["java", "-jar", SMALI_JAR, "a", smali_dir, "-o", dex_path],
        check=True
    )
    print("编译完成")
def load_used_full():
    if not os.path.exists(TEMP_FILE):
        return set()
    with open(TEMP_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())
def save_used_full(used):
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        for name in sorted(used):
            f.write(name + "\n")
def next_fragment(dict_list, used_frag):
    idx = 0
    while True:
        for name in dict_list:
            cand = name if idx == 0 else f"{name}{idx}"
            if cand not in used_frag:
                used_frag.add(cand)
                return cand
        idx += 1
def scan_smali_classes():
    classes = []
    for root, _, files in os.walk(SMALI_DIR):
        for f in files:
            if f.endswith(".smali"):
                rel = os.path.relpath(os.path.join(root, f), SMALI_DIR)
                cls = rel.replace(".smali", "").replace(os.sep, "/")
                classes.append(f"L{cls};")
    return sorted(list(set(classes)))
def gen_mapping(classes, app_package):
    pkg_path = app_package.replace(".", "/") + "/"
    with open(DICT_FILE, "r", encoding="utf-8") as f:
        dict_list = [line.strip() for line in f if line.strip()]
    used_full = load_used_full()
    used_frag = set()
    chain_map = {}
    num_pattern = re.compile(r'^\d+$')
    mapping_lines = []
    all_chains = set()
    for old_full in classes:
        old_stripped = old_full[1:-1]
        if "/" in old_stripped:
            _, cls = old_stripped.rsplit("/", 1)
        else:
            cls = old_stripped
        tokens = re.split(r'(\$+)', cls)
        parts = [p for p in tokens[0::2] if p]
        for i in range(len(parts)):
            if i == len(parts)-1 and num_pattern.match(parts[i]):
                continue
            chain = "$".join(parts[:i+1])
            all_chains.add(chain)
    for chain in sorted(all_chains):
        chain_map[chain] = next_fragment(dict_list, used_frag)
    for old_full in classes:
        old_stripped = old_full[1:-1]
        if "/" in old_stripped:
            pkg, cls = old_stripped.rsplit("/", 1)
            pkg += "/"
        else:
            pkg = ""
            cls = old_stripped
        tokens = re.split(r'(\$+)', cls)
        seps = [s for s in tokens[1::2] if s]
        parts = [p for p in tokens[0::2] if p]
        new_parts = []
        for i, part in enumerate(parts):
            if i == len(parts)-1 and num_pattern.match(part):
                new_parts.append(part)
                continue
            chain = "$".join(parts[:i+1])
            new_parts.append(chain_map[chain])
        new_cls = ""
        for i in range(len(new_parts)):
            new_cls += new_parts[i]
            if i < len(seps):
                new_cls += seps[i]
        new_full = f"L{pkg_path}{new_cls};"
        idx = 1
        while new_full in used_full:
            new_cls += str(idx)
            new_full = f"L{pkg_path}{new_cls};"
            idx += 1
        used_full.add(new_full)
        mapping_lines.append(f"{old_full}->{new_full}\n")
    mapping_lines.sort(key=lambda x: len(x))
    new_classes = [line.split("->")[-1].strip() for line in mapping_lines]
    if len(new_classes) != len(set(new_classes)):
        print("错误：类名重复")
        sys.exit(1)
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        f.writelines(mapping_lines)
    save_used_full(used_full)
    print(f"mapping.txt生成完成")
def obfuscate_smali(smali_root):
    text_rules = []
    path_map = {}
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "->" not in line:
                continue
            old_full, new_full = line.split("->")
            text_rules.append((old_full, new_full))
            old_raw = old_full.lstrip("L").rstrip(";")
            new_raw = new_full.lstrip("L").rstrip(";")
            path_map[old_raw] = new_raw
    print("替换类引用")
    for root, _, files in os.walk(smali_root):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            f_path = os.path.join(root, fname)
            with open(f_path, "r", encoding="utf-8") as fp:
                content = fp.read()
            for old_s, new_s in text_rules:
                content = content.replace(old_s, new_s)
            with open(f_path, "w", encoding="utf-8") as fp:
                fp.write(content)
    print("重命名+移动文件")
    for root, _, files in os.walk(smali_root):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            rel_path = os.path.relpath(root, smali_root)
            curr_raw = (fname[:-6] if rel_path == "." else os.path.join(rel_path, fname[:-6])).replace(os.sep, "/")
            if curr_raw not in path_map:
                continue
            target_raw = path_map[curr_raw]
            target_parts = target_raw.split("/")
            target_cls = target_parts[-1]
            target_dir = os.path.join(smali_root, *target_parts[:-1])
            os.makedirs(target_dir, exist_ok=True)
            old_file = os.path.join(root, fname)
            new_file = os.path.join(target_dir, f"{target_cls}.smali")
            if old_file != new_file:
                os.rename(old_file, new_file)
    print("清理空目录")
    for root, dirs, _ in os.walk(smali_root, topdown=False):
        for d in dirs:
            d_path = os.path.join(root, d)
            if not os.listdir(d_path):
                os.rmdir(d_path)
    print("混淆即将完成")
def main():
    if len(sys.argv) != 2:
        print("用法：python dexobf.py 包名")
        return
    if not os.path.exists(ORIG_DEX):
        print(f"错误：缺少 {ORIG_DEX}")
        return
    if not os.path.exists(DICT_FILE):
        print(f"错误：缺少 {DICT_FILE}")
        return
    download_jar()
    app_package = sys.argv[1]
    os.makedirs(BASE_DIR, exist_ok=True)
    dex2smali(ORIG_DEX, SMALI_DIR)
    classes = scan_smali_classes()
    if not classes:
        print("未扫描到任何类，dex 可能为空或损坏")
        return
    with open(TREE_FILE, "w", encoding="utf-8") as f:
        for c in classes:
            f.write(c + "\n")
    print(f"共 {len(classes)} 个类")
    gen_mapping(classes, app_package)
    obfuscate_smali(SMALI_DIR)
    smali2dex(SMALI_DIR, OUT_DEX)
    if os.path.exists(SMALI_DIR):
        shutil.rmtree(SMALI_DIR)
    print(f"全部完成！输出：{OUT_DEX}")
if __name__ == "__main__":
    main()
