import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import filedialog, messagebox
from threading import Thread, Event
import time
import queue

# --- Imports for Tray Icon & EXE ---
import pystray
from PIL import Image, ImageDraw, ImageFont
import os
import sys
# -----------------------------------

# ----------------- Helper function for PyInstaller -----------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# -------------------------------------------------------------------

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ----------------- Helper functions -----------------
def file_md5(path: Path, stop_event: Event, chunk_size=8192):
# ... existing code ...
    h = hashlib.md5()
    try:
        with path.open("rb") as f:
            while True:
                if stop_event.is_set():
                    return None  # Interrupted
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
    except Exception as e:
        print(f"Error hashing {path}: {e}")
        return None
    return h.hexdigest()

def ensure_backup_subfolder(backup_root: Path, file: Path):
# ... existing code ...
    file_type = file.suffix[1:].lower() if file.suffix else "other"
    try:
        creation_date = datetime.fromtimestamp(file.stat().st_ctime)
    except Exception:
        creation_date = datetime.now()
    date_folder = creation_date.strftime("%Y-%m-%d")
    target = backup_root / file_type / date_folder
    target.mkdir(parents=True, exist_ok=True)
    return target

def get_next_run_time(schedule_mode, schedule_hour):
# ... existing code ...
    now = datetime.now()
    if schedule_mode == "Run every hour":
        next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    elif schedule_mode == "Run every day at...":
        try:
            run_hour = int(schedule_hour)
            if not 0 <= run_hour <= 23:
                run_hour = 8
        except Exception:
            run_hour = 8
        
        next_run = now.replace(hour=run_hour, minute=0, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
    else:
        next_run = now + timedelta(days=999)
        
    return next_run

def wait_with_stop_check(total_wait_seconds, stop_event: Event):
# ... existing code ...
    waited = 0
    while waited < total_wait_seconds:
        if stop_event.is_set():
            return False
        sleep_duration = min(1.0, total_wait_seconds - waited)
        time.sleep(sleep_duration)
        waited += sleep_duration
    return True

# ----------------- Core backup logic (Unchanged) -----------------
def run_backup_once(source: Path, backup: Path, log_callback, progress_callback, stop_event: Event):
# ... existing code ...
    if not source.exists():
        log_callback(f"Source {source} does not exist.")
        return
    try:
        backup.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log_callback(f"Error creating backup dir {backup}: {e}")
        return
    try:
        files = [p for p in source.iterdir() if p.is_file()]
    except Exception as e:
        log_callback(f"Error reading source folder {source}: {e}")
        return
    total = len(files)
    if total == 0:
        log_callback("No files to backup.")
        progress_callback(0, "")
        return

    log_callback("Indexing existing backup files (this may take a while)...")
    existing_hashes = set()
    try:
        for f in backup.rglob("*"):
            if stop_event.is_set():
                log_callback("Backup stopped during indexing.")
                return
            if f.is_file():
                h = file_md5(f, stop_event)
                if h:
                    existing_hashes.add(h)
                if stop_event.is_set():
                    log_callback("Backup stopped during indexing.")
                    return
    except Exception as e:
        log_callback(f"Error during backup indexing: {e}")
    log_callback(f"Index complete. Found {len(existing_hashes)} existing files.")

    processed = 0
    copied_count = 0
    skipped_count = 0
    for f in files:
# ... existing code ...
        if stop_event.is_set():
            log_callback("Backup stopped by user.")
            break
        processed += 1
        progress_callback(int(processed/total*100), f.name)
        try:
            h = file_md5(f, stop_event)
            if not h:
                if stop_event.is_set():
                    log_callback("Backup stopped during hashing.")
                    break
                log_callback(f"Could not read/hash {f.name}, skipping.")
                continue
            if h in existing_hashes:
                skipped_count += 1
                continue
            target_folder = ensure_backup_subfolder(backup, f)
            target_path = target_folder / f.name
            if target_path.exists():
                ts = datetime.now().strftime("%H%M%S")
                target_path = target_folder / f"{f.stem}_{ts}{f.suffix}"
            shutil.copy2(f, target_path)
            existing_hashes.add(h)
            log_callback(f"Copied {f.name} -> {target_path.relative_to(backup)}")
            copied_count += 1
        except Exception as e:
            log_callback(f"Error copying {f.name}: {e}")

    if skipped_count > 0:
        log_callback(f"Skipped {skipped_count} duplicate files.")
    progress_callback(100, "")
    log_callback(f"Backup run complete. Copied {copied_count} new files.")

# ----------------- GUI Application -----------------
class SmartOrganizerApp(ctk.CTk):
    def __init__(self):
# ... existing code ...
        super().__init__()
        self.title("Smart File Organizer Pro v5 (EXE-Ready)")
        self.geometry("900x600")
        
        # --- MODIFIED: Bind close button ("X") to hide_to_tray ---
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # state
# ... existing code ...
        self.auto_thread = None
        self.manual_thread = None
        self.stop_event = Event()
        self.is_running_auto = False
        self.is_running_manual = False

        # --- NEW: Tray icon state ---
# ... existing code ...
        self.tray_icon = None
        self.tray_thread = None
        # ----------------------------

        self.gui_queue = queue.Queue()
# ... existing code ...
        self.after(100, self.process_gui_queue)

        self.grid_columnconfigure(1, weight=1)
# ... existing code ...
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=180)
# ... existing code ...
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=(10, 5), pady=10)
        self.main = ctk.CTkFrame(self)
        self.main.grid(row=0, column=1, sticky="nswe", padx=(5, 10), pady=10)

        ctk.CTkLabel(self.sidebar, text="Smart Organizer", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10,20))
