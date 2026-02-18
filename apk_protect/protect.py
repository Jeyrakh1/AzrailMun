#!/usr/bin/env python3
"""
Полная защита APK от декомпиляции:
- Обфускация пакета и всех классов через smali
- Анти-отладка и анти-декомпиляция
- Скрытие имён исходников
"""

import os
import re
import shutil
import random
import string
from pathlib import Path

DECOMPILED_DIR = "koyo_decompiled"
OUTPUT_DIR = "koyo_protected"
SMALI_DIRS = ["smali", "smali_classes2", "smali_classes3", "smali_classes4", "smali_classes5"]

EXCLUDE_PREFIXES = (
    "Landroid/", "Ljava/", "Ljavax/", "Ldalvik/", "Lkotlin/",
    "Lkotlinx/", "Lorg/json/", "Lorg/xml/", "Lorg/w3c/",
    "Landroidx/", "Lcom/google/", "Lokhttp3/", "Lretrofit2/",
    "Lcom/squareup/", "Lorg/conscrypt/", "Lorg/bouncycastle/",
    "Lorg/openjsse/", "Lorg/apache/", r"Lj\$/"
)

# Маппинг компонентов Android (должны быть в манифесте)
MANIFEST_CLASSES = {
    "MainActivity": "a", "SmsReceiver": "b", "MmsReceiver": "c",
    "SendSmsService": "d", "ComposeSmsActivity": "e",
    "BuildConfig": "f", "SyncForegroundService": "g",
    "HeartbeatForegroundService": "h", "AlarmReceiver": "i",
    "BootReceiver": "j", "SyncScheduler": "k"
}

def random_ident(length=8):
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))

def build_full_mapping(smali_base):
    """Построить полный маппинг для пакета com.xzaqp5om.vou6y1dd"""
    app_package = "com/xzaqp5om/vou6y1dd"
    new_package = "a/b/c/d"
    mapping = {}
    used_names = set(MANIFEST_CLASSES.values())
    
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if not smali_path.exists():
            continue
        app_dir = smali_path / "com" / "xzaqp5om" / "vou6y1dd"
        if not app_dir.exists():
            continue
            
        for smali_file in app_dir.rglob("*.smali"):
            rel = smali_file.relative_to(app_dir)
            class_name = rel.stem
            base_class = class_name.split("$")[0]
            
            if base_class in MANIFEST_CLASSES:
                new_name = MANIFEST_CLASSES[base_class]
            else:
                while True:
                    new_name = random_ident(8)
                    if new_name not in used_names:
                        used_names.add(new_name)
                        break
            
            if "$" in class_name:
                new_name += "$" + "$".join(class_name.split("$")[1:])
            
            full_old = "L" + app_package + "/" + class_name.replace("$", "/$") if "$" in class_name else "L" + app_package + "/" + class_name
            if "/$" in full_old:
                full_old = "L" + app_package + "/" + class_name
            full_old = "L" + app_package + "/" + class_name
            full_new = "L" + new_package + "/" + new_name
            
            mapping[full_old] = full_new
            
            # Внутренние классы
            if "$" in class_name:
                inner_old = "L" + app_package + "/" + base_class + "$" + "$".join(class_name.split("$")[1:])
                inner_new = "L" + new_package + "/" + MANIFEST_CLASSES.get(base_class, mapping.get("L" + app_package + "/" + base_class, "L" + new_package + "/" + random_ident(8))[-9:-1]) + "$" + "$".join(class_name.split("$")[1:])
                if base_class in MANIFEST_CLASSES:
                    inner_new = "L" + new_package + "/" + MANIFEST_CLASSES[base_class] + "$" + "$".join(class_name.split("$")[1:])
                mapping[full_old] = full_new
    
    # Добавляем подпакеты (sync и т.д.)
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if not smali_path.exists():
            continue
        for subdir in (smali_path / "com" / "xzaqp5om" / "vou6y1dd").iterdir():
            if subdir.is_dir():
                for smali_file in subdir.rglob("*.smali"):
                    rel = smali_file.relative_to(smali_path / "com" / "xzaqp5om" / "vou6y1dd")
                    parts = str(rel).replace("\\", "/").replace(".smali", "").split("/")
                    class_name = parts[-1]
                    base_class = class_name.split("$")[0]
                    
                    new_name = MANIFEST_CLASSES.get(base_class, random_ident(8))
                    if new_name in MANIFEST_CLASSES.values() and base_class not in MANIFEST_CLASSES:
                        new_name = random_ident(8)
                    if base_class not in MANIFEST_CLASSES:
                        used_names.add(new_name)
                    
                    if "$" in class_name:
                        new_name += "$" + "$".join(class_name.split("$")[1:])
                    
                    full_old = "L" + "com/xzaqp5om/vou6y1dd/" + str(rel).replace("\\", "/").replace(".smali", ";").replace(";", "")
                    full_old = "Lcom/xzaqp5om/vou6y1dd/" + str(rel).replace("\\", "/").replace(".smali", "")
                    full_new = "La/b/c/d/" + new_name
                    mapping["L" + full_old] = full_new + ";" if not full_new.endswith(";") else full_new
                    mapping[full_old] = full_new
    
    return mapping

