import customtkinter
import os
import subprocess
import sys
from datetime import datetime
import mss
import mss.tools
from PIL import Image, ImageTk, ImageDraw, ImageFont
import numpy as np
import cv2
import threading
import time
import tkinter
import json
import traceback
import tempfile
import atexit
import psutil
import signal

# Opcjonalnie importuj pyautogui dla obsługi kursora
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Opcjonalnie importuj pynput dla przechwytywania klawiszy
try:
    from pynput import mouse, keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

def resource_path(relative_path):
    """ Zwraca bezwględną ścieżkę do zasobu, działa dla dev i dla PyInstallera """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_ffmpeg_availability():
    """Sprawdza, czy FFmpeg jest dostępny w ścieżce projektu."""
    try:
        path = resource_path('ffmpeg')
        if sys.platform == "win32" and not path.endswith('.exe'):
            path += '.exe'
        # If running on Unix-like system and a bundled ffmpeg exists but isn't executable,
        # try to set the executable bit. This fixes cases where downloads (e.g., from Drive)
        # lost the executable permission.
        if not sys.platform == "win32":
            try:
                if os.path.exists(path) and not os.access(path, os.X_OK):
                    os.chmod(path, 0o755)
            except Exception:
                # ignore permission errors here; later subprocess.run will report if not executable
                pass
        if not os.path.exists(path):
            return False
        subprocess.run([path, "-version"], check=True, capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, PermissionError):
        return False

IS_WIN = sys.platform == "win32"
if IS_WIN:
    try:
        from win32gui import GetWindowLong, SetWindowLong
        from win32con import GWL_STYLE, WS_MAXIMIZEBOX, WS_THICKFRAME
        PYWIN32_AVAILABLE = True
    except ImportError:
        PYWIN32_AVAILABLE = False

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule_show)
        self.widget.bind("<Leave>", self.hide_tooltip)
        
    def schedule_show(self, event=None):
        self.cancel_schedule()
        self.id = self.widget.after(500, self.show_tooltip)

    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self.tooltip_window = customtkinter.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.wm_attributes("-topmost", True)
        label = customtkinter.CTkLabel(self.tooltip_window, text=self.text, fg_color="#2b2b2b", corner_radius=5, font=("Arial", 12))
        label.pack(ipadx=5, ipady=3)

    def hide_tooltip(self, event=None):
        self.cancel_schedule()
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def cancel_schedule(self):
        if self.id:
            self.widget.after_cancel(self.id)

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class ConfigManager:
    def __init__(self, base_path):
        if sys.platform == "win32":
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        elif sys.platform == "darwin":
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            desktop_path = os.path.join(os.path.expanduser("~"), "Pulpit")
            if not os.path.exists(desktop_path):
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.base_path = desktop_path
        self.config_dir = os.path.join(self.base_path, "C2_videos")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "battlelog_config.json")
        self.config = self.load_config()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Błąd ładowania konfiguracji: {e}")
            return {}
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisywania konfiguracji: {e}")
    
    def get_radar_name(self):
        return self.config.get('radar_name', None)
    
    def set_radar_name(self, name):
        self.config['radar_name'] = name
        self.save_config()
    
    def get_language(self):
        return self.config.get('language', 'PL')
    
    def set_language(self, lang):
        self.config['language'] = lang
        self.save_config()
    
    def get_always_on_top(self):
        return self.config.get('always_on_top', "off")
    
    def set_always_on_top(self, enabled):
        self.config['always_on_top'] = enabled
        self.save_config()
    
    def get_photo_button_visible(self):
        return self.config.get('photo_button_visible', "off")
    
    def set_photo_button_visible(self, visible):
        self.config['photo_button_visible'] = visible
        self.save_config()
    
    def get_video_button_visible(self):
        return self.config.get('video_button_visible', "on")
    
    def set_video_button_visible(self, visible):
        self.config['video_button_visible'] = visible
        self.save_config()
    
    def get_video_duration(self):
        return self.config.get('video_duration', "9")
    
    def set_video_duration(self, duration):
        self.config['video_duration'] = duration
        self.save_config()
    
    def get_video_quality(self):
        return self.config.get('video_quality', "medium")
    
    def set_video_quality(self, quality):
        self.config['video_quality'] = quality
        self.save_config()
    
    def get_loop_record(self):
        return self.config.get('loop_record', "on")
    
    def set_loop_record(self, enabled):
        self.config['loop_record'] = enabled
        self.save_config()
    
    def get_record_cursor(self):
        return self.config.get('record_cursor', "on")
    
    def set_record_cursor(self, enabled):
        self.config['record_cursor'] = enabled
        self.save_config()
    
    def get_capture_keys(self):
        return self.config.get('capture_keys', "on")
    
    def set_capture_keys(self, enabled):
        self.config['capture_keys'] = enabled
        self.save_config()

    def get_video_recording_mode(self):
        return self.config.get('video_recording_mode', "separate")

    def set_video_recording_mode(self, mode):
        self.config['video_recording_mode'] = mode
        self.save_config()

    def get_photo_monitors(self):
        return self.config.get('photo_monitors', None)

    def set_photo_monitors(self, states):
        self.config['photo_monitors'] = states
        self.save_config()

    def get_video_monitors(self):
        return self.config.get('video_monitors', None)

    def set_video_monitors(self, states):
        self.config['video_monitors'] = states
        self.save_config()

    def reset_config(self):
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                self.config = {}
        except Exception as e:
            print(f"Błąd resetowania konfiguracji: {e}")

class SingleInstanceApp:
    def __init__(self, app_name="BattleLog"):
        self.app_name = app_name
        self.lock_file = None
        self.lock_path = os.path.join(tempfile.gettempdir(), f"{app_name}_lock.tmp")
        
    def is_running(self):
        try:
            if os.path.exists(self.lock_path):
                try:
                    with open(self.lock_path, 'r') as f:
                        pid = int(f.read().strip())
                    if IS_WIN:
                        try:
                            import psutil
                            return psutil.pid_exists(pid)
                        except ImportError:
                            import subprocess
                            try:
                                result = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, stderr=subprocess.DEVNULL)
                                return str(pid) in str(result)
                            except subprocess.CalledProcessError:
                                return False
                    else:
                        try:
                            os.kill(pid, 0)
                            return True
                        except OSError:
                            return False
                except (ValueError, IOError):
                    self.cleanup()
                    return False
            return False
        except Exception as e:
            print(f"Błąd sprawdzania instancji: {e}")
            return False
    
    def create_lock(self):
        try:
            with open(self.lock_path, 'w') as f:
                f.write(str(os.getpid()))
            self.lock_file = self.lock_path
            atexit.register(self.cleanup)
            return True
        except Exception as e:
            print(f"Błąd tworzenia lock file: {e}")
            return False
    
    def cleanup(self):
        try:
            if self.lock_file and os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                self.lock_file = None
        except Exception as e:
            print(f"Błąd usuwania lock file: {e}")
    
    def show_already_running_message(self, language="PL"):
        try:
            root = tkinter.Tk()
            root.withdraw()
            import tkinter.messagebox as msgbox
            titles = {"PL": "BattleLog już działa", "EN": "BattleLog is already running", "UA": "BattleLog вже запущено"}
            messages = {"PL": "Aplikacja BattleLog jest już uruchomiona.\n\nSprawdź pasek zadań lub spróbuj zamknąć poprzednią instancję.", "EN": "BattleLog is already running.\n\nCheck the taskbar or try closing the previous instance.", "UA": "BattleLog вже запущено.\n\nПеревірте панель завдань або спробуйте закрити попередній екземпляр."}
            title = titles.get(language, titles["EN"])
            message = messages.get(language, messages["EN"])
            msgbox.showwarning(title, message)
        except Exception:
            print({"PL": "BŁĄD: Aplikacja BattleLog jest już uruchomiona!", "EN": "ERROR: BattleLog is already running!", "UA": "ПОМИЛКА: BattleLog вже запущено!"}.get(language, "ERROR: BattleLog is already running!"))

class RadarNameDialog(customtkinter.CTkToplevel):
    pass

