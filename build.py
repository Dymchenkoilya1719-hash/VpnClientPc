#!/usr/bin/env python3
"""
Скрипт для сборки VPN-клиента в EXE файл.
Использует PyInstaller для создания исполняемого файла.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    print("🔨 Начинаем сборку VPN-клиента...")
    
    # Очищаем предыдущие сборки
    for folder in ['build', 'dist', '__pycache__']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ Удалена папка {folder}")
    
    # Путь к иконке
    icon_path = os.path.join('assets', 'icon.ico')
    icon_arg = f'--icon={icon_path}' if os.path.exists(icon_path) else ''
    
    # Команда для PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=NaixVPN',
        '--add-data=config:config',
        '--add-data=assets:assets',
        icon_arg,
        '--distpath=dist',
        '--buildpath=build',
        '--specpath=build',
        'main.py'
    ]
    
    # Удаляем пустые аргументы
    cmd = [arg for arg in cmd if arg]
    
    print(f"\n📦 Выполняю команду: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            exe_path = os.path.join('dist', 'NaixVPN.exe')
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)  # в MB
                print(f"\n✅ Сборка успешна!")
                print(f"📄 Файл расположен: {exe_path}")
                print(f"💾 Размер: {file_size:.2f} MB")
                print(f"\n🎉 Готово! Ты можешь скачать NaixVPN.exe из папки dist")
                return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при сборке: {e}")
        print("\n📝 Убедись, что установлены зависимости:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