def build_simple_mapping(smali_base):
    """Простой маппинг: пакет + все классы приложения"""
    app_package = "com/xzaqp5om/vou6y1dd"
    new_package = "a/b/c/d"
    mapping = {}
    used = set()
    
    def get_new_name(base):
        if base in MANIFEST_CLASSES:
            return MANIFEST_CLASSES[base]
        n = random_ident(8)
        while n in used:
            n = random_ident(8)
        used.add(n)
        return n
    
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if not smali_path.exists():
            continue
        base_path = smali_path / "com" / "xzaqp5om" / "vou6y1dd"
        if not base_path.exists():
            continue
            
        for smali_file in base_path.rglob("*.smali"):
            rel = smali_file.relative_to(base_path)
            path_str = str(rel).replace("\\", "/")
            class_name = path_str.replace(".smali", "")
            base_class = class_name.split("$")[0]
            
            new_name = get_new_name(base_class)
            if "$" in class_name:
                new_name += "$" + "$".join(class_name.split("$")[1:])
            
            full_old = "Lcom/xzaqp5om/vou6y1dd/" + path_str.replace(".smali", "")
            full_new = "La/b/c/d/" + new_name
            mapping[full_old] = full_new
    
    return mapping

def apply_mapping(content, mapping):
    """Применить маппинг к содержимому"""
    # Сортируем по длине (длинные первыми)
    for old_name, new_name in sorted(mapping.items(), key=lambda x: -len(x[0])):
        content = content.replace(old_name, new_name)
    # Строковый формат com.xzaqp5om.vou6y1dd
    content = content.replace("com.xzaqp5om.vou6y1dd", "a.b.c.d")
    return content

def process_all_files(smali_base, mapping):
    """Обработать все файлы"""
    count = 0
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if smali_path.exists():
            for f in smali_path.rglob("*.smali"):
                try:
                    c = f.read_text(encoding='utf-8', errors='ignore')
                    nc = apply_mapping(c, mapping)
                    if nc != c:
                        f.write_text(nc, encoding='utf-8')
                        count += 1
                except Exception as e:
                    print(f"  Error {f}: {e}")
    
    for f in smali_base.rglob("*.xml"):
        try:
            c = f.read_text(encoding='utf-8', errors='ignore')
            nc = apply_mapping(c, mapping)
            nc = nc.replace("com.xzaqp5om.vou6y1dd", "a.b.c.d")
            for old, new in MANIFEST_CLASSES.items():
                nc = nc.replace("." + old, "." + new)
            nc = nc.replace("a.b.c.d.sync.g", "a.b.c.d.g").replace("a.b.c.d.sync.h", "a.b.c.d.h")
            nc = nc.replace("a.b.c.d.sync.i", "a.b.c.d.i").replace("a.b.c.d.sync.j", "a.b.c.d.j")
            if nc != c:
                f.write_text(nc, encoding='utf-8')
                count += 1
        except: pass
    
    return count