# ... existing code ...
        self.btn_organizer = ctk.CTkButton(self.sidebar, text="Manual Backup", command=lambda: self.show_frame("organizer"))
        self.btn_auto = ctk.CTkButton(self.sidebar, text="Automation", command=lambda: self.show_frame("auto"))
        self.btn_logs = ctk.CTkButton(self.sidebar, text="Logs", command=lambda: self.show_frame("logs"))
        for b in (self.btn_organizer, self.btn_auto, self.btn_logs):
            b.pack(fill="x", padx=12, pady=6)
        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Idle", anchor="w", font=ctk.CTkFont(size=12))
# ... existing code ...
        self.status_label.pack(side="bottom", fill="x", padx=12, pady=(10,10))

        self.frames = {}
# ... existing code ...
        self._create_organizer_frame()
        self._create_auto_frame()
        self._create_logs_frame()

        self.show_frame("organizer")

        # --- NEW: Setup and start the tray icon ---
# ... existing code ...
        self.setup_tray_icon()
        # ------------------------------------------

    # ---------- Thread-safe GUI updates (Unchanged) ----------
    def process_gui_queue(self):
# ... existing code ...
        while not self.gui_queue.empty():
            try:
                task, args = self.gui_queue.get_nowait()
                task(*args)
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error processing GUI queue: {e}")
        self.after(100, self.process_gui_queue)

    def safe_log(self, text: str):
# ... existing code ...
        self.gui_queue.put((self._log_task, (text,)))

    def safe_progress_update(self, percent, filename):
# ... existing code ...
        self.gui_queue.put((self._progress_update_task, (percent, filename)))

    def safe_set_running_state(self, manual, auto):
# ... existing code ...
        self.gui_queue.put((self._set_running_state_task, (manual, auto)))

    # ---------- GUI Task Implementations (Unchanged) ----------
    def _log_task(self, text: str):
# ... existing code ...
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {text}\n"
        try:
            self.log_preview.insert("end", line)
            self.log_preview.see("end")
            self.full_log.insert("end", line)
            self.full_log.see("end")
        except Exception as e:
            print(f"Error updating log textbox: {e}")

    def _progress_update_task(self, percent, filename):
