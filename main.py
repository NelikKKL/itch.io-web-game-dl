import os
import sys
import threading
import requests
import pyperclip
import json
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

# Инициализация настроек темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

class ItchDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Itch.io Web Downloader")
        self.geometry("700(520") # Немного увеличил высоту для доп. текста

        # Переменные
        self.api_key = ctk.StringVar(value="")
        self.download_path = ctk.StringVar(value=str(Path.home() / "Desktop"))
        self.status_msg = ctk.StringVar(value="Готов к работе")
        self.progress_text = ctk.StringVar(value="") # Переменная для "50MB / 100MB"
        self.current_theme = "dark"
        self.cancel_flag = False
        
        self.load_settings()

        self.api_key.trace_add("write", self.save_settings)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Боковое меню ---
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ITCH-DLW", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=10)

        btn_colors = {"fg_color": "#444444", "hover_color": "#555555"}

        self.home_btn = ctk.CTkButton(self.sidebar_frame, text="Главная", command=self.show_home, corner_radius=10, **btn_colors)
        self.home_btn.pack(pady=10, padx=10)

        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="Настройки", command=self.show_settings, corner_radius=10, **btn_colors)
        self.settings_btn.pack(pady=10, padx=10)

        # --- Основной контейнер ---
        self.main_container = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.home_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.settings_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        self.setup_home_frame()
        self.setup_settings_frame()
        self.show_home()

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_key.set(data.get("api_key", ""))
            except Exception: pass

    def save_settings(self, *args):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"api_key": self.api_key.get()}, f)
        except Exception: pass

    def show_home(self):
        self.settings_frame.grid_remove()
        self.home_frame.grid(row=0, column=0, sticky="nsew")

    def show_settings(self):
        self.home_frame.grid_remove()
        self.settings_frame.grid(row=0, column=0, sticky="nsew")

    def setup_home_frame(self):
        btn_colors = {"fg_color": "#444444", "hover_color": "#555555"}
        accent_color = "#ff4c4c" # Цвет кнопки скачивания

        input_container = ctk.CTkFrame(self.home_frame, fg_color=("#3d3d3d" if self.current_theme == "dark" else "#dbdbdb"), corner_radius=15)
        input_container.pack(fill="x", pady=(20, 10))

        self.url_entry = ctk.CTkEntry(input_container, placeholder_text="Введите ссылку на игру...", 
                                      border_width=0, fg_color="transparent", height=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=10)

        self.paste_btn = ctk.CTkButton(input_container, text="📋", width=40, height=30, 
                                       command=self.paste_from_clipboard, corner_radius=8, **btn_colors)
        self.paste_btn.pack(side="right", padx=5)

        self.path_label = ctk.CTkLabel(self.home_frame, textvariable=self.download_path, font=ctk.CTkFont(size=11))
        self.path_label.pack(pady=2)

        self.dir_btn = ctk.CTkButton(self.home_frame, text="Выбрать папку", command=self.choose_directory, corner_radius=10, **btn_colors)
        self.dir_btn.pack(pady=10)

        buttons_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=10)
        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.dl_btn = ctk.CTkButton(buttons_frame, text="СКАЧАТЬ", fg_color=accent_color, hover_color="#ff6666", 
                                    text_color="white", font=ctk.CTkFont(weight="bold"), height=45, 
                                    corner_radius=10, command=self.start_download_thread)
        self.dl_btn.grid(row=0, column=0, padx=5, sticky="ew")

        self.cancel_btn = ctk.CTkButton(buttons_frame, text="ОТМЕНА", fg_color="#666666", hover_color="#777777", 
                                        text_color="white", font=ctk.CTkFont(weight="bold"), height=45, 
                                        corner_radius=10, command=self.cancel_download, state="disabled")
        self.cancel_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.status_label = ctk.CTkLabel(self.home_frame, textvariable=self.status_msg, font=ctk.CTkFont(size=18, weight="bold"))
        self.status_label.pack(pady=(10, 0))

        # Метка для мегабайт (50MB / 100MB)
        self.progress_info_label = ctk.CTkLabel(self.home_frame, textvariable=self.progress_text, font=ctk.CTkFont(size=12))
        self.progress_info_label.pack(pady=0)

        # Прогресс-бар с цветом кнопки скачивания
        self.progress_bar = ctk.CTkProgressBar(self.home_frame, progress_color=accent_color)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

    def setup_settings_frame(self):
        btn_colors = {"fg_color": "#444444", "hover_color": "#555555"}
        ctk.CTkLabel(self.settings_frame, text="Настройки", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.settings_frame, text="Itch.io API Key:").pack(anchor="w", padx=20)
        self.api_entry = ctk.CTkEntry(self.settings_frame, textvariable=self.api_key, placeholder_text="Ваш ключ...", width=400)
        self.api_entry.pack(pady=5, padx=20)
        self.theme_switch = ctk.CTkSwitch(self.settings_frame, text="Светлая тема", command=self.toggle_theme)
        self.theme_switch.pack(pady=10, padx=20, anchor="w")
        self.log_btn = ctk.CTkButton(self.settings_frame, text="Создать log.txt на рабочем столе", command=self.create_log, corner_radius=10, **btn_colors)
        self.log_btn.pack(pady=20, padx=20, anchor="w")

    def toggle_theme(self):
        if self.current_theme == "dark":
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
        else:
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"

    def paste_from_clipboard(self):
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, pyperclip.paste())

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path: self.download_path.set(path)

    def create_log(self):
        log_path = Path.home() / "Desktop" / "log.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Log generated. API Key: {self.api_key.get()[:5]}***\nStatus: {self.status_msg.get()}")
        self.status_msg.set("📄 Лог создан")

    def cancel_download(self):
        self.cancel_flag = True
        self.status_msg.set("⚠️ Отмена...")
        self.cancel_btn.configure(state="disabled")

    def start_download_thread(self):
        self.dl_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        threading.Thread(target=self.download_logic, daemon=True).start()

    def download_logic(self):
        self.cancel_flag = False
        url = self.url_entry.get().strip()
        key = self.api_key.get().strip()

        if not url or not key:
            self.status_msg.set("❌ Введите ключ и ссылку!")
            self.reset_ui_state()
            return

        self.status_msg.set("🔍 Поиск игры...")
        self.progress_bar.pack(fill="x", pady=10, padx=20)
        self.progress_bar.set(0)
        self.progress_text.set("")

        try:
            search_url = f"https://itch.io/api/1/{key}/search/games?query={url}"
            data = requests.get(search_url).json()

            if 'games' not in data or not data['games']:
                self.status_msg.set("❌ Игра не найдена")
                self.reset_ui_state()
                return

            game_id = data['games'][0]['id']
            uploads_url = f"https://itch.io/api/1/{key}/game/{game_id}/uploads"
            uploads_data = requests.get(uploads_url).json()
            web_uploads = [u for u in uploads_data.get('uploads', []) if u.get('type') == 'html']

            if not web_uploads:
                self.status_msg.set("❌ Web-версия отсутствует")
                self.reset_ui_state()
                return

            upload = web_uploads[0]
            filename = upload.get('filename') or f"game_{upload['id']}.zip"
            
            dl_link_url = f"https://itch.io/api/1/{key}/upload/{upload['id']}/download"
            dl_data = requests.get(dl_link_url).json()

            if 'url' in dl_data:
                self.status_msg.set("Скачивание...")
                response = requests.get(dl_data['url'], stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                save_path = Path(self.download_path.get()) / filename
                downloaded = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.cancel_flag:
                            break
                        
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Расчет прогресса в MB
                            done_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            
                            if total_size > 0:
                                self.progress_bar.set(downloaded / total_size)
                                self.progress_text.set(f"{done_mb:.1f} MB / {total_mb:.1f} MB")
                            else:
                                self.progress_text.set(f"{done_mb:.1f} MB / ???")

                if self.cancel_flag:
                    self.status_msg.set("❌ Загрузка отменена")
                    self.progress_text.set("")
                    if save_path.exists(): os.remove(save_path)
                else:
                    self.status_msg.set("✅ Успешно скачано!")
                    self.progress_bar.set(1)
            else:
                self.status_msg.set("❌ Ошибка получения ссылки")

        except Exception as e:
            self.status_msg.set("❌ Ошибка сети")
            print(f"Error: {e}")
        finally:
            self.reset_ui_state()

    def reset_ui_state(self):
        self.dl_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

if __name__ == "__main__":
    app = ItchDownloaderApp()
    app.mainloop()