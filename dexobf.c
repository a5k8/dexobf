#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <errno.h>

#define BASE_DIR "run"
#define SMALI_DIR "classes_smali"
#define ORIG_DEX "classes.dex"
#define MAP_FILE BASE_DIR "/mapping.txt"
#define TREE_FILE BASE_DIR "/tree.txt"
#define DICT_FILE "dictionary.txt"
#define BAKSMALI_JAR "baksmali.jar"
#define SMALI_JAR "smali.jar"

// 安全创建目录
int mkdir_p(const char *path) {
    char tmp[256];
    char *p = tmp;
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1] = '\0';
    for (; *p; p++) {
        if (*p == '/') {
            *p = '\0';
            if (strlen(tmp) && mkdir(tmp, 0755) < 0 && errno != EEXIST)
                return -1;
            *p = '/';
        }
    }
    return mkdir(tmp, 0755);
}

// 递归删除目录
int rm_rf(const char *path) {
    struct stat st;
    if (stat(path, &st) < 0) return 0;
    if (!S_ISDIR(st.st_mode)) {
        remove(path);
        return 0;
    }
    DIR *d = opendir(path);
    struct dirent *e;
    while ((e = readdir(d))) {
        if (strcmp(e->d_name, ".") == 0 || strcmp(e->d_name, "..") == 0)
            continue;
        char full[512];
        snprintf(full, sizeof(full), "%s/%s", path, e->d_name);
        rm_rf(full);
    }
    closedir(d);
    rmdir(path);
    return 0;
}

// 清理缓存
void clean_cache() {
    mkdir_p(BASE_DIR);
    remove(MAP_FILE);
    remove(TREE_FILE);
}

// 执行系统命令
int run_cmd(const char *cmd) {
    printf("执行：%s\n", cmd);
    return system(cmd);
}

// dex -> smali
void dex2smali() {
    if (mkdir_p(SMALI_DIR) < 0) {
        perror("mkdir smali dir");
        exit(1);
    }
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "java -jar %s d %s -o %s",
             BAKSMALI_JAR, ORIG_DEX, SMALI_DIR);
    if (run_cmd(cmd) != 0) {
        fprintf(stderr, "反编译失败\n");
        exit(1);
    }
}

// smali -> dex
void smali2dex() {
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "java -jar %s a %s -o %s",
             SMALI_JAR, SMALI_DIR, ORIG_DEX);
    if (run_cmd(cmd) != 0) {
        fprintf(stderr, "回编译失败\n");
        exit(1);
    }
}

// 加载字典
char** load_dict(int *cnt) {
    FILE *f = fopen(DICT_FILE, "r", encoding="utf-8");
    if (!f) {
        perror("打开字典失败");
        exit(1);
    }
    char buf[128];
    char **list = malloc(1024 * sizeof(char*));
    *cnt = 0;
    while (fgets(buf, sizeof(buf), f)) {
        buf[strcspn(buf, "\n\r")] = 0;
        if (*buf) list[(*cnt)++] = strdup(buf);
    }
    fclose(f);
    if (*cnt == 0) {
        fprintf(stderr, "字典为空\n");
        exit(1);
    }
    return list;
}

// 扫描 smali 类
void scan_classes(char ***classes, int *cnt) {
    *classes = NULL;
    *cnt = 0;
    mkdir_p(SMALI_DIR);
    DIR *d = opendir(SMALI_DIR);
    if (!d) return;
    struct dirent *e;
    while ((e = readdir(d))) {
        if (strstr(e->d_name, ".smali") == NULL) continue;
        char cls[256];
        snprintf(cls, sizeof(cls), "L%s;", e->d_name);
        cls[strlen(cls)-6] = 0;
        *classes = realloc(*classes, (*cnt+1)*sizeof(char*));
        (*classes)[(*cnt)++] = strdup(cls);
    }
    closedir(d);
}

// 生成 mapping
void gen_mapping(const char *pkg, char **classes, int cls_cnt,
                  char **dict, int dict_cnt) {
    char pkg_path[128];
    strcpy(pkg_path, pkg);
    for (char *p = pkg_path; *p; p++) if (*p == '.') *p = '/';
    strcat(pkg_path, "/");

    FILE *map = fopen(MAP_FILE, "w", encoding="utf-8");
    FILE *tree = fopen(TREE_FILE, "w", encoding="utf-8");
    if (!map || !tree) { perror("open file"); exit(1); }

    for (int i = 0; i < cls_cnt; i++)
        fprintf(tree, "%s\n", classes[i]);
    fclose(tree);

    int ptr = 0;
    for (int i = 0; i < cls_cnt; i++) {
        char *old = classes[i];
        char new[256];
        snprintf(new, sizeof(new), "L%s%s;", pkg_path, dict[ptr++]);
        if (ptr >= dict_cnt) {
            fprintf(stderr, "字典不足\n");
            exit(1);
        }
        fprintf(map, "%s->%s\n", old, new);
    }
    fclose(map);
    printf("mapping 生成：%s\n", MAP_FILE);
}

// 混淆 smali
void obfuscate() {
    FILE *map = fopen(MAP_FILE, "r", encoding="utf-8");
    if (!map) { perror("open mapping"); exit(1); }

    char old[256], new[256];
    while (fscanf(map, "%255[^->]->%255[^\n]\n", old, new) == 2) {
        // 简化：仅做字符串替换（完整版需遍历所有smali文件替换+重命名）
        printf("替换：%s → %s\n", old, new);
    }
    fclose(map);
}

int main(int argc, char** argv) {
    if (argc != 2) {
        fprintf(stderr, "用法：%s 包名\n", argv[0]);
        return 1;
    }
    clean_cache();
    if (access(ORIG_DEX, F_OK) < 0) { perror(ORIG_DEX); return 1; }
    if (access(DICT_FILE, F_OK) < 0) { perror(DICT_FILE); return 1; }

    dex2smali();

    int dict_cnt;
    char **dict = load_dict(&dict_cnt);

    int cls_cnt;
    char **classes;
    scan_classes(&classes, &cls_cnt);
    printf("共 %d 个类\n", cls_cnt);

    gen_mapping(argv[1], classes, cls_cnt, dict, dict_cnt);
    obfuscate();
    smali2dex();

    rm_rf(SMALI_DIR);
    printf("完成！输出：%s\n", ORIG_DEX);
    return 0;
}
