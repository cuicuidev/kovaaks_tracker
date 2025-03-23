import os
import sys
import threading
import winreg
import ctypes

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests

TERMS_AND_SERVICES = """Terms and Services.\n""" * 100

HOME = os.getenv("HOME")
if HOME is None:
    HOME = os.path.expanduser("~")

DEFAULT_INSTALLATION_DIR = os.path.join(HOME, "FPSAimTrainer Tracker")
DEFAULT_STEAM_DIR = "C:\\Program Files (x86)\\Steam"
DEFAULT_STATS_DIR = f"{DEFAULT_STEAM_DIR}\\steamapps\\common\\FPSAimTrainer\\FPSAimTrainer\\stats"

STARTUP_DIR = os.path.join(HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
DOTFILES_DIR = os.path.join(HOME, ".kvkstracker")

user_profile = os.environ['USERPROFILE']

key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")

desktop_path, _ = winreg.QueryValueEx(key, "Desktop")

DESKTOP = os.path.expandvars(desktop_path)

API_URL = "https://chubby-krystyna-cuicuidev-da9ab1a9.koyeb.app" # "http://127.0.0.1:8000/"

class Setup(tk.Tk):

    def __init__(self) -> None:
        super().__init__()

        self.title("KovaaK's Tracker Tool Setup")
        self.geometry("600x450")
        self.resizable(False, False)

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create the main UI layout."""
        self.welcome_frame = tk.Frame(self)
        self.sign_in_frame = tk.Frame(self)
        self.sign_up_frame = tk.Frame(self)
        self.terms_frame = tk.Frame(self)
        self.install_frame = tk.Frame(self)
        self.progress_frame = tk.Frame(self)
        self.complete_frame = tk.Frame(self)

        self.show_welcome_screen()

    def show_welcome_screen(self) -> None:
        """Display the welcome screen."""
        self.clear_frames()

        label = tk.Label(self.welcome_frame, text="Welcome to KovaaK's Tracker Tool Setup", font=("Arial", 16))
        label.pack(pady=20)

        next_button = tk.Button(self.welcome_frame, text="Next", command=self.show_sign_in_screen)
        next_button.pack(pady=20)

        self.welcome_frame.pack()

    def show_sign_in_screen(self) -> None:
        self.clear_frames()
        for widget in self.sign_up_frame.winfo_children():
            widget.destroy()

        label = tk.Label(self.sign_in_frame, text="Sign In", font=("Arial", 12))
        label.pack(pady=20)

        user_label = tk.Label(self.sign_in_frame, text="Username", font=("Arial", 12))
        user_label.pack(pady=5)

        self.username_var = tk.StringVar()
        user_entry = tk.Entry(self.sign_in_frame, textvariable=self.username_var, width=30)
        user_entry.pack(pady=5)

        passwd_label = tk.Label(self.sign_in_frame, text="Password", font=("Arial", 12))
        passwd_label.pack(pady=5)

        self.passwd_var = tk.StringVar()
        passwd_entry = tk.Entry(self.sign_in_frame, textvariable=self.passwd_var, width=30)
        passwd_entry.pack(pady=5)

        sign_in_button = tk.Button(self.sign_in_frame, text="Sign In", command=self.obtain_access_token)
        sign_in_button.pack(pady=5)

        sign_up_button = tk.Button(self.sign_in_frame, text="Register", command=self.show_sign_up_screen)
        sign_up_button.pack(pady=15)

        self.sign_in_frame.pack()

    def obtain_access_token(self) -> None:
        response = requests.post(f"{API_URL}/auth/token", data={
            "grant_type" : "password",
            "username" : self.username_var.get(),
            "password" : self.passwd_var.get(),
            })
        
        try:
            self.access_token = response.json()["access_token"]
        except Exception as e:
            messagebox.showerror("Error", "Authentication failed.")
            return
        
        self.show_terms_screen()

    def show_sign_up_screen(self) -> None:
        self.clear_frames()
        for widget in self.sign_in_frame.winfo_children():
            widget.destroy()

        label = tk.Label(self.sign_up_frame, text="Register", font=("Arial", 12))
        label.pack(pady=10)

        email_label = tk.Label(self.sign_up_frame, text="Email", font=("Arial", 12))
        email_label.pack(pady=5)

        self.email_var = tk.StringVar()
        email_entry = tk.Entry(self.sign_up_frame, textvariable=self.email_var, width=30)
        email_entry.pack(pady=5)

        user_label = tk.Label(self.sign_up_frame, text="Username", font=("Arial", 12))
        user_label.pack(pady=5)

        self.username_var = tk.StringVar()
        user_entry = tk.Entry(self.sign_up_frame, textvariable=self.username_var, width=30)
        user_entry.pack(pady=5)

        passwd_label = tk.Label(self.sign_up_frame, text="Password", font=("Arial", 12))
        passwd_label.pack(pady=5)

        self.passwd_var = tk.StringVar()
        passwd_entry = tk.Entry(self.sign_up_frame, textvariable=self.passwd_var, width=30)
        passwd_entry.pack(pady=5)

        passwd_label = tk.Label(self.sign_up_frame, text="Confirm Password", font=("Arial", 12))
        passwd_label.pack(pady=5)

        self.conf_passwd_var = tk.StringVar()
        conf_passwd_entry = tk.Entry(self.sign_up_frame, textvariable=self.conf_passwd_var, width=30)
        conf_passwd_entry.pack(pady=5)

        sign_up_button = tk.Button(self.sign_up_frame, text="Register", command=self.sign_up_request)
        sign_up_button.pack(pady=5)

        sign_in_button = tk.Button(self.sign_up_frame, text="Sign Up", command=self.show_sign_in_screen)
        sign_in_button.pack(pady=5)

        self.sign_up_frame.pack()

    def sign_up_request(self) -> None:
        if self.passwd_var.get() != self.conf_passwd_var.get():
            messagebox.showwarning("Passwords do not match.")
            return

        response = requests.post(f"{API_URL}/auth/signup", json={
            "email" : self.email_var.get(),
            "username" : self.username_var.get(),
            "password" : self.passwd_var.get(),
            })
        
        if response.status_code != 200:
            messagebox.showerror("Error", f"Signup failed. {response.text}")
            return
        
        self.obtain_access_token()

    def show_terms_screen(self):
        """Display the terms and conditions screen."""
        self.clear_frames()

        label = tk.Label(self.terms_frame, text="Please read the Terms of Service and Privacy Policy", font=("Arial", 12))
        label.pack(pady=10)

        text_area = scrolledtext.ScrolledText(self.terms_frame, wrap=tk.WORD, width=60, height=10)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        text_area.insert(tk.END, TERMS_AND_SERVICES)

        self.terms_var = tk.BooleanVar()
        terms_checkbox = tk.Checkbutton(self.terms_frame, text="I accept the Terms of Service and Privacy Policy", variable=self.terms_var)
        terms_checkbox.pack(pady=10)

        next_button = tk.Button(self.terms_frame, text="Next", command=self.check_terms_accepted)
        next_button.pack(pady=10)

        self.terms_frame.pack()

    def check_terms_accepted(self) -> None:
        """Check if terms are accepted before proceeding."""
        if not self.terms_var.get():
            messagebox.showwarning("Warning", "You must accept the terms to proceed.")
        else:
            self.show_install_screen()

    def show_install_screen(self) -> None:
        """Display the installation path selection screen."""
        self.clear_frames()

        label = tk.Label(self.install_frame, text="Choose the installation directory", font=("Arial", 12))
        label.pack(pady=10)

        self.install_dir_var = tk.StringVar(value=DEFAULT_INSTALLATION_DIR)

        install_entry = tk.Entry(self.install_frame, textvariable=self.install_dir_var, width=50)
        install_entry.pack(pady=5)

        browse_button = tk.Button(self.install_frame, text="Browse", command=self.select_install_dir)
        browse_button.pack(pady=5)

        label_stats = tk.Label(self.install_frame, text="Choose the stats folder path", font=("Arial", 12))
        label_stats.pack(pady=10)

        self.stats_dir_var = tk.StringVar(value=DEFAULT_STATS_DIR)

        stats_entry = tk.Entry(self.install_frame, textvariable=self.stats_dir_var, width=50)
        stats_entry.pack(pady=5)

        browse_stats_button = tk.Button(self.install_frame, text="Browse", command=self.select_stats_dir)
        browse_stats_button.pack(pady=5)

        install_button = tk.Button(self.install_frame, text="Install", command=self.start_installation)
        install_button.pack(pady=20)

        self.install_frame.pack()

    def select_install_dir(self) -> None:
        """Open a file dialog for installation path selection."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.install_dir_var.set(dir_path)

    def select_stats_dir(self) -> None:
        """Open a file dialog for stats path selection."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.stats_dir_var.set(dir_path)

    def start_installation(self) -> None:
        """Start the installation process in a separate thread."""
        self.clear_frames()
        install_dir = self.install_dir_var.get()
        stats_dir = self.stats_dir_var.get()

        if not install_dir:
            messagebox.showwarning("Warning", "Please select an installation directory.")
            return
        
        if not stats_dir:
            messagebox.showwarning("Warning", "Please specify where the stats folder is located.")
            return
        
        if not os.path.exists(install_dir):
            try:
                os.makedirs(install_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize install directory: {e}")
                return

        if not os.path.exists(stats_dir):
            messagebox.showerror("Error", f"Stats not found at <{stats_dir}>.")
            return
        
        self.clear_frames()
        label = tk.Label(self.progress_frame, text="Installing...", font=("Arial", 12))
        label.pack(pady=20)

        self.progress_frame.pack()

        threading.Thread(target=self.install, args=(install_dir, stats_dir, self.access_token)).start()

    def install(self, install_dir: str, stats_dir: str, access_token: str) -> None:
        """Extracts the app into the installation directory."""
        try:

            if not os.path.exists(DOTFILES_DIR):
                os.makedirs(DOTFILES_DIR)

            with open(os.path.join(DOTFILES_DIR, "config.csv"), "w") as file:
                time_interval_seconds = 15
                file.write(f"time_interval_seconds,{time_interval_seconds};stats_dir,\"{stats_dir}\"")
            
            with open(os.path.join(DOTFILES_DIR, "access_token.txt"), "w") as file:
                file.write(access_token)
        
            executable_path = os.path.join(install_dir, "kovaaks_tracker.exe")

            try:
                with requests.get(f"{API_URL}/download/kovaaks_tracker.exe", stream=True) as response:
                    response.raise_for_status()
                    with open(executable_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
            except requests.RequestException:
                messagebox.showerror("Error", "Failed to download kovaaks_tracker.exe.")
                return

            # shutil.copyfile("zig-out/bin/kovaaks_tracker.exe", executable_path)
            self.create_symlink(executable_path, os.path.join(DESKTOP, "KovaaK's Tracker Tool.exe"))
    
            self.show_complete_screen(install_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install the app. Error {e}.")
            self.quit()

    def create_symlink(self, target: str, link_name: str) -> None:
        """Create a symbolic link pointing to target."""
        try:
            if os.path.exists(link_name):
                os.remove(link_name)
            os.symlink(target, link_name)
        except OSError as e: pass

    def show_complete_screen(self, install_dir) -> None:
        """Display the installation completion screen."""
        self.clear_frames()

        label = tk.Label(self.complete_frame, text="Installation Complete!", font=("Arial", 16))
        label.pack(pady=20)

        finish = lambda : self.finish(install_dir)
        finish_button = tk.Button(self.complete_frame, text="Finish", command=finish)
        finish_button.pack(pady=10)

        self.complete_frame.pack()

    def finish(self, install_dir: str) -> None:
        # os.startfile(os.path.join(install_dir, "kovaaks_tracker.exe"))
        self.quit()

    def clear_frames(self) -> None:
        """Remove all current frames from the window."""
        for widget in self.winfo_children():
            widget.pack_forget()

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def request_admin_privileges():
        """Relaunch the script with admin privileges."""
        if os.name == "nt":
            try:
                pythonw_executable = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                ctypes.windll.shell32.ShellExecuteW(None, "runas", pythonw_executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to request admin privileges: {e}")

def main() -> None:
    
    try:
        if not is_admin():
            request_admin_privileges()
            return
        app = Setup()
        app.mainloop()
    except: pass


if __name__ == "__main__":
    main()