# ... existing code ...
        try:
            self.progress.set(percent / 100.0)
            if percent == 100:
                self.live_label.configure(text="Idle")
            elif filename:
                self.live_label.configure(text=f"Processing: {filename} ({percent}%)")
            else:
                self.live_label.configure(text="Idle")
        except Exception as e:
            print(f"Error updating progress: {e}")
    
    def _set_running_state_task(self, manual, auto):
# ... existing code ...
        self.is_running_manual = manual
        self.is_running_auto = auto
        is_running = manual or auto
        if auto:
            self.status_label.configure(text="Status: Schedule ON", text_color="green")
        elif manual:
            self.status_label.configure(text="Status: Backup Running...", text_color="orange")
        else:
            self.status_label.configure(text="Status: Idle", text_color="gray")
        self.btn_run_once.configure(text="Run Backup Now" if not manual else "Stop Backup",
                                    fg_color="#1f6feb" if not manual else "red",
                                    state="normal" if not auto else "disabled")
        self.btn_browse_source.configure(state="disabled" if is_running else "normal")
        self.btn_browse_backup.configure(state="disabled" if is_running else "normal")
        self.btn_start_auto.configure(state="disabled" if is_running else "normal")
        self.btn_stop_auto.configure(state="normal" if auto else "disabled")
        self.schedule_combo.configure(state="disabled" if is_running else "normal")
        self.hour_combo.configure(state="disabled" if is_running else "normal")


    # ---------- Frames (Unchanged) ----------
    def _create_organizer_frame(self):
# ... existing code ...
        frm = ctk.CTkFrame(self.main)
        frm.grid_columnconfigure(1, weight=1)
        self.frames["organizer"] = frm
        ctk.CTkLabel(frm, text="Manual Backup", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, pady=8)
        ctk.CTkLabel(frm, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=12)
        self.source_var = ctk.StringVar()
        self.source_entry = ctk.CTkEntry(frm, textvariable=self.source_var)
        self.source_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        self.btn_browse_source = ctk.CTkButton(frm, text="Browse", width=80, command=self.browse_source)
        self.btn_browse_source.grid(row=1, column=2, padx=(0, 12), pady=6)
        ctk.CTkLabel(frm, text="Backup Folder:").grid(row=2, column=0, sticky="w", padx=12)
        self.backup_var = ctk.StringVar()
        self.backup_entry = ctk.CTkEntry(frm, textvariable=self.backup_var)
        self.backup_entry.grid(row=2, column=1, sticky="ew", padx=6, pady=6)
        self.btn_browse_backup = ctk.CTkButton(frm, text="Browse", width=80, command=self.browse_backup)
        self.btn_browse_backup.grid(row=2, column=2, padx=(0, 12), pady=6)
        action_row = ctk.CTkFrame(frm)
        action_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=10)
        self.btn_run_once = ctk.CTkButton(action_row, text="Run Backup Now", command=self.toggle_manual_backup, fg_color="#1f6feb")
        self.btn_run_once.pack(side="left", padx=6)
        self.btn_clear_log = ctk.CTkButton(action_row, text="Clear Log", command=self.clear_log)
        self.btn_clear_log.pack(side="left", padx=6)
        self.progress = ctk.CTkProgressBar(frm)
        self.progress.set(0)
        self.progress.grid(row=4, column=0, columnspan=3, sticky="ew", padx=12, pady=(10, 2))
        self.live_label = ctk.CTkLabel(frm, text="Idle", anchor="w")
        self.live_label.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12)
        ctk.CTkLabel(frm, text="Recent Log:").grid(row=6, column=0, columnspan=3, sticky="w", padx=20, pady=(20,0))
        self.log_preview = ctk.CTkTextbox(frm, height=150)
        self.log_preview.grid(row=7, column=0, columnspan=3, sticky="nswe", padx=12, pady=6)
        frm.grid_rowconfigure(7, weight=1)

    def _create_auto_frame(self):
