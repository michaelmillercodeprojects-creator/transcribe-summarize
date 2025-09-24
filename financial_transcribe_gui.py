#!/usr/bin/env python3
"""
Financial Email Transcription - GUI Application
Optimized desktop application for monitoring and transcribing financial webinars from email
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
import time

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
        self.service_thread = None
        
        # Load configuration
        self.config_file = "gui_config.json"
        self.config = self.load_config()
        
        # Apply saved window geometry
        if "window_geometry" in self.config:
            try:
                self.root.geometry(self.config["window_geometry"])
            except tk.TclError:
                pass  # Invalid geometry, use default
        
        self.create_widgets()
        self.setup_menu()
        self.check_dependencies_silent()
        
        # Start log queue checking
        self.root.after(100, self.process_log_queue)
    
    def load_config(self):
        """Load GUI configuration from file"""
        default_config = {
            "output_email": "",
            "check_interval": 300,
            "auto_start": False,
            "window_geometry": "800x600",
            "openai_api_key": "",
            "email_address": "",
            "email_password": ""
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
        
        # Create notebook for tabbed settings
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # API & Email Tab
        api_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(api_frame, text="API & Email")
        
        # OpenAI API Key row
        api_key_frame = ttk.Frame(api_frame)
        api_key_frame.pack(fill=tk.X, pady=(5, 8))
        
        ttk.Label(api_key_frame, text="OpenAI API Key:", width=18).pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar(value=self.config.get("openai_api_key", ""))
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key_var, show="*", width=35)
        self.api_key_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Show/Hide API key button
        self.show_api_key = False
        self.toggle_api_btn = ttk.Button(api_key_frame, text="Show", width=6,
                                        command=self.toggle_api_key_visibility)
        self.toggle_api_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output Email row (where reports are sent)
        output_email_frame = ttk.Frame(api_frame)
        output_email_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(output_email_frame, text="Send Reports To:", width=18).pack(side=tk.LEFT)
        self.output_email_var = tk.StringVar(value=self.config.get("output_email", ""))
        self.output_email_entry = ttk.Entry(output_email_frame, textvariable=self.output_email_var, width=35)
        self.output_email_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Separator
        ttk.Separator(api_frame, orient='horizontal').pack(fill=tk.X, pady=(10, 10))
        
        # Email Credentials section
        ttk.Label(api_frame, text="Email Credentials (for sending reports):", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Email address row
        email_addr_frame = ttk.Frame(api_frame)
        email_addr_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(email_addr_frame, text="From Email:", width=18).pack(side=tk.LEFT)
        self.email_address_var = tk.StringVar(value=self.config.get("email_address", ""))
        self.email_address_entry = ttk.Entry(email_addr_frame, textvariable=self.email_address_var, width=35)
        self.email_address_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Email password row
        email_pass_frame = ttk.Frame(api_frame)
        email_pass_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(email_pass_frame, text="App Password:", width=18).pack(side=tk.LEFT)
        self.email_password_var = tk.StringVar(value=self.config.get("email_password", ""))
        self.email_password_entry = ttk.Entry(email_pass_frame, textvariable=self.email_password_var, show="*", width=35)
        self.email_password_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Show/Hide password button
        self.show_email_pass = False
        self.toggle_pass_btn = ttk.Button(email_pass_frame, text="Show", width=6,
                                         command=self.toggle_email_pass_visibility)
        self.toggle_pass_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # General Tab
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text="General")
        
        # Check interval row
        interval_frame = ttk.Frame(general_frame)
        interval_frame.pack(fill=tk.X, pady=(10, 8))
        
        ttk.Label(interval_frame, text="Check Interval (sec):", width=20).pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(self.config.get("check_interval", 300)))
        interval_spin = ttk.Spinbox(interval_frame, from_=60, to=3600, 
                                   textvariable=self.interval_var, width=10)
        interval_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        # Options frame (in general tab)
        options_frame = ttk.Frame(general_frame)
        options_frame.pack(fill=tk.X, pady=(10, 8))
        
        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar(value=self.config.get("auto_start", False))
        auto_start_cb = ttk.Checkbutton(options_frame, text="Auto-start service on launch", 
                                       variable=self.auto_start_var)
        auto_start_cb.pack(anchor=tk.W)
        
        # Save settings button (spans both tabs)
        save_settings_frame = ttk.Frame(settings_frame)
        save_settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_settings_btn = ttk.Button(save_settings_frame, text="Save All Settings", 
                                      command=self.save_settings)
        save_settings_btn.pack(side=tk.RIGHT)
        
        # Test credentials button
        test_creds_btn = ttk.Button(save_settings_frame, text="Test Email", 
                                   command=self.test_email_credentials)
        test_creds_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
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
            self.is_running = False  # Set flag first to stop read loop
            
            if self.service_process:
                try:
                    # Try graceful termination first
                    self.service_process.terminate()
                    
                    # Wait briefly for graceful shutdown
                    try:
                        self.service_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        # Force kill if still running
                        self.service_process.kill()
                        self.service_process.wait()
                        
                except (ProcessLookupError, OSError):
                    pass  # Process already ended
                
                self.service_process = None
            
            # Update UI
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
            # Check if email script exists
            if not os.path.exists("email_transcribe_financial.py"):
                self.log_message("ERROR: email_transcribe_financial.py not found")
                self.root.after(0, self.stop_service)
                return
            
            # Build command with interval setting
            interval = self.config.get("check_interval", 300)
            cmd = [sys.executable, "email_transcribe_financial.py", "--interval", str(interval)]
            
            self.log_message(f"Starting email service with {interval}s interval...")
            
            self.service_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=os.getcwd()
            )
            
            # Read output line by line
            for line in iter(self.service_process.stdout.readline, ''):
                if not self.is_running:  # Service was stopped
                    break
                    
                if line:
                    line = line.strip()
                    if line:  # Only log non-empty lines
                        self.log_message(line)
                
                # Check if process was terminated
                if self.service_process.poll() is not None:
                    break
            
            # Process ended
            if self.is_running:
                return_code = self.service_process.returncode
                self.log_message(f"Service process ended (exit code: {return_code})")
                self.root.after(0, self.stop_service)
                
        except FileNotFoundError:
            self.log_message("ERROR: Python or email script not found")
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
            self.config["output_email"] = self.output_email_var.get()
            self.config["check_interval"] = int(self.interval_var.get())
            self.config["auto_start"] = self.auto_start_var.get()
            self.config["openai_api_key"] = self.api_key_var.get()
            self.config["email_address"] = self.email_address_var.get()
            self.config["email_password"] = self.email_password_var.get()
            
            # Also save to .env file for the transcription scripts
            self.save_to_env()
            
            self.save_config()
            self.log_message("Settings saved to GUI config and .env file")
            messagebox.showinfo("Settings", "Settings saved successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid check interval value")
        except Exception as e:
            self.log_message(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def save_to_env(self):
        """Save settings to .env file for the transcription scripts"""
        try:
            env_lines = []
            
            # Read existing .env file if it exists
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add our values
            env_dict = {}
            for line in env_lines:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_dict[key] = value
            
            # Update with our values
            if self.api_key_var.get():
                env_dict['OPENAI_API_KEY'] = self.api_key_var.get()
            if self.email_address_var.get():
                env_dict['EMAIL_ADDRESS'] = self.email_address_var.get()
            if self.email_password_var.get():
                env_dict['EMAIL_PASSWORD'] = self.email_password_var.get()
            if self.output_email_var.get():
                env_dict['OUTPUT_EMAIL'] = self.output_email_var.get()
            
            # Write back to .env file
            with open('.env', 'w') as f:
                for key, value in env_dict.items():
                    f.write(f"{key}={value}\n")
                    
        except Exception as e:
            self.log_message(f"Warning: Could not save to .env file: {e}")
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.api_key_entry.config(show="")
            self.toggle_api_btn.config(text="Hide")
        else:
            self.api_key_entry.config(show="*")
            self.toggle_api_btn.config(text="Show")
    
    def toggle_email_pass_visibility(self):
        """Toggle email password visibility"""
        self.show_email_pass = not self.show_email_pass
        if self.show_email_pass:
            self.email_password_entry.config(show="")
            self.toggle_pass_btn.config(text="Hide")
        else:
            self.email_password_entry.config(show="*")
            self.toggle_pass_btn.config(text="Show")
    
    def test_email_credentials(self):
        """Test email credentials by sending a test message"""
        def run_test():
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                email_addr = self.email_address_var.get()
                email_pass = self.email_password_var.get()
                output_email = self.output_email_var.get()
                
                if not email_addr or not email_pass:
                    self.log_message("ERROR: Email address and password required for test")
                    return
                
                if not output_email:
                    output_email = email_addr  # Send to self if no output email specified
                
                self.log_message("Testing email credentials...")
                
                # Create test message
                msg = MIMEMultipart()
                msg['From'] = email_addr
                msg['To'] = output_email
                msg['Subject'] = "Financial Transcription GUI - Test Email"
                
                body = """This is a test email from the Financial Transcription GUI.
                
