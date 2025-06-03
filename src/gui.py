# src/gui.py

import threading
import tkinter as tk
import customtkinter as ctk
import asyncio
import queue # This is threading.Queue, used by the GUI
import logging
import os
from pathlib import Path # <<< ADD THIS LINE
from typing import Dict
# from datetime import datetime # Not directly used

# Module-level logger for gui.py itself
module_logger = logging.getLogger('gui_app_module')

# Try to import the new function names from main.py
try:
    from main import (
        main_loop_for_gui, 
        load_app_config_for_gui, 
        CONNECT_OVER_CDP_PORT
    )
    main_loop = main_loop_for_gui
    load_config = load_app_config_for_gui
    module_logger.info("Successfully imported functions from main.py")

except ImportError as e:
    module_logger.critical(f"CRITICAL IMPORT ERROR: Kon main.py niet importeren: {e}", exc_info=True)
    # Dummy functions if main.py import fails
    async def main_loop(config, stop_event=None, gui_queue=None): # Name 'main_loop' for dummy
        print("DUMMY main_loop called because of import error")
        module_logger.error("DUMMY main_loop running due to import error.")
        if gui_queue: gui_queue.put(("log", ("DUMMY MODE: Main logic not loaded.", "CRITICAL")))
        if stop_event: 
            try:
                await stop_event.wait() # Prevent busy loop
            except asyncio.CancelledError: pass
        else: await asyncio.sleep(3600) # Sleep for a long time if no stop_event
        return

    def load_config(config_path): # Name 'load_config' for dummy
        print(f"DUMMY load_config called because of import error: {config_path}")
        module_logger.error("DUMMY load_config running due to import error.")
        return {"app_settings": {"monitoring_interval_s":300}, "targets": [], "logging": {"level": "INFO"}}

    CONNECT_OVER_CDP_PORT = None # Fallback if not imported


class GuiLoggingHandler(logging.Handler):
    def __init__(self, text_widget, gui_queue_ref: queue.Queue): # Expecting threading.Queue
        super().__init__()
        self.text_widget = text_widget
        self.gui_queue_ref = gui_queue_ref 
        # Formatter with more details
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)-7s] %(name)-15s: %(message)s', datefmt='%H:%M:%S')

    def emit(self, record):
        msg = self.format(record)
        # Ensure that putting to queue is thread-safe if called from different threads,
        # but logging handlers are usually called synchronously from the logging thread.
        try:
            self.gui_queue_ref.put(("log", (msg, record.levelname)))
        except Exception as e:
            print(f"Error in GuiLoggingHandler putting to queue: {e}")


