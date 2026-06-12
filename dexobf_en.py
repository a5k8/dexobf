import sys
import os
import re
import shutil
import subprocess
BASE_DIR = "run"
SMALI_DIR = "classes_smali"
ORIG_DEX = "classes.dex"
MAP_FILE = os.path.join(BASE_DIR, "mapping.txt")
TREE_FILE = os.path.join(BASE_DIR, "tree.txt")
DICT_FILE = "dictionary.txt"
BAKSMALI_JAR = "baksmali.jar"
SMALI_JAR = "smali.jar"
def clean_cache():
    os.makedirs(BASE_DIR, exist_ok=True)
    for f in [MAP_FILE, TREE_FILE]:
        if os.path.exists(f):
            os.remove(f)
def dex2smali(dex_path, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    print("Decompiling......")
    try:
        subprocess.run(
            ["java", "-jar", BAKSMALI_JAR, "d", dex_path, "-o", out_dir],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Decompilation failed: {e}")
        sys.exit(1)
    print("Decompilation completed")
def smali2dex(smali_dir, dex_path):
    print("Compiling......")
    try:
        subprocess.run(
            ["java", "-jar", SMALI_JAR, "a", smali_dir, "-o", dex_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)
    print("Compilation completed")
def load_dictionary(dict_path="dictionary.txt"):
    if not os.path.exists(dict_path):
        print(f"Error! {dict_path} not found")
        sys.exit(1)
    dict_list = []
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:
                dict_list.append(name)
    if not dict_list:
        print("Error! No valid names in dictionary.txt")
        sys.exit(1)
    print(f"Dictionary loaded, {len(dict_list)} valid names total")
    return dict_list
def scan_smali_classes():
    classes = []
    for root, _, files in os.walk(SMALI_DIR):
        for f in files:
            if f.endswith(".smali"):
                rel = os.path.relpath(os.path.join(root, f), SMALI_DIR)
                cls = rel.replace(".smali", "").replace(os.sep, "/")
                classes.append(f"L{cls};")
    classes = list(set(classes))
    classes.sort()
    return classes
def gen_mapping(classes, app_package, dict_list):
    pkg_path = app_package.replace(".", "/") + "/"
    chain_map = {}
    dict_ptr = 0
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
        if dict_ptr >= len(dict_list):
            print("Error! Insufficient dictionary entries, please expand dictionary.txt")
            sys.exit(1)
        chain_map[chain] = dict_list[dict_ptr]
        dict_ptr += 1
    for old_full in classes:
        old_stripped = old_full[1:-1]
        if "/" in old_stripped:
            _, cls = old_stripped.rsplit("/", 1)
        else:
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
        mapping_lines.append(f"{old_full}->{new_full}\n")
    mapping_lines.sort(key=lambda x: len(x))
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        f.writelines(mapping_lines)
    print("mapping.txt generated")
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
    print("Replacing class references......")
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
    print("Renaming and moving files......")
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
    print("Cleaning empty directories......")
    for root, dirs, _ in os.walk(smali_root, topdown=False):
        for d in dirs:
            d_path = os.path.join(root, d)
            if not os.listdir(d_path):
                os.rmdir(d_path)
    print("Obfuscation nearly complete")
def main():
    clean_cache()
    if len(sys.argv) != 2:
        print("Usage: python dexobf.py <package_name>")
        return
    if not os.path.exists(ORIG_DEX):
        print(f"Error! {ORIG_DEX} missing")
        return
    if not os.path.exists(DICT_FILE):
        print(f"Error! {DICT_FILE} missing")
        return
    app_package = sys.argv[1]
    os.makedirs(BASE_DIR, exist_ok=True)
    dex2smali(ORIG_DEX, SMALI_DIR)
    dict_list = load_dictionary()
    classes = scan_smali_classes()
    if not classes:
        print("Error! No classes found")
        return
    with open(TREE_FILE, "w", encoding="utf-8") as f:
        for c in classes:
            f.write(c + "\n")
    print(f"Total {len(classes)} classes")
    gen_mapping(classes, app_package, dict_list)
    obfuscate_smali(SMALI_DIR)
    smali2dex(SMALI_DIR, ORIG_DEX)
    if os.path.exists(SMALI_DIR):
        shutil.rmtree(SMALI_DIR)
    print(f"Completed! Output: {ORIG_DEX}")
if __name__ == "__main__":
    main()