# ... existing code ...
        frm = ctk.CTkFrame(self.main)
        self.frames["auto"] = frm
        frm.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frm, text="Automation / Scheduled Backup", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=8)
        ctk.CTkLabel(frm, text="Set a schedule to run the backup automatically.").pack(pady=(0,10), padx=12)
        info_frame = ctk.CTkFrame(frm, fg_color="transparent")
        info_frame.pack(fill="x", padx=12, pady=10)
        info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(info_frame, text="Source:").grid(row=0, column=0, sticky="w")
        self.auto_src_label = ctk.CTkLabel(info_frame, text="(not set)", anchor="w", fg_color="gray10", corner_radius=5)
        self.auto_src_label.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(info_frame, text="Backup:").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.auto_bkp_label = ctk.CTkLabel(info_frame, text="(not set)", anchor="w", fg_color="gray10", corner_radius=5)
        self.auto_bkp_label.grid(row=1, column=1, sticky="ew", padx=5, pady=(8,0))
        schedule_frame = ctk.CTkFrame(frm)
        schedule_frame.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(schedule_frame, text="Schedule:").grid(row=0, column=0, padx=5, pady=10)
        self.schedule_var = ctk.StringVar(value="Disabled")
        self.schedule_combo = ctk.CTkComboBox(
            schedule_frame,
            variable=self.schedule_var,
            values=["Disabled", "Run every hour", "Run every day at..."],
            command=self.on_schedule_change
        )
        self.schedule_combo.grid(row=0, column=1, padx=5, pady=10)
        self.hour_label = ctk.CTkLabel(schedule_frame, text="Hour (0-23):")
        self.hour_label.grid(row=0, column=2, padx=(10, 5), pady=10)
        self.hour_var = ctk.StringVar(value="8")
        self.hour_combo = ctk.CTkComboBox(
            schedule_frame,
            variable=self.hour_var,
            width=70,
            values=[str(h) for h in range(24)]
        )
        self.hour_combo.grid(row=0, column=3, padx=5, pady=10)
        btn_row = ctk.CTkFrame(frm)
        btn_row.pack(pady=20)
        self.btn_start_auto = ctk.CTkButton(btn_row, text="Start Schedule", command=self.start_auto_backup, fg_color="green")
        self.btn_stop_auto = ctk.CTkButton(btn_row, text="Stop Schedule", command=self.stop_auto_backup, fg_color="red", state="disabled")
        self.btn_start_auto.grid(row=0, column=0, padx=6)
        self.btn_stop_auto.grid(row=0, column=1, padx=6)
        self.on_schedule_change(self.schedule_var.get())

    def on_schedule_change(self, choice):
# ... existing code ...
        if choice == "Run every day at...":
            self.hour_label.grid()
            self.hour_combo.grid()
        else:
            self.hour_label.grid_remove()
            self.hour_combo.grid_remove()

    def _create_logs_frame(self):
# ... existing code ...
        frm = ctk.CTkFrame(self.main)
        frm.grid_rowconfigure(1, weight=1)
        frm.grid_columnconfigure(0, weight=1)
        self.frames["logs"] = frm
        ctk.CTkLabel(frm, text="Full Activity Log", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=8)
        self.full_log = ctk.CTkTextbox(frm)
        self.full_log.grid(row=1, column=0, sticky="nswe", padx=12, pady=6)

    # ---------- Actions (Most are unchanged) ----------
    def show_frame(self, name):
# ... existing code ...
        for f in self.frames.values():
            f.grid_remove()
        self.frames[name].grid(row=0, column=0, sticky="nswe")
        if name == "auto":
            self.auto_src_label.configure(text=self.source_var.get() or "(not set)")
            self.auto_bkp_label.configure(text=self.backup_var.get() or "(not set)")

    def validate_paths(self):