class BattleLogApp(customtkinter.CTk):
    RECORD_FPS = 15
    WIDGETS_PER_ROW = 4
    TILE_WIDTH = 1920
    TILE_HEIGHT = 1080

    def __init__(self):
        super().__init__()
        self.start_panel = None
        
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        else:
            self.application_path = os.path.dirname(os.path.abspath(__file__))
        
        self.config_manager = ConfigManager(self.application_path)

        self.configure(fg_color="#040C1B")
        self.ffmpeg_available = check_ffmpeg_availability()
        self.title("BattleLog")
        self.geometry("600x800")
        self.resizable(False, False)

        try:
            icon_path = resource_path("ikona.png")
            self.app_icon = tkinter.PhotoImage(file=icon_path)
            self.wm_iconphoto(False, self.app_icon)
        except Exception as e:
            print(f"Nie udało się załadować ikony: {e}")

        # ZMIANA: Powiąż funkcję modyfikującą styl okna ze zdarzeniem jego wyświetlenia
        if IS_WIN and PYWIN32_AVAILABLE:
            self.bind("<Map>", self._disable_maximize_button)
        
        self.is_recording = False
        self.is_processing_screenshot = False
        self.is_finalizing_video = False
        self.manual_stop = False
        self.countdown_job = None
        self.is_expanded = False
        self.recording_start_time = None 
        self.recording_threads = []
        self.temp_video_files = {}
        
        # Zarządzanie zasobami i responsywnością
        self.processing_process = None
        self.processing_cancelled = threading.Event()
        self.loop_stop_requested = False  # Flaga dla zatrzymania pętli bez anulowania przetwarzania
        self.progress_callback = None
        
        # Status tracking dla kombinowanych komunikatów
        self.recording_status = ""
        self.processing_status = ""

        # Licznik aktywnych procesów przetwarzania
        self.active_processing_threads = 0
        self.processing_lock = threading.Lock()

        # Kolejka zadań przetwarzania i worker który wykonuje je sekwencyjnie
        import collections
        self.processing_queue = collections.deque()
        self.processing_worker_thread = None
        self.processing_worker_lock = threading.Lock()
        self.processing_worker_running = False

        self.pressed_keys = set()
        self.mouse_buttons = set()
        self.key_listener = None
        self.mouse_listener = None
        self.key_times = {}
        self.mouse_times = {}
        self.OVERLAY_HOLD_MS = 300

        self.monitor_checkboxes = []
        self.video_checkboxes = []

        self.COLOR_INFO = ("#000000", "#FFFFFF")
        self.COLOR_SUCCESS = ("#006400", "#32CD32")
        self.COLOR_ERROR = ("#8B0000", "#FF4500")

        self.photo_button_visible_var = customtkinter.StringVar(value=self.config_manager.get_photo_button_visible())
        self.video_button_visible_var = customtkinter.StringVar(value=self.config_manager.get_video_button_visible())
        self.always_on_top_var = customtkinter.StringVar(value=self.config_manager.get_always_on_top())
        self.loop_record_var = customtkinter.StringVar(value=self.config_manager.get_loop_record())
        self.video_quality_var = customtkinter.StringVar(value=self.config_manager.get_video_quality())
        self.cursor_record_var = customtkinter.StringVar(value=self.config_manager.get_record_cursor())
        self.capture_keys_var = customtkinter.StringVar(value=self.config_manager.get_capture_keys())
        
        self.video_recording_mode_var = customtkinter.StringVar(value=self.config_manager.get_video_recording_mode())
        self.video_recording_mode_display_var = customtkinter.StringVar()

        self.other_controls = []
        self._last_valid_duration = self.config_manager.get_video_duration()

        self.language = self.config_manager.get_language()
        self.setup_ui()
        self.start_panel = None
        if self.needs_radar_name_dialog():
            self.show_start_panel()
        else:
            self.deiconify()
            self.update_app_language(self.language)
        
        atexit.register(self.cleanup_temp_files)


    def update_app_language(self, lang):
        self.language = lang
        if hasattr(self, 'language_var'):
            self.language_var.set(lang)
        tr = TRANSLATIONS[lang]
        
        self.settings_section_label.configure(text=tr["settings_section"])
        self.language_label.configure(text=tr["language"])
        self.on_top_label.configure(text=tr["always_on_top"])
        self.buttons_label.configure(text=tr["buttons"])
        
        if self.other_controls:
            self.other_controls[1].configure(text=tr["photo"]) 
            self.other_controls[2].configure(text=tr["video"]) 
        
        self.radar_settings_section_label.configure(text=tr["radar_settings_section"])
        self.radar_name_label.configure(text=tr["radar_name_label"])
        self.keyword_entry.configure(placeholder_text=tr["keyword_placeholder"])
        self.save_name_button.configure(text=tr["save"])
        self.save_name_button_tooltip.text = tr["tooltip_save_radar_name"]
        self.open_folder_button_tooltip.text = tr["tooltip_open_folder"]
        
        self.photo_video_settings_label.configure(text=tr["photo_video_settings_section"])
        self.photo_monitors_label.configure(text=tr["monitors_photo"])
        self.identify_monitors_button_tooltip.text = tr["tooltip_identify_monitors"]
        self.video_monitor_label.configure(text=tr["monitors_video"])
        
        self.video_mode_label.configure(text=tr["video_recording_mode"])
        mode_values = [tr["mode_separate"], tr["mode_merged"]]
        self.video_mode_segmented.configure(values=mode_values)
        current_mode_internal = self.video_recording_mode_var.get()
        self.video_recording_mode_display_var.set(tr["mode_separate"] if current_mode_internal == "separate" else tr["mode_merged"])

        self.duration_label.configure(text=tr["video_duration"])
        self.seconds_label.configure(text=tr["seconds"])
        self.quality_label.configure(text=tr["video_quality"])
        
        quality_values = [tr["quality_low"], tr["quality_medium"], tr["quality_high"]]
        self.quality_segmented.configure(values=quality_values)
        current_quality_key = f"quality_{self.video_quality_var.get()}"
        if current_quality_key in tr:
            self.quality_segmented.set(tr[current_quality_key])
        
        self.loop_label.configure(text=tr["loop_record"])
        self.cursor_label.configure(text=tr["record_cursor"])
        if PYNPUT_AVAILABLE:
            self.keys_label.configure(text=tr["capture_keys"])
        else:
            self.keys_label.configure(text=tr["capture_keys_disabled"])
        
        self.screenshot_button_tooltip.text = tr["tooltip_screenshot"]
        self.record_button_tooltip.text = tr["tooltip_record"]

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) 
        
        left_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(9, 5), pady=5, sticky="nsew")

        buttons_frame = customtkinter.CTkFrame(left_frame, fg_color="transparent")
        buttons_frame.pack(expand=True)

        icon_size = (20, 20)
        try:
            camera_icon_image = customtkinter.CTkImage(Image.open(resource_path("camera_icon.png")), size=icon_size)
            self.video_icon_image = customtkinter.CTkImage(Image.open(resource_path("video_icon.png")), size=icon_size)
            # load base stop icon
            stop_img = Image.open(resource_path("stop.png"))
            self.stop_icon_image = customtkinter.CTkImage(stop_img, size=icon_size)
        except Exception as e:
            print(f"Błąd ładowania ikon przycisków: {e}")
            camera_icon_image = self.video_icon_image = self.stop_icon_image = None
        
        self.COLOR_NORMAL = "#82C8FF"
        self.COLOR_HOVER = "#62A8DF"
        self.COLOR_DISABLED = "#555555"
        self.COLOR_RECORDING = "#FF4444"      # Czerwony dla nagrywania
        self.COLOR_RECORDING_HOVER = "#CC3333" # Ciemniejszy czerwony przy hover

        self.screenshot_button = customtkinter.CTkButton(buttons_frame, text="", image=camera_icon_image, command=self.trigger_screenshot, width=40, height=40, cursor="hand2", fg_color=self.COLOR_NORMAL, hover_color=self.COLOR_HOVER)
        self.record_button = customtkinter.CTkButton(buttons_frame, text="", image=self.video_icon_image, command=self.toggle_record, width=40, height=40, cursor="hand2", fg_color=self.COLOR_NORMAL, hover_color=self.COLOR_HOVER)

        self.screenshot_button_tooltip = ToolTip(self.screenshot_button, TRANSLATIONS["PL"]["tooltip_screenshot"])
        self.record_button_tooltip = ToolTip(self.record_button, TRANSLATIONS["PL"]["tooltip_record"])
        
        self.expand_button = customtkinter.CTkButton(self, text=">", width=28, height=28, command=self.toggle_expand, fg_color="#040C1B", hover_color="#2b2b2b")
        self.expand_button.grid(row=0, column=1, padx=(0, 5), pady=0, sticky="ns")

        self.status_bar_frame = customtkinter.CTkFrame(self, fg_color="#1C1C1E", corner_radius=0, height=20)
        self.status_bar_frame.pack_propagate(False)
        self.status_label = customtkinter.CTkLabel(self.status_bar_frame, text="", font=(None, 10), anchor="w")
        self.status_label.pack(pady=0, padx=10, fill="x", expand=True)
        
        self.options_frame = self.create_options_frame()
        self.update_window_size()
        self._update_button_visibility()
        self._toggle_always_on_top()

    def create_options_frame(self):
        options_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        
        settings_section_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        settings_section_frame.pack(side="top", fill="x", pady=(10, 10), anchor="w", padx=5)
        self.settings_section_label = customtkinter.CTkLabel(settings_section_frame, text=TRANSLATIONS[self.language]["settings_section"], font=(None, 15, "bold"))
        self.settings_section_label.pack(side="left", anchor="w")
        
        language_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        language_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.language_label = customtkinter.CTkLabel(language_frame, text=TRANSLATIONS[self.language]["language"])
        self.language_label.pack(side="left", padx=(0, 10))
        self.language_var = customtkinter.StringVar(value=self.language)
        self.language_segmented = customtkinter.CTkSegmentedButton(language_frame, values=["PL", "EN", "UA"], variable=self.language_var, command=self._on_language_change)
        self.language_segmented.pack(side="left", padx=10)
        
        on_top_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        on_top_frame.pack(side="top", fill=None, pady=(0, 10), anchor="w", padx=0)
        on_top_inner = customtkinter.CTkFrame(on_top_frame, fg_color="transparent")
        on_top_inner.pack(side="left", fill=None, padx=0, pady=0)
        on_top_checkbox = customtkinter.CTkCheckBox(on_top_inner, text="", width=18, variable=self.always_on_top_var, onvalue="on", offvalue="off", command=self._toggle_always_on_top)
        on_top_checkbox.pack(side="left", padx=(0, 2))
        self.on_top_label = customtkinter.CTkLabel(on_top_inner, text=TRANSLATIONS[self.language]["always_on_top"], width=0, font=(None, 13))
        self.on_top_label.pack(side="left", padx=(0, 0))
        
        buttons_visibility_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        buttons_visibility_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.buttons_label = customtkinter.CTkLabel(buttons_visibility_frame, text=TRANSLATIONS[self.language]["buttons"])
        self.buttons_label.pack(side="left", padx=(0, 10))
        photo_visibility_checkbox = customtkinter.CTkCheckBox(buttons_visibility_frame, text=TRANSLATIONS[self.language]["photo"], variable=self.photo_button_visible_var, onvalue="on", offvalue="off", command=self._update_button_visibility)
        photo_visibility_checkbox.pack(side="left", padx=3)
        video_visibility_checkbox = customtkinter.CTkCheckBox(buttons_visibility_frame, text=TRANSLATIONS[self.language]["video"], variable=self.video_button_visible_var, onvalue="on", offvalue="off", command=self._update_button_visibility)
        video_visibility_checkbox.pack(side="left", padx=3)
        
        radar_settings_section_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        radar_settings_section_frame.pack(side="top", fill="x", pady=(10, 10), anchor="w", padx=5)
        self.radar_settings_section_label = customtkinter.CTkLabel(radar_settings_section_frame, text=TRANSLATIONS[self.language]["radar_settings_section"], font=(None, 15, "bold"))
        self.radar_settings_section_label.pack(side="left", anchor="w")
        
        radar_name_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        radar_name_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.radar_name_label = customtkinter.CTkLabel(radar_name_frame, text=TRANSLATIONS[self.language]["radar_name_label"])
        self.radar_name_label.pack(side="left", padx=(0, 10))
        self.keyword_char_limit = 20
        self.keyword_var = customtkinter.StringVar()
        self.keyword_var.trace_add("write", self.limit_keyword_length)
        self.keyword_entry = customtkinter.CTkEntry(radar_name_frame, placeholder_text=TRANSLATIONS[self.language]["keyword_placeholder"], textvariable=self.keyword_var)
        self.keyword_entry.pack(side="left", fill="x", expand=True)
        radar_name = self.config_manager.get_radar_name()
        if radar_name: self.keyword_entry.insert(0, radar_name)
        else: self.keyword_entry.insert(0, "")
        
        self.save_name_button = customtkinter.CTkButton(radar_name_frame, text=TRANSLATIONS[self.language]["save"], width=80, command=self.save_radar_name_from_settings)
        self.save_name_button.pack(side="left", padx=5)
        self.save_name_button_tooltip = ToolTip(self.save_name_button, TRANSLATIONS[self.language]["tooltip_save_radar_name"])
        
        try: folder_icon_image = customtkinter.CTkImage(Image.open(resource_path("folder_icon.png")), size=(20, 20))
        except Exception: folder_icon_image = None
        self.open_folder_button = customtkinter.CTkButton(radar_name_frame, text="", image=folder_icon_image, width=30, height=30, fg_color="#EEEEEE", hover_color="#8E8E93", command=self.open_log_folder, cursor="hand2")
        self.open_folder_button.pack(side="right", padx=5)
        self.open_folder_button_tooltip = ToolTip(self.open_folder_button, TRANSLATIONS[self.language]["tooltip_open_folder"])

        photo_video_settings_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        photo_video_settings_frame.pack(side="top", fill="x", pady=(10, 10), anchor="w", padx=5)
        self.photo_video_settings_label = customtkinter.CTkLabel(photo_video_settings_frame, text=TRANSLATIONS[self.language]["photo_video_settings_section"], font=(None, 15, "bold"))
        self.photo_video_settings_label.pack(side="left", anchor="w")

        photo_monitor_main_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        photo_monitor_main_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.photo_monitors_label = customtkinter.CTkLabel(photo_monitor_main_frame, text=TRANSLATIONS["PL"]["monitors_photo"])
        self.photo_monitors_label.pack(side="left", padx=(0, 3))
        
        photo_monitor_container = customtkinter.CTkFrame(photo_monitor_main_frame, fg_color="transparent")
        photo_monitor_container.pack(side="left")
        self.monitor_vars = []
        saved_photo_states = self.config_manager.get_photo_monitors()
        row_frame = None
        with mss.mss() as sct:
            num_monitors = len(sct.monitors[1:])
            for i in range(num_monitors):
                if i % self.WIDGETS_PER_ROW == 0:
                    row_frame = customtkinter.CTkFrame(photo_monitor_container, fg_color="transparent")
                    row_frame.pack(side="top", anchor="w")
                
                var = customtkinter.StringVar()
                if saved_photo_states and i < len(saved_photo_states):
                    var.set(saved_photo_states[i])
                else:
                    var.set("on")
                    
                checkbox = customtkinter.CTkCheckBox(row_frame, text=f"{i+1}", variable=var, onvalue="on", offvalue="off", command=self._save_monitor_selections)
                checkbox.pack(side="left", padx=1)
                self.monitor_vars.append(var)
                self.monitor_checkboxes.append(checkbox)

        try: monitors_icon = customtkinter.CTkImage(Image.open(resource_path("monitors_icon.png")), size=(20, 20)) 
        except Exception: monitors_icon = None
        self.identify_monitors_button = customtkinter.CTkButton(photo_monitor_main_frame, text="", image=monitors_icon, width=30, height=30, fg_color="#EEEEEE", hover_color="#8E8E93", command=self.identify_monitors, cursor="question_arrow")
        self.identify_monitors_button.pack(side="right", padx=5)
        self.identify_monitors_button_tooltip = ToolTip(self.identify_monitors_button, TRANSLATIONS["PL"]["identify_monitors"])

        video_monitor_main_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        video_monitor_main_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.video_monitor_label = customtkinter.CTkLabel(video_monitor_main_frame, text=TRANSLATIONS["PL"]["monitors_video"])
        self.video_monitor_label.pack(side="left", padx=(0, 3))
        video_monitor_container = customtkinter.CTkFrame(video_monitor_main_frame, fg_color="transparent")
        video_monitor_container.pack(side="left")
        self.video_monitor_vars = []
        self.video_checkboxes = []
        saved_video_states = self.config_manager.get_video_monitors()
        row_frame = None
        with mss.mss() as sct:
            num_monitors = min(len(sct.monitors) - 1, 4)
            for i in range(num_monitors):
                if i % self.WIDGETS_PER_ROW == 0:
                    row_frame = customtkinter.CTkFrame(video_monitor_container, fg_color="transparent")
                    row_frame.pack(side="top", anchor="w")
                
                var = customtkinter.StringVar()
                if saved_video_states and i < len(saved_video_states):
                    var.set(saved_video_states[i])
                else:
                    var.set("on" if i == 0 else "off")

                checkbox = customtkinter.CTkCheckBox(row_frame, text=f"{i+1}", variable=var, onvalue="on", offvalue="off", command=self._save_monitor_selections)
                checkbox.pack(side="left", padx=1)
                self.video_monitor_vars.append(var)
                self.video_checkboxes.append(checkbox)
        
        video_mode_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        video_mode_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.video_mode_label = customtkinter.CTkLabel(video_mode_frame, text=TRANSLATIONS[self.language]["video_recording_mode"])
        self.video_mode_label.pack(side="left", padx=(0, 10))
        tr = TRANSLATIONS[self.language]
        self.video_mode_segmented = customtkinter.CTkSegmentedButton(video_mode_frame, values=[tr["mode_separate"], tr["mode_merged"]], variable=self.video_recording_mode_display_var, command=self._on_video_mode_change)
        self.video_mode_segmented.pack(side="left", padx=10)
        
        duration_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        duration_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.duration_label = customtkinter.CTkLabel(duration_frame, text=TRANSLATIONS["PL"]["video_duration"])
        self.duration_label.pack(side="left")
        self.duration_entry = customtkinter.CTkEntry(duration_frame, width=40)
        self.duration_entry.insert(0, self.config_manager.get_video_duration())
        self.duration_entry.bind("<KeyRelease>", self._on_duration_change)
        self.duration_entry.bind("<FocusOut>", self._on_duration_change)
        self.duration_entry.pack(side="left", padx=5)
        self.seconds_label = customtkinter.CTkLabel(duration_frame, text=TRANSLATIONS["PL"]["seconds"])
        self.seconds_label.pack(side="left")

        quality_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        quality_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.quality_label = customtkinter.CTkLabel(quality_frame, text=TRANSLATIONS[self.language]["video_quality"])
        self.quality_label.pack(side="left", padx=(0, 10))
        self.quality_segmented = customtkinter.CTkSegmentedButton(quality_frame, values=[tr["quality_low"], tr["quality_medium"], tr["quality_high"]], command=self._on_quality_change)
        self.quality_segmented.pack(side="left", padx=10)
        
        loop_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        loop_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.loop_checkbox = customtkinter.CTkCheckBox(loop_frame, text="", width=18, variable=self.loop_record_var, onvalue="on", offvalue="off", command=self._on_loop_record_change)
        self.loop_checkbox.pack(side="left", padx=(0, 3))
        self.loop_label = customtkinter.CTkLabel(loop_frame, text=TRANSLATIONS[self.language]["loop_record"])
        self.loop_label.pack(side="left", padx=(0, 0))

        cursor_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        cursor_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        self.cursor_checkbox = customtkinter.CTkCheckBox(cursor_frame, text="", width=18, variable=self.cursor_record_var, onvalue="on", offvalue="off", command=self._on_record_cursor_change)
        self.cursor_checkbox.pack(side="left", padx=(0, 3))
        self.cursor_label = customtkinter.CTkLabel(cursor_frame, text=TRANSLATIONS[self.language]["record_cursor"])
        self.cursor_label.pack(side="left", padx=(0, 0))

        keys_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        keys_frame.pack(side="top", fill="x", pady=(0, 10), anchor="w", padx=5)
        if PYNPUT_AVAILABLE:
            self.capture_keys_checkbox = customtkinter.CTkCheckBox(keys_frame, text="", width=18, variable=self.capture_keys_var, onvalue="on", offvalue="off", command=self._on_capture_keys_change)
            self.capture_keys_checkbox.pack(side="left", padx=(0, 3))
            self.keys_label = customtkinter.CTkLabel(keys_frame, text=TRANSLATIONS[self.language]["capture_keys"])
            self.keys_label.pack(side="left", padx=(0, 0))
        else:
            self.capture_keys_checkbox = customtkinter.CTkCheckBox(keys_frame, text="", width=18, variable=self.capture_keys_var, onvalue="on", offvalue="off", state="disabled", command=self._on_capture_keys_change)
            self.capture_keys_checkbox.pack(side="left", padx=(0, 3))
            self.keys_label = customtkinter.CTkLabel(keys_frame, text=TRANSLATIONS[self.language]["capture_keys_disabled"], state="disabled")
            self.keys_label.pack(side="left", padx=(0, 0))
        
        self.other_controls = [on_top_checkbox, photo_visibility_checkbox, video_visibility_checkbox, self.loop_checkbox, self.cursor_checkbox, self.capture_keys_checkbox, self.quality_segmented, self.video_mode_segmented]

        info_frame = customtkinter.CTkFrame(options_frame, fg_color="transparent")
        info_frame.pack(side="top", fill="x", pady=(10, 0), anchor="w", padx=5)
        def open_company_website(event=None):
            import webbrowser
            webbrowser.open_new_tab("https://apsystems.tech/")

        info_label = customtkinter.CTkLabel(info_frame, text="BattleLog v.1.9.3  © Advanced Protection Systems  |  https://apsystems.tech/", font=(None, 11, "italic"), text_color="#FFFFFF", cursor="hand2")
        info_label.pack(side="left", anchor="w")
        info_label.bind("<Button-1>", open_company_website)
        return options_frame

    def _save_monitor_selections(self):
        photo_states = [var.get() for var in self.monitor_vars]
        self.config_manager.set_photo_monitors(photo_states)
        
        video_states = [var.get() for var in self.video_monitor_vars]
        self.config_manager.set_video_monitors(video_states)

    def _on_language_change(self, lang):
        self.config_manager.set_language(lang)
        self.language = lang
        self.update_app_language(lang)

    def _on_quality_change(self, selected_value):
        tr = TRANSLATIONS[self.language]
        reverse_map = {tr["quality_high"]: "high", tr["quality_medium"]: "medium", tr["quality_low"]: "low"}
        quality_key = reverse_map.get(selected_value, "high")
        self.video_quality_var.set(quality_key)
        self.config_manager.set_video_quality(quality_key)

    def _on_video_mode_change(self, selected_display_value):
        tr = TRANSLATIONS[self.language]
        reverse_map = {tr["mode_separate"]: "separate", tr["mode_merged"]: "merged"}
        internal_mode = reverse_map.get(selected_display_value, "separate")
        
        self.video_recording_mode_var.set(internal_mode)
        self.config_manager.set_video_recording_mode(internal_mode)

    def _on_duration_change(self, event):
        try:
            raw_value = self.duration_entry.get()
            if raw_value == "": return
            duration = int(raw_value)
            original_duration = duration
            if duration < 1: duration = 1
            elif duration > 120: duration = 120
            if duration != original_duration:
                current_cursor = self.duration_entry.index(tkinter.INSERT)
                self.duration_entry.delete(0, "end")
                self.duration_entry.insert(0, str(duration))
                new_cursor = min(current_cursor, len(str(duration)))
                self.duration_entry.icursor(new_cursor)
                self.duration_entry.configure(border_color="red")
                self.after(1000, lambda: self.duration_entry.configure(border_color="default"))
            self.config_manager.set_video_duration(str(duration))
        except ValueError:
            if hasattr(self, '_last_valid_duration'):
                self.duration_entry.delete(0, "end")
                self.duration_entry.insert(0, self._last_valid_duration)
            else:
                self.duration_entry.delete(0, "end")
                self.duration_entry.insert(0, "9")
            self.duration_entry.configure(border_color="red")
            self.after(1000, lambda: self.duration_entry.configure(border_color="default"))
        try:
            self._last_valid_duration = self.duration_entry.get()
        except:
            self._last_valid_duration = "540"

    def _on_loop_record_change(self):
        self.config_manager.set_loop_record(self.loop_record_var.get())

    def _on_record_cursor_change(self):
        self.config_manager.set_record_cursor(self.cursor_record_var.get())

    def _on_capture_keys_change(self):
        self.config_manager.set_capture_keys(self.capture_keys_var.get())

    def toggle_record(self):
        # Blokuj tylko nowe nagrania podczas robienia zrzutów ekranu,
        # ale zawsze pozwól na zatrzymanie aktywnego nagrywania
        if self.is_processing_screenshot:
            return
        
        # Jeśli trwa przetwarzanie w tle i jesteśmy w trakcie nagrywania, pozwól zatrzymać pętlę
        if self.is_finalizing_video and self.is_recording:
            # Zatrzymaj tylko pętlę nagrywania, pozwól na dokończenie aktualnego przetwarzania
            self.loop_stop_requested = True

        # Jeśli trwa przetwarzanie w tle, nie blokujemy już rozpoczęcia nowego nagrania.
        # Zamiast tego pokazujemy informacyjny status przetwarzania i pozwalamy użytkownikowi
        # rozpocząć nowe nagranie natychmiast.
        if self.is_finalizing_video and not self.is_recording:
            try:
                self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing"], "#FFD700"))
            except Exception:
                pass

        if not self.is_recording:
            # --- Rozpoczęcie pierwszego nagrania ---
            self.manual_stop = False
            self.processing_cancelled.clear()  # Reset flagi anulowania
            self.loop_stop_requested = False   # Reset flagi zatrzymania pętli
            self.set_controls_state("disabled")
            self.screenshot_button.configure(fg_color=self.COLOR_DISABLED)
            # Zmień przycisk na czerwony z ikoną stopu
            self.record_button.configure(
                image=self.stop_icon_image,
                fg_color=self.COLOR_RECORDING,
                hover_color=self.COLOR_RECORDING_HOVER
            )
            self._start_capture_segment()
        else:
            # --- Ręczne zatrzymanie ---
            self.manual_stop = True
            self.is_recording = False # Sygnał dla wątków przechwytywania
            
            # Zatrzymaj pętlę, ale pozwól dokończyć przetwarzanie w tle
            self.loop_stop_requested = True
            
            # NIGDY nie anuluj przetwarzania podczas normalnego zatrzymania nagrywania
            # Pozwól wszystkim aktualnym procesom dokończyć się
            
            self.stop_key_listeners()
            if self.countdown_job:
                self.after_cancel(self.countdown_job)
                self.countdown_job = None
            # Pokaż komunikat zatrzymania. Przywróć przycisk nagrywania tak, aby
            # użytkownik mógł od razu rozpocząć nowe nagranie nawet jeśli przetwarzanie
            # w tle nadal trwa.
            self.update_recording_status(TRANSLATIONS[self.language]["stopping"])
            try:
                self.record_button.configure(
                    state="normal",
                    image=self.video_icon_image,
                    fg_color=self.COLOR_NORMAL,
                    hover_color=self.COLOR_HOVER
                )
            except Exception:
                # Jeśli przy konfiguracji przycisku wystąpi problem, ignorujemy — nie blokuje to przetwarzania
                pass
            self.after(250, self.wait_for_threads_to_finish)

    def _start_capture_segment(self):
        self.is_recording = True
        self.recording_start_time = time.time()
        self.temp_video_files.clear()

        if self.capture_keys_var.get() == "on" and not (self.key_listener and self.key_listener.is_alive()):
            self.start_key_listeners()
        
        try:
            duration_minutes = max(1, min(int(self.duration_entry.get()), 120))
            duration = duration_minutes * 60  # Konwersja minut na sekundy
        except (ValueError, TypeError):
            duration_minutes = 9
            duration = duration_minutes * 60
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(duration_minutes))

        self.recording_threads = []
        selected_monitors = [i + 1 for i, var in enumerate(self.video_monitor_vars) if var.get() == "on"]

        if not selected_monitors:
            self.show_status(TRANSLATIONS[self.language]["error_no_video_monitor"], self.COLOR_ERROR)
            self.reset_status()
            return
        
        for monitor_index in selected_monitors:
            thread = threading.Thread(target=self._capture_to_temp_file_thread, args=(duration, monitor_index))
            self.recording_threads.append(thread)
            thread.start()

        self.update_countdown(duration)

    def wait_for_threads_to_finish(self):
        if any(thread.is_alive() for thread in self.recording_threads):
            self.after(100, self.wait_for_threads_to_finish)
            return
        
        # Wszystkie wątki przechwytywania zakończyły się.
        self._initiate_processing_and_next_step()

    def _initiate_processing_and_next_step(self):
        completed_files = self.temp_video_files.copy()
        
        if completed_files:
            self.is_finalizing_video = True
            keyword = self.keyword_entry.get() or "log"
            mode = self.video_recording_mode_var.get()
            selected_monitors = [i + 1 for i, var in enumerate(self.video_monitor_vars) if var.get() == "on"]
            
            # Enqueue processing task instead of creating a new thread
            task = {
                'keyword': keyword,
                'mode': mode,
                'selected_monitors': selected_monitors,
                'files_to_process': completed_files
            }
            
            with self.processing_worker_lock:
                self.processing_queue.append(task)
                if not self.processing_worker_running:
                    self.processing_worker_running = True
                    self.processing_worker_thread = threading.Thread(target=self._processing_worker)
                    self.processing_worker_thread.start()
            
            # Show processing status immediately
            self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing"], "#FFD700"))

        # Kontynuuj pętlę nagrywania tylko jeśli nie zostało ręcznie zatrzymane 
        # i przetwarzanie nie zostało anulowane
        if (self.loop_record_var.get() == "on" and 
            not self.manual_stop and 
            not self.loop_stop_requested and
            not self.processing_cancelled.is_set()):
            self._start_capture_segment()
        else:
            # Jeśli zatrzymano pętlę, ale nie ręcznie - zatrzymaj nagrywanie
            if self.loop_stop_requested and not self.manual_stop:
                self.manual_stop = True
                
            if not completed_files: # Jeśli nic nie zostało nagrane, zresetuj od razu
                self.reset_status()
            else:
                # Użyj nowego systemu statusu przetwarzania z wyrazistym kolorem
                self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing"], "#FFD700"))

    def _processing_thread(self, keyword, mode, selected_monitors, files_to_process):
        try:
            # Ustaw niski priorytet dla całego wątku przetwarzania
            try:
                if not IS_WIN:
                    os.nice(10)  # Zwiększ nice value (niższy priorytet)
                else:
                    import win32process
                    win32process.SetPriorityClass(-1, win32process.BELOW_NORMAL_PRIORITY_CLASS)
            except:
                pass  # Kontynuuj nawet jeśli nie udało się ustawić priorytetu
            
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            if not self.processing_cancelled.is_set():
                if mode == "separate":
                    self._process_separate_videos(keyword, timestamp_str, files_to_process)
                elif mode == "merged":
                    self._process_merged_video(keyword, timestamp_str, selected_monitors, files_to_process)
            
            # Komunikaty o zakończeniu będą wyświetlane w finally gdy wszystkie procesy się zakończą
            if not self.processing_cancelled.is_set():
                self.after(0, lambda: self.update_recording_status(TRANSLATIONS[self.language]["recorded"], self.COLOR_SUCCESS))

        except Exception as e:
            if not self.processing_cancelled.is_set():
                error_details = traceback.format_exc()
                print(f"KRYTYCZNY BŁĄD PODCZAS PRZETWARZANIA WIDEO (Etap 2):\n{error_details}")
                self.after(0, lambda: self.show_status(f"Błąd przetwarzania: {e}", self.COLOR_ERROR))
                self.after(4000, self.hide_status)
        finally:
            self.processing_process = None
            self.is_finalizing_video = False
            
            # Worker handles counter management and completion status
            # Just handle manual stop reset if needed
            if self.manual_stop:
                with self.processing_lock:
                    threads_remaining = self.active_processing_threads
                if threads_remaining <= 1:  # This thread is about to finish
                    self.after(0, self.reset_status)
            
            # Sprzątanie przetworzonych plików
            for path, _ in files_to_process.values():
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError as e:
                    print(f"Nie udało się usunąć przetworzonego pliku tymczasowego {path}: {e}")
    
    def set_controls_state(self, state):
        self.expand_button.configure(state=state)
        self.keyword_entry.configure(state=state)
        self.save_name_button.configure(state=state)
        self.duration_entry.configure(state=state)
        self.identify_monitors_button.configure(state=state)
        for control in self.other_controls:
            control.configure(state=state)
        for checkbox in self.monitor_checkboxes:
            checkbox.configure(state=state)
        for checkbox in self.video_checkboxes:
            checkbox.configure(state=state)
        
        self.loop_label.configure(state=state)
        self.cursor_label.configure(state=state)
        self.keys_label.configure(state=state if PYNPUT_AVAILABLE else "disabled")
    
    def draw_cursor_on_image(self, image_pil, cursor_x, cursor_y):
        if not PYAUTOGUI_AVAILABLE or self.cursor_record_var.get() != "on":
            return image_pil
        
        if cursor_x is not None and cursor_y is not None:
            try:
                draw = ImageDraw.Draw(image_pil)
                cursor_size = 15
                draw.line((cursor_x - cursor_size, cursor_y, cursor_x + cursor_size, cursor_y), fill='red', width=3)
                draw.line((cursor_x, cursor_y - cursor_size, cursor_x, cursor_y + cursor_size), fill='red', width=3)
            except Exception as e:
                print(f"Błąd rysowania kursora: {e}")
        return image_pil

    def format_key_name(self, key):
        key_str = str(key)
        key_mappings = {'Key.ctrl_l': 'CTRL', 'Key.ctrl_r': 'CTRL', 'Key.alt_l': 'ALT', 'Key.alt_r': 'ALT', 'Key.shift_l': 'SHIFT', 'Key.shift_r': 'SHIFT', 'Key.space': 'SPACE', 'Key.enter': 'ENTER', 'Key.tab': 'TAB', 'Key.esc': 'ESC', 'Key.backspace': 'BACKSPACE', 'Key.delete': 'DELETE', 'Key.up': '↑', 'Key.down': '↓', 'Key.left': '←', 'Key.right': '→', 'Key.f1': 'F1', 'Key.f2': 'F2', 'Key.f3': 'F3', 'Key.f4': 'F4', 'Key.f5': 'F5', 'Key.f6': 'F6', 'Key.f7': 'F7', 'Key.f8': 'F8', 'Key.f9': 'F9', 'Key.f10': 'F10', 'Key.f11': 'F11', 'Key.f12': 'F12'}
        if key_str in key_mappings: return key_mappings[key_str]
        try:
            if key.char: return key.char.upper()
        except AttributeError:
             if key_str.startswith("Key."): return key_str[4:].upper()
        return key_str.upper()

    def format_mouse_button(self, button):
        if hasattr(button, 'name'):
            name = button.name
            return name.capitalize()
        return str(button)

    def start_key_listeners(self):
        if not PYNPUT_AVAILABLE: return
        try:
            self.key_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
            self.key_listener.start()
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll)
            self.mouse_listener.start()
        except Exception as e:
            print(f"Błąd uruchamiania listenerów klawiszy: {e}")
    
    def stop_key_listeners(self):
        try:
            if self.key_listener: self.key_listener.stop(); self.key_listener = None
            if self.mouse_listener: self.mouse_listener.stop(); self.mouse_listener = None
            self.pressed_keys.clear(); self.mouse_buttons.clear()
            if hasattr(self, 'key_times'): self.key_times.clear()
            if hasattr(self, 'mouse_times'): self.mouse_times.clear()
        except Exception as e:
            print(f"Błąd zatrzymywania listenerów klawiszy: {e}")
    
    def on_key_press(self, key):
        try:
            formatted_key = self.format_key_name(key)
            self.pressed_keys.add(formatted_key)
            if hasattr(self, 'key_times'): self.key_times[formatted_key] = time.time()
        except Exception as e:
            print(f"Błąd obsługi naciśnięcia klawisza: {e}")
    
    def on_key_release(self, key):
        try:
            formatted_key = self.format_key_name(key)
            self.pressed_keys.discard(formatted_key)
        except Exception as e:
            print(f"Błąd obsługi zwolnienia klawisza: {e}")
    
    def on_mouse_click(self, x, y, button, pressed):
        try:
            formatted_button = self.format_mouse_button(button)
            if pressed:
                self.mouse_buttons.add(formatted_button)
                if hasattr(self, 'mouse_times'): self.mouse_times[formatted_button] = time.time()
            else:
                self.mouse_buttons.discard(formatted_button)
        except Exception as e:
            print(f"Błąd obsługi kliknięcia myszy: {e}")
    
    def on_mouse_scroll(self, x, y, dx, dy):
        pass
    
    def draw_keys_on_image(self, image_pil, draw_here=False, cursor_x=None, cursor_y=None):
        if not self.capture_keys_var.get() == "on" or not PYNPUT_AVAILABLE:
            return image_pil
        
        now = time.time()
        hold_s = self.OVERLAY_HOLD_MS / 1000.0
        keys_to_show = {k for k, t in self.key_times.items() if (now - t) < hold_s} | self.pressed_keys
        mouse_to_show = {b for b, t in self.mouse_times.items() if (now - t) < hold_s} | self.mouse_buttons

        if not draw_here or not (keys_to_show or mouse_to_show):
            return image_pil

        try:
            draw = ImageDraw.Draw(image_pil)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font = ImageFont.load_default()

            text_lines = []
            if keys_to_show:
                text_lines.append(f"Keys: {', '.join(sorted(list(keys_to_show)))}")
            if mouse_to_show:
                text_lines.append(f"Mouse: {', '.join(sorted(list(mouse_to_show)))}")
            
            overlay_text = "\n".join(text_lines)
            
            bbox = draw.multiline_textbbox((0, 0), overlay_text, font=font, spacing=4)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            
            pos_x, pos_y = 15, image_pil.height - (text_height + 15)

            if cursor_x is not None and cursor_y is not None:
                offset_x = 30
                pos_x = cursor_x - text_width - offset_x
                pos_y = cursor_y - 20
                
                if pos_x < 10:
                    pos_x = cursor_x + offset_x

            pos_x = max(10, min(pos_x, image_pil.width - text_width - 10))
            pos_y = max(10, min(pos_y, image_pil.height - text_height - 10))

            background_pos = (pos_x - 5, pos_y - 5, pos_x + text_width + 5, pos_y + text_height + 5)
            
            overlay_bg = Image.new('RGBA', image_pil.size, (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(overlay_bg)
            bg_draw.rectangle(background_pos, fill=(0, 0, 0, 180))
            
            image_pil = Image.alpha_composite(image_pil.convert('RGBA'), overlay_bg).convert('RGB')
            draw = ImageDraw.Draw(image_pil)
            
            draw.multiline_text((pos_x, pos_y), overlay_text, fill="yellow", font=font, spacing=4)

        except Exception as e:
            print(f"Błąd rysowania nakładki klawiszy: {e}")
            
        return image_pil
        
    def _create_filename(self, timestamp_str, keyword, media_type, monitor_number, extension, actual_duration=None):
        safe_keyword = keyword.strip()
        forbidden_chars = '<>:"/\\|?*'
        for char in forbidden_chars: safe_keyword = safe_keyword.replace(char, '_')
        safe_keyword = safe_keyword.replace(' ', '_')
        safe_keyword = safe_keyword or "log"
        duration_suffix = f"--t{actual_duration}s" if actual_duration is not None else ""
        return f"{timestamp_str}_{safe_keyword}--{media_type}--s{monitor_number}{duration_suffix}{extension}"

    def take_screenshot(self, keyword):
        if not keyword: keyword = self.config_manager.get_radar_name() or "log"
        self.is_processing_screenshot = True
        self.show_status(TRANSLATIONS[self.language]["saving"]) 
        self.set_controls_state("disabled")
        self.record_button.configure(state="disabled")
        self.update_idletasks()
        try:
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_dir = os.path.join(self.config_manager.config_dir, datetime.now().strftime("%Y-%m-%d"))
            os.makedirs(log_dir, exist_ok=True)
            with mss.mss() as sct:
                selected_monitors_indices = [i for i, var in enumerate(self.monitor_vars) if var.get() == "on"]
                if not selected_monitors_indices: raise Exception(TRANSLATIONS[self.language]["no_monitor_selected"])
                for i in selected_monitors_indices:
                    monitor_number = i + 1
                    filename = self._create_filename(timestamp_str, keyword, "photo", monitor_number, ".jpg")
                    output_path = os.path.join(log_dir, filename)
                    sct_img = sct.grab(sct.monitors[monitor_number])
                    pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    pil_img.save(output_path, "jpeg", quality=80)
            self.show_status(TRANSLATIONS[self.language]["saved"], self.COLOR_SUCCESS)
        except Exception as e:
            self.show_status(TRANSLATIONS[self.language]["save_error"].format(error=str(e)), self.COLOR_ERROR)
        self.after(1500, self.reset_status)

    def _capture_to_temp_file_thread(self, duration, monitor_index):
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time() * 1000)
            temp_filename = f"battlelog_temp_{timestamp}_{monitor_index}.mp4"
            temp_output_path = os.path.join(temp_dir, temp_filename)
            
            with mss.mss() as sct:
                monitor = sct.monitors[monitor_index]
                frame_width = monitor["width"] - (monitor["width"] % 2)
                frame_height = monitor["height"] - (monitor["height"] % 2)
                monitor_adjusted = {**monitor, 'width': frame_width, 'height': frame_height}
                
                ffmpeg_path = resource_path('ffmpeg')
                if IS_WIN and not ffmpeg_path.endswith('.exe'): ffmpeg_path += '.exe'
                
                command = [
                    ffmpeg_path, '-y',
                    '-f', 'rawvideo',
                    '-vcodec', 'rawvideo',
                    '-s', f'{frame_width}x{frame_height}',
                    '-pix_fmt', 'bgr24',
                    '-framerate', str(self.RECORD_FPS),
                    '-i', '-',
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '0',
                    temp_output_path
                ]
                
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if IS_WIN else 0
                # ensure bundled ffmpeg is executable on Unix-like systems (fixes permission lost after download)
                try:
                    if not IS_WIN and os.path.exists(ffmpeg_path) and not os.access(ffmpeg_path, os.X_OK):
                        os.chmod(ffmpeg_path, 0o755)
                except Exception:
                    pass
                ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=creationflags)
                
                capture_start_time = time.monotonic()
                
                while self.is_recording and (time.monotonic() - capture_start_time) < duration:
                    loop_start_time = time.monotonic()
                    
                    sct_img = sct.grab(monitor_adjusted)
                    pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    relative_cursor_x, relative_cursor_y, cursor_on_this_monitor = None, None, False

                    if PYAUTOGUI_AVAILABLE:
                        global_mouse_x, global_mouse_y = pyautogui.position()
                        if (monitor_adjusted['left'] <= global_mouse_x < monitor_adjusted['left'] + monitor_adjusted['width'] and
                            monitor_adjusted['top'] <= global_mouse_y < monitor_adjusted['top'] + monitor_adjusted['height']):
                            cursor_on_this_monitor = True
                            relative_cursor_x = global_mouse_x - monitor_adjusted['left']
                            relative_cursor_y = global_mouse_y - monitor_adjusted['top']

                    pil_img = self.draw_cursor_on_image(pil_img, relative_cursor_x, relative_cursor_y)
                    pil_img = self.draw_keys_on_image(pil_img, draw_here=cursor_on_this_monitor, cursor_x=relative_cursor_x, cursor_y=relative_cursor_y)
                    
                    frame_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    try:
                        ffmpeg_process.stdin.write(frame_bgr.tobytes())
                    except (IOError, BrokenPipeError):
                        break
                    
                    elapsed_time = time.monotonic() - loop_start_time
                    sleep_time = (1 / self.RECORD_FPS) - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                actual_duration = int(time.monotonic() - capture_start_time)
                self.temp_video_files[monitor_index] = (temp_output_path, actual_duration)

                # Najpierw zakończ pisanie do FFmpeg
                try:
                    _, stderr = ffmpeg_process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    ffmpeg_process.kill()
                    _, stderr = ffmpeg_process.communicate()
                
                # Dopiero potem zamknij stdin (jeśli jeszcze nie zamknięty)
                if ffmpeg_process.stdin and not ffmpeg_process.stdin.closed:
                    ffmpeg_process.stdin.close()
                    
                if ffmpeg_process.returncode != 0:
                    print(f"--- BŁĘDY Z FFmpeg (PRZECHWYTYWANIE {monitor_index}) ---\n{stderr.decode('utf-8', errors='ignore')}\n---")

        except Exception:
            error_details = traceback.format_exc()
            print(f"KRYTYCZNY BŁĄD W WĄTKU PRZECHWYTYWANIA (monitor {monitor_index}):\n{error_details}")
            if monitor_index in self.temp_video_files:
                path, _ = self.temp_video_files[monitor_index]
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                del self.temp_video_files[monitor_index]

    def _process_separate_videos(self, keyword, timestamp_str, files_to_process):
        log_dir = os.path.join(self.config_manager.config_dir, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(log_dir, exist_ok=True)
        
        quality_key = self.video_quality_var.get()
        crf_map = {"high": "20", "medium": "25", "low": "30"}
        crf_value = crf_map.get(quality_key, "25")
        
        ffmpeg_path = resource_path('ffmpeg')
        if IS_WIN and not ffmpeg_path.endswith('.exe'): ffmpeg_path += '.exe'

        total_files = len(files_to_process)
        completed_files = 0

        for monitor_index, (temp_path, actual_duration) in files_to_process.items():
            # Sprawdź czy operacja została anulowana
            if self.processing_cancelled.is_set():
                break
                
            final_filename = self._create_filename(timestamp_str, keyword, "video", monitor_index, ".mp4", actual_duration)
            final_output_path = os.path.join(log_dir, final_filename)

            command = [
                ffmpeg_path, '-y',
                '-i', temp_path,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-crf', crf_value,
                '-filter:v', f'scale={self.TILE_WIDTH}:{self.TILE_HEIGHT},setpts=0.5*PTS',
                '-r', '30',
                final_output_path
            ]
            
            # Uruchom proces z niskim priorytetem i możliwością anulowania
            try:
                process = subprocess.Popen(command, 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE,
                                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                
                # Ustaw niski priorytet procesu
                try:
                    if hasattr(psutil, 'Process'):
                        p = psutil.Process(process.pid)
                        p.nice(19 if not IS_WIN else psutil.BELOW_NORMAL_PRIORITY_CLASS)
                except:
                    pass  # Kontynuuj nawet jeśli nie udało się ustawić priorytetu
                
                self.processing_process = process
                
                # Czekaj na zakończenie z możliwością przerwania
                while process.poll() is None:
                    if self.processing_cancelled.is_set():
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                        except:
                            try:
                                process.kill()
                            except:
                                pass
                        break
                    time.sleep(0.1)  # Krótka pauza żeby nie blokować UI
                
                if not self.processing_cancelled.is_set() and process.returncode == 0:
                    completed_files += 1
                    # Aktualizuj komunikat o przetwarzaniu (bez szczegółowego progress dla pojedynczego wątku)
                    self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing"], "#FFD700"))
                elif process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, command)
                    
            except Exception as e:
                if not self.processing_cancelled.is_set():
                    raise e

    def _process_merged_video(self, keyword, timestamp_str, monitor_indices, files_to_process):
        log_dir = os.path.join(self.config_manager.config_dir, datetime.now().strftime("%Y-%m-%d"))
        os.makedirs(log_dir, exist_ok=True)

        quality_key = self.video_quality_var.get()
        crf_map = {"high": "20", "medium": "25", "low": "30"}
        crf_value = crf_map.get(quality_key, "25")

        ffmpeg_path = resource_path('ffmpeg')
        if IS_WIN and not ffmpeg_path.endswith('.exe'): ffmpeg_path += '.exe'
        
        temp_paths_in_order = [(files_to_process[idx][0], files_to_process[idx][1]) for idx in monitor_indices if idx in files_to_process]
        num_monitors = len(temp_paths_in_order)
        
        if num_monitors == 0: return

        command = [ffmpeg_path, '-y']
        for temp_path, _ in temp_paths_in_order:
            command.extend(['-i', temp_path])

        if num_monitors <= 2:
            canvas_width, canvas_height = self.TILE_WIDTH * num_monitors, self.TILE_HEIGHT
        else:
            canvas_width, canvas_height = self.TILE_WIDTH * 2, self.TILE_HEIGHT * 2
        
        filter_complex = [f"[{i}:v]scale={self.TILE_WIDTH}:{self.TILE_HEIGHT}[v{i}]" for i in range(num_monitors)]
        
        if num_monitors == 1: filter_complex.append("[v0]pad=w=iw:h=ih[outv]")
        elif num_monitors == 2: filter_complex.append("[v0][v1]hstack=inputs=2[outv]")
        elif num_monitors == 3: filter_complex.extend([f"color=s={canvas_width}x{canvas_height}:c=black[base]", "[base][v0]overlay=0:0[tmp1]", "[tmp1][v1]overlay=w:0[tmp2]", "[tmp2][v2]overlay=0:h[outv]"])
        elif num_monitors == 4: filter_complex.extend(["[v0][v1]hstack[top]", "[v2][v3]hstack[bottom]", "[top][bottom]vstack[outv]"])
        
        filter_complex.append("[outv]setpts=0.5*PTS[final_v]")

        command.extend(['-filter_complex', ";".join(filter_complex), '-map', '[final_v]'])
        
        actual_duration = temp_paths_in_order[0][1] if temp_paths_in_order else 0

        monitor_id_str = "merged-" + "-".join(map(str, monitor_indices))
        final_filename = self._create_filename(timestamp_str, keyword, "video", monitor_id_str, ".mp4", actual_duration)
        final_output_path = os.path.join(log_dir, final_filename)
        
        command.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'ultrafast', '-crf', crf_value, '-r', '30', final_output_path])

        # Uruchom proces z możliwością anulowania
        try:
            process = subprocess.Popen(command, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            
            # Ustaw niski priorytet procesu
            try:
                if hasattr(psutil, 'Process'):
                    p = psutil.Process(process.pid)
                    p.nice(19 if not IS_WIN else psutil.BELOW_NORMAL_PRIORITY_CLASS)
            except:
                pass  # Kontynuuj nawet jeśli nie udało się ustawić priorytetu
            
            self.processing_process = process
            
            # Czekaj na zakończenie z możliwością przerwania
            while process.poll() is None:
                if self.processing_cancelled.is_set():
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except:
                        try:
                            process.kill()
                        except:
                            pass
                    break
                time.sleep(0.1)  # Krótka pauza żeby nie blokować UI
            
            if not self.processing_cancelled.is_set() and process.returncode == 0:
                # Aktualizuj komunikat o przetwarzaniu
                self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing"], "#FFD700"))
            elif process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)
                
        except Exception as e:
            if not self.processing_cancelled.is_set():
                raise e

    def _toggle_always_on_top(self):
        self.attributes("-topmost", self.always_on_top_var.get() == "on")
        self.config_manager.set_always_on_top(self.always_on_top_var.get())

    def _disable_maximize_button(self, event=None):
        """
        Wyłącza przycisk maksymalizacji i odświeża ramkę okna.
        Wywoływana po wyświetleniu okna (zdarzenie <Map>).
        """
        if IS_WIN and PYWIN32_AVAILABLE:
            try:
                import ctypes
                hwnd = self.winfo_id()
                style = GetWindowLong(hwnd, GWL_STYLE)
                style &= ~WS_MAXIMIZEBOX  # Wyłącz przycisk maksymalizacji
                style &= ~WS_THICKFRAME   # Wyłącz możliwość zmiany rozmiaru
                SetWindowLong(hwnd, GWL_STYLE, style)

                # Kluczowy fragment: zmuś system Windows do przerysowania ramki
                # z uwzględnieniem nowych stylów. Flagi oznaczają:
                # SWP_NOMOVE, SWP_NOSIZE, SWP_NOZORDER, SWP_FRAMECHANGED
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
            except Exception as e:
                print(f"Nie można było usunąć przycisku maksymalizacji: {e}")

    def _update_button_visibility(self):
        self.screenshot_button.pack_forget(); self.record_button.pack_forget()
        if self.photo_button_visible_var.get() == "on": self.screenshot_button.pack(side="left", padx=(0, 5))
        if self.video_button_visible_var.get() == "on": self.record_button.pack(side="left", padx=(5, 0))
        self.config_manager.set_photo_button_visible(self.photo_button_visible_var.get())
        self.config_manager.set_video_button_visible(self.video_button_visible_var.get())

    def update_recording_status(self, status="", color="white"):
        """Aktualizuje status nagrywania i łączy z procesowaniem"""
        self.recording_status = status
        self._update_combined_status(color)

    def update_processing_status(self, status="", color="#FFD700"):  
        """Aktualizuje status przetwarzania i łączy z nagrywaniem"""
        self.processing_status = status
        self._update_combined_status(color)

    def _update_combined_status(self, color="white"):
        """Łączy statusy nagrywania i przetwarzania w jeden komunikat"""
        status_parts = []
        
        if self.recording_status:
            status_parts.append(f"🔴 {self.recording_status}")
        
        if self.processing_status:
            status_parts.append(f"⚙️ {self.processing_status}")
        
        if status_parts:
            combined_text = " | ".join(status_parts)
            self.status_label.configure(text=combined_text, text_color=color)
            self.status_bar_frame.place(relx=0, rely=1, anchor="sw", relwidth=1)
        else:
            self.hide_status()

    def show_status(self, text, color="white"):
        """Zachowana kompatybilność - wyświetla pojedynczy status"""
        self.recording_status = ""
        self.processing_status = ""
        self.status_label.configure(text=text, text_color=color)
        self.status_bar_frame.place(relx=0, rely=1, anchor="sw", relwidth=1)

    def hide_status(self):
        self.recording_status = ""
        self.processing_status = ""
        self.status_bar_frame.place_forget()
        self.status_label.configure(text="")
        self.status_bar_frame.place_forget()

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.options_frame.grid(row=0, column=2, padx=(10, 10), pady=10, sticky="nsew")
            self.grid_columnconfigure(2, weight=3); self.expand_button.configure(text="<")
        else:
            self.options_frame.grid_forget(); self.grid_columnconfigure(2, weight=0); self.expand_button.configure(text=">")
        self.update_idletasks(); self.update_window_size()

    def update_window_size(self):
        if self.start_panel is not None: return
        if self.is_expanded:
            self.geometry(f"600x750")
        else:
            self.geometry(f"220x75")

    def limit_keyword_length(self, *args):
        value = self.keyword_var.get()
        if len(value) > self.keyword_char_limit: self.keyword_var.set(value[:self.keyword_char_limit])

    def trigger_screenshot(self):
        if self.is_processing_screenshot or self.is_recording: return
        self.take_screenshot(self.keyword_entry.get() or "log")

    def update_countdown(self, remaining_time):
        if not self.is_recording or self.manual_stop:
            # Wyczyść status nagrywania gdy nagranie się kończy
            self.update_recording_status("")
            return
        
        if remaining_time > 0:
            recording_text = TRANSLATIONS[self.language]["recording"].format(seconds=int(remaining_time))
            self.update_recording_status(recording_text)
            self.countdown_job = self.after(1000, lambda: self.update_countdown(remaining_time - 1))
        else:
            self.is_recording = False
            self.update_recording_status("")
            self.after(250, self.wait_for_threads_to_finish)

    def open_log_folder(self):
        log_path = os.path.abspath(self.config_manager.config_dir)
        os.makedirs(log_path, exist_ok=True)
        try:
            if sys.platform.startswith('linux'):
                subprocess.Popen(["xdg-open", log_path], env={k: v for k, v in os.environ.items() if k != 'LD_LIBRARY_PATH'})
            elif IS_WIN: os.startfile(log_path)
            elif sys.platform == "darwin": subprocess.Popen(["open", log_path])
        except (OSError, FileNotFoundError) as e:
            self.show_status(TRANSLATIONS[self.language]["open_folder_error"].format(error=str(e)), self.COLOR_ERROR)

    def identify_monitors(self):
        if self.is_recording or self.is_processing_screenshot: return
        self.show_status(TRANSLATIONS[self.language]["identify_monitors_status"], self.COLOR_INFO)
        self.set_controls_state("disabled"); self.record_button.configure(state="disabled")
        self.monitor_id_windows = []
        with mss.mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:]):
                monitor_id = i + 1
                monitor_window = customtkinter.CTkToplevel(self)
                monitor_window.geometry(f"150x80+{monitor['left'] + 10}+{monitor['top'] + 10}")
                monitor_window.wm_attributes("-topmost", True); monitor_window.wm_attributes("-alpha", 0.8)
                monitor_window.configure(fg_color="#42A5F5")
                label = customtkinter.CTkLabel(monitor_window, text=TRANSLATIONS[self.language]["monitor_label"].format(id=monitor_id, size=f"{monitor['width']}x{monitor['height']}"), text_color="white", font=("Arial", 10, "bold"))
                label.pack(pady=5); self.monitor_id_windows.append(monitor_window)
        self.after(3000, self.close_monitor_id_windows)

    def close_monitor_id_windows(self):
        for window in self.monitor_id_windows: window.destroy()
        self.monitor_id_windows = []; self.reset_status()

    def reset_status(self):
        self.is_processing_screenshot = False
        self.is_recording = False
        self.is_finalizing_video = False
        self.manual_stop = False
        self.loop_stop_requested = False  # Reset flagi zatrzymania pętli
        
        # Czyścimy tylko status nagrywania, zachowujemy status przetwarzania jeśli trwa
        self.update_recording_status("")  # Wyczyść komunikat o nagrywaniu
        
        self.set_controls_state("normal")
        # Przywróć normalny niebieski kolor i ikonę kamery 
        self.record_button.configure(
            state="normal", 
            image=self.video_icon_image,
            fg_color=self.COLOR_NORMAL,
            hover_color=self.COLOR_HOVER
        )
        self.screenshot_button.configure(fg_color=self.COLOR_NORMAL)
        
        # Nie czyścimy całego paska statusu, aby zachować informację o przetwarzaniu
        if not self.processing_status:
            self.hide_status()

    def _processing_worker(self):
        """Worker thread that processes tasks from the queue sequentially"""
        while True:
            task = None
            
            with self.processing_worker_lock:
                if self.processing_queue:
                    task = self.processing_queue.popleft()
                else:
                    # No more tasks, stop the worker
                    self.processing_worker_running = False
                    break
            
            if task:
                # Increment active processing counter
                with self.processing_lock:
                    self.active_processing_threads += 1
                
                try:
                    # Process the task using existing _processing_thread logic
                    self._processing_thread(
                        task['keyword'], 
                        task['mode'], 
                        task['selected_monitors'], 
                        task['files_to_process']
                    )
                except Exception as e:
                    print(f"Error in processing worker: {e}")
                finally:
                    # Decrement counter in finally block
                    with self.processing_lock:
                        self.active_processing_threads -= 1
                        threads_remaining = self.active_processing_threads
                    
                    # If this was the last task and no more are queued, show completion
                    with self.processing_worker_lock:
                        queue_empty = len(self.processing_queue) == 0
                    
                    if threads_remaining == 0 and queue_empty:
                        if not self.processing_cancelled.is_set():
                            self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing_completed"], "#32CD32"))
                            self.after(2000, lambda: self.update_processing_status(""))
                        else:
                            self.after(0, lambda: self.update_processing_status(TRANSLATIONS[self.language]["processing_cancelled"], "#FFA500"))
                            self.after(1500, lambda: self.update_processing_status(""))

    def _check_processing_responsiveness(self):
        """Okresowo sprawdza czy przetwarzanie nie blokuje UI"""
        if self.is_finalizing_video and not self.processing_cancelled.is_set():
            # Pozwól na przetwarzanie eventów UI
            self.update_idletasks()
            # Zaplanuj następne sprawdzenie za 100ms
            self.after(100, self._check_processing_responsiveness)

    def cleanup_temp_files(self):
        if hasattr(self, 'temp_video_files'):
            for path, _ in self.temp_video_files.values():
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError as e:
                    print(f"Nie udało się usunąć pliku tymczasowego {path}: {e}")
            self.temp_video_files.clear()
    
    def needs_radar_name_dialog(self):
        old_config_file = os.path.join(self.application_path, "battlelog_config.json")
        if os.path.exists(old_config_file) and old_config_file != self.config_manager.config_file:
            try:
                with open(old_config_file, 'r', encoding='utf-8') as f:
                    old_config = json.load(f)
                    if 'radar_name' in old_config and old_config['radar_name'] != "Radar name":
                        self.config_manager.set_radar_name(old_config['radar_name'])
                        os.remove(old_config_file)
                        return False
                os.remove(old_config_file)
            except Exception as e:
                print(f"Błąd przenoszenia starej konfiguracji: {e}")
        
        radar_name = self.config_manager.get_radar_name()
        if radar_name is None or radar_name == "Radar name":
            return True
        else:
            self.keyword_entry.delete(0, "end")
            self.keyword_entry.insert(0, radar_name)
            return False
    
    def show_radar_name_dialog(self):
        try:
            self.deiconify(); self.update()
            dialog = RadarNameDialog(self)
            self.withdraw()
            self.wait_window(dialog)
            result = dialog.get_result()
            if result:
                self.config_manager.set_radar_name(result)
                self.keyword_entry.delete(0, "end")
                self.keyword_entry.insert(0, result)
            else:
                self.keyword_entry.delete(0, "end")
                self.keyword_entry.insert(0, "Radar name")
            self.deiconify(); self.lift()
        except Exception as e:
            print(f"Błąd w dialogu: {e}")
            self.deiconify()
    
    def _sanitize_radar_name(self, name):
        sanitized_name = name.strip()
        forbidden_chars = '<>:"/\\|?*'
        for char in forbidden_chars: sanitized_name = sanitized_name.replace(char, '_')
        sanitized_name = sanitized_name.replace(' ', '_')
        return sanitized_name

    def save_radar_name_from_settings(self):
        current_name = self.keyword_var.get()
        sanitized_name = self._sanitize_radar_name(current_name)
        if not sanitized_name: return
        self.keyword_var.set(sanitized_name)
        self.config_manager.set_radar_name(sanitized_name)
        self.show_status(TRANSLATIONS[self.language]["radar_name_saved"], self.COLOR_SUCCESS)
        self.after(2000, self.reset_status)

    def show_start_panel(self):
        self.deiconify()
        self.geometry("600x520")
        self.update_idletasks()
        self.start_panel = customtkinter.CTkFrame(self, fg_color="#101820", corner_radius=12)
        self.start_panel.place(relx=0.5, rely=0.5, anchor="c", relwidth=0.7, relheight=0.5)
        self.start_lang_var = customtkinter.StringVar(value="PL")
        lang_segmented = customtkinter.CTkSegmentedButton(self.start_panel, values=["PL", "EN", "UA"], variable=self.start_lang_var, command=self.update_start_panel_language)
        lang_segmented.pack(pady=(20, 10))
        self.start_title_label = customtkinter.CTkLabel(self.start_panel, text=TRANSLATIONS["PL"]["welcome"], font=("Arial", 20, "bold"), wraplength=420, justify="left")
        self.start_title_label.pack(pady=(0, 10))
        
        def format_desc(desc):
            idx = desc.find("), ")
            return desc[:idx+3] + "\n" + desc[idx+3:] if idx != -1 else desc

        self.start_desc_label = customtkinter.CTkLabel(self.start_panel, text=format_desc(TRANSLATIONS["PL"]["desc"]), font=("Arial", 13), wraplength=420, justify="center")
        self.start_desc_label.pack(pady=(0, 15))
        self.start_name_var = customtkinter.StringVar()
        self.start_name_entry = customtkinter.CTkEntry(self.start_panel, width=300, textvariable=self.start_name_var, placeholder_text=TRANSLATIONS["PL"]["name_placeholder"])
        self.start_name_entry.pack(pady=(0, 8))
        self.start_name_entry.focus()
        self.start_name_entry.bind("<Return>", lambda e: self._start_panel_ok())
        button_frame = customtkinter.CTkFrame(self.start_panel, fg_color="transparent")
        button_frame.pack(pady=(0, 0))
        self.start_save_btn = customtkinter.CTkButton(button_frame, text=TRANSLATIONS["PL"]["save"], width=120, height=32, command=self._start_panel_ok)
        self.start_save_btn.pack(side="left", padx=(0, 10))
        self.start_save_btn_tooltip = ToolTip(self.start_save_btn, TRANSLATIONS["PL"]["tooltip_save"])
        self.lift()
        self.update_window_size()
        self.set_controls_state("disabled")

    def update_start_panel_language(self, lang):
        tr = TRANSLATIONS[lang]
        self.start_title_label.configure(text=tr["welcome"])
        def format_desc(desc):
            idx = desc.find("), ")
            return desc[:idx+3] + "\n" + desc[idx+3:] if idx != -1 else desc
        self.start_desc_label.configure(text=format_desc(tr["desc"]), justify="center")
        self.start_name_entry.configure(placeholder_text=tr["name_placeholder"])
        self.start_save_btn.configure(text=tr["save"])
        self.start_save_btn_tooltip.text = tr["tooltip_save"]

    def _start_panel_ok(self):
        raw_name = self.start_name_var.get()
        name = self._sanitize_radar_name(raw_name)
        lang = self.start_lang_var.get() if hasattr(self, 'start_lang_var') else 'PL'
        if name:
            self.config_manager.set_radar_name(name)
            self.config_manager.set_language(lang)
            self.keyword_var.set(name)
            self.keyword_entry.delete(0, "end")
            self.keyword_entry.insert(0, name)
            self.start_panel.destroy()
            self.start_panel = None
            self.geometry("600x750")
            self.update_window_size()
            self.set_controls_state("normal")
            self.update_app_language(lang)
        else:
            for child in self.start_panel.winfo_children():
                if isinstance(child, customtkinter.CTkEntry):
                    child.configure(border_color="red")
                    self.after(1000, lambda c=child: c.configure(border_color="default"))

    def _start_panel_cancel(self):
        self.keyword_entry.delete(0, "end")
        self.keyword_entry.insert(0, "Radar name")
        self.start_panel.destroy()
        self.start_panel = None
        self.geometry("600x750")
        self.update_window_size()
        self.set_controls_state("normal")