class App(ctk.CTk):
    def __init__(self, app_config_initial): 
        super().__init__()
        self.logger = logging.getLogger('gui_app.AppInstance')
        self.logger.debug("App __init__ started.")

        self.title("Ticket Monitor Deluxe")
        self.geometry("950x700") 
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue")

        self.config = app_config_initial 
        self.bot_thread = None
        self.bot_running = False
        # Use threading.Event for cross-thread signaling with asyncio.Event used internally by main_loop_for_gui
        self.stop_bot_threading_event = threading.Event() # For signaling the bot thread from GUI
        self.stop_bot_asyncio_event = asyncio.Event() # Passed to main_loop_for_gui
        
        self.gui_queue = queue.Queue() # This is a threading.Queue

        # --- Layout ---
        self.grid_columnconfigure(0, weight=3) 
        self.grid_columnconfigure(1, weight=1, minsize=280) 
        self.grid_rowconfigure(0, weight=1)    
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.log_textbox = ctk.CTkTextbox(self.left_frame, state="disabled", wrap="word", font=("Arial", 12))
        self.log_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.log_textbox.tag_config("INFO", foreground="white") 
        self.log_textbox.tag_config("DEBUG", foreground="gray70")
        self.log_textbox.tag_config("WARNING", foreground="orange")
        self.log_textbox.tag_config("ERROR", foreground="red") # Added ERROR
        self.log_textbox.tag_config("CRITICAL", foreground="#FF0000", font=("Arial", 12, "bold")) # Bolder CRITICAL

        self.control_frame = ctk.CTkFrame(self, width=280) 
        self.control_frame.grid(row=0, column=1, padx=(0,10), pady=10, sticky="ns")
        self.control_frame.grid_propagate(False)
        
        self.start_stop_button = ctk.CTkButton(self.control_frame, text="Start Bot", command=self.toggle_bot, width=240)
        self.start_stop_button.pack(pady=20, padx=20)
        
        self.status_label_title = ctk.CTkLabel(self.control_frame, text="Status:", font=("Arial", 14, "bold"))
        self.status_label_title.pack(pady=(10,0), padx=20, anchor="w")
        self.status_label = ctk.CTkLabel(self.control_frame, text="Gestopt", font=("Arial", 12), wraplength=240, justify=tk.LEFT, anchor="nw")
        self.status_label.pack(pady=(0,10), padx=10, fill="x")
        
        self.ip_label_title = ctk.CTkLabel(self.control_frame, text="Gedetecteerd IP:", font=("Arial", 14, "bold")) # Placeholder
        self.ip_label_title.pack(pady=(10,0), padx=20, anchor="w")
        self.ip_label = ctk.CTkLabel(self.control_frame, text="Nog niet gecheckt", font=("Arial", 11), wraplength=240, justify=tk.LEFT, anchor="nw")
        self.ip_label.pack(pady=(0,10), padx=10, fill="x")
        
        self.targets_title_label = ctk.CTkLabel(self.control_frame, text="Targets Status:", font=("Arial", 14, "bold"))
        self.targets_title_label.pack(pady=(10,0), padx=20, anchor="w")
        self.targets_display_frame = ctk.CTkScrollableFrame(self.control_frame, height=250) # Initial height
        self.targets_display_frame.pack(pady=5, padx=10, fill="both", expand=True)
        self.target_status_labels: Dict[str, ctk.CTkLabel] = {} # URL -> Label widget for status

        self.cdp_status_label = ctk.CTkLabel(self.control_frame, text="", justify=tk.LEFT, wraplength=240, font=("Arial", 10))
        self.cdp_status_label.pack(pady=(10,5), padx=20, fill="x", side="bottom")

        # --- Setup ---
        self.setup_gui_logging() 
        self.load_app_config_and_populate_targets_gui() 
        self.update_cdp_info_label() 

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after_id_process_queue = self.after(100, self.process_gui_queue)
        self.logger.debug("App __init__ finished.")

    def get_cdp_info_text(self) -> str:
        # Access CONNECT_OVER_CDP_PORT that was imported (or is None)
        cdp_port_val = CONNECT_OVER_CDP_PORT # This is from the import
        
        # Check if cdp_endpoint is also set in the loaded config (more direct)
        config_cdp_endpoint = self.config.get('app_settings', {}).get('cdp_endpoint', None)

        info_lines = []
        if config_cdp_endpoint:
            info_lines.append(f"CDP Active (config): {config_cdp_endpoint}")
        elif cdp_port_val: # Fallback to the old constant if imported
            info_lines.append(f"CDP Mode (legacy): Port {cdp_port_val}")
        else:
            info_lines.append("CDP Mode: NIET ACTIEF")

        proxy_enabled_in_config = self.config.get('proxy',{}).get('enabled', False)
        if config_cdp_endpoint or cdp_port_val : # If any CDP mode is active
            if proxy_enabled_in_config: 
                info_lines.append("WAARSCHUWING: Proxy AAN in config, wordt genegeerd in CDP mode.")
            else: 
                info_lines.append("Proxy in config is correct UIT voor CDP.")
        else: # Not in CDP mode
            if not proxy_enabled_in_config and self.config: 
                info_lines.append("WAARSCHUWING: Proxy UIT in config, EIGEN IP wordt gebruikt!")
            elif proxy_enabled_in_config: 
                info_lines.append("Proxy in config staat AAN.")
            else: 
                info_lines.append("Config niet geladen voor proxy check.") # Should not happen if config loaded
        return "\n".join(info_lines)


    def update_cdp_info_label(self):
        cdp_text = self.get_cdp_info_text()
        if hasattr(self, 'cdp_status_label') and self.cdp_status_label.winfo_exists():
            self.cdp_status_label.configure(text=cdp_text)

    def setup_gui_logging(self):
        gui_handler = GuiLoggingHandler(self.log_textbox, self.gui_queue)
        root_logger = logging.getLogger() # Get the root logger
        
        # Remove any existing GuiLoggingHandler instances to prevent duplicate messages
        for handler in list(root_logger.handlers): 
            if isinstance(handler, GuiLoggingHandler):
                self.logger.debug(f"Removing existing GUI handler: {handler}")
                root_logger.removeHandler(handler)
        
        root_logger.addHandler(gui_handler)
        # The effective log level for the handler will be the minimum of its own level
        # and the logger's level. Set handler level to DEBUG to catch everything from root.
        gui_handler.setLevel(logging.DEBUG)
        
        # Root logger level will be set by config load later.
        # For now, ensure GUI handler can receive messages.
        self.logger.info("GUI Logging Handler opgezet.")


    def load_app_config_and_populate_targets_gui(self):
        try:
            # Determine config file path (similar to main.py's logic)
            script_dir = os.path.dirname(os.path.abspath(__file__)) # gui.py location
            # Assuming config is in a 'config' folder one level up from 'src' where gui.py is
            possible_config_paths = [
                os.path.join(script_dir, '..', 'config', 'config.yaml'), # if src/gui.py
                os.path.join(script_dir, 'config.yaml'), # if gui.py is next to config.yaml
                'config/config.yaml' # if project root is CWD
            ]
            config_file_to_load = None
            for path_option in possible_config_paths:
                if os.path.exists(path_option):
                    config_file_to_load = os.path.abspath(path_option)
                    break
            
            if not config_file_to_load:
                self.logger.error(f"Config file 'config.yaml' niet gevonden. Paden geprobeerd: {possible_config_paths}")
                self.config = {"app_settings": {}, "targets": [], "logging": {"level": "INFO"}} 
                tk.messagebox.showerror("Config Error", "config.yaml niet gevonden!")
                return

            self.logger.info(f"Loading config from: {config_file_to_load}")
            self.config = load_config(config_path=Path(config_file_to_load)) # Use the imported load_config
            
            if self.config:
                log_cfg = self.config.get('app_settings', {}).get('logging', {}) # Check under app_settings too
                if not log_cfg and 'logging' in self.config: log_cfg = self.config.get('logging',{})

                log_level_str = log_cfg.get('level', 'INFO').upper()
                numeric_log_level = getattr(logging, log_level_str, logging.INFO)
                
                # Set level for root logger and other relevant loggers
                logging.getLogger().setLevel(numeric_log_level) 
                self.logger.setLevel(numeric_log_level) 
                logging.getLogger('gui_app_module').setLevel(numeric_log_level)
                # Set levels for loggers used by the bot logic if desired
                for bot_logger_name in ['__main__', 'core.browser_manager', 'monitor', 'ALERT', 'GUIAyncBridge']: # Added more
                    logging.getLogger(bot_logger_name).setLevel(numeric_log_level)

                self.logger.info(f"Config loaded into GUI. Effective logging level set to {log_level_str}.")
                self.populate_target_display_from_config() 
                self.update_cdp_info_label()
            else:
                self.logger.error("Failed to load config into GUI (load_config returned None or empty).")
                self.config = {"app_settings": {}, "targets": [], "logging": {"level": "INFO"}}
        except Exception as e:
            self.logger.error(f"Error loading config for GUI or populating targets: {e}", exc_info=True)
            self.config = {"app_settings": {}, "targets": [], "logging": {"level": "INFO"}} # Fallback config
            tk.messagebox.showerror("Config Error", f"Fout bij laden config.yaml: {e}")


    def populate_target_display_from_config(self):
        for widget in self.targets_display_frame.winfo_children(): widget.destroy()
        self.target_status_labels.clear() # Clear old labels

        if self.config and self.config.get("targets"):
            targets = self.config.get("targets", [])
            for i, target_data in enumerate(targets):
                if not isinstance(target_data, dict): 
                    self.logger.warning(f"Target item {i} is not a dictionary, skipping: {target_data}")
                    continue

                event_name = target_data.get('event_name', f'Target {i+1}')
                platform = target_data.get('platform', 'N/A')
                target_url = target_data.get('url', f'#NO_URL_TARGET_{i}') # Unique key if URL missing
                enabled = target_data.get('enabled', False)
                
                short_event = event_name[:25] + '...' if len(event_name) > 25 else event_name
                
                item_f = ctk.CTkFrame(self.targets_display_frame, fg_color="transparent")
                item_f.pack(fill="x", pady=2, padx=2)
                item_f.grid_columnconfigure(0, weight=3) # Text label
                item_f.grid_columnconfigure(1, weight=2) # Status label

                base_text = f"{platform}: {short_event} ({'Actief' if enabled else 'Inactief'})"
                info_l = ctk.CTkLabel(item_f, text=base_text, wraplength=160, justify=tk.LEFT, anchor="w", font=("Arial", 11))
                info_l.grid(row=0, column=0, sticky="w", padx=(0,5))
                
                # Store status label by URL (or unique key if URL is missing) for updates
                status_l = ctk.CTkLabel(item_f, text="Wacht...", wraplength=80, justify=tk.RIGHT, anchor="e", font=("Arial", 10))
                status_l.grid(row=0, column=1, sticky="e")
                self.target_status_labels[target_url] = status_l
        else:
            ctk.CTkLabel(self.targets_display_frame, text="Geen targets geconfigureerd.").pack(pady=10)


    def bot_task_wrapper(self):
        try:
            if not self.config:
                self.gui_queue.put(("log", ("Config niet geladen, bot start niet.", "ERROR")))
                self.gui_queue.put(("status_update", "Fout: Config niet geladen"))
                self.gui_queue.put(("bot_stopped", "Status: Gestopt (Config Fout)"))
                return

            self.logger.info("Bot thread gestart.")
            self.gui_queue.put(("log", ("Bot thread gestart.", "INFO")))
            self.gui_queue.put(("status_update", "Status: Bot draait..."))
            
            # Create a new asyncio event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Reset and use the asyncio.Event for the new loop
            self.stop_bot_asyncio_event.clear()

            # Run the main_loop (which is now main_loop_for_gui)
            loop.run_until_complete(main_loop(self.config, self.stop_bot_asyncio_event, self.gui_queue))
            
            self.logger.info("Bot thread finished main_loop.")
            self.gui_queue.put(("log", ("Bot thread finished main_loop.", "INFO")))
        except Exception as e:
            self.logger.error(f"Exception in bot thread: {e}", exc_info=True)
            self.gui_queue.put(("log", (f"Exception in bot thread: {e}", "ERROR")))
        finally:
            if 'loop' in locals() and loop.is_running():
                loop.call_soon_threadsafe(loop.stop) # Stop the loop if it's still running
            self.gui_queue.put(("bot_stopped", "Status: Gestopt (thread beëindigd)"))
            # Ensure the threading.Event is also set if bot stops unexpectedly
            self.stop_bot_threading_event.set() 


    def toggle_bot(self):
        if not self.bot_running: # To start the bot
            self.logger.info("Attempting to start bot...")
            # Ensure config is loaded (or reloaded)
            self.load_app_config_and_populate_targets_gui() 
            if not self.config or not self.config.get("targets"):
                tk.messagebox.showerror("Config Error", "Config.yaml niet geladen of geen targets gedefinieerd.")
                self.status_label.configure(text="Status: Gestopt (Config Fout)")
                self.logger.warning("Bot start aborted: Config error or no targets.")
                return

            self.bot_running = True
            self.stop_bot_threading_event.clear() # Clear threading event for the wrapper
            self.stop_bot_asyncio_event.clear() # Clear asyncio event for main_loop_for_gui
            
            self.start_stop_button.configure(text="Stop Bot", fg_color="red")
            self.status_label.configure(text="Status: Bot start...") 
            
            self.bot_thread = threading.Thread(target=self.bot_task_wrapper, daemon=True)
            self.bot_thread.start()
            self.logger.info("Bot start procedure initiated.")
        else: # To stop the bot
            self.logger.info("Stop Bot aangevraagd via GUI.")
            self.status_label.configure(text="Status: Stoppen...") 
            
            # Signal both events:
            # 1. asyncio.Event for tasks inside main_loop_for_gui
            if hasattr(self.stop_bot_asyncio_event, '_loop') and self.stop_bot_asyncio_event._loop:
                 self.stop_bot_asyncio_event._loop.call_soon_threadsafe(self.stop_bot_asyncio_event.set)
            else: # If loop not available, indicates an issue or bot never fully started
                 self.stop_bot_asyncio_event.set() # Fallback set

            # 2. threading.Event for the bot_task_wrapper loop or other thread checks
            self.stop_bot_threading_event.set() 
            
            # Button state will be updated by "bot_stopped" message from queue
            # self.start_stop_button.configure(text="Start Bot") # Moved to process_gui_queue
            # self.bot_running = False # Moved to process_gui_queue


    def process_gui_queue(self):
        try:
            while True: 
                message_type, data = self.gui_queue.get_nowait()
                
                if message_type == "log":
                    msg, levelname = data
                    if hasattr(self, 'log_textbox') and self.log_textbox.winfo_exists():
                        self.log_textbox.configure(state='normal')
                        tag_name = levelname.upper()
                        valid_tags = {"INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"}
                        tag_name = tag_name if tag_name in valid_tags else "INFO"
                        self.log_textbox.insert(tk.END, msg + "\n", (tag_name,)) # Pass tag as a tuple
                        self.log_textbox.configure(state='disabled')
                        self.log_textbox.see(tk.END)
                
                elif message_type == "status_update": # General bot status
                    if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                        self.status_label.configure(text=str(data))
                
                elif message_type == "ip_update": # For future IP display
                     if hasattr(self, 'ip_label') and self.ip_label.winfo_exists():
                        self.ip_label.configure(text=str(data) if data else "Nog niet gecheckt")

                elif message_type == "target_status_update": # From original GUI
                    # Data expected: (target_url, status_string, is_hit_bool)
                    target_url, status_string, is_hit = data
                    if target_url in self.target_status_labels and self.target_status_labels[target_url].winfo_exists():
                        lbl = self.target_status_labels[target_url]
                        # Keep the original text part (event name etc.) if it's there
                        # For now, just update with status_string
                        new_text = f"{status_string}" 
                        default_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
                        
                        color = "lightgreen" if is_hit else \
                                "orange" if "BLOCK" in status_string.upper() else \
                                "red" if "ERROR" in status_string.upper() else \
                                default_color[1] if isinstance(default_color, tuple) else default_color # Handle dark/light mode color tuple

                        lbl.configure(text=new_text, text_color=color)
                        if is_hit:
                            self.status_label.configure(text=f"ALERT! Hit voor {target_url}!", text_color="lightgreen")
                            self.bell() # System beep
                
                elif message_type == "status": # Specific target status (name, message)
                    # Data expected: (target_name, status_message)
                    target_name, status_msg = data
                    # Find label by target_name (event_name) or update a general status area
                    # This requires mapping event_name to its URL if labels are keyed by URL
                    # For simplicity, we update the main status label if it's not a hit/block
                    # Look for the URL associated with this target_name from self.config
                    found_url = None
                    for t_cfg in self.config.get("targets", []):
                        if t_cfg.get("event_name") == target_name:
                            found_url = t_cfg.get("url")
                            break
                    if found_url and found_url in self.target_status_labels:
                         lbl = self.target_status_labels[found_url]
                         default_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
                         color = default_color[1] if isinstance(default_color, tuple) else default_color
                         lbl.configure(text=status_msg, text_color=color)

                elif message_type in ["hit", "blocked", "error"]: # target-specific events
                    # Data expected: (target_name, message_detail, target_url_optional)
                    target_name, detail, *url_info = data
                    target_url = url_info[0] if url_info else None

                    if not target_url: # Try to find URL from config if not provided
                        for t_cfg in self.config.get("targets", []):
                            if t_cfg.get("event_name") == target_name:
                                target_url = t_cfg.get("url", f"#NO_URL_{target_name}")
                                break
                        if not target_url: target_url = f"#NO_URL_FALLBACK_{target_name}"


                    if target_url in self.target_status_labels:
                        lbl = self.target_status_labels[target_url]
                        default_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
                        color = default_color[1] if isinstance(default_color, tuple) else default_color # Handle dark/light
                        
                        text_prefix = ""
                        if message_type == "hit":
                            color = "lightgreen"; text_prefix = "HIT! "
                            self.status_label.configure(text=f"ALERT! {text_prefix} ({target_name})", text_color=color)
                            self.bell()
                        elif message_type == "blocked":
                            color = "orange"; text_prefix = "Blocked: "
                        elif message_type == "error":
                            color = "red"; text_prefix = "Error: "
                        
                        lbl.configure(text=f"{text_prefix}{str(detail)[:30]}", text_color=color) # Show detail, truncated
                    else:
                        self.logger.warning(f"Target URL '{target_url}' for '{target_name}' not found in status labels for '{message_type}' update.")


                elif message_type == "bot_stopped":
                    if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                        self.status_label.configure(text=str(data), text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]) # Reset color
                    if hasattr(self, 'start_stop_button') and self.start_stop_button.winfo_exists():
                        self.start_stop_button.configure(text="Start Bot", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]) # Reset color
                    self.bot_running = False
                    self.stop_bot_threading_event.set() # Ensure this is set
                    self.logger.info("Bot stopped signal processed by GUI, UI updated.")
                
                self.gui_queue.task_done()
        except queue.Empty:
            pass # No messages in queue, normal
        except Exception as q_err:
            self.logger.error(f"Error processing GUI queue: {q_err}", exc_info=True)
        finally:
            if hasattr(self, 'after_id_process_queue') and self.after_id_process_queue:
                try: self.after_cancel(self.after_id_process_queue)
                except: pass # Might already be cancelled or invalid
            if self.winfo_exists(): # Check if window still exists
                self.after_id_process_queue = self.after(100, self.process_gui_queue)


    def on_closing(self):
        self.logger.info("GUI is closing...")
        if hasattr(self, 'after_id_process_queue') and self.after_id_process_queue:
             try: self.after_cancel(self.after_id_process_queue)
             except Exception as e: self.logger.debug(f"Error cancelling after_id_process_queue: {e}")
        
        if self.bot_running and self.bot_thread and self.bot_thread.is_alive():
            self.logger.info("Bot is running, attempting to stop it gracefully...")
            self.status_label.configure(text="Status: Geforceerd stoppen...")
            
            # Signal stop events
            if hasattr(self.stop_bot_asyncio_event, '_loop') and self.stop_bot_asyncio_event._loop:
                 self.stop_bot_asyncio_event._loop.call_soon_threadsafe(self.stop_bot_asyncio_event.set)
            else: self.stop_bot_asyncio_event.set()
            self.stop_bot_threading_event.set()
            
            self.bot_thread.join(timeout=5.0) # Increased timeout
            if self.bot_thread.is_alive():
                self.logger.warning("Bot thread still active after 5s timeout during closing.")
            else:
                self.logger.info("Bot thread successfully joined.")
        else:
            self.logger.info("Bot was not running or thread not alive on close.")
            
        self.destroy()
        self.logger.info("GUI destroyed.")
        # Consider sys.exit(0) if this is the main thread and other non-daemon threads might keep app alive.
        # However, if bot_thread is daemon, it should exit when main GUI thread exits.