# ... existing code ...
        src_s = self.source_var.get()
        bkp_s = self.backup_var.get()
        if not src_s or not bkp_s:
            messagebox.showwarning("Missing folder", "Please set both source and backup folders.")
            return None, None
        src = Path(src_s)
        bkp = Path(bkp_s)
        if not src.exists() or not src.is_dir():
            messagebox.showwarning("Invalid Source", f"Source folder does not exist or is not a directory:\n{src}")
            return None, None
        if not bkp.exists():
            try:
                bkp.mkdir(parents=True, exist_ok=True)
                self.safe_log(f"Created backup directory: {bkp}")
            except Exception as e:
                messagebox.showerror("Invalid Backup", f"Could not create backup folder:\n{bkp}\nError: {e}")
                return None, None
        if not bkp.is_dir():
             messagebox.showwarning("Invalid Backup", f"Backup path is not a directory:\n{bkp}")
             return None, None
        if src.resolve() == bkp.resolve():
            messagebox.showerror("Dangerous Operation", "Source and Backup folders cannot be the same!")
            return None, None
        if bkp.resolve() in src.resolve().parents:
            messagebox.showerror("Dangerous Operation", "Cannot set backup folder to be inside the source folder!")
            return None, None
        return src, bkp

    def browse_source(self):
# ... existing code ...
        p = filedialog.askdirectory()
        if p:
            self.source_var.set(p)

    def browse_backup(self):
# ... existing code ...
        p = filedialog.askdirectory()
        if p:
            self.backup_var.set(p)

    def clear_log(self):
# ... existing code ...
        self.log_preview.delete("1.0", "end")
        self.full_log.delete("1.0", "end")

    def toggle_manual_backup(self):
# ... existing code ...
        if self.is_running_manual:
            self.stop_manual_backup()
        else:
            self.run_backup_now()

    def run_backup_now(self):
# ... existing code ...
        if self.is_running_auto or self.is_running_manual:
            messagebox.showinfo("Busy", "A backup job is already running.")
            return
        src, bkp = self.validate_paths()
        if not src or not bkp:
            return
        self.safe_log("Starting manual backup...")
        self.stop_event.clear()
        self.safe_set_running_state(manual=True, auto=False)
        self.manual_thread = Thread(target=self.run_backup_job, args=(src, bkp), daemon=True)
        self.manual_thread.start()

    def stop_manual_backup(self):
# ... existing code ...
        if self.manual_thread and self.manual_thread.is_alive():
            self.safe_log("Stopping manual backup...")
            self.stop_event.set()
        else:
            self.safe_log("Manual backup not running.")

    # ---------- MODIFIED Schedule/Auto control (Unchanged logic) ----------
    def schedule_worker(self, src: Path, bkp: Path, schedule_mode: str, schedule_hour: str):
# ... existing code ...
        self.safe_log(f"Schedule started: {schedule_mode} " + (f"at {schedule_hour}:00" if schedule_mode == "Run every day at..." else ""))
        while not self.stop_event.is_set():
            next_run = get_next_run_time(schedule_mode, schedule_hour)
            wait_seconds = (next_run - datetime.now()).total_seconds()
            if wait_seconds < 0:
                wait_seconds = 60 
            self.safe_log(f"Next run scheduled for {next_run.strftime('%Y-%m-%d %H:%M')}. Waiting {wait_seconds/60:.0f} minutes...")
            wait_completed = wait_with_stop_check(wait_seconds, self.stop_event)
            if not wait_completed:
                break
            self.safe_log("Scheduled run starting...")
            run_backup_once(src, bkp, self.safe_log, self.safe_progress_update, self.stop_event)
            self.safe_log("Scheduled run complete.")
        self.safe_log("Schedule stopped.")
        self.safe_set_running_state(manual=False, auto=False)

    def start_auto_backup(self):
