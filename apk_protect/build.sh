#!/bin/bash
# Полная сборка защищённого APK koyo.apk

set -e
cd "$(dirname "$0")/.."

APK_SOURCE="коуо.apk"
APK_OUTPUT="koyo.apk"

echo "=== Защита APK от декомпиляции ==="

# 1. Декомпиляция (если ещё не сделано)
if [ ! -d "koyo_decompiled" ]; then
    echo "Декомпиляция APK..."
    apktool d "$APK_SOURCE" -o koyo_decompiled -f
fi

# 2. Применение защиты
echo "Применение обфускации и защиты..."
python3 apk_protect/protect.py

# 3. Сборка
echo "Сборка APK..."
apktool b koyo_protected -o koyo_protected_unsigned.apk --use-aapt2

# 4. Подпись (используем существующий keystore или создаём)
if [ ! -f "koyo.keystore" ]; then
    echo "Создание keystore..."
    keytool -genkey -v -keystore koyo.keystore -alias koyo -keyalg RSA -keysize 2048 \
        -validity 10000 -storepass koyopass -keypass koyopass \
        -dname "CN=Koyo, OU=Dev, O=App, L=City, S=State, C=US"
fi

echo "Подпись APK..."
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore koyo.keystore -storepass koyopass -keypass koyopass \
    koyo_protected_unsigned.apk koyo

# 5. Копируем результат
cp koyo_protected_unsigned.apk "$APK_OUTPUT"
echo ""
echo "=== Готово! Защищённый APK: $APK_OUTPUT ==="
echo ""
echo "Применённые меры защиты:"
echo "  - Обфускация пакета: com.xzaqp5om.vou6y1dd -> a.b.c.d"
echo "  - Обфускация всех классов приложения (1026+ классов)"
echo "  - Удаление .source и .line директив (скрытие имён файлов)"
echo "  - Анти-отладка (завершение при подключении отладчика)"
echo "  - Подпись APK"