TRANSLATIONS = {
    "PL": {
        "welcome": "Witaj w BattleLog!",
        "desc": "Podaj nazwę radaru (np. 01/25), która będzie używana\nw nazwach plików nagrań i zrzutów ekranu:",
        "save": "Zapisz",
        "note": "Nazwa/Notatka:",
        "language": "Język:",
        "name_placeholder": "np. Radar Alpha, Pozycja 1, itp.",
        "keyword_placeholder": "Wpisz słowo klucz...",
        "always_on_top": "Zawsze na wierzchu",
        "buttons": "Przyciski:",
        "photo": "Zdjęcie",
        "video": "Video",
        "monitors_photo": "Monitory (dla foto):",
        "identify_monitors": "Zidentyfikuj monitory (pokaż ich numery)",
        "monitors_video": "Monitor (dla video):",
        "video_duration": "Czas video:",
        "seconds": "min (max 120)",
        "loop_record": "Nagrywaj w pętli",
        "record_cursor": "Nagrywaj kursor myszy",
        "capture_keys": "Przechwytuj klawisze",
        "capture_keys_disabled": "Przechwytuj klawisze (niedostępne)",
        "open_folder": "Otwórz folder z zapisanymi plikami",
        "saving": "Zapisywanie...",
        "saved": "Zapisano!",
        "save_error": "Błąd zapisu: {error}",
        "recording": "Nagrywanie... {seconds}s",
        "processing": "Przetwarzanie wideo...",
        "processing_progress": "Przetwarzanie... {progress}%",
        "processing_completed": "Zakończono przetwarzanie",
        "processing_cancelled": "Przetwarzanie anulowane",
        "recorded": "Nagrano!",
        "stopping": "Kończenie przechwytywania...",
        "ffmpeg_error": "FFmpeg niedostępny, zapisuję jako .AVI",
        "open_folder_error": "Nie można otworzyć folderu: {error}",
        "identify_monitors_status": "Identyfikacja monitorów...",
        "monitor_label": "Monitor: {id}\nRozmiar: {size}",
        "no_monitor_selected": "Nie wybrano monitora!",
        "record_error": "Błąd nagrywania: {error}",
        "log": "log",
        "tooltip_save": "Zapisz nazwę radaru i kontynuuj",
        "tooltip_screenshot": "Zrób zrzut ekranu (Screenshot)",
        "tooltip_record": "Rozpocznij/Zatrzymaj nagrywanie (Record/Stop)",
        "tooltip_identify_monitors": "Zidentyfikuj monitory (pokaż ich numery)",
        "tooltip_open_folder": "Otwórz folder z zapisanymi plikami",
        "settings_section": "Ustawienia aplikacji:",
        "radar_settings_section": "Nagrania:",
        "radar_name_label": "Nazwa radaru:",
        "photo_video_settings_section": "Ustawienia foto/video:",
        "radar_name_saved": "Nazwa radaru zapisana!",
        "tooltip_save_radar_name": "Zapisz i zastosuj nową nazwę radaru",
        "video_quality": "Jakość video:",
        "quality_high": "Wysoka",
        "quality_medium": "Średnia",
        "quality_low": "Niska",
        "video_recording_mode": "Tryb nagrywania:",
        "mode_separate": "Osobne pliki",
        "mode_merged": "Połączone wideo",
        "error_no_video_monitor": "Błąd: Nie wybrano monitora do nagrywania!",
        "error_too_many_monitors": "Błąd: Max 4 monitory dla trybu połączonego!",
    },
    "EN": {
        "welcome": "Hi in BattleLog!",
        "desc": "Type your radar name (ex. 01/25), it will show up in files and screenshots:",
        "save": "Save",
        "note": "Name/Note:",
        "language": "Language:",
        "name_placeholder": "Radar Alpha, Position 1, etc.",
        "keyword_placeholder": "Type keyword...",
        "always_on_top": "Always on top",
        "buttons": "Buttons:",
        "photo": "Photo",
        "video": "Video",
        "monitors_photo": "Monitors (for photo):",
        "identify_monitors": "Show monitor numbers",
        "monitors_video": "Monitor (for video):",
        "video_duration": "Video time:",
        "seconds": "min (max 120)",
        "loop_record": "Loop recording",
        "record_cursor": "Show mouse cursor",
        "capture_keys": "Capture keys",
        "capture_keys_disabled": "Capture keys (unavailable)",
        "open_folder": "Open saved files folder",
        "saving": "Saving...",
        "saved": "Saved!",
        "save_error": "Save error: {error}",
        "recording": "Recording... {seconds}s",
        "processing": "Processing video...",
        "processing_progress": "Processing... {progress}%",
        "processing_completed": "Processing completed",
        "processing_cancelled": "Processing cancelled",
        "recorded": "Done!",
        "stopping": "Finalizing capture...",
        "ffmpeg_error": "FFmpeg not found, saving as .AVI",
        "open_folder_error": "Can't open folder: {error}",
        "identify_monitors_status": "Showing monitor numbers...",
        "monitor_label": "Monitor: {id}\nSize: {size}",
        "no_monitor_selected": "No monitor selected!",
        "record_error": "Recording error: {error}",
        "log": "log",
        "tooltip_save": "Save radar name and go on",
        "tooltip_screenshot": "Take a screenshot",
        "tooltip_record": "Start/Stop recording",
        "tooltip_identify_monitors": "Show monitor numbers",
        "tooltip_open_folder": "Open saved files folder",
        "settings_section": "App settings:",
        "radar_settings_section": "Recordings:",
        "radar_name_label": "Radar name:",
        "photo_video_settings_section": "Photo/Video Settings:",
        "radar_name_saved": "Radar name saved!",
        "tooltip_save_radar_name": "Save and apply the new radar name",
        "video_quality": "Video quality:",
        "quality_high": "High",
        "quality_medium": "Medium",
        "quality_low": "Low",
        "video_recording_mode": "Recording mode:",
        "mode_separate": "Separate files",
        "mode_merged": "Merged video",
        "error_no_video_monitor": "Error: No monitor selected for recording!",
        "error_too_many_monitors": "Error: Max 4 monitors for merged mode!",
    },
    "UA": {
        "welcome": "Привіт у BattleLog!",
        "desc": "Введи назву радара (наприклад, 01/25), вона з'явить ся в файлах та скріншотах:",
        "save": "Зберегти",
        "note": "Назва/Нотатка:",
        "language": "Мова:",
        "name_placeholder": "Радар Альфа, Позиція 1, тощо.",
        "keyword_placeholder": "Введи ключове слово...",
        "always_on_top": "Завжди зверху",
        "buttons": "Кнопки:",
        "photo": "Фото",
        "video": "Відео",
        "monitors_photo": "Монітори (для фото):",
        "identify_monitors": "Показати номери моніторів",
        "monitors_video": "Монітор (для відео):",
        "video_duration": "Час відео:",
        "seconds": "хв (макс 120)",
        "loop_record": "Запис по колу",
        "record_cursor": "Показати курсор миші",
        "capture_keys": "Захоплювати клавіші",
        "capture_keys_disabled": "Захоплювати клавіші (недоступно)",
        "open_folder": "Відкрити папку з файлами",
        "saving": "Зберігаю...",
        "saved": "Збережено!",
        "save_error": "Помилка збереження: {error}",
        "recording": "Запис... {seconds}с",
        "processing": "Обробка відео...",
        "recorded": "Готово!",
        "stopping": "Завершення захоплення...",
        "ffmpeg_error": "FFmpeg не знайдено, зберігаю як .AVI",
        "open_folder_error": "Не можу відкрити папку: {error}",
        "identify_monitors_status": "Показую номери моніторів...",
        "monitor_label": "Монітор: {id}\nРозмір: {size}",
        "no_monitor_selected": "Монітор не вибрано!",
        "record_error": "Помилка запису: {error}",
        "processing_progress": "Обробка... {progress}%",
        "processing_completed": "Обробку завершено",
        "processing_cancelled": "Обробку скасовано",
        "log": "log",
        "tooltip_save": "Зберегти назву радара і вперед",
        "tooltip_screenshot": "Зробити скріншот",
        "tooltip_record": "Почати/Зупинити запис",
        "tooltip_identify_monitors": "Показати номери моніторів",
        "tooltip_open_folder": "Відкрити папку з файлами",
        "settings_section": "Налаштування додатку:",
        "radar_settings_section": "Записи:",
        "radar_name_label": "Назва радара:",
        "photo_video_settings_section": "Налаштування фото/відео:",
        "radar_name_saved": "Назву радара збережено!",
        "tooltip_save_radar_name": "Зберегти та застосувати нову назву радара",
        "video_quality": "Якість відео:",
        "quality_high": "Висока",
        "quality_medium": "Середня",
        "quality_low": "Низька",
        "video_recording_mode": "Режим запису:",
        "mode_separate": "Окремі файли",
        "mode_merged": "Об'єднане відео",
        "error_no_video_monitor": "Помилка: Не вибрано монітор для запису!",
        "error_too_many_monitors": "Помилка: Макс. 4 монітори для об'єднаного режиму!",
    },
}

if __name__ == "__main__":
    singleton = SingleInstanceApp("BattleLog")
    
    config = ConfigManager("")
    lang = config.get_language()
    
    if singleton.is_running():
        singleton.show_already_running_message(lang)
        sys.exit(0)
    
    if not singleton.create_lock():
        print("BŁĄD: Nie można utworzyć pliku blokady")
        root = tkinter.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("Błąd krytyczny", "Nie można utworzyć pliku blokady. Aplikacja nie może zostać uruchomiona.")
        sys.exit(1)
    
    try:
        app = BattleLogApp()
        app.mainloop()
    finally:
        pass