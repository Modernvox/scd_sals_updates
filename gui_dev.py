import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Toplevel, Label
import os
import logging
import asyncio
import threading
import time
from datetime import datetime, timezone, timedelta
import webbrowser

import requests
import sqlite3
from PIL import Image, ImageTk
import socketio

from config import PRIMARY_COLOR, get_resource_path, load_config, DEFAULT_DATA_DIR, TIER_LIMITS, PAYMENT_LINKS, load_email, save_email, clear_saved_email, ensure_data_dir
from bidder_manager import BidderManager
from telegram_service import TelegramService
from database import DatabaseManager
from reportlab.lib.units import inch
from annotate_labels import annotate_whatnot_pdf_with_bins_skip_missing
from dotenv import load_dotenv
load_dotenv()

class SwiftSaleGUI(tk.Frame):
    def __init__(
        self,
        master,
        stripe_service,
        api_token,
        user_email,
        base_url,
        dev_unlock_code,
        telegram_bot_token,
        telegram_chat_id,
        dev_access_granted,
        log_info,
        log_error
    ):
        self.dev_access_granted = dev_access_granted
        logging.debug("Initializing SwiftSaleGUI")
        self.master = master
        self.root = master
        ttk.Style(self.master).theme_use('clam')
        # ──────────────────────────────────────────────────────────────────
        # Dark‐mode overrides for all ttk widgets
        self.master.configure(bg="#000000")
        style = ttk.Style(self.master)

        # Frame backgrounds
        style.configure("TFrame", background="000000")
        style.configure("TLabelFrame", background="#286057")
        style.configure("TLabelframe.Label", background="#286057", foreground="#FFFFFF")

        # Section panels (slightly lighter panel style)
        style.configure(
            "Section.TFrame",
            background="#000000",
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "Section.TLabel",
            background="#000000",
            foreground="#E1E1E1",
            font=("Segoe UI", 12, "bold")
        )

        # Labels (primary + secondary)
        style.configure(
            "TLabel",
            background="#000000",
            foreground="#FFFFFF",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Secondary.TLabel",
            background="#000000",
            foreground="#A0A0A0",
            font=("Segoe UI", 9, "italic")
        )

        # Entry and Combobox fields
        style.configure(
            "TEntry",
            fieldbackground="#FFFFFF",
            background="#252526",
            foreground="#000000",
            font=("Segoe UI", 10)
        )
        style.map("TEntry",
                  bordercolor=[("focus", "#286057")],
                  borderwidth=[("focus", 2)]
        )

        style.configure(
            "TCombobox",
            fieldbackground="#252526",
            background="#252526",
            foreground="#FFFFFF",
            font=("Segoe UI", 10)
        )
        style.map("TCombobox",
                  bordercolor=[("focus", "#2A9D8F")],
                  borderwidth=[("focus", 2)]
        )

        # Treeview (bidders/analytics tables)
        style.configure(
            "Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#252526",
            rowheight=24,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#F0F0F0",
            foreground="#000000",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview.Heading",
                  background=[("active", "#E0E0E0")],
                  foreground=[("active", "#000000")]
        )
        style.map("Treeview",
                  background=[("selected", "#3baea3")],
                  foreground=[("selected", "#FFFFFF")]
        )

        # Buttons
        style.configure(
            "TButton",
            background=PRIMARY_COLOR, 
            foreground="#E1E1E1",
            font=("Segoe UI", 10),
            borderwidth=1,
            relief="ridge",
            focuscolor="#2A9D8F"
        )
        style.map("TButton",
                  background=[("active", "#3baea3"), ("disabled", "#5A5A5E")],
                  foreground=[("disabled", "#A0A0A0")]
        )

        # Primary (muted teal accent) button
        style.configure(
            "Primary.TButton",
            background="#286057",        # idle state (static)
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat"
        )
        style.map("Primary.TButton",
                  background=[("active", "#3baea3"), ("disabled", "#5A5A5E"), ("pressed", "#378474"), ("disabled", "#5A5A5E") ], 
                  foreground=[("disabled", "#A0A0A0")]
        )

        # Danger (orange accent) button
        style.configure(
            "Danger.TButton",
            background="#FF9500",
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat"
        )
        style.map("Danger.TButton",
                  background=[("active", "#CC7A00"), ("disabled", "#5A5A5E")],
                  foreground=[("disabled", "#A0A0A0")]
        )

        # Checkbutton / Radiobutton
        style.configure(
            "TCheckbutton",
            background="#000000",
            foreground="#FFFFFF",
            font=("Segoe UI", 10)
        )
        style.configure(
            "TRadiobutton",
            background="#000000",
            foreground="#FFFFFF",
            font=("Segoe UI", 10)
        )

        # Notebook Tabs
        style.configure(
            "TNotebook",
            background="#000000",
            tabmargins=[2, 5, 2, 0]
        )
        style.configure(
            "TNotebook.Tab",
            background="#000000",
            foreground="#2A9D8F",
            font=("Segoe UI", 10, "bold"),
            padding=[10, 5]
        )
        style.map("TNotebook.Tab",
                  background=[("selected", "#286057")],
                  foreground=[("selected", "#FFFFFF")]
        )

        style.configure(
            "Green.TButton",
            background="#286057",     # idle
            foreground="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Green.TButton",
            background=[
                ("active", "#378474"),   # hover
                ("pressed", "#2E645B"),  # pressed
                ("!disabled", "#286057") # idle
            ],
            foreground=[("disabled", "#A0A0A0")]
        )

        # ─── 2) Define Yellow.TButton style (blink variant) ──────────────
        style.configure(
            "Yellow.TButton",
            background="#FFD54F",     # blink idle
            foreground="#333333",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Yellow.TButton",
            background=[
                ("active", "#FFEB3B"),   # hover
                ("pressed", "#FBC02D"),  # pressed
                ("!disabled", "#FFD54F") # idle
            ],
            foreground=[("disabled", "#A0A0A0")]
        )

        # ──────────────────────────────────────────────────────────────────
        self.master.title("SwiftSale")
        self.master.geometry("1100x650")
        
        ensure_data_dir()

        self.stripe_service = stripe_service
        self.api_token = api_token.strip()
        self.user_email = user_email or load_email()
        if not self.user_email:
            self.user_email = self.prompt_login()
            if self.user_email:
                save_email(self.user_email)
        self.subscription = None  # or leave it unset until the later logic
        self.base_url = base_url
        self.dev_unlock_code = dev_unlock_code
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.log_info = log_info
        self.log_error = log_error

        self.db_manager = DatabaseManager()
        self.bidder_manager = BidderManager()
        self.latest_bin_assignment = "Waiting for bidder..."

        subscription = self.db_manager.get_subscription(self.user_email)
        if subscription:
            db_tier = subscription.get("tier", "Trial")
            license_key = subscription.get("license_key")

            # ✅ Check with Stripe to confirm subscription is still valid and tier is accurate
            verified_tier, verified_license = self.stripe_service.verify_subscription(self.user_email, db_tier, license_key)

            # Update local tier and license regardless of mismatch
            self.tier = verified_tier
            self.license_key = verified_license
            logging.info(
                f"[SUBSCRIPTION] Verified {self.user_email}: tier={self.tier}, license={self.license_key}"
            )
        else:
            self.tier = "Trial"
            self.license_key = None
            logging.info("No subscription found: Defaulting to Trial tier")

        self.sio = socketio.Client()

        self.loop = None

        def run_asyncio_loop():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.loop.run_forever()
            except Exception as e:
                self.log_error(f"Asyncio loop failed: {e}", exc_info=True)

        self.loop_thread = threading.Thread(target=run_asyncio_loop, daemon=True)
        self.loop_thread.start()
        time.sleep(0.1)

        self.telegram_service = TelegramService(
            self.telegram_bot_token,
            chat_id=self.telegram_chat_id,
            loop=self.loop
        )

        self.chat_id = ""
        self.top_buyer_text = "WTG {username} you nabbed {qty} auctions so far!"
        self.giveaway_announcement_text = "Givvy is up! Make sure you LIKE & SHARE! Winner announced shortly!"
        self.flash_sale_announcement_text = "Flash Sale! Grab these deals before they sell out!"
        self.multi_buyer_mode = False

        try:
            settings = self.db_manager.get_settings(self.user_email)
            if settings:
                self.chat_id = settings.get("chat_id", "")
                self.top_buyer_text = settings.get("top_buyer_text", self.top_buyer_text)
                self.giveaway_announcement_text = settings.get("giveaway_announcement_text", self.giveaway_announcement_text)
                self.flash_sale_announcement_text = settings.get("flash_sale_announcement_text", self.flash_sale_announcement_text)
                self.multi_buyer_mode = settings.get("multi_buyer_mode", False)
        except Exception as e:
            self.log_error(f"Failed to load settings for {self.user_email}: {e}", exc_info=True)

        self.default_x_offset = 2.6
        self.default_y_offset = 5.3

        self.settings_initialized = False
        self.subscription_initialized = False
        self.annotate_initialized = False

        self.master.after(500, self._blink_start_button)
        self.setup_ui()
        self.register_socketio_events()
        self.setup_socketio()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Control-Alt-d>", self.enable_dev_mode_prompt)
        self.log_info("SwiftSale GUI initialized")

    def refresh_tier_settings(self):
        self.max_bins = TIER_LIMITS.get(self.tier, 20)
        self.update_bins_used_display()
        self.check_bin_limit_and_update_ui()

    def register_socketio_events(self):
        @self.sio.on('update')
        def on_update(data):
            self.latest_bin_assignment = data.get('data', "Waiting for bidder...")
            logging.debug(f"Received SocketIO update: {self.latest_bin_assignment}")
            self.root.after(0, self.update_header_and_footer)

    def setup_socketio(self):
        @self.sio.event
        def connect():
            self.log_info("Connected to Flask server via SocketIO")
            self.sio.emit('connect')

        @self.sio.event
        def disconnect():
            self.log_info("Disconnected from Flask server via SocketIO")

        retries = 3
        config = load_config()
        port = config.get("PORT", 5000)
        while retries > 0:
            try:
                self.sio.connect(f'http://localhost:{port}', wait_timeout=5)
                break
            except socketio.exceptions.ConnectionError as e:
                retries -= 1
                logging.warning(f"SocketIO connection attempt failed: {e}. Retries left: {retries}")
                if retries == 0:
                    self.log_error(f"Failed to connect to Flask server via SocketIO: {e}")
                    messagebox.showerror(
                        "SocketIO Error",
                        "Failed to connect to server. Please ensure the SwiftSale application is running."
                    )
                time.sleep(2)

        
    def get_device_id():
        return platform.node().strip().lower()

    def enable_dev_mode_prompt(self, event=None):
        import platform
        import psycopg2
        from psycopg2 import sql
        from datetime import datetime, timezone
        from tkinter import messagebox, simpledialog

        db_connection_string = os.getenv("DEV_CODE_DB_URL") or os.getenv("DATABASE_URL")
        device_id = platform.node().strip().lower()    

        code = simpledialog.askstring("Developer Mode", "Enter developer code:")
        if not code:
            return

        try:
            with psycopg2.connect(db_connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT email, expires_at, used, assigned_to, device_id FROM dev_codes
                        WHERE code = %s
                    """, (code,))
                    result = cursor.fetchone()

                    if not result:
                        self.log_info(f"Dev unlock attempt failed: code '{code}' not found.")
                        messagebox.showwarning("Denied", "Invalid or unrecognized code.")
                        return

                    email, expires_at, used, assigned_to, bound_device = result
                    now = datetime.now(timezone.utc)

                    if used:
                        if assigned_to != self.user_email or bound_device != device_id:
                            self.log_info(f"Dev code '{code}' rejected: bound to {assigned_to}/{bound_device}, tried {self.user_email}/{device_id}")
                            messagebox.showwarning("Denied", "This code is already in use on another device/email.")
                            return
                        if expires_at and now > expires_at:
                            self.log_info(f"Dev code '{code}' denied: expired on {expires_at}")
                            messagebox.showwarning("Denied", "This code has expired.")
                            return

                    else:
                        expires = None if code.lower() == "brandi9933" else now + timedelta(hours=48)
                        cursor.execute("UPDATE dev_codes SET used = TRUE, assigned_to = %s, device_id = %s, expires_at = %s WHERE code = %s", (self.user_email, device_id, expires, code))
                        conn.commit()                                       

                    self.tier = "Gold"
                    self.license_key = "DEV_MODE"
                    self.refresh_tier_settings()

                    if hasattr(self, "tier_var"):
                        self.tier_var.set("Gold")
                    self.root.title("SwiftSale – Developer Mode (Gold)")
                    self.log_info(f"Dev mode unlocked for {email} using code '{code}'")
                    messagebox.showinfo("Unlocked", "Gold tier unlocked!")

                    
        except Exception as e:
            import traceback
            self.log_error(f"Database error during code validation: {e}\n{traceback.format_exc()}")
            messagebox.showerror("Validation Error", str(e))

    def update_header_and_footer(self):
        self.header_label.config(text=f"SwiftSale - {self.user_email} ({self.tier})       |       Build Whatnot Orders in Realtime with the SwiftSale App!")
        self.footer_label.config(text=f"SwiftSale - {self.tier} Tier - Latest Bin: {self.latest_bin_assignment}")
        logging.debug("Updated header and footer")

    def prompt_login(self):
        email = simpledialog.askstring("Login", "Enter your email:")

        if not email:
            print("No email provided — starting in Trial mode.")
            messagebox.showinfo("Trial Mode", "No email entered.\nYou're using the app in Trial mode (20 bins).")
            return ""  # return blank to fall back on Trial
            
        email = email.strip()
        print(f"User logged in with email: {email}")
        return email

    def load_settings(self):
        defaults = {
            "top_buyer_text": "WTG {username} you nabbed {qty} auctions so far!",
            "giveaway_announcement_text": "Givvy is up! Make sure you LIKE & SHARE! Winner announced shortly!",
            "flash_sale_announcement_text": "Flash Sale! Grab these deals before they sell out!",
            "chat_id": "",
            "multi_buyer_mode": False
        }
        try:
            settings = self.db_manager.get_settings(self.user_email)
            if settings:
                self.chat_id = settings.get("chat_id", defaults["chat_id"])
                self.top_buyer_text = settings.get("top_buyer_text") or defaults["top_buyer_text"]
                self.giveaway_announcement_text = settings.get("giveaway_announcement_text") or defaults["giveaway_announcement_text"]
                self.flash_sale_announcement_text = settings.get("flash_sale_announcement_text") or defaults["flash_sale_announcement_text"]
                self.multi_buyer_mode = settings.get("multi_buyer_mode", defaults["multi_buyer_mode"])
                self.log_info(f"Loaded settings for {self.user_email}")
            else:
                self.chat_id = defaults["chat_id"]
                self.top_buyer_text = defaults["top_buyer_text"]
                self.giveaway_announcement_text = defaults["giveaway_announcement_text"]
                self.flash_sale_announcement_text = defaults["flash_sale_announcement_text"]
                self.multi_buyer_mode = defaults["multi_buyer_mode"]
                self.log_info(f"No settings found; using defaults for {self.user_email}")
        except Exception as e:
            self.log_error(f"Failed to load settings for {self.user_email}: {e}", exc_info=True)
            self.chat_id = defaults["chat_id"]
            self.top_buyer_text = defaults["top_buyer_text"]
            self.giveaway_announcement_text = defaults["giveaway_announcement_text"]
            self.flash_sale_announcement_text = defaults["flash_sale_announcement_text"]
            self.multi_buyer_mode = defaults["multi_buyer_mode"]

    def save_settings(self):
        try:
            chat_id = self.chat_id_entry.get().strip()
            top_buyer_text = self.top_buyer_entry.get().strip()
            giveaway_text = self.giveaway_entry.get().strip()
            flash_sale_text = self.flash_sale_entry.get().strip()
            multi_buyer_mode = self.multi_buyer_var.get()

            if chat_id and not (chat_id.startswith('@') or chat_id.isdigit()):
                messagebox.showerror("Error", "Invalid Telegram Chat ID! It must start with '@' or be a numeric ID.")
                logging.warning("Save settings: Invalid chat ID format")
                return

            if not top_buyer_text:
                messagebox.showerror("Error", "Top Buyer Text cannot be empty!")
                logging.warning("Save settings: Empty top buyer text")
                return
            if not giveaway_text:
                messagebox.showerror("Error", "Giveaway Text cannot be empty!")
                logging.warning("Save settings: Empty giveaway text")
                return
            if not flash_sale_text:
                messagebox.showerror("Error", "Flash Sale Text cannot be empty!")
                logging.warning("Save settings: Empty flash sale text")
                return

            self.db_manager.save_settings(
                self.user_email,
                chat_id,
                top_buyer_text,
                giveaway_text,
                flash_sale_text,
                multi_buyer_mode
            )
            self.chat_id = chat_id
            self.top_buyer_text = top_buyer_text
            self.giveaway_announcement_text = giveaway_text
            self.flash_sale_announcement_text = flash_sale_text
            self.multi_buyer_mode = multi_buyer_mode
            messagebox.showinfo("Success", "Settings saved!")
            self.log_info("Settings saved successfully")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to save settings: Database error - {e}")
            self.log_error(f"Failed to save settings: {e}", exc_info=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            self.log_error(f"Failed to save settings: {e}", exc_info=True)

    def build_settings_ui(self, parent_frame):
        settings_frame = ttk.LabelFrame(parent_frame, text="Settings", font=("Arial", 12), style="Section.TFrame")
        settings_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(settings_frame, text="Telegram Chat ID:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.chat_id_entry = ttk.Entry(settings_frame)
        self.chat_id_entry.insert(0, self.chat_id)
        self.chat_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        telegram_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_telegram_help
        )
        telegram_help_button.grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(settings_frame, text="Top Buyer Text:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.top_buyer_entry = ttk.Entry(settings_frame)
        self.top_buyer_entry.insert(0, self.top_buyer_text)
        self.top_buyer_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        top_buyer_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_top_buyer_help
        )
        top_buyer_help_button.grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(settings_frame, text="Giveaway Text:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.giveaway_entry = ttk.Entry(settings_frame)
        self.giveaway_entry.insert(0, self.giveaway_announcement_text)
        self.giveaway_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        giveaway_text_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_giveaway_text_help
        )
        giveaway_text_help_button.grid(row=2, column=2, padx=5, pady=2)

        ttk.Label(settings_frame, text="Flash Sale Text:", style="TLabel").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.flash_sale_entry = ttk.Entry(settings_frame)
        self.flash_sale_entry.insert(0, self.flash_sale_announcement_text)
        self.flash_sale_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        flash_sale_text_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_flash_sale_text_help
        )
        flash_sale_text_help_button.grid(row=3, column=2, padx=5, pady=2)

        self.multi_buyer_var = tk.BooleanVar(value=self.multi_buyer_mode)
        ttk.Checkbutton(
            settings_frame, text="Multi-Buyer Top Message", variable=self.multi_buyer_var, style="TCheckbutton"
        ).grid(row=4, column=0, columnspan=2, pady=2)

        save_settings_button = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings, width=15, style="Primary.TButton")
        save_settings_button.grid(row=5, column=0, columnspan=2, pady=5)
        logging.debug("Save Settings button initialized")

    def build_subscription_ui(self, parent_frame):
        subscription_frame = ttk.LabelFrame(parent_frame, text="Subscription", font=("Arial", 12), style="TFrame")
        subscription_frame.pack(fill=tk.X, pady=5, padx=5)

        self.tier_var = tk.StringVar(value=self.tier)
        tiers = ["Trial", "Bronze", "Silver", "Gold"]
        ttk.Label(subscription_frame, text="Select Tier:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.OptionMenu(subscription_frame, self.tier_var, self.tier, *tiers).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        status, next_billing = self.stripe_service.get_subscription_status(self.license_key)
        ttk.Label(subscription_frame, text=f"Status: {status}", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(subscription_frame, text=f"Next Billing: {next_billing}", style="TLabel").grid(row=1, column=1, sticky="w", padx=5, pady=2)

        upgrade_button = ttk.Button(subscription_frame, text="Upgrade", command=self.on_upgrade, width=12, style="Primary.TButton")
        upgrade_button.grid(row=2, column=0, pady=5, sticky="ew")
        logging.debug("Upgrade button initialized")

        downgrade_button = ttk.Button(subscription_frame, text="Downgrade", command=self.on_downgrade, width=12, style="Primary.TButton")
        downgrade_button.grid(row=2, column=1, pady=5, sticky="ew")
        logging.debug("Downgrade button initialized")

        cancel_button = ttk.Button(subscription_frame, text="Cancel", command=self.on_cancel, width=12, style="Primary.TButton")
        cancel_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        logging.debug("Cancel button initialized")

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#286057")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        logo_path = get_resource_path("swiftsale_logo.png")
        try:
            logo_img = Image.open(logo_path).resize((50, 50), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(
                header_frame,
                image=self.logo,
                bg="#286057",
                borderwidth=0
             ).pack(side=tk.LEFT, padx=10)
        except Exception as e:
            self.log_error(f"Failed to load logo: {e}")
            ttk.Label(
                header_frame,
                text="SwiftSale",
                font=("Arial", 14),
                style="TLabel"
            ).pack(side=tk.LEFT, padx=10)

        self.header_label = tk.Label(
            header_frame,
            text=f"SwiftSale - {self.user_email} ({self.tier}) | Build Whatnot Orders in Realtime with the SwiftSale App!",
            font=("Arial", 14, "bold"),
            bg="#286057",
            fg="#FFFFFF",
            highlightbackground="#286057",
            highlightthickness=0
        )
        self.header_label.pack(side=tk.LEFT, padx=10)

        self.main_frame = ttk.Frame(self.root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(self.main_frame, bg="#000000")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        input_frame = ttk.LabelFrame(left_frame, text="Add Bidder", style="TFrame")
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Username:", style="TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.username_entry = ttk.Entry(input_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.username_entry.bind("<Button-1>", self.auto_paste_username)

        add_bidder_button = ttk.Button(input_frame, text="Add Bidder", command=self.add_bidder, style="Primary.TButton", width=12)
        add_bidder_button.grid(row=0, column=2, padx=5, pady=2, sticky="ew")
        logging.debug("Add Bidder button initialized")

        clear_button = ttk.Button(input_frame, text="Clear", command=self.clear_username, style="Danger.TButton", width=12)
        clear_button.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        logging.debug("Clear button initialized")

        ttk.Label(input_frame, text="Quantity:", style="TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.qty_entry = ttk.Entry(input_frame)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(input_frame, text="Weight:", style="TLabel").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.weight_entry = ttk.Entry(input_frame)
        self.weight_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        self.giveaway_var = tk.BooleanVar()
        ttk.Checkbutton(
            input_frame, text="Giveaway", variable=self.giveaway_var, style="TCheckbutton"
        ).grid(row=3, column=0, columnspan=2, pady=2)

        analytics_frame = ttk.LabelFrame(left_frame, text="Analytics", style="TFrame")
        analytics_frame.pack(fill=tk.X, pady=5)

        ttk.Label(analytics_frame, text="Top Buyers:", style="TLabel").pack(anchor="w", padx=5)
        self.top_buyers_text = tk.Text(analytics_frame, height=5, width=30, bg="#FFFFFF", fg="#000000")
        self.top_buyers_text.pack(padx=5, pady=5, fill=tk.X)

        self.top_buyer_copy_label = tk.Label(
            analytics_frame,
            text="Click to copy top buyer(s) message",
            font=("Segoe UI", 10, "underline"),
            fg="#2A9D8F",
            bg="#000000",
            cursor="hand2"
        )
        self.top_buyer_copy_label.pack(anchor="w", padx=10)
        self.top_buyer_copy_label.bind("<Button-1>", self.copy_top_buyer_message)

        self.stats_label = ttk.Label(analytics_frame, text="Avg Sell Rate: N/A", style="TLabel")
        self.stats_label.pack(anchor="w", padx=10)

        analytics_button_row = tk.Frame(analytics_frame, bg="#000000")
        analytics_button_row.pack(fill=tk.X, pady=5)

        show_sell_rate_button = ttk.Button(analytics_button_row, text="Show Sell Rate", command=self.show_avg_sell_rate, width=15, style="Primary.TButton")
        show_sell_rate_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Show Sell Rate button initialized")

        self.start_show_button = ttk.Button(analytics_button_row, text="Start Show", command=self.start_show, style="Primary.TButton", width=15)
        self.start_show_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Start Show button initialized")

        self._is_blinking = True
        self._blink_job = None
        self.master.after(500, self._blink_start_button)

        start_giveaway_button = ttk.Button(analytics_button_row, text="Start Giveaway", command=self.copy_giveaway_message, width=15, style="Primary.TButton")
        start_giveaway_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Start Giveaway button initialized")

        start_flash_sale_button = ttk.Button(analytics_button_row, text="Start Flash Sale", command=self.copy_flash_sale, width=15, style="Primary.TButton")
        start_flash_sale_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Start Flash Sale button initialized")

        giveaway_help_button = ttk.Button(
            analytics_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_giveaway_help
        )
        giveaway_help_button.pack(anchor="w", padx=5, pady=2)

        right_frame = tk.Frame(self.main_frame, bg="#000000")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)        

        # Add Bins Used display
        self.bins_used_frame = tk.Frame(right_frame, bg="#4d7a31")
        self.bins_used_frame.pack(fill=tk.X, padx=5, pady=2, side=tk.TOP)
        self.bins_used_label = tk.Label(
            self.bins_used_frame,
            text="Bins Used: 0/20",
            bg="#4d7a31",  # Match the frame's background
            fg="#FFFFFF",  # Ensure text is readable (white)
            font=("Arial", 12, "bold")  # Optional: Match the style's appearance
        )
        self.bins_used_label.pack(side=tk.RIGHT)
        self.update_bins_used_display()  # Initialize the display

        self.bidders_frame = ttk.LabelFrame(right_frame, text="", style="TFrame")
        self.bidders_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.header_frame = tk.Frame(self.bidders_frame, bg="#000000")
        self.header_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(self.header_frame, text="Bidders", style="Section.TLabel").pack(side=tk.LEFT)
        self.toggle_button = ttk.Button(self.header_frame, text="+", width=2, command=self.toggle_treeview, style="Primary.TButton")
        self.toggle_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Toggle button initialized")

        latest_bidder_box = tk.Frame(
            self.bidders_frame,
            bg="#FFFFFF",
            relief="raised",
            borderwidth=2,
            highlightbackground="#286057",
            highlightthickness=1
        )
        latest_bidder_box.pack(padx=5, pady=5, fill=tk.X)

        self.latest_bidder_label = tk.Label(
            latest_bidder_box,
            text="Latest: None",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF",
            fg="#000000",
            pady=8,
            padx=10
        )
        self.latest_bidder_label.pack(fill=tk.X)

        self.tree_frame = tk.Frame(self.bidders_frame, bg="#000000")
        self.bidders_tree = ttk.Treeview(
            self.tree_frame,
            columns=("Username", "Quantity", "Bin", "Giveaway", "Weight", "Timestamp"),
            show="headings",
            height=10
        )
        self.bidders_tree.heading("Username", text="Username")
        self.bidders_tree.heading("Quantity", text="Qty")
        self.bidders_tree.heading("Bin", text="Bin")
        self.bidders_tree.heading("Giveaway", text="Giveaway")
        self.bidders_tree.heading("Weight", text="Weight")
        self.bidders_tree.heading("Timestamp", text="Timestamp")
        self.bidders_tree.column("Username", width=150)
        self.bidders_tree.column("Quantity", width=60, anchor="center")
        self.bidders_tree.column("Bin", width=60, anchor="center")
        self.bidders_tree.column("Giveaway", width=80, anchor="center")
        self.bidders_tree.column("Weight", width=80, anchor="center")
        self.bidders_tree.column("Timestamp", width=150)
        self.bidders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.bidders_tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bidders_tree.configure(yscrollcommand=self.scrollbar.set)

        button_row_frame = tk.Frame(self.bidders_frame, bg="#000000")
        button_row_frame.pack(fill=tk.X, pady=5)

        print_bidders_button = ttk.Button(button_row_frame, text="Print Bidders", command=self.print_bidders, width=15, style="Primary.TButton")
        print_bidders_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Print Bidders button initialized")
        print_bidders_help_button = ttk.Button(
            button_row_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_print_bidders_help
        )
        print_bidders_help_button.pack(side=tk.LEFT, padx=2)

        import_csv_button = ttk.Button(button_row_frame, text="Import CSV", command=self.import_csv, width=15, style="Primary.TButton")
        import_csv_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Import CSV button initialized")
        import_csv_help_button = ttk.Button(
            button_row_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_import_csv_help
        )
        import_csv_help_button.pack(side=tk.LEFT, padx=2)

        export_csv_button = ttk.Button(button_row_frame, text="Export CSV", command=self.export_csv, width=15, style="Primary.TButton")
        export_csv_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Export CSV button initialized")
        export_csv_help_button = ttk.Button(
            button_row_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_export_csv_help
        )
        export_csv_help_button.pack(side=tk.LEFT, padx=2)

        
        sort_bin_frame = tk.Frame(self.bidders_frame, bg="#000000")
        sort_bin_frame.pack(fill=tk.X, pady=(0, 10))

        sort_bin_asc_button = ttk.Button(sort_bin_frame, text="Sort by Bin ↑", width=15, command=lambda: self.sort_treeview_by_bin(ascending=True), style="Primary.TButton")
        sort_bin_asc_button.pack(side=tk.LEFT, padx=5)
        sort_bin_asc_help_button = ttk.Button(
            sort_bin_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_sort_bin_asc_help
        )
        sort_bin_asc_help_button.pack(side=tk.LEFT, padx=2)

        sort_bin_desc_button = ttk.Button(sort_bin_frame, text="Sort by Bin ↓", width=15, command=lambda: self.sort_treeview_by_bin(ascending=False), style="Primary.TButton")
        sort_bin_desc_button.pack(side=tk.LEFT, padx=5)
        sort_bin_desc_help_button = ttk.Button(
            sort_bin_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_sort_bin_desc_help
        )
        sort_bin_desc_help_button.pack(side=tk.LEFT, padx=2)

        clear_bidders_button = ttk.Button(sort_bin_frame, text="Clear Bidders", command=self.clear_bidders, style="Danger.TButton", width=15)
        clear_bidders_button.pack(side=tk.LEFT, padx=5)
        logging.debug("Clear Bidders button initialized")
        clear_bidders_help_button = ttk.Button(
            sort_bin_frame,
            text="?",
            style="Primary.TButton",
            width=2,
            command=self.show_clear_bidders_help
        )
        clear_bidders_help_button.pack(side=tk.LEFT, padx=2)

        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 10))

        self.notebook = ttk.Notebook(self.root)
        self.settings_frame = tk.Frame(self.notebook, bg="#000000")
        self.subscription_frame = tk.Frame(self.notebook, bg="#000000")
        self.annotate_frame = tk.Frame(self.notebook, bg="#000000")

        self.notebook.add(self.settings_frame, text="Settings")
        self.notebook.add(self.subscription_frame, text="Subscription")
        self.notebook.add(self.annotate_frame, text="Annotate Labels")

        self.notebook.bind("<<NotebookTabChanged>>", self.handle_tab_change)
        self.notebook.pack(fill=tk.X, padx=10, pady=(5, 10), expand=False)

        credit_frame = ttk.Frame(self.root, style="TFrame")
        credit_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        credit_label = ttk.Label(
            credit_frame,
            text="Developed By Michael St Pierre, ©2025",
            style="TLabel"
        )
        credit_label.pack(anchor="center", pady=5)
        self.log_info("Credit label added to GUI")

        self.update_btn = ttk.Button(
            self.master,
            text="Check for Updates",
            command=self.check_for_update,
            style="Primary.TButton"
        )
        self.update_btn.pack(side="bottom", pady=10)

        footer_frame = tk.Frame(self.root, bg="#000000")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.footer_label = tk.Label(
            footer_frame,
            text="SwiftSale - Manage your bidders efficiently",
            font=("Arial", 10),
            bg="#000000",
            fg="#FFFFFF"
        )
        self.footer_label.pack(pady=5)

        self.update_header_and_footer()
        self.update_top_buyers()
        self.print_bidders()

    def show_giveaway_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x400")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Handling Unrecorded Giveaways (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "SwiftSale assigns bins sequentially (1-300) to winning bidders, not giveaway winners, unless manually recorded during the show (not recommended).\n\n"
            "If you assign bins 1-20 but skip 2 giveaways, bins are still assigned 1-20 to bidders in order.\n\n"
            "To match printed labels, export labels in ascending order by first order time before printing. Remove any labels for unrecorded giveaways manually.\n\n"
            "This ensures labels align with the bin sequence (Bin 1 to last assigned), avoiding errors."
        )
        help_content = tk.Text(
            help_window,
            height=15,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed giveaway help pop-up")

    def update_bins_used_display(self):
        try:
            current_bins = self.bidder_manager.get_bin_count()
            max_bins = TIER_LIMITS.get(self.tier, {}).get("bins", 20)  # Default to 20 if tier not found
            self.bins_used_label.config(text=f"Bins Used: {current_bins}/{max_bins}")
            logging.debug(f"Updated bins used display: {current_bins}/{max_bins}")
        except Exception as e:
            self.log_error(f"Failed to update bins used display: {e}")
            self.bins_used_label.config(text="Bins Used: Error")

    def show_telegram_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x400")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Telegram Notifications (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "SwiftSale sends bin assignment notifications to a Telegram chat in real-time.\n\n"
            "**Note**: Chat ID is optional; leave blank to disable.\n\n"
            "**Steps**:\n"
            "1. **Get Chat ID**:\n"
            "   - Create/add bot to a Telegram group.\n"
            "   - Use @getidsbot to get the Chat ID (@public or numeric).\n"
            "2. **Enter Chat ID**:\n"
            "   - Input in 'Settings' > 'Telegram Chat ID' and save.\n"
            "3. **Notifications**:\n"
            "   - New bin assignments send messages (e.g., 'Username: testuser | Bin: 5').\n\n"
            "**Notes**:\n"
            "- Ensure bot has message permissions.\n"
            "- Notifications only for new bins, not giveaways.\n"
            "- Check ID/permissions if notifications fail."
        )
        help_content = tk.Text(
            help_window,
            height=15,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Clicked Telegram Help Button")

    def show_top_buyer_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Top Buyer Text (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "'Top Buyer Text' creates a custom message for top buyers, copied to clipboard.\n\n"
            "**Customize**:\n"
            "- Use [username] for buyer's name.\n"
            "- Use [qty] for item count.\n"
            "**Example**:\n"
            "- 'WTG [username] you’ve snagged [qty]!' becomes 'WTG testuser you’ve snagged 5!'.\n\n"
            "**Tips**:\n"
            "- Keep it concise and celebratory.\n"
            "- Save settings to apply."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Top Buyer Text help pop-up")

    def show_giveaway_text_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Giveaway Text (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "'Giveaway Text' sets the giveaway announcement, copied to clipboard.\n\n"
            "**Customize**:\n"
            "- Enter static text (no placeholders yet).\n"
            "**Example**:\n"
            "- 'Giveaway is up! Like & Share!' is copied when clicking 'Start Giveaway'.\n\n"
            "**Tips**:\n"
            "- Make it exciting.\n"
            "- Save settings to apply."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Giveaway Text help pop-up")

    def show_flash_sale_text_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Flash Sale Text (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "'Flash Sale Text' sets the flash sale announcement, copied to clipboard.\n\n"
            "**Customize**:\n"
            "- Enter static text (no placeholders yet).\n"
            "**Example**:\n"
            "- 'Flashsale is live! Grab deals!' is copied when clicking 'Start Flash Sale'.\n\n"
            "**Tips**:\n"
            "- Use urgent language.\n"
            "- Save settings to apply."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Flash Sale Text help pop-up")

    def show_print_bidders_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Print Bidders (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Print Bidders' button updates the bidders list displayed in the table.\n\n"
            "**Purpose**:\n"
            "- Refreshes the table to show all current bidders, their quantities, bin numbers, giveaway status, weights, and timestamps.\n"
            "- Organizes bidders by their most recent transaction.\n\n"
            "**Tips**:\n"
            "- Use this to ensure the table reflects the latest bidder data after adding or modifying actions.\n"
            "- The table is automatically updated after actions like adding bidders or importing a CSV."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Print Bidders help pop-up")

    def show_import_csv_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Import CSV (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Import CSV' button loads bidder data from a CSV file into the application.\n\n"
            "**Purpose**:\n"
            "- Allows bulk-import of bidder data (usernames, quantities, weights, etc.) from a CSV file.\n"
            "- Updates the bidders table and analytics after importing.\n\n"
            "**Tips**:\n"
            "- Ensure the CSV file follows the expected format (check documentation for column requirements).\n"
            "- Use this to quickly populate bidder data from external sources.\n"
            "- The latest bidder label is reset to 'None' after importing."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Import CSV help pop-up")

    def show_export_csv_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Export CSV (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Export CSV' button saves all current bidder data to a CSV file.\n\n"
            "**Purpose**:\n"
            "- Exports all bidder transactions (usernames, quantities, weights, etc.) to a CSV file for external use or backup.\n"
            "- Creates a file in your chosen location.\n\n"
            "**Tips**:\n"
            "- Use this to save a snapshot of your bidder data for reporting or sharing.\n"
            "- The exported file can be re-imported into SwiftSale or used in other tools.\n"
            "- Check the file path in the success message to locate the saved CSV."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Export CSV help pop-up")

    

    def show_sort_bin_asc_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Sort by Bin ↑ (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Sort by Bin ↑' button sorts the bidders table by bin number in ascending order.\n\n"
            "**Purpose**:\n"
            "- Rearranges the table so bidders with lower bin numbers appear first.\n"
            "- Bidders without bin numbers are placed at the end.\n\n"
            "**Tips**:\n"
            "- Use this to organize the table for easier reference, such as when preparing labels.\n"
            "- Sorting only affects the table display, not the underlying data.\n"
            "- Click 'Sort by Bin ↓' to reverse the order."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Sort by Bin Ascending help")

    def show_sort_bin_desc_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Sort by Bin ↓ (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Sort by Bin ↓' button sorts the bidders table by bin number in descending order.\n\n"
            "**Purpose**:\n"
            "- Rearranges the table so bidders with higher bin numbers appear first.\n"
            "- Bidders without bin numbers are placed at the end.\n\n"
            "**Tips**:\n"
            "- Use this to view the most recent bin assignments at the top.\n"
            "- Sorting only affects the table display, not the underlying data.\n"
            "- Click 'Sort by Bin ↑' to reverse the order."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Sort by Bin Descending help")

    def show_clear_bidders_help(self, event=None):
        help_window = tk.Toplevel(self.root)
        help_window.title("SwiftSale Help")
        help_window.geometry("600x300")
        help_window.configure(bg="#2D2D30")
        help_window.transient(self.root)
        help_window.grab_set()

        title_label = ttk.Label(
            help_window,
            text="Clear Bidders (SwiftSale)",
            style="HelpTitle.TLabel",
            wraplength=550,
            justify="center"
        )
        title_label.pack(pady=10)

        help_text = (
            "The 'Clear Bidders' button removes all bidder data from the application.\n\n"
            "**Purpose**:\n"
            "- Resets the bidders list, table, and analytics, clearing all transactions and bin assignments.\n"
            "- Resets the latest bidder label to 'Waiting for bidder...'.\n\n"
            "**Tips**:\n"
            "- Use this to start a new show or clear test data.\n"
            "- This action is irreversible; export your data to CSV first if you need a backup.\n"
            "- Analytics and the table are updated to reflect the cleared state."
        )
        help_content = tk.Text(
            help_window,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#252526",
            fg="#E1E1E1",
            borderwidth=0,
            highlightthickness=0
        )
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)
        help_content.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        close_button = ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=10,
            style="Primary.TButton"
        )
        close_button.pack(pady=10)
        logging.debug("Displayed Clear Bidders help pop-up")

    def build_settings_ui(self, parent_frame):
        settings_frame = tk.LabelFrame(parent_frame, text="Settings", font=("Arial", 12), bg="#F5F5F5")
        settings_frame.pack(fill=tk.X, pady=5, padx=5)

        tk.Label(settings_frame, text="Telegram Chat ID:", bg="#F5F5F5").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.chat_id_entry = ttk.Entry(settings_frame)
        self.chat_id_entry.insert(0, self.chat_id)
        self.chat_id_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        telegram_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Help.TButton",
            width=2,
            command=self.show_telegram_help
        )
        telegram_help_button.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(settings_frame, text="Top Buyer Text:", bg="#F5F5F5").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.top_buyer_entry = ttk.Entry(settings_frame)
        self.top_buyer_entry.insert(0, self.top_buyer_text)
        self.top_buyer_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        top_buyer_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Help.TButton",
            width=2,
            command=self.show_top_buyer_help
        )
        top_buyer_help_button.grid(row=1, column=2, padx=5, pady=2)

        tk.Label(settings_frame, text="Giveaway Text:", bg="#F5F5F5").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.giveaway_entry = ttk.Entry(settings_frame)
        self.giveaway_entry.insert(0, self.giveaway_announcement_text)
        self.giveaway_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        giveaway_text_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Help.TButton",
            width=2,
            command=self.show_giveaway_text_help
        )
        giveaway_text_help_button.grid(row=2, column=2, padx=5, pady=2)

        tk.Label(settings_frame, text="Flash Sale Text:", bg="#F5F5F5").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.flash_sale_entry = ttk.Entry(settings_frame)
        self.flash_sale_entry.insert(0, self.flash_sale_announcement_text)
        self.flash_sale_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        flash_sale_text_help_button = ttk.Button(
            settings_frame,
            text="?",
            style="Help.TButton",
            width=2,
            command=self.show_flash_sale_text_help
        )
        flash_sale_text_help_button.grid(row=3, column=2, padx=5, pady=2)

        self.multi_buyer_var = tk.BooleanVar(value=self.multi_buyer_mode)
        tk.Checkbutton(
            settings_frame, text="Multi-Buyer Top Message", variable=self.multi_buyer_var, bg="#F5F5F5"
        ).grid(row=4, column=0, columnspan=2, pady=2)

        save_settings_button = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings, width=15)
        save_settings_button.grid(row=5, column=0, columnspan=2, pady=5)
        logging.debug("Save Settings button initialized")

    def build_subscription_ui(self, parent_frame):
        subscription_frame = tk.LabelFrame(parent_frame, text="Subscription", font=("Arial", 12), bg="#F5F5F5")
        subscription_frame.pack(fill=tk.X, pady=5, padx=5)

        self.tier_var = tk.StringVar(value=self.tier)
        tiers = ["Trial", "Bronze", "Silver", "Gold"]
        tk.Label(subscription_frame, text="Select Tier:", bg="#FFFFFF").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.OptionMenu(subscription_frame, self.tier_var, self.tier, *tiers).grid(
            row=0, column=1, padx=5, pady=2, sticky="ew"
        )

        status, next_billing = self.stripe_service.get_subscription_status(self.license_key)
        tk.Label(subscription_frame, text=f"Status: {status}", bg="#FFFFFF").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Label(subscription_frame, text=f"Next Billing: {next_billing}", bg="#F5F5F5").grid(row=1, column=1, sticky="w", padx=5, pady=2)

        upgrade_button = ttk.Button(subscription_frame, text="Upgrade", command=self.on_upgrade, width=12)
        upgrade_button.grid(row=2, column=0, pady=5, sticky="ew")
        logging.debug("Upgrade button initialized")

        downgrade_button = ttk.Button(subscription_frame, text="Downgrade", command=self.on_downgrade, width=12)
        downgrade_button.grid(row=2, column=1, pady=5, sticky="ew")
        logging.debug("Downgrade button initialized")

        cancel_button = ttk.Button(subscription_frame, text="Cancel", command=self.on_cancel, width=12)
        cancel_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        logging.debug("Cancel button initialized")

    def build_annotate_ui(self, parent_frame):
        annotate_frame = tk.LabelFrame(parent_frame, text="Annotate Whatnot Labels", font=("Arial", 12), bg="#F5F5F5")
        annotate_frame.pack(fill=tk.X, pady=(10, 5), padx=5)

        tk.Label(annotate_frame, text="X Offset:", bg="#F5F5F5").grid(row=0, column=0, sticky="e", padx=(5, 2), pady=5)
        self.x_offset_var = tk.StringVar(value=str(self.default_x_offset))
        x_entry = ttk.Entry(annotate_frame, textvariable=self.x_offset_var, width=7)
        x_entry.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        tk.Label(annotate_frame, text="inches", bg="#F5F5F5").grid(row=0, column=2, sticky="w", padx=(0, 10), pady=5)

        tk.Label(annotate_frame, text="Y Offset:", bg="#000000").grid(row=0, column=3, sticky="e", padx=(5, 2), pady=5)
        self.y_offset_var = tk.StringVar(value=str(self.default_y_offset))
        y_entry = ttk.Entry(annotate_frame, textvariable=self.y_offset_var, width=7)
        y_entry.grid(row=0, column=4, padx=(0, 5), pady=5, sticky="w")
        tk.Label(annotate_frame, text="inches", bg="#F5F5F5").grid(row=0, column=5, sticky="w", padx=(0, 5), pady=5)

        annotate_button = ttk.Button(
            annotate_frame,
            text="Annotate 4\"×6\" Labels (SwiftSale App: Bin #)",
            command=self.on_annotate_labels_clicked,
            width=40
        )
        annotate_button.grid(row=1, column=0, columnspan=6, pady=(5, 10))

    def handle_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        logging.debug(f"Tab changed to index: {selected_tab}")

        if selected_tab == 0 and not self.settings_initialized:
            self.build_settings_ui(self.settings_frame)
            self.settings_initialized = True
            logging.debug("Settings tab UI initialized")
        elif selected_tab == 1 and not self.subscription_initialized:
            self.build_subscription_ui(self.subscription_frame)
            self.subscription_initialized = True
            logging.debug("Subscription tab UI initialized")
        elif selected_tab == 2 and not self.annotate_initialized:
            self.build_annotate_ui(self.annotate_frame)
            self.annotate_initialized = True
            logging.debug("Annotate Labels tab UI initialized")

    

    def copy_top_buyer_message(self, event):
        top_buyers = self.bidder_manager.get_top_buyers()
        if not top_buyers:
            messagebox.showwarning("No Top Buyers", "No top buyers available to copy.")
            logging.debug("No top buyers to copy")
            return

        if self.multi_buyer_mode:
            messages = []
            for username, qty, _ in top_buyers:
                message = self.top_buyer_text.replace("{username}", username).replace("{qty}", str(qty))
                messages.append(message)
            final_message = "\n".join(messages)
        else:
            top_username, top_qty, _ = top_buyers[0]
            final_message = self.top_buyer_text.replace("{username}", top_username).replace("{qty}", str(top_qty))

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(final_message)
            messagebox.showinfo("Success", f"Copied to clipboard:\n{final_message}")
            logging.debug(f"Copied top buyer message: {final_message}")
        except tk.TclError as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            self.log_error(f"Clipboard copy failed: {e}")

    def copy_giveaway_message(self):
        message = self.giveaway_announcement_text
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(message)
            messagebox.showinfo("Success", f"Copied to clipboard:\n{message}")
            logging.debug(f"Copied giveaway message: {message}")
        except tk.TclError as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            self.log_error(f"Clipboard copy failed: {e}")

    def copy_flash_sale(self):
        message = self.flash_sale_announcement_text
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(message)
            messagebox.showinfo("Success", f"Copied to clipboard:\n{message}")
            logging.debug(f"Copied flash sale message: {message}")
        except tk.TclError as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")
            self.log_error(f"Clipboard copy failed: {e}")

    def toggle_treeview(self):
        if self.tree_frame.winfo_ismapped():
            self.tree_frame.pack_forget()
            self.toggle_button.config(text="+")
            logging.debug("Hid Treeview in Bidders section")
        else:
            self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, after=self.header_frame)
            self.toggle_button.config(text="−")
            logging.debug("Showed Treeview in Bidders section")

    def clear_username(self):
        self.username_entry.delete(0, tk.END)
        logging.debug("Username field cleared")

    def auto_paste_username(self, event):
        try:
            clipboard_content = self.root.clipboard_get()
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, clipboard_content.strip())
        except tk.TclError:
            logging.warning("Auto-paste failed: Clipboard empty or inaccessible")
        return "break"

    def add_bidder(self):
        try:
            username = self.username_entry.get().strip().lower()
            original_username = self.username_entry.get().strip()
            qty_str = self.qty_entry.get().strip()
            weight = self.weight_entry.get().strip() or None
            is_giveaway = self.giveaway_var.get()

            if not username:
                messagebox.showerror("Error", "Username is required")
                logging.warning("Add bidder: Empty username")
                return
            if not qty_str:
                messagebox.showerror("Error", "Quantity cannot be empty")
                logging.warning("Add bidder: Empty quantity")
                return
            try:
                qty = int(qty_str)
                if qty < 0:
                    messagebox.showerror("Error", "Quantity cannot be negative")
                    logging.warning("Add bidder: Negative quantity")
                    return
                if qty == 0 and not is_giveaway:
                    messagebox.showerror("Error", "Quantity must be positive for non-giveaway bids")
                    logging.warning("Add bidder: Zero quantity for non-giveaway")
                    return
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a valid number")
                logging.warning(f"Add bidder: Invalid quantity '{qty_str}'")
                return

            try:
                cursor = self.bidder_manager.conn.cursor()
                cursor.execute(
                    "SELECT bin_number FROM bin_assignments WHERE username = ?", (username,)
                )
                row = cursor.fetchone()
                user_already_has_bin = (row is not None)
            except sqlite3.Error as e:
                logging.error(f"Error checking existing bin in bidders.db: {e}", exc_info=True)
                user_already_has_bin = False

            if not is_giveaway and not user_already_has_bin:
                current_total_bins = self.bidder_manager.get_bin_count()
                max_bins = TIER_LIMITS.get(self.tier, {}).get("bins", 0)
                if current_total_bins + 1 > max_bins:
                    messagebox.showerror(
                        "Tier Limit Reached",
                        f"Your {self.tier} tier limits you to {max_bins} bins. "
                        "Please upgrade your subscription to add more bins."
                    )
                    logging.warning(
                        f"Tier limit reached: tier={self.tier}, total_bins={current_total_bins}, max={max_bins}"
                    )
                    return

            bin_num, giveaway_num = self.bidder_manager.add_transaction(
                username, original_username, qty, weight, is_giveaway
            )

            if bin_num:
                self.latest_bin_assignment = f"Username: {original_username} | Bin: {bin_num}"
                display_text = f"Latest: {original_username} - Bin "
                self.latest_bidder_label.config(text=display_text + str(bin_num), font=("Arial", 16, "bold"))
                if hasattr(self, 'bin_number_label'):
                    self.bin_number_label.destroy()
                self.bin_number_label = tk.Label(
                    self.latest_bidder_label.master,
                    text=str(bin_num),
                    font=("Arial", 22, "bold"),
                    bg="#FFFFFF",
                    fg="#000000"
                )
                self.bin_number_label.place(in_=self.latest_bidder_label, relx=1.0, rely=0.5, anchor="w")

                if self.chat_id:
                    future = self.telegram_service.run_async(
                        self.telegram_service.send_bin_number(self.chat_id, original_username, bin_num)
                    )
                    try:
                        if future and not future.result(timeout=5):
                            messagebox.showwarning("Telegram Error", "Failed to send Telegram notification")
                    except Exception as e:
                        messagebox.showwarning("Telegram Error", f"Failed to send Telegram notification: {e}")

                self.sio.emit('update', {'data': self.latest_bin_assignment})
                self.update_bins_used_display()  # Update the bins used display

            elif giveaway_num:
                self.latest_bidder_label.config(text=f"Latest: {original_username} - Giveaway #{giveaway_num}")
                if hasattr(self, 'bin_number_label'):
                    self.bin_number_label.destroy()

            else:
                messagebox.showerror("Error", "Failed to assign bin or giveaway number")
                logging.warning("Add bidder: No bin or giveaway number assigned")
                return

            self.update_bin_display()
            self.update_top_buyers()
            self.update_stats()
            self.show_avg_sell_rate(show_message=False)

            self.username_entry.delete(0, tk.END)
            self.qty_entry.delete(0, tk.END)
            self.qty_entry.insert(0, "1")
            self.weight_entry.delete(0, tk.END)
            self.giveaway_var.set(False)

        except Exception as e:
            self.log_error(f"Failed to add bidder: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to add bidder: {e}")

    def on_upgrade(self):
        new_tier = self.tier_var.get()

        if new_tier == self.tier:
            return messagebox.showinfo("Info", f"You are already on the {self.tier} tier.")
        if new_tier == "Trial":
            return messagebox.showinfo("Info", "Cannot upgrade to Trial tier. Please select a paid tier.")

        link = PAYMENT_LINKS.get(new_tier)
        if not link:
            return messagebox.showerror("Error", f"No payment link defined for tier: {new_tier}")

        webbrowser.open(link)
        self.log_info(f"Opened Payment Link for {new_tier}: {link}")

        wait = Toplevel(self.root)
        Label(wait, text="Waiting for payment confirmation…").pack(padx=20, pady=20)
        wait.grab_set()

        def poll():
            for _ in range(30):
                time.sleep(2)
                try:
                    r = requests.get(
                        f"{self.base_url}/subscription-status",
                        params={"email": self.user_email},
                        timeout=5
                    )
                    if r.ok:
                        updated_tier = r.json().get("tier")
                        if updated_tier and updated_tier != self.tier:
                            self.tier = updated_tier
                            self.tier_var.set(updated_tier)
                            self.update_header_and_footer()
                            wait.destroy()
                            self.root.after(0, lambda: [
                                messagebox.showinfo("Success", f"Your subscription is now {updated_tier}! 🎉"),
                                self.update_bins_used_display(),
                                        self.log_info(f"Upgraded to {updated_tier} and updated bins display")
                            ])
                            return
                except Exception as e:
                    self.log_info(f"Poll error: {str(e)}")
                    pass

            wait.destroy()
            messagebox.showwarning(
                "Timeout",
                "We didn’t detect your subscription update. Please try again later."
            )

        threading.Thread(target=poll, daemon=True).start()

    def on_downgrade(self):
        new_tier = self.tier_var.get()
        tiers = ["Trial", "Bronze", "Silver", "Gold"]
        if new_tier == self.tier:
            return messagebox.showinfo("Info", f"You are already on the {self.tier} tier.")
        if new_tier != "Trial" and tiers.index(new_tier) >= tiers.index(self.tier):
            return messagebox.showinfo("Info", "Please select a lower tier to downgrade.")

        try:
            wait = tk.Toplevel(self.root)
            tk.Label(wait, text="Processing downgrade…").pack(padx=20, pady=20)
            wait.grab_set()

            success = self.stripe_service.downgrade_subscription(self.user_email, self.tier, new_tier, self.license_key)
            if not success:
                wait.destroy()
                messagebox.showerror("Error", "Failed to downgrade subscription.")
                self.log_error(f"Failed to downgrade subscription for {self.user_email} to {new_tier}")
                return

            DB_PATH = os.getenv('DB_PATH', os.path.join(DEFAULT_DATA_DIR, 'subscriptions.db'))
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT tier, license_key FROM subscriptions WHERE email = ?", (self.user_email,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == new_tier:
                self.tier = new_tier
                self.license_key = "" if new_tier == "Trial" else result[1]
                self.tier_var.set(new_tier)
                self.update_header_and_footer()
                wait.destroy()
                messagebox.showinfo("Success", f"Downgraded to {new_tier} tier.")
                self.log_info(f"Downgraded subscription for {self.user_email} to {new_tier}")
                self.update_bins_used_display()  # Update bins used display after tier change
            else:
                wait.destroy()
                messagebox.showerror("Error", "Downgrade failed: Tier not updated in database.")
                self.log_error(f"Downgrade failed for {self.user_email}: Tier not updated")
                
        except Exception as e:
            wait.destroy()
            messagebox.showerror("Error", f"Failed to downgrade subscription: {e}")
            self.log_error(f"Failed to downgrade subscription for {self.user_email}: {e}", exc_info=True)

    def on_cancel(self):
        if self.tier == "Trial":
            messagebox.showinfo("Info", "You are already on the Trial tier.")
            return

        try:
            success = self.stripe_service.cancel_subscription(self.user_email, self.license_key)
            if not success:
                messagebox.showerror("Error", "Failed to cancel subscription.")
                self.log_error(f"Failed to cancel subscription for {self.user_email}")
                return
            self.tier = "Trial"
            self.license_key = ""
            self.tier_var.set("Trial")
            self.update_header_and_footer()
            messagebox.showinfo("Success", "Subscription canceled. Reverted to Trial tier.")
            self.log_info(f"Canceled subscription for {self.user_email}")
            self.update_bins_used_display()  # Update bins used display after tier change to Trial
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cancel subscription: {e}")
            self.log_error(f"Failed to cancel subscription for {self.user_email}: {e}", exc_info=True)

    def update_bin_display(self):
        self.print_bidders()

    def update_top_buyers(self):
        top_buyers = self.bidder_manager.get_top_buyers()
        text_lines = []
        for username, qty, bin_number in top_buyers:
            if bin_number is not None:
                text_lines.append(f"{username}: {qty} items, Bin# {bin_number}")
            else:
                text_lines.append(f"{username}: {qty} items, No bin assigned")
        text = "\n".join(text_lines)
        self.top_buyers_text.delete("1.0", tk.END)
        self.top_buyers_text.insert(tk.END, text or "No buyers yet.")
        logging.debug("Updated top buyers display")

    def show_avg_sell_rate(self, show_message=True):
        if not self.bidder_manager.show_start_time:
            if show_message:
                messagebox.showwarning("Warning", "Please click 'Start Show' first.")
            self.stats_label.config(text="Average Sell Rate: N/A")
            logging.debug("Sell rate not available: Show not started")
            return

        rates = self.bidder_manager.get_avg_sell_rate()
        items_per_hour, items_per_minute, projected_2h, projected_3h, projected_4h = rates

        if items_per_minute > 0:
            detailed_text = (
                f"Current sell rate is {items_per_minute:.2f}/min "
                f"estimated {int(round(items_per_hour))} per hour, "
                f"{int(round(projected_3h))}/3hr show, {int(round(projected_4h))}/4hr show"
            )
            concise_text = f"Sell Rate: {items_per_minute:.2f}/min, {int(round(items_per_hour))}/hr"

            if show_message:
                messagebox.showinfo("Success", detailed_text)
        else:
            concise_text = "Average Sell Rate: N/A"
            detailed_text = "No valid transactions for sell rate."
            if show_message:
                messagebox.showwarning("Warning", detailed_text)

        self.stats_label.config(text=concise_text)
        logging.debug(f"Updated sell rate: {concise_text}")

    def update_stats(self):
        self.show_avg_sell_rate(show_message=False)

    def print_bidders(self):
        for item in self.bidders_tree.get_children():
            self.bidders_tree.delete(item)

        transactions = self.bidder_manager.print_bidders()
        if not transactions:
            logging.debug("No transactions to display in Treeview")
            return

        bidder_transactions = {}
        for trans in transactions:
            username, qty, bin_num, giveaway_num, weight, timestamp = trans
            if username not in bidder_transactions:
                bidder_transactions[username] = []
            bidder_transactions[username].append((username, qty, bin_num, giveaway_num, weight, timestamp))

        sorted_bidders = sorted(
            bidder_transactions.items(),
            key=lambda x: x[1][0][-1],  # Sort by most recent timestamp
            reverse=True
        )

        for username, trans_list in sorted_bidders:
            latest_trans = trans_list[0]
            _, qty, bin_num, giveaway_num, weight, timestamp = latest_trans
            bin_text = str(bin_num) if bin_num else ""
            giveaway_text = f"#{giveaway_num}" if giveaway_num else ""
            weight_text = weight if weight else ""

            parent = self.bidders_tree.insert(
                "", tk.END, text=username, values=(username, qty, bin_text, giveaway_text, weight_text, timestamp)
            )

            for trans in trans_list:
                _, qty, bin_num, giveaway_num, weight, timestamp = trans
                bin_text = str(bin_num) if bin_num else ""
                giveaway_text = f"#{giveaway_num}" if giveaway_num else ""
                weight_text = weight if weight else ""
                self.bidders_tree.insert(
                    parent, tk.END, values=("", qty, bin_text, giveaway_text, weight_text, timestamp)
                )

        logging.debug("Updated bidders Treeview")

    def sort_treeview_by_bin(self, ascending=True):
        children = self.bidders_tree.get_children()
        items_with_bins = []

        for item in children:
            values = self.bidders_tree.item(item)["values"]
            try:
                bin_value = int(values[2])
            except (IndexError, ValueError):
                bin_value = float('inf')
            items_with_bins.append((item, bin_value))

        sorted_items = sorted(items_with_bins, key=lambda x: x[1], reverse=not ascending)

        for index, (item_id, _) in enumerate(sorted_items):
            self.bidders_tree.move(item_id, '', index)

        self.log_info(f"Sorted Treeview by Bin {'ascending' if ascending else 'descending'}")

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.bidder_manager.import_csv(file_path)
                self.update_bin_display()
                self.update_top_buyers()
                self.update_stats()
                self.print_bidders()
                self.latest_bidder_label.config(text="Latest: None")
                if hasattr(self, 'bin_number_label'):
                    self.bin_number_label.destroy()
                messagebox.showinfo("Success", "CSV imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import CSV: {e}")
                self.log_error(f"Import CSV failed: {e}", exc_info=True)

    def export_csv(self):
        try:
            file_path = self.bidder_manager.export_csv()
            messagebox.showinfo("Success", f"Bidder data exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")
            self.log_error(f"Export CSV failed: {e}", exc_info=True)

    def _blink_start_button(self):
        if not self._is_blinking:
            return

        current_style = self.start_show_button.cget("style")

        if current_style == "Green.TButton":
              next_style = "Yellow.TButton"
        else:
           next_style = "Yellow.TButton"

        self.start_show_button.configure(style=next_style)
        self._blink_job = self.master.after(500, self._blink_start_button)

    def start_show(self):
        self._is_blinking = False
        if self._blink_job is not None:
            try:
                self.master.after_cancel(self._blink_job)
            except Exception:
                pass
            self._blink_job = None

        try:
            self.start_show_button.configure(style="Green.TButton")
        except Exception:
            pass

        try:
            self.bidder_manager.start_show()
            self.show_avg_sell_rate(show_message=False)
            messagebox.showinfo("Success", "Show started!")
            self.log_info("Show started via GUI")
        except Exception as e:
            self.log_error(f"Failed to start show: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start show: {e}")

    def check_for_update(self):
        try:
            url = "https://raw.githubusercontent.com/Modernvox/swiftsale-launcher/main/version.json"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            messagebox.showerror("Update Check Failed", f"Could not reach update server:\n{e}")
            return

        server_version = data.get("version")
        download_url = data.get("download_url")
        notes = data.get("notes", "")

        if server_version and server_version != self.current_version:
            if messagebox.askyesno(
                "Update Available",
                f"Version {server_version} is available.\n\nChanges:\n{notes}\n\nDownload now?"
            ):
                webbrowser.open(download_url)
        else:
            messagebox.showinfo("Up to Date", "You’re running the latest version.")

    def clear_bidders(self):
        self.bidder_manager.clear_bidders()
        self.update_bin_display()
        self.update_top_buyers()
        self.update_stats()
        self.print_bidders()
        self.latest_bin_assignment = "Waiting for bidder..."
        self.latest_bidder_label.config(text="Latest: None")
        if hasattr(self, 'bin_number_label'):
            self.bin_number_label.destroy()
        self.sio.emit('update', {'data': self.latest_bin_assignment})
        messagebox.showinfo("Success", "Bidder data cleared!")
        self.log_info("Cleared bidder data via GUI")

    def on_closing(self):
        self.log_info("Closing application")
        self.db_manager.close()
        if hasattr(self, 'sio') and self.sio.connected:
            self.sio.disconnect()
        if hasattr(self, 'loop'):
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop_thread.join(timeout=1)
        self.root.destroy()

    def on_annotate_labels_clicked(self):
        pdf_path = filedialog.askopenfilename(
            title="Select Whatnot 4\"×6\" labels PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not pdf_path:
            return

        bidders_db = self.bidder_manager.bidders_db_path


        output_path = filedialog.asksaveasfilename(
            title="Save annotated labels as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not output_path:
            return

        try:
            x_offset_in = float(self.x_offset_var.get())
            y_offset_in = float(self.y_offset_var.get())
        except ValueError:
            messagebox.showerror("Error", "Offsets must be valid numbers (e.g. 0.5, 4.8).")
            return

        stamp_x = x_offset_in * inch
        stamp_y = y_offset_in * inch

        try:
            skipped = annotate_whatnot_pdf_with_bins_skip_missing(
                whatnot_pdf_path=pdf_path,
                bidders_db_path=bidders_db,
                output_pdf_path=output_path,
                stamp_x=stamp_x,
                stamp_y=stamp_y,
                font_name="Helvetica-Bold",
                font_size_app=12,
                font_size_bin=24
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to annotate PDF:\n{e}")
            return

        if skipped:
            msg = "The following pages contained “(username)” but no bin was found:\n\n"
            for page_idx, uname in skipped:
                msg += f"  • Page {page_idx+1}: username='{uname}'\n"
            msg += "\nPlease add a bin for each username or remove their parentheses from the PDF. Note: These labels will be marked as potential Giveaways or flash Sales"
            messagebox.showwarning("Missing bins", msg)
        else:
            messagebox.showinfo("Success", "All applicable pages were stamped with bin numbers.")
            import webbrowser
            webbrowser.open(output_path)


if __name__ == "__main__":
    import sys
    root = tk.Tk()
    try:
        config = load_config()
        required_env_vars = ["API_TOKEN", "USER_EMAIL", "APP_BASE_URL", "PORT", "DATABASE_URL"]
        if os.getenv("ENV", "development") != "development":
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                logging.error(f"Missing environment variables: {', '.join(missing_vars)}")
                messagebox.showerror(
                    "Startup Error",
                    f"Missing environment variables: {', '.join(missing_vars)}. "
                    "Please set them in the environment."
                )
                sys.exit(1)  # ← FIXED

        app = SwiftSaleGUI(
            root,
            stripe_service=None,
            api_token=config.get("API_TOKEN", ""),
            user_email=config.get("USER_EMAIL", "") or "testuser@example.com",  # avoid recursive app call
            base_url=config.get("APP_BASE_URL", "http://localhost:5000"),
            dev_unlock_code=config.get("DEV_UNLOCK_CODE", ""),
            telegram_bot_token=config.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=config.get("TELEGRAM_CHAT_ID", ""),
            dev_access_granted=False,  # ← FIXED
            log_info=logging.info,
            log_error=logging.error
        )
    except Exception as e:
        logging.error(f"Failed to load config at startup: {e}", exc_info=True)
        messagebox.showerror("Startup Error", f"Failed to load configuration: {e}")
        sys.exit(1)  # ← FIXED

    root.mainloop()