# ... existing code ...
        if self.is_running_auto or self.is_running_manual:
            messagebox.showinfo("Busy", "A backup job is already running.")
            return
        src, bkp = self.validate_paths()
        if not src or not bkp:
            return
        schedule_mode = self.schedule_var.get()
        schedule_hour = self.hour_var.get()
        if schedule_mode == "Disabled":
            messagebox.showinfo("Schedule Disabled", "Please select a valid schedule (e.g., 'Run every hour').")
            return
        self.stop_event.clear()
        self.safe_set_running_state(manual=False, auto=True)
        self.auto_thread = Thread(target=self.schedule_worker, args=(src, bkp, schedule_mode, schedule_hour), daemon=True)
        self.auto_thread.start()

    def stop_auto_backup(self):
# ... existing code ...
        if self.auto_thread and self.auto_thread.is_alive():
            self.safe_log("Stopping schedule...")
            self.stop_event.set()
        else:
            self.safe_log("Schedule not running.")

    def run_backup_job(self, src, bkp):
# ... existing code ...
        try:
            run_backup_once(src, bkp, self.safe_log, self.safe_progress_update, self.stop_event)
        except Exception as e:
            self.safe_log(f"CRITICAL ERROR in backup thread: {e}")
        finally:
            self.safe_set_running_state(manual=False, auto=False)

    # ----------------- MODIFIED Tray Icon Functions -----------------
    def create_icon_image_fallback(self):
        """ Creates a simple 64x64 icon for the tray as a fallback """
        try:
            font = ImageFont.truetype("tahoma.ttf", 32)
        except IOError:
            font = ImageFont.load_default()
        image = Image.new('RGB', (64, 64), (20, 20, 20))
        d = ImageDraw.Draw(image)
        d.ellipse([(4, 4), (60, 60)], fill=(30, 100, 200), outline='white')
        d.text((15, 14), "SO", font=font, fill='white')
        return image

    def setup_tray_icon(self):
        """ Creates and runs the system tray icon in a separate thread """
        
        # --- MODIFIED: Try to load icon.ico first, use fallback on error ---
        try:
            icon_path = resource_path("icon.ico")
            image = Image.open(icon_path)
        except Exception as e:
            self.safe_log(f"Icon file 'icon.ico' not found. Using generated icon. Error: {e}")
            image = self.create_icon_image_fallback()
        # --- END MODIFICATION ---

        menu = (
            pystray.MenuItem('Show', self.show_window, default=True),
            pystray.MenuItem('Quit', self.quit_application)
        )
        self.tray_icon = pystray.Icon("SmartOrganizer", image, "Smart Organizer", menu)
        
        self.tray_thread = Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def hide_to_tray(self):
# ... existing code ...
        """ Hides the main window """
        self.withdraw()
        # You can add a notification here if you want
        # self.tray_icon.notify("Running in background", "Smart Organizer is still active.")

    def show_window(self):
# ... existing code ...
        """ Shows the main window from the tray """
        self.deiconify() # Un-hide
        self.lift() # Bring to front
        self.attributes("-topmost", 1)
        # Unset topmost after a moment so it doesn't stay above all windows
        self.after(100, lambda: self.attributes("-topmost", 0))

    def quit_application(self):
# ... existing code ...
        """ This is the new 'on_close' logic, called by the tray menu """
        self.safe_log("Quit requested, stopping all tasks...")
        
        # Stop all threads
        self.stop_event.set()
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Wait for threads to hopefully stop
        if self.manual_thread and self.manual_thread.is_alive():
            self.manual_thread.join(timeout=1)
        if self.auto_thread and self.auto_thread.is_alive():
            self.auto_thread.join(timeout=1)
        
        self.destroy() # Destroy the main window, which exits the app

# ----------------- Run -----------------
if __name__ == "__main__":
# ... existing code ...
    app = SmartOrganizerApp()
    app.mainloop()