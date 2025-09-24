#!/usr/bin/env python3
"""
Financial Email Transcription - GUI Application
Easy-to-use desktop application for monitoring and transcribing financial webinars from email
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import queue
import subprocess
import sys
import os
import json
from datetime import datetime
import webbrowser

class FinancialTranscribeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Email Transcription Service")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        self.service_process = None
        self.is_running = False
        
        # Load configuration
        self.config_file = "gui_config.json"
        self.config = self.load_config()
        
        self.create_widgets()
        self.setup_menu()
        self.check_dependencies()
        
        # Start log queue checking
        self.root.after(100, self.process_log_queue)
    
    def load_config(self):
        """Load GUI configuration from file"""
        default_config = {
            "email": "",
            "check_interval": 300,
            "auto_start": False,
            "window_geometry": "800x600"
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            self.log_message(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save GUI configuration to file"""
        try:
            self.config["window_geometry"] = self.root.geometry()
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_message(f"Error saving config: {e}")
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Financial Email Transcription Service", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Service Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start Service", 
                                   command=self.start_service)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Service", 
                                  command=self.stop_service, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_btn = ttk.Button(button_frame, text="Restart", 
                                     command=self.restart_service, state=tk.DISABLED)
        self.restart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Test button
        self.test_btn = ttk.Button(button_frame, text="Test Once", 
                                  command=self.test_once)
        self.test_btn.pack(side=tk.LEFT, padx=(20, 0))
        
        # Settings Panel
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Email settings
        email_frame = ttk.Frame(settings_frame)
        email_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(email_frame, text="Email:").pack(side=tk.LEFT)
        self.email_var = tk.StringVar(value=self.config.get("email", ""))
        self.email_entry = ttk.Entry(email_frame, textvariable=self.email_var, width=40)
        self.email_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Check interval
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(interval_frame, text="Check Interval (seconds):").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.config.get("check_interval", 300)))
        interval_spin = ttk.Spinbox(interval_frame, from_=60, to=3600, 
                                   textvariable=self.interval_var, width=10)
        interval_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar(value=self.config.get("auto_start", False))
        auto_start_cb = ttk.Checkbutton(settings_frame, text="Auto-start service on launch", 
                                       variable=self.auto_start_var)
        auto_start_cb.pack(anchor=tk.W, pady=(5, 0))
        
        # Save settings button
        save_settings_btn = ttk.Button(settings_frame, text="Save Settings", 
                                      command=self.save_settings)
        save_settings_btn.pack(anchor=tk.E, pady=(10, 0))
        
        # Log Panel
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, 
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(5, 0))
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial log message
        self.log_message("Financial Email Transcription Service GUI started")
        
        # Auto-start if enabled
        if self.config.get("auto_start", False):
            self.root.after(1000, self.start_service)  # Delay to ensure GUI is ready
    
    def setup_menu(self):
        """Create the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Output Folder", command=self.open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Process File...", command=self.process_file)
        tools_menu.add_command(label="Process URL...", command=self.process_url)
        tools_menu.add_separator()
        tools_menu.add_command(label="Check Dependencies", command=self.check_dependencies)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Thread-safe logging
        self.log_queue.put(log_entry)
    
    def process_log_queue(self):
        """Process log messages from queue (called periodically)"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
                self.status_bar.config(text=message.strip().split('] ', 1)[-1])
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)
    
    def start_service(self):
        """Start the email monitoring service"""
        if self.is_running:
            self.log_message("Service is already running")
            return
        
        try:
            # Start the service in a separate thread
            self.service_thread = threading.Thread(target=self.run_service, daemon=True)
            self.service_thread.start()
            
            self.is_running = True
            self.status_label.config(text="Running", foreground="green")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            
            self.log_message("Service started successfully")
            
        except Exception as e:
            self.log_message(f"Error starting service: {e}")
            messagebox.showerror("Error", f"Failed to start service: {e}")
    
    def stop_service(self):
        """Stop the email monitoring service"""
        if not self.is_running:
            self.log_message("Service is not running")
            return
        
        try:
            if self.service_process:
                self.service_process.terminate()
                self.service_process = None
            
            self.is_running = False
            self.status_label.config(text="Stopped", foreground="red")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
            
            self.log_message("Service stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping service: {e}")
    
    def restart_service(self):
        """Restart the service"""
        self.log_message("Restarting service...")
        self.stop_service()
        self.root.after(2000, self.start_service)  # Wait 2 seconds before restart
    
    def run_service(self):
        """Run the email service (in separate thread)"""
        try:
            # Run the email transcription script
            cmd = [sys.executable, "email_transcribe_financial.py"]
            
            self.service_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in iter(self.service_process.stdout.readline, ''):
                if line:
                    self.log_message(line.strip())
                
                # Check if process was terminated
                if self.service_process.poll() is not None:
                    break
            
            # Process ended
            if self.is_running:
                self.log_message("Service process ended unexpectedly")
                self.root.after(0, self.stop_service)
                
        except Exception as e:
            self.log_message(f"Service error: {e}")
            self.root.after(0, self.stop_service)
    
    def test_once(self):
        """Run a single test check"""
        def run_test():
            try:
                self.log_message("Running single test check...")
                result = subprocess.run(
                    [sys.executable, "email_transcribe_financial.py", "--once"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            self.log_message(f"TEST: {line}")
                
                if result.stderr:
                    for line in result.stderr.split('\n'):
                        if line.strip():
                            self.log_message(f"ERROR: {line}")
                
                self.log_message("Test completed")
                
            except subprocess.TimeoutExpired:
                self.log_message("Test timed out after 5 minutes")
            except Exception as e:
                self.log_message(f"Test error: {e}")
        
        # Run test in separate thread
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
    
    def save_settings(self):
        """Save current settings"""
        try:
            self.config["email"] = self.email_var.get()
            self.config["check_interval"] = int(self.interval_var.get())
            self.config["auto_start"] = self.auto_start_var.get()
            
            self.save_config()
            self.log_message("Settings saved")
            messagebox.showinfo("Settings", "Settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid check interval value")
        except Exception as e:
            self.log_message(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log cleared")
    
    def save_log(self):
        """Save log to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"Log saved to {filename}")
                
        except Exception as e:
            self.log_message(f"Error saving log: {e}")
            messagebox.showerror("Error", f"Failed to save log: {e}")
    
    def open_output_folder(self):
        """Open the output folder"""
        output_folder = "output"
        if os.path.exists(output_folder):
            if sys.platform == "win32":
                os.startfile(output_folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_folder])
            else:
                subprocess.run(["xdg-open", output_folder])
        else:
            messagebox.showinfo("Info", "Output folder does not exist yet")
    
    def process_file(self):
        """Process a single audio/video file"""
        filename = filedialog.askopenfilename(
            title="Select audio/video file",
            filetypes=[
                ("Audio/Video files", "*.mp3 *.mp4 *.wav *.m4a *.mov *.avi"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            def run_process():
                try:
                    self.log_message(f"Processing file: {filename}")
                    result = subprocess.run(
                        [sys.executable, "transcribe_financial.py", filename],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log_message(line)
                    
                    if result.stderr:
                        for line in result.stderr.split('\n'):
                            if line.strip():
                                self.log_message(f"ERROR: {line}")
                    
                    self.log_message("File processing completed")
                    
                except Exception as e:
                    self.log_message(f"Error processing file: {e}")
            
            # Run in separate thread
            threading.Thread(target=run_process, daemon=True).start()
    
    def process_url(self):
        """Process a URL"""
        url = tk.simpledialog.askstring("Process URL", "Enter audio/video URL:")
        if url:
            def run_process():
                try:
                    self.log_message(f"Processing URL: {url}")
                    result = subprocess.run(
                        [sys.executable, "transcribe_financial.py", url],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log_message(line)
                    
                    if result.stderr:
                        for line in result.stderr.split('\n'):
                            if line.strip():
                                self.log_message(f"ERROR: {line}")
                    
                    self.log_message("URL processing completed")
                    
                except Exception as e:
                    self.log_message(f"Error processing URL: {e}")
            
            # Run in separate thread
            threading.Thread(target=run_process, daemon=True).start()
    
    def check_dependencies(self):
        """Check if all dependencies are installed"""
        dependencies = [
            ("Python", sys.executable),
            ("email_transcribe_financial.py", "email_transcribe_financial.py"),
            ("transcribe_financial.py", "transcribe_financial.py")
        ]
        
        missing = []
        for name, path in dependencies:
            if name == "Python":
                continue  # Already running Python
            elif not os.path.exists(path):
                missing.append(name)
        
        if missing:
            msg = f"Missing dependencies: {', '.join(missing)}"
            self.log_message(msg)
            messagebox.showwarning("Dependencies", msg)
        else:
            msg = "All dependencies found"
            self.log_message(msg)
            messagebox.showinfo("Dependencies", msg)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Financial Email Transcription Service
        
Version 1.0
        
A desktop application for automatically monitoring emails 
and transcribing financial webinars and audio content.

Features:
• Automatic email monitoring
• Audio/video transcription
• Financial analysis generation
• HTML email reports
• Easy-to-use GUI interface

© 2025 Financial Transcription Service"""
        
        messagebox.showinfo("About", about_text)
    
    def show_docs(self):
        """Show documentation"""
        docs_text = """How to Use:

1. SETUP:
   - Enter your email address in Settings
   - Set check interval (default: 300 seconds)
   - Save settings

2. START SERVICE:
   - Click 'Start Service' to begin monitoring
   - Service will check for new emails automatically
   - View activity in the log panel

3. MANUAL PROCESSING:
   - Use 'Test Once' for a single check
   - Use Tools menu to process files/URLs directly

4. MONITORING:
   - Green status = Running
   - Red status = Stopped
   - Check logs for detailed activity

5. TROUBLESHOOTING:
   - Use 'Check Dependencies' in Tools menu
   - Check log for error messages
   - Try 'Restart' if service becomes unresponsive

The service will automatically process emails containing:
• Webinar links and recordings
• Audio/video attachments
• Financial content for analysis"""
        
        # Create documentation window
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(doc_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, docs_text)
        text_widget.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Service is running. Stop service and quit?"):
                self.stop_service()
                self.save_config()
                self.root.destroy()
        else:
            self.save_config()
            self.root.destroy()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = FinancialTranscribeGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()

if __name__ == "__main__":
    main()