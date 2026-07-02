import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Путь к файлам конфигурации
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
SERVERS_FILE = os.path.join(CONFIG_DIR, 'servers.json')

class VPNClient:
    def __init__(self, root):
        self.root = root
        self.root.title("NaixVPN")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Установка иконки если существует
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.is_connected = False
        self.current_server = None
        self.vpn_process = None
        
        self.setup_ui()
        self.load_servers()
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        
        # Верхняя панель с логотипом
        header_frame = tk.Frame(self.root, bg="#1e1e2e", height=80)
        header_frame.pack(fill="x", pady=10)
        header_frame.pack_propagate(False)
        
        title = tk.Label(header_frame, text="NaixVPN", font=("Arial", 24, "bold"), 
                        fg="#00d4ff", bg="#1e1e2e")
        title.pack(pady=15)
        
        # Основная панель
        main_frame = tk.Frame(self.root, bg="#ffffff")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Статус
        status_frame = tk.LabelFrame(main_frame, text="Статус подключения", 
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = tk.Label(status_frame, text="● Отключено", 
                                     font=("Arial", 12), fg="#ff0000")
        self.status_label.pack(side="left")
        
        self.server_info = tk.Label(status_frame, text="Сервер: не выбран", 
                                   font=("Arial", 9), fg="#666666")
        self.server_info.pack(side="left", padx=(20, 0))
        
        # Выбор сервера
        server_frame = tk.LabelFrame(main_frame, text="Доступные серверы", 
                                    font=("Arial", 10, "bold"), padx=10, pady=10)
        server_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Скроллбар для списка
        scrollbar = tk.Scrollbar(server_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.server_list = tk.Listbox(server_frame, yscrollcommand=scrollbar.set, 
                                      font=("Arial", 10), height=10)
        self.server_list.pack(fill="both", expand=True)
        scrollbar.config(command=self.server_list.yview)
        
        # Кнопки управления
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        self.connect_button = tk.Button(button_frame, text="Подключиться", 
                                        command=self.toggle_connection,
                                        font=("Arial", 11, "bold"),
                                        bg="#00d4ff", fg="#ffffff",
                                        padx=20, pady=10, cursor="hand2")
        self.connect_button.pack(fill="x", pady=(0, 5))
        
        settings_button = tk.Button(button_frame, text="Настройки", 
                                   command=self.show_settings,
                                   font=("Arial", 11),
                                   bg="#f0f0f0", fg="#333333",
                                   padx=20, pady=8, cursor="hand2")
        settings_button.pack(fill="x")
        
        # Нижняя панель со статистикой
        stats_frame = tk.LabelFrame(main_frame, text="Статистика", 
                                   font=("Arial", 10, "bold"), padx=10, pady=10)
        stats_frame.pack(fill="x")
        
        self.data_sent = tk.Label(stats_frame, text="Отправлено: 0 MB", 
                                 font=("Arial", 9))
        self.data_sent.pack(anchor="w")
        
        self.data_received = tk.Label(stats_frame, text="Получено: 0 MB", 
                                     font=("Arial", 9))
        self.data_received.pack(anchor="w")
        
        self.ping_label = tk.Label(stats_frame, text="Пинг: - ms", 
                                  font=("Arial", 9))
        self.ping_label.pack(anchor="w")
    
    def load_servers(self):
        """Загрузка списка серверов из конфигурации"""
        try:
            if os.path.exists(SERVERS_FILE):
                with open(SERVERS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    servers = data.get('servers', [])
            else:
                servers = [
                    {'name': '🇳🇱 Нидерланды', 'ip': '185.225.76.1'},
                    {'name': '🇵🇱 Польша', 'ip': '185.225.76.2'},
                    {'name': '🇫🇮 Финляндия', 'ip': '185.225.76.3'},
                    {'name': '🇫🇷 Франция', 'ip': '185.225.76.4'},
                    {'name': '🇩🇪 Германия', 'ip': '185.225.76.5'},
                    {'name': '🇸🇪 Швеция', 'ip': '185.225.76.6'},
                    {'name': '🇬🇧 Великобритания', 'ip': '185.225.76.7'},
                    {'name': '🇨🇦 Канада', 'ip': '185.225.76.8'},
                ]
            
            self.server_list.delete(0, tk.END)
            for server in servers:
                self.server_list.insert(tk.END, f"{server['name']} ({server['ip']})")
            
            if servers:
                self.server_list.selection_set(0)
                self.current_server = servers[0]
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить серверы: {e}")
    
    def toggle_connection(self):
        """Переключение состояния подключения"""
        if not self.is_connected:
            self.connect_to_vpn()
        else:
            self.disconnect_from_vpn()
    
    def connect_to_vpn(self):
        """Подключение к VPN"""
        selection = self.server_list.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выбери сервер для подключения!")
            return
        
        server_name = self.server_list.get(selection[0])
        
        # Запуск подключения в отдельном потоке
        thread = threading.Thread(target=self._connect_thread, args=(server_name,))
        thread.daemon = True
        thread.start()
    
    def _connect_thread(self, server_name):
        """Поток подключения к VPN"""
        try:
            self.connect_button.config(state="disabled", text="Подключение...")
            self.root.update()
            
            # Имитация подключения
            self.is_connected = True
            self.current_server = server_name
            
            # Обновление UI
            self.status_label.config(text="● Подключено", fg="#00ff00")
            self.server_info.config(text=f"Сервер: {server_name}")
            self.connect_button.config(state="normal", text="Отключиться", bg="#ff0000")
            
            # Логирование
            self.log_connection("connected", server_name)
            messagebox.showinfo("Успех", f"Подключено к {server_name}")
        
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))
            self.connect_button.config(state="normal", text="Подключиться", bg="#00d4ff")
    
    def disconnect_from_vpn(self):
        """Отключение от VPN"""
        try:
            self.is_connected = False
            self.status_label.config(text="● Отключено", fg="#ff0000")
            self.server_info.config(text="Сервер: не выбран")
            self.connect_button.config(state="normal", text="Подключиться", bg="#00d4ff")
            
            self.log_connection("disconnected", self.current_server)
            messagebox.showinfo("Успех", "Отключено от VPN")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отключиться: {e}")
    
    def show_settings(self):
        """Показать окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Содержимое окна настроек
        frame = tk.Frame(settings_window, padx=15, pady=15)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="Настройки NaixVPN", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 15))
        
        # Чекбокс автозапуска
        auto_start = tk.BooleanVar()
        tk.Checkbutton(frame, text="Автоподключение при запуске", 
                      variable=auto_start, font=("Arial", 10)).pack(anchor="w", pady=5)
        
        # Чекбокс уведомлений
        notifications = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text="Показывать уведомления", 
                      variable=notifications, font=("Arial", 10)).pack(anchor="w", pady=5)
        
        # Выбор протокола
        tk.Label(frame, text="Протокол:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(15, 5))
        protocol_var = tk.StringVar(value="OpenVPN")
        tk.Radiobutton(frame, text="OpenVPN", variable=protocol_var, 
                      value="OpenVPN", font=("Arial", 10)).pack(anchor="w")
        tk.Radiobutton(frame, text="WireGuard", variable=protocol_var, 
                      value="WireGuard", font=("Arial", 10)).pack(anchor="w")
        
        # Кнопка сохранения
        def save_settings():
            messagebox.showinfo("Успех", "Настройки сохранены")
            settings_window.destroy()
        
        tk.Button(frame, text="Сохранить", command=save_settings, 
                 font=("Arial", 11), bg="#00d4ff", fg="#ffffff",
                 padx=15, pady=8).pack(fill="x", pady=(15, 0))
    
    def log_connection(self, status, server):
        """Логирование событий подключения"""
        log_file = os.path.join(os.path.dirname(__file__), 'vpn.log')
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {status.upper()}: {server}\n")
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNClient(root)
    root.mainloop()