# --- Function to start the GUI ---
def start_gui():
    # Basic logging for GUI startup sequence itself, before config fully loads logging settings
    startup_logger = logging.getLogger('gui_app_startup')
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-7s] %(name)-20s :: %(message)s")
    
    config = None
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_config_paths = [
            os.path.join(script_dir, '..', 'config', 'config.yaml'),
            'config/config.yaml' 
        ]
        config_file_to_load = None
        for path_option in possible_config_paths:
            if os.path.exists(path_option):
                config_file_to_load = os.path.abspath(path_option)
                break
        
        if not config_file_to_load:
            startup_logger.fatal(f"FATAL: config.yaml niet gevonden. Paden geprobeerd: {possible_config_paths}")
            # Show a simple Tkinter error if ctk might not be initialized
            root_tk = tk.Tk()
            root_tk.withdraw() # Hide the main Tk window
            tk.messagebox.showerror("Config Error", "config.yaml niet gevonden! Applicatie kan niet starten.")
            root_tk.destroy()
            return 
        
        startup_logger.info(f"Attempting to load config from: {config_file_to_load} for GUI.")
        # Use the imported load_config (which is load_app_config_for_gui from main.py)
        config = load_config(config_path=Path(config_file_to_load))

        if config:
            log_cfg = config.get('app_settings', {}).get('logging', {})
            if not log_cfg and 'logging' in config: log_cfg = config.get('logging',{})
            log_level_str = log_cfg.get('level', 'INFO').upper()
            log_file = log_cfg.get('log_file', 'ticket_monitor_gui.log') # GUI specific log file from config
            
            # Re-initialize logging based on config for all loggers
            # This assumes _init_logging is available or we replicate its logic
            # For simplicity, if main.py's _init_logging is comprehensive, we rely on it being called
            # by main_loop_for_gui. Here, we just ensure the GUI's own loggers are at a good level.
            numeric_log_level = getattr(logging, log_level_str, logging.INFO)
            logging.getLogger().setLevel(numeric_log_level) # Set root logger level
            startup_logger.info(f"Logging level set to {log_level_str} by GUI init from config.")
        else:
            startup_logger.error("Config kon niet geladen worden voor GUI start. Fallback config wordt gebruikt.")
            config = {"app_settings": {"monitoring_interval_s":300}, "targets":[], "logging":{"level":"INFO"}}
    
    except Exception as e:
        startup_logger.critical(f"Fatal error during GUI initialization config load: {e}", exc_info=True)
        config = {"app_settings": {"monitoring_interval_s":300}, "targets":[], "logging":{"level":"INFO"}}
        # Show error before attempting to start App
        root_tk = tk.Tk(); root_tk.withdraw(); tk.messagebox.showerror("Init Error", f"Fout bij initialisatie: {e}"); root_tk.destroy()
        return

    app = App(app_config_initial=config) 
    app.mainloop()

# This check is mostly for when gui.py is run directly for testing.
# In normal operation, main.py's __main__ block would call start_gui().
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO) # Basic logging if run directly
    module_logger.info("Starting GUI application directly (gui.py is __main__)...")
    start_gui()