If you received this, your email credentials are working correctly!

Configuration:
- From: {}
- To: {}
- Time: {}""".format(email_addr, output_email, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Send via Gmail SMTP
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_addr, email_pass)
                text = msg.as_string()
                server.sendmail(email_addr, output_email, text)
                server.quit()
                
                self.log_message("✅ Email test successful! Check your inbox.")
                
            except Exception as e:
                self.log_message(f"❌ Email test failed: {e}")
        
        # Run test in separate thread
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
    
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
                ("Audio/Video files", "*.mp3 *.mp4 *.wav *.m4a *.mov *.avi *.flv *.webm"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            def run_process():
                try:
                    if not os.path.exists("transcribe_financial.py"):
                        self.log_message("ERROR: transcribe_financial.py not found")
                        return
                    
                    self.log_message(f"Processing file: {os.path.basename(filename)}")
                    
                    # Use correct command line arguments
                    result = subprocess.run(
                        [sys.executable, "transcribe_financial.py", "--input", filename],
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30 minute timeout
                    )
                    
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log_message(line)
                    
                    if result.stderr:
                        for line in result.stderr.split('\n'):
                            if line.strip():
                                self.log_message(f"ERROR: {line}")
                    
                    if result.returncode == 0:
                        self.log_message("✅ File processing completed successfully")
                    else:
                        self.log_message(f"❌ File processing failed (exit code: {result.returncode})")
                    
                except subprocess.TimeoutExpired:
                    self.log_message("⏰ File processing timed out after 30 minutes")
                except Exception as e:
                    self.log_message(f"❌ Error processing file: {e}")
            
            # Run in separate thread
            threading.Thread(target=run_process, daemon=True).start()
    
    def process_url(self):
        """Process a URL"""
        # Create a custom dialog with more space and examples
        dialog = tk.Toplevel(self.root)
        dialog.title("Process URL")
        dialog.geometry("500x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter audio/video URL:", font=('Arial', 10, 'bold')).pack(pady=10)
        tk.Label(dialog, text="Supports: YouTube, Dropbox, Google Drive, Zoom, etc.", 
                font=('Arial', 8)).pack()
        
        url_var = tk.StringVar()
        url_entry = tk.Entry(dialog, textvariable=url_var, width=60)
        url_entry.pack(pady=10, padx=20, fill=tk.X)
        url_entry.focus()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        result = {'url': None}
        
        def ok_clicked():
            result['url'] = url_var.get().strip()
            dialog.destroy()
            
        def cancel_clicked():
            dialog.destroy()
        
        tk.Button(button_frame, text="Process", command=ok_clicked, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel_clicked, width=10).pack(side=tk.LEFT, padx=5)
        
        # Handle Enter key
        url_entry.bind('<Return>', lambda e: ok_clicked())
        
        dialog.wait_window()
        
        url = result['url']
        if url:
            def run_process():
                try:
                    if not os.path.exists("transcribe_financial.py"):
                        self.log_message("ERROR: transcribe_financial.py not found")
                        return
                    
                    self.log_message(f"Processing URL: {url}")
                    
                    # Use correct command line arguments
                    result = subprocess.run(
                        [sys.executable, "transcribe_financial.py", "--input", url],
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30 minute timeout
                    )
                    
                    if result.stdout:
                        for line in result.stdout.split('\n'):
                            if line.strip():
                                self.log_message(line)
                    
                    if result.stderr:
                        for line in result.stderr.split('\n'):
                            if line.strip():
                                self.log_message(f"ERROR: {line}")
                    
                    if result.returncode == 0:
                        self.log_message("✅ URL processing completed successfully")
                    else:
                        self.log_message(f"❌ URL processing failed (exit code: {result.returncode})")
                    
                except subprocess.TimeoutExpired:
                    self.log_message("⏰ URL processing timed out after 30 minutes")
                except Exception as e:
                    self.log_message(f"❌ Error processing URL: {e}")
            
            # Run in separate thread
            threading.Thread(target=run_process, daemon=True).start()
    
    def check_dependencies_silent(self):
        """Silently check dependencies on startup"""
        missing = []
        if not os.path.exists("email_transcribe_financial.py"):
            missing.append("email_transcribe_financial.py")
        if not os.path.exists("transcribe_financial.py"):
            missing.append("transcribe_financial.py")
        
        if missing:
            self.log_message(f"⚠️ Missing files: {', '.join(missing)}")
        else:
            self.log_message("✅ All required files found")
    
    def check_dependencies(self):
        """Check if all dependencies are installed (verbose)"""
        dependencies = [
            ("Python", sys.executable, "✅"),
            ("email_transcribe_financial.py", "email_transcribe_financial.py", None),
            ("transcribe_financial.py", "transcribe_financial.py", None),
            ("Output folder", "output", None)
        ]
        
        results = []
        missing = []
        
        for name, path, status in dependencies:
            if name == "Python":
                results.append(f"✅ {name}: {sys.version.split()[0]}")
            elif name == "Output folder":
                if os.path.exists(path):
                    results.append(f"✅ {name}: exists")
                else:
                    results.append(f"ℹ️ {name}: will be created when needed")
            elif os.path.exists(path):
                results.append(f"✅ {name}: found")
            else:
                results.append(f"❌ {name}: missing")
                missing.append(name)
        
        result_text = "\n".join(results)
        
        if missing:
            msg = f"Dependency Check Results:\n\n{result_text}\n\nMissing: {', '.join(missing)}"
            self.log_message(f"Missing dependencies: {', '.join(missing)}")
            messagebox.showwarning("Dependencies", msg)
        else:
            msg = f"Dependency Check Results:\n\n{result_text}\n\n✅ All dependencies satisfied!"
            self.log_message("All dependencies found")
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
        try:
            if self.is_running:
                if messagebox.askokcancel("Quit", "Service is running. Stop service and quit?"):
                    self.log_message("Shutting down...")
                    self.stop_service()
                    time.sleep(0.5)  # Brief pause for cleanup
                    self.save_config()
                    self.root.destroy()
            else:
                self.save_config()
                self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            # Force quit if error occurs
            try:
                self.root.destroy()
            except:
                pass

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