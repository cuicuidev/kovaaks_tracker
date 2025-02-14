import os
import shutil
import threading

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser

TERMS_AND_SERVICES = """Terms and Services.\n""" * 100

HOME = os.getenv("HOME")
if HOME is None:
    HOME = os.path.expanduser("~")

DEFAULT_INSTALLATION_DIR = os.path.join(HOME, "FPSAimTrainer Tracker")
DEFAULT_STEAM_DIR = "C:\\Program Files (x86)\\Steam"
DEFAULT_STATS_DIR = f"{DEFAULT_STEAM_DIR}\\steamapps\\common\\FPSAimTrainer\\FPSAimTrainer\\stats"

STARTUP_DIR = os.path.join(HOME, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
DOTFILES_DIR = os.path.join(HOME, ".kvkstracker")

class Setup(tk.Tk):

    def __init__(self) -> None:
        super().__init__()

        self.title("KovaaK's Tracker Tool Setup")
        self.geometry("600x350")
        self.resizable(False, False)

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create the main UI layout."""
        self.welcome_frame = tk.Frame(self)
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

        next_button = tk.Button(self.welcome_frame, text="Next", command=self.show_terms_screen)
        next_button.pack(pady=20)

        self.welcome_frame.pack()

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

        label_steam = tk.Label(self.install_frame, text="Choose the Steam directory", font=("Arial", 12))
        label_steam.pack(pady=10)

        self.steam_dir_var = tk.StringVar(value=DEFAULT_STEAM_DIR)

        steam_entry = tk.Entry(self.install_frame, textvariable=self.steam_dir_var, width=50)
        steam_entry.pack(pady=5)

        browse_steam_button = tk.Button(self.install_frame, text="Browse", command=self.select_steam_dir)
        browse_steam_button.pack(pady=5)

        install_button = tk.Button(self.install_frame, text="Install", command=self.start_installation)
        install_button.pack(pady=20)

        self.install_frame.pack()

    def select_install_dir(self) -> None:
        """Open a file dialog for installation path selection."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.install_dir_var.set(dir_path)

    def select_steam_dir(self) -> None:
        """Open a file dialog for Steam path selection."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.steam_dir_var.set(dir_path)

    def start_installation(self) -> None:
        """Start the installation process in a separate thread."""
        install_dir = self.install_dir_var.get()
        steam_dir = self.steam_dir_var.get()

        if not install_dir:
            messagebox.showwarning("Warning", "Please select an installation directory.")
            return
        
        if not steam_dir:
            messagebox.showwarning("Warning", "Please specify where Steam is installed.")
            return
        
        if not os.path.exists(install_dir):
            try:
                os.makedirs(install_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to initialize install directory: {e}")
                return

        if not os.path.exists(steam_dir):
            messagebox.showerror("Error", f"Steam not found at <{steam_dir}>.")
            return

        stats_dir = f"{steam_dir}\\steamapps\\common\\FPSAimTrainer\\FPSAimTrainer\\stats"
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdWljdWkiLCJleHAiOjE3NzEwMzYxMDF9.iJE1wfSbszvd1Kmfkyq-I2eqKzNkmWP2ZdHve2PpXaM"
        
        self.clear_frames()
        label = tk.Label(self.progress_frame, text="Installing...", font=("Arial", 12))
        label.pack(pady=20)

        self.progress_frame.pack()

        threading.Thread(target=self.install, args=(install_dir, stats_dir, access_token)).start()

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
            shutil.copyfile("zig-out/bin/kovaaks_tracker.exe", executable_path)
            self.create_symlink(executable_path, os.path.join(STARTUP_DIR, "kvks_tracker.exe"))
    
            self.show_complete_screen(install_dir)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install the app. Error {e}.")

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
        os.startfile(os.path.join(install_dir, "kovaaks_tracker.exe"), show_cmd=0)
        #os.startfile(r"C:\Users\Dmitry\Documents\projects\kovaaks_tracker\zig-out\bin\kovaaks_tracker.exe", show_cmd=0)
        self.quit()

    def clear_frames(self) -> None:
        """Remove all current frames from the window."""
        for widget in self.winfo_children():
            widget.pack_forget()

if __name__ == "__main__":
    setup = Setup()
    setup.mainloop()