def move_smali_files(smali_base, mapping):
    """Переместить smali файлы в новую структуру согласно маппингу"""
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if not smali_path.exists():
            continue
        old_base = smali_path / "com" / "xzaqp5om" / "vou6y1dd"
        if not old_base.exists():
            continue
            
        new_base = smali_path / "a" / "b" / "c" / "d"
        new_base.mkdir(parents=True, exist_ok=True)
        
        for smali_file in list(old_base.rglob("*.smali")):
            rel = smali_file.relative_to(old_base)
            path_str = str(rel).replace("\\", "/")
            class_key = "Lcom/xzaqp5om/vou6y1dd/" + path_str.replace(".smali", "")
            
            if class_key in mapping:
                new_class = mapping[class_key]
                new_name = new_class.replace("La/b/c/d/", "").replace(";", "")
            else:
                base_class = rel.stem.split("$")[0]
                new_name = MANIFEST_CLASSES.get(base_class, random_ident(8))
                if "$" in rel.stem:
                    new_name += "$" + "$".join(rel.stem.split("$")[1:])
            
            new_path = new_base / (new_name + ".smali")
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(smali_file), str(new_path))
        
        for subdir in list(old_base.iterdir()):
            if subdir.is_dir():
                for smali_file in list(subdir.rglob("*.smali")):
                    rel = smali_file.relative_to(subdir)
                    parent_rel = smali_file.relative_to(old_base)
                    class_key = "Lcom/xzaqp5om/vou6y1dd/" + str(parent_rel).replace("\\", "/").replace(".smali", "")
                    
                    if class_key in mapping:
                        new_class = mapping[class_key]
                        new_name = new_class.replace("La/b/c/d/", "").replace(";", "")
                    else:
                        new_name = rel.stem
                    
                    new_path = new_base / (new_name + ".smali")
                    shutil.move(str(smali_file), str(new_path))
        
        try:
            shutil.rmtree(smali_path / "com")
        except: pass

def remove_source_directives(smali_base):
    """Удалить .source и .line"""
    for smali_dir in SMALI_DIRS:
        smali_path = smali_base / smali_dir
        if smali_path.exists():
            for f in smali_path.rglob("*.smali"):
                try:
                    c = f.read_text(encoding='utf-8', errors='ignore')
                    c = re.sub(r'\.source\s+"[^"]*"\s*\n', '', c)
                    c = re.sub(r'\.line\s+\d+\s*\n', '', c)
                    f.write_text(c, encoding='utf-8')
                except: pass

def add_anti_debug(smali_base):
    """Добавить анти-отладку"""
    anti_smali = '''.class public La/b/c/d/x;
.super Ljava/lang/Object;

.method public static a(Landroid/content/Context;)V
    .locals 2
    :try_start_0
    invoke-static {}, Landroid/os/Debug;->isDebuggerConnected()Z
    move-result v0
    if-eqz v0, :cond_0
    invoke-static {}, Landroid/os/Process;->myPid()I
    move-result v0
    invoke-static {v0}, Landroid/os/Process;->killProcess(I)V
    :cond_0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    :catch_0
    return-void
.end method
'''
    target = smali_base / "smali" / "a" / "b" / "c" / "d"
    target.mkdir(parents=True, exist_ok=True)
    (target / "x.smali").write_text(anti_smali, encoding='utf-8')

def inject_anti_debug(main_activity_path):
    """Инжектировать вызов анти-отладки"""
    try:
        c = main_activity_path.read_text(encoding='utf-8', errors='ignore')
        inject = '\n    invoke-static {p0}, La/b/c/d/x;->a(Landroid/content/Context;)V\n'
        # После super.<init>
        pattern = r'(invoke-direct\s+\{p0\},\s*L[^;]+;-><init>\(\)V)'
        if re.search(pattern, c) and 'La/b/c/d/x;->a' not in c:
            c = re.sub(pattern, r'\1' + inject, c, count=1)
            main_activity_path.write_text(c, encoding='utf-8')
            return True
    except Exception as e:
        print(f"Inject error: {e}")
    return False

def main():
    base = Path(__file__).parent.parent
    decompiled = base / DECOMPILED_DIR
    output = base / OUTPUT_DIR
    
    if not decompiled.exists():
        print(f"Not found: {decompiled}")
        return 1
    
    print("Copying to protected...")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(decompiled, output)
    
    print("Building mapping...")
    mapping = build_simple_mapping(output)
    print(f"  Mapped {len(mapping)} classes")
    
    print("Applying mapping...")
    n = process_all_files(output, mapping)
    print(f"  Updated {n} files")
    
    print("Moving smali files...")
    move_smali_files(output, mapping)
    
    print("Removing source directives...")
    remove_source_directives(output)
    
    print("Adding anti-debug...")
    add_anti_debug(output)
    
    main_activity = output / "smali" / "a" / "b" / "c" / "d" / "a.smali"
    if main_activity.exists():
        inject_anti_debug(main_activity)
        print("  Injected into MainActivity")
    
    print("Done!")
    return 0

if __name__ == "__main__":
    exit(main())
