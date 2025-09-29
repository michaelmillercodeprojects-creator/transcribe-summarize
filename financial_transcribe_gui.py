#!/usr/bin/env python3
"""
Financial Audio Transcription - GUI Application
Desktop application for transcribing financial audio/video content
"""

# Standard library imports
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime

# GUI imports
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Email imports (used in test_email_credentials)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class FinancialTranscribeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Financial Audio Transcription Suite")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        
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
        
        # Check system dependencies
        self.check_dependencies()
        
        # Start log queue checking
        self.root.after(100, self.process_log_queue)
    
    def load_config(self):
        """Load GUI configuration from file"""
        default_config = {
            "output_email": "",
            "send_email": False,
            "window_geometry": "800x600",
            "openai_api_key": "",
            "email_address": "",
            "email_password": "",
            "vimeo_client_id": "",
            "vimeo_client_secret": "",
            "vimeo_access_token": ""
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
        title_label = ttk.Label(main_frame, text="Financial Audio Transcription Suite", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Processing Panel
        processing_frame = ttk.LabelFrame(main_frame, text="Process Audio/Video", padding=10)
        processing_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Processing buttons
        button_frame = ttk.Frame(processing_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Process File", 
                  command=self.process_file).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Process URL", 
                  command=self.process_url).pack(side=tk.LEFT, padx=(0, 10))
        
        # Email toggle
        self.send_email_var = tk.BooleanVar(value=self.config.get("send_email", False))
        ttk.Checkbutton(button_frame, text="Send results via email", 
                       variable=self.send_email_var).pack(side=tk.RIGHT)
        
        # Status Panel
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(fill=tk.X)
        
        ttk.Label(status_info_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_info_frame, text="Ready to Process", 
                                     foreground="green", font=('Arial', 9, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(status_info_frame, text="|").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(status_info_frame, text="Mode: Direct Processing").pack(side=tk.LEFT)
        
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
        
        # Separator
        ttk.Separator(api_frame, orient='horizontal').pack(fill=tk.X, pady=(10, 10))
        
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
        
        # Email sending option
        email_option_frame = ttk.Frame(general_frame)
        email_option_frame.pack(fill=tk.X, pady=(10, 8))
        
        ttk.Label(email_option_frame, text="Default email behavior:").pack(anchor=tk.W, pady=(0, 5))
        self.default_send_email_var = tk.BooleanVar(value=self.config.get("send_email", False))
        ttk.Checkbutton(email_option_frame, text="Send results via email by default", 
                       variable=self.default_send_email_var).pack(anchor=tk.W)
        
        # Vimeo Tab
        vimeo_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(vimeo_frame, text="Vimeo")
        
        # Vimeo API credentials section
        ttk.Label(vimeo_frame, text="Vimeo API Configuration (for private videos):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 10))
        
        # Instructions
        instructions_text = """To access private Vimeo videos, you need to create a Vimeo app and get API credentials:
1. Go to https://developer.vimeo.com/apps
2. Create a new app
3. Copy the Client ID and Client Secret below
4. Generate an access token if needed for specific use cases"""
        instructions_label = ttk.Label(vimeo_frame, text=instructions_text, font=('Arial', 8), foreground="#666")
        instructions_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Vimeo Client ID row
        vimeo_id_frame = ttk.Frame(vimeo_frame)
        vimeo_id_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(vimeo_id_frame, text="Client ID:", width=15).pack(side=tk.LEFT)
        self.vimeo_client_id_var = tk.StringVar(value=self.config.get("vimeo_client_id", ""))
        self.vimeo_client_id_entry = ttk.Entry(vimeo_id_frame, textvariable=self.vimeo_client_id_var, width=40)
        self.vimeo_client_id_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Vimeo Client Secret row
        vimeo_secret_frame = ttk.Frame(vimeo_frame)
        vimeo_secret_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(vimeo_secret_frame, text="Client Secret:", width=15).pack(side=tk.LEFT)
        self.vimeo_client_secret_var = tk.StringVar(value=self.config.get("vimeo_client_secret", ""))
        self.vimeo_client_secret_entry = ttk.Entry(vimeo_secret_frame, textvariable=self.vimeo_client_secret_var, show="*", width=40)
        self.vimeo_client_secret_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Show/Hide Vimeo secret button
        self.show_vimeo_secret = False
        self.toggle_vimeo_btn = ttk.Button(vimeo_secret_frame, text="Show", width=6,
                                          command=self.toggle_vimeo_secret_visibility)
        self.toggle_vimeo_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Vimeo Access Token row (optional for some use cases)
        vimeo_token_frame = ttk.Frame(vimeo_frame)
        vimeo_token_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(vimeo_token_frame, text="Access Token:", width=15).pack(side=tk.LEFT)
        self.vimeo_access_token_var = tk.StringVar(value=self.config.get("vimeo_access_token", ""))
        self.vimeo_access_token_entry = ttk.Entry(vimeo_token_frame, textvariable=self.vimeo_access_token_var, show="*", width=40)
        self.vimeo_access_token_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # Show/Hide Vimeo token button
        self.show_vimeo_token = False
        self.toggle_vimeo_token_btn = ttk.Button(vimeo_token_frame, text="Show", width=6,
                                                command=self.toggle_vimeo_token_visibility)
        self.toggle_vimeo_token_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Test Vimeo button
        test_vimeo_frame = ttk.Frame(vimeo_frame)
        test_vimeo_frame.pack(fill=tk.X, pady=(15, 0))
        
        test_vimeo_btn = ttk.Button(test_vimeo_frame, text="Test Vimeo Connection", 
                                   command=self.test_vimeo_credentials)
        test_vimeo_btn.pack(side=tk.LEFT)
        
        # Console Tab
        console_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(console_frame, text="Console")
        
        # Console text area
        self.console_text = scrolledtext.ScrolledText(console_frame, height=20, 
                                                     font=('Consolas', 9),
                                                     background='#1e1e1e', foreground='#d4d4d4')
        self.console_text.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
        
        # Console controls
        console_controls = ttk.Frame(console_frame)
        console_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(console_controls, text="Clear Console", 
                  command=self.clear_console).pack(side=tk.LEFT)
        ttk.Button(console_controls, text="Save Console Log", 
                  command=self.save_console_log).pack(side=tk.LEFT, padx=(5, 0))
        
        # Initial console message
        self.console_message("Financial Audio Transcription Console")
        self.console_message("=" * 40)
        self.console_message("System initialized and ready for processing")
        
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
        
        # Activity Log Panel (simplified)
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, 
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(log_controls, text="View detailed output in Console tab", 
                 font=('Arial', 8), foreground="#666").pack(side=tk.RIGHT)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready to process files and URLs", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial log message
        self.log_message("Financial Audio Transcription Suite started - Ready to process")
        self.log_message("Click 'Process File' or 'Process URL' to begin transcription")
        
        # Set email toggle to saved default
        self.send_email_var.set(self.config.get("send_email", False))
        
        # Check system readiness after GUI is created
        self.root.after(1000, self.check_system_readiness)
    
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
        tools_menu.add_command(label="Check Dependencies", command=self.check_full_dependencies)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Thread-safe logging
        self.log_queue.put(log_entry)
        
        # Also log to console (simplified format)
        try:
            console_timestamp = datetime.now().strftime("%H:%M:%S")
            console_entry = f"[{console_timestamp}] {message}\n"
            self.console_text.insert(tk.END, console_entry)
            self.console_text.see(tk.END)
        except:
            # Console might not be initialized yet
            pass
    
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
    
    def check_system_readiness(self):
        """Check if system is ready for processing"""
        try:
            issues = []
            
            # Check for transcription script
            if not os.path.exists("transcribe_financial.py"):
                issues.append("transcribe_financial.py not found")
            
            # Check for API key
            api_key = self.config.get("openai_api_key", "")
            if not api_key and not os.getenv("OPENAI_API_KEY"):
                issues.append("OpenAI API key not configured")
            
            # Update status based on readiness
            if issues:
                self.status_label.config(text="Configuration Needed", foreground="orange")
                for issue in issues:
                    self.log_message(f"WARNING: {issue}")
                self.log_message("Please configure settings and ensure required files are present")
            else:
                self.status_label.config(text="Ready to Process", foreground="green")
                self.log_message("System ready - All components available")
                
                # Check email configuration
                email_addr = self.config.get("email_address", "")
                if email_addr and self.config.get("email_password", ""):
                    self.log_message("Email delivery configured and ready")
                else:
                    self.log_message("Email delivery not configured (optional)")
                    
        except Exception as e:
            self.log_message(f"Error checking system readiness: {e}")
            self.status_label.config(text="Error", foreground="red")
    
    def save_settings(self):
        """Save current settings"""
        try:
            self.config["output_email"] = self.output_email_var.get()
            self.config["send_email"] = self.default_send_email_var.get()
            self.config["openai_api_key"] = self.api_key_var.get()
            self.config["email_address"] = self.email_address_var.get()
            self.config["email_password"] = self.email_password_var.get()
            self.config["vimeo_client_id"] = self.vimeo_client_id_var.get()
            self.config["vimeo_client_secret"] = self.vimeo_client_secret_var.get()
            self.config["vimeo_access_token"] = self.vimeo_access_token_var.get()
            
            # Also save to .env file for the transcription scripts
            self.save_to_env()
            
            self.save_config()
            self.log_message("Settings saved to GUI config and .env file")
            messagebox.showinfo("Settings", "Settings saved successfully!")
            
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
            
            # Update with our values (use names expected by transcription script)
            if self.api_key_var.get():
                env_dict['OPENAI_API_KEY'] = self.api_key_var.get()
            if self.email_address_var.get():
                env_dict['SENDER_EMAIL'] = self.email_address_var.get()
                env_dict['EMAIL_ADDRESS'] = self.email_address_var.get()  # Keep for compatibility
            if self.email_password_var.get():
                env_dict['SENDER_PASSWORD'] = self.email_password_var.get()
                env_dict['EMAIL_PASSWORD'] = self.email_password_var.get()  # Keep for compatibility
            if self.output_email_var.get():
                env_dict['OUTPUT_EMAIL'] = self.output_email_var.get()
            if self.vimeo_client_id_var.get():
                env_dict['VIMEO_CLIENT_ID'] = self.vimeo_client_id_var.get()
            if self.vimeo_client_secret_var.get():
                env_dict['VIMEO_CLIENT_SECRET'] = self.vimeo_client_secret_var.get()
            if self.vimeo_access_token_var.get():
                env_dict['VIMEO_ACCESS_TOKEN'] = self.vimeo_access_token_var.get()
            
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
    
    def toggle_vimeo_secret_visibility(self):
        """Toggle Vimeo client secret visibility"""
        self.show_vimeo_secret = not self.show_vimeo_secret
        if self.show_vimeo_secret:
            self.vimeo_client_secret_entry.config(show="")
            self.toggle_vimeo_btn.config(text="Hide")
        else:
            self.vimeo_client_secret_entry.config(show="*")
            self.toggle_vimeo_btn.config(text="Show")
    
    def toggle_vimeo_token_visibility(self):
        """Toggle Vimeo access token visibility"""
        self.show_vimeo_token = not self.show_vimeo_token
        if self.show_vimeo_token:
            self.vimeo_access_token_entry.config(show="")
            self.toggle_vimeo_token_btn.config(text="Hide")
        else:
            self.vimeo_access_token_entry.config(show="*")
            self.toggle_vimeo_token_btn.config(text="Show")
    
    def test_email_credentials(self):
        """Test email credentials by sending a test message"""
        def run_test():
            try:
                # Update status
                self.status_label.config(text="Testing Email", foreground="blue")
                self.status_bar.config(text="Testing email credentials...")
                
                email_addr = self.email_address_var.get()
                email_pass = self.email_password_var.get()
                output_email = self.output_email_var.get()
                
                if not email_addr or not email_pass:
                    self.log_message("ERROR: Email address and password required for test")
                    self.status_label.config(text="Email Test Failed", foreground="red")
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
                
                self.log_message("Email test successful! Check your inbox.")
                self.status_label.config(text="Ready to Process", foreground="green")
                self.status_bar.config(text="Email test completed successfully")
                
            except Exception as e:
                self.log_message(f"Email test failed: {e}")
                self.status_label.config(text="Email Test Failed", foreground="red")
                self.status_bar.config(text="Email test failed")
        
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
                    # Update status to show processing
                    self.status_label.config(text="Processing File", foreground="blue")
                    self.status_bar.config(text="Processing file...")
                    
                    if not os.path.exists("transcribe_financial.py"):
                        self.log_message("ERROR: transcribe_financial.py not found")
                        self.status_label.config(text="Error", foreground="red")
                        return
                    
                    self.log_message(f"Processing file: {os.path.basename(filename)}")
                    
                    # Get absolute paths for Python and script
                    python_exe = sys.executable
                    script_path = os.path.abspath("transcribe_financial.py")
                    
                    # Verify script exists
                    if not os.path.exists(script_path):
                        self.log_message(f"ERROR: Script not found at {script_path}")
                        self.status_label.config(text="Error", foreground="red")
                        return
                    
                    # Build command with absolute paths and unbuffered output
                    cmd = [python_exe, "-u", script_path, "--input", filename]
                    if self.send_email_var.get() and self.config.get("output_email"):
                        cmd.extend(["--email", self.config.get("output_email")])
                        self.log_message(f"Email delivery enabled to: {self.config.get('output_email')}")
                    
                    self.log_message("Starting transcription process...")
                    self.log_message(f"Python: {python_exe}")
                    self.log_message(f"Script: {script_path}")
                    self.log_message(f"Full command: {' '.join(cmd)}")
                    
                    # Use Popen for real-time output streaming
                    self.log_message("Launching subprocess...")
                    
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True,
                            cwd=os.getcwd()  # Ensure working directory is set
                        )
                        self.log_message(f"Subprocess launched with PID: {process.pid}")
                    except Exception as e:
                        self.log_message(f"Failed to launch subprocess: {e}")
                        self.status_label.config(text="Launch Error", foreground="red")
                        return
                    
                    # Stream output in real-time
                    start_time = time.time()
                    last_output_time = start_time
                    
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.log_message(output.strip())
                            last_output_time = time.time()
                        else:
                            # Check if process is hanging (no output for 60 seconds)
                            current_time = time.time()
                            if current_time - last_output_time > 60:
                                elapsed = current_time - start_time
                                self.log_message(f"[DEBUG] No output for 60s... Process still running ({elapsed:.0f}s total)")
                                last_output_time = current_time
                            time.sleep(0.1)
                    
                    # Get return code
                    return_code = process.poll()
                    
                    if return_code == 0:
                        self.log_message("File processing completed successfully")
                        self.status_label.config(text="Ready to Process", foreground="green")
                        self.status_bar.config(text="File processing completed")
                    else:
                        self.log_message(f"File processing failed (exit code: {return_code})")
                        self.status_label.config(text="Processing Failed", foreground="red")
                        self.status_bar.config(text="File processing failed")
                    
                except subprocess.TimeoutExpired:
                    self.log_message("⚠️ File processing timed out after 30 minutes")
                    self.log_message("This usually happens with very large files or network issues")
                    self.log_message("Try with a smaller file or check your internet connection")
                    self.status_label.config(text="Processing Timeout", foreground="red")
                    self.status_bar.config(text="Processing timed out")
                except FileNotFoundError as e:
                    self.log_message(f"❌ File not found: {e}")
                    self.log_message("Make sure transcribe_financial.py is in the same directory")
                    self.status_label.config(text="Processing Error", foreground="red")
                    self.status_bar.config(text="File not found")
                except Exception as e:
                    self.log_message(f"❌ Error processing file: {e}")
                    self.log_message("Check the error details above for more information")
                    self.status_label.config(text="Processing Error", foreground="red")
                    self.status_bar.config(text="Processing error")
            
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
        
        ttk.Button(button_frame, text="OK", command=ok_clicked).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel_clicked).pack(side=tk.LEFT)
        
        # Enter key submits
        url_entry.bind('<Return>', lambda e: ok_clicked())
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        url = result['url']
        if url:
            def run_process():
                try:
                    # Update status to show processing
                    self.status_label.config(text="Processing URL", foreground="blue")
                    self.status_bar.config(text="Processing URL...")
                    
                    if not os.path.exists("transcribe_financial.py"):
                        self.log_message("ERROR: transcribe_financial.py not found")
                        self.status_label.config(text="Error", foreground="red")
                        return
                    
                    self.log_message(f"Processing URL: {url}")
                    
                    # Build command with email option if enabled
                    cmd = [sys.executable, "-u", "transcribe_financial.py", "--input", url]
                    if self.send_email_var.get() and self.config.get("output_email"):
                        cmd.extend(["--email", self.config.get("output_email")])
                        self.log_message(f"Email delivery enabled to: {self.config.get('output_email')}")
                    
                    result = subprocess.run(
                        cmd,
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
                        self.log_message("URL processing completed successfully")
                        self.status_label.config(text="Ready to Process", foreground="green")
                        self.status_bar.config(text="URL processing completed")
                    else:
                        self.log_message(f"URL processing failed (exit code: {result.returncode})")
                        self.status_label.config(text="Processing Failed", foreground="red")
                        self.status_bar.config(text="URL processing failed")
                    
                except subprocess.TimeoutExpired:
                    self.log_message("URL processing timed out after 30 minutes")
                    self.status_label.config(text="Processing Timeout", foreground="red")
                    self.status_bar.config(text="Processing timed out")
                except Exception as e:
                    self.log_message(f"Error processing URL: {e}")
                    self.status_label.config(text="Processing Error", foreground="red")
                    self.status_bar.config(text="Processing error")
            
            # Run in separate thread
            threading.Thread(target=run_process, daemon=True).start()
    
    def check_full_dependencies(self):
        """Check if all required dependencies are available"""
        def run_check():
            missing_deps = []
            available_deps = []
            problems = []
            
            # Check Python packages
            deps = ["openai", "yt-dlp", "requests", "beautifulsoup4"]
            for dep in deps:
                try:
                    result = subprocess.run([sys.executable, "-c", f"import {dep}"], 
                                          capture_output=True)
                    if result.returncode == 0:
                        available_deps.append(dep)
                    else:
                        missing_deps.append(dep)
                        problems.append(f"MISSING: {dep}: not installed")
                except Exception:
                    missing_deps.append(dep)
                    problems.append(f"MISSING: {dep}: not installed")
            
            # Additional checks - tkinter is already imported at top
            available_deps.append("tkinter")
            
            # Show results
            if missing_deps:
                result_text = f"Missing Dependencies ({len(missing_deps)}):\\n\\n"
                result_text += "\\n".join(problems)
                if available_deps:
                    result_text += f"\\n\\nAvailable ({len(available_deps)}): {', '.join(available_deps)}"
                result_text += "\\n\\nInstall missing dependencies with:\\npip install " + " ".join(missing_deps)
                messagebox.showwarning("Dependencies Check", result_text)
            else:
                result_text = f"All dependencies available ({len(available_deps)}):\\n\\n"
                result_text += "\\n".join([f"• {dep}" for dep in available_deps])
                messagebox.showinfo("Dependencies Check", result_text)
        
        # Run check in separate thread
        threading.Thread(target=run_check, daemon=True).start()
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Financial Audio Transcription Suite

A desktop application for transcribing and analyzing financial audio/video content using OpenAI's APIs.

Features:
• Process local audio/video files
• Process URLs from YouTube, Dropbox, etc.
• Optional email delivery of results
• Configurable API key and email settings

Version: 2.0
"""
        messagebox.showinfo("About", about_text)
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            # Check ffmpeg
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
            self.log_message("✓ FFmpeg is available")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            self.log_message("⚠️ FFmpeg not found - audio processing may fail")
            self.log_message("Install FFmpeg: https://ffmpeg.org/download.html")
        
        # Check transcribe_financial.py
        if os.path.exists("transcribe_financial.py"):
            self.log_message("✓ transcribe_financial.py found")
        else:
            self.log_message("❌ transcribe_financial.py not found in current directory")
        
        # Check for API key
        try:
            from dotenv import load_dotenv
            load_dotenv()
            if os.getenv("OPENAI_API_KEY"):
                self.log_message("✓ OpenAI API key configured")
            else:
                self.log_message("⚠️ OpenAI API key not found - set OPENAI_API_KEY environment variable")
        except ImportError:
            self.log_message("⚠️ python-dotenv not installed - API key loading may fail")
        
        self.log_message("System check complete\n")

    def console_message(self, message):
        """Add message to console tab"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            self.console_text.insert(tk.END, formatted_message)
            self.console_text.see(tk.END)
        except Exception as e:
            # Fallback to regular log if console not available
            self.log_message(f"Console: {message}")

    def clear_console(self):
        """Clear console output"""
        self.console_text.delete(1.0, tk.END)
        self.console_message("Console cleared")

    def save_console_log(self):
        """Save console log to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Console Log",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.console_message(f"Console log saved to {filename}")
        except Exception as e:
            self.console_message(f"Error saving console log: {e}")

    def test_vimeo_credentials(self):
        """Test Vimeo API credentials"""
        client_id = self.vimeo_client_id_var.get().strip()
        client_secret = self.vimeo_client_secret_var.get().strip()
        
        if not client_id or not client_secret:
            messagebox.showerror("Error", "Please enter both Vimeo Client ID and Client Secret")
            return
            
        self.console_message("Testing Vimeo API credentials...")
        
        def test_thread():
            try:
                import vimeo
                v = vimeo.VimeoClient(
                    token=None,
                    key=client_id,
                    secret=client_secret
                )
                # Test with a simple API call
                response = v.get('/me')
                if response.status_code == 200:
                    self.console_message("✓ Vimeo API credentials are valid")
                    self.log_message("✓ Vimeo API test successful")
                    messagebox.showinfo("Success", "Vimeo API credentials are valid!")
                else:
                    self.console_message(f"❌ Vimeo API test failed: HTTP {response.status_code}")
                    messagebox.showerror("Error", f"Vimeo API test failed: HTTP {response.status_code}")
            except ImportError:
                self.console_message("❌ PyVimeo not installed. Run: pip install PyVimeo")
                messagebox.showerror("Error", "PyVimeo not installed. Please install it with: pip install PyVimeo")
            except Exception as e:
                self.console_message(f"❌ Vimeo API test failed: {e}")
                messagebox.showerror("Error", f"Vimeo API test failed: {e}")
        
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def on_closing(self):
        """Handle window closing"""
        self.save_config()
        self.root.destroy()

def main():
    """Main function to run the GUI"""
    try:
        root = tk.Tk()
        app = FinancialTranscribeGUI(root)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()