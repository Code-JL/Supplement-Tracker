"""
Supplement Tracker Application

This module contains the main Supplement Tracker application built using Tkinter.
It allows users to track their supplement inventory, calculate costs, and more.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import webbrowser
from typing import List, Dict
import sys
import os
import logging
import shutil
import gzip
import time

# Set up logging
logging.basicConfig(
    filename='supplement_tracker.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BackupManager:
    """
    Manages the backup system for supplement data files.
    
    This class handles creating, managing, and restoring backups of supplement data files.
    It supports automatic and manual backups, rotation of old backups, and metadata tracking.
    """
    
    def __init__(self, settings, max_backups=5, backup_dir='./backup'):
        """
        Initialize the BackupManager.
        
        Args:
            settings (dict): The application settings dictionary.
            max_backups (int): Maximum number of backups to keep (default: 5).
            backup_dir (str): Directory to store backups (default: './backup').
        """
        self.settings = settings
        
        # Initialize backup settings with defaults if not present
        if 'backup' not in self.settings:
            self.settings['backup'] = {
                'max_backups': max_backups,
                'backup_dir': backup_dir,
                'compression_enabled': False,
                'min_backup_interval_minutes': 60
            }
        
        self.backup_settings = self.settings['backup']
        self.last_backup_time = 0
        self.backup_index_file = os.path.join(self.backup_settings['backup_dir'], 'backup_index.json')
        self.backup_index = self._load_backup_index()
        
        # Ensure backup directory exists
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create the backup directory if it doesn't exist."""
        try:
            os.makedirs(self.backup_settings['backup_dir'], exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Failed to create backup directory: {str(e)}", exc_info=True)
            return False
    
    def _load_backup_index(self):
        """Load the backup index file or create a new one if it doesn't exist."""
        if os.path.exists(self.backup_index_file):
            try:
                with open(self.backup_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load backup index: {str(e)}", exc_info=True)
                return {'backups': []}
        return {'backups': []}
    
    def _save_backup_index(self):
        """Save the backup index to file."""
        try:
            with open(self.backup_index_file, 'w') as f:
                json.dump(self.backup_index, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to save backup index: {str(e)}", exc_info=True)
            return False
    
    def generate_backup_filename(self, source_file):
        """
        Generate a backup filename based on the current date and time.
        
        Args:
            source_file (str): The original file path.
            
        Returns:
            str: The generated backup filename.
        """
        # Get the base filename without path
        base_filename = os.path.basename(source_file)
        name, ext = os.path.splitext(base_filename)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}{ext}"
        
        # Check for collisions
        counter = 1
        full_path = os.path.join(self.backup_settings['backup_dir'], backup_name)
        while os.path.exists(full_path):
            backup_name = f"backup_{timestamp}_{counter}{ext}"
            full_path = os.path.join(self.backup_settings['backup_dir'], backup_name)
            counter += 1
        
        return full_path
    
    def should_create_backup(self, is_auto_save=True):
        """
        Determine if a backup should be created based on settings and timing.
        
        Args:
            is_auto_save (bool): Whether this is an automatic save (default: True).
            
        Returns:
            bool: True if a backup should be created, False otherwise.
        """
        # Always create backup for manual saves
        if not is_auto_save:
            return True
        
        # Check time since last backup
        current_time = time.time()
        min_interval = self.backup_settings['min_backup_interval_minutes'] * 60
        
        if current_time - self.last_backup_time >= min_interval:
            return True
        
        return False
    
    def create_backup(self, source_file, is_auto_save=True):
        """
        Create a backup of the specified file.
        
        Args:
            source_file (str): The path to the file to back up.
            is_auto_save (bool): Whether this is an automatic save (default: True).
            
        Returns:
            str: The path to the created backup file, or None if backup failed.
        """
        if not os.path.exists(source_file):
            logging.error(f"Source file does not exist: {source_file}")
            return None
        
        # Check if we should create a backup
        if not self.should_create_backup(is_auto_save):
            return None
        
        try:
            # Generate backup filename
            backup_file = self.generate_backup_filename(source_file)
            
            # Copy the file
            if self.backup_settings.get('compression_enabled', False):
                with open(source_file, 'rb') as f_in:
                    with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_file = f"{backup_file}.gz"
            else:
                shutil.copy2(source_file, backup_file)
            
            # Update backup index
            file_size = os.path.getsize(backup_file)
            backup_info = {
                'filename': os.path.basename(backup_file),
                'original_file': source_file,
                'timestamp': datetime.now().isoformat(),
                'is_auto': is_auto_save,
                'size': file_size
            }
            
            self.backup_index['backups'].append(backup_info)
            self._save_backup_index()
            
            # Update last backup time
            self.last_backup_time = time.time()
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            logging.info(f"Created backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}", exc_info=True)
            return None
    
    def list_backups(self):
        """
        List all available backups.
        
        Returns:
            list: A list of backup information dictionaries.
        """
        return sorted(self.backup_index['backups'], 
                     key=lambda x: x['timestamp'], 
                     reverse=True)
    
    def cleanup_old_backups(self):
        """
        Remove old backups to stay within the maximum limit.
        
        Returns:
            int: Number of backups removed.
        """
        backups = self.list_backups()
        max_backups = self.backup_settings['max_backups']
        
        if len(backups) <= max_backups:
            return 0
        
        removed = 0
        for backup in backups[max_backups:]:
            try:
                backup_path = os.path.join(self.backup_settings['backup_dir'], backup['filename'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    removed += 1
            except Exception as e:
                logging.error(f"Failed to remove old backup: {str(e)}", exc_info=True)
        
        # Update the index
        self.backup_index['backups'] = backups[:max_backups]
        self._save_backup_index()
        
        return removed
    
    def restore_from_backup(self, backup_file, target_file):
        """
        Restore a file from a backup.
        
        Args:
            backup_file (str): The backup file to restore from.
            target_file (str): The target file to restore to.
            
        Returns:
            bool: True if restoration was successful, False otherwise.
        """
        try:
            backup_path = os.path.join(self.backup_settings['backup_dir'], backup_file)
            
            if not os.path.exists(backup_path):
                logging.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Handle compressed backups
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, target_file)
            
            logging.info(f"Restored from backup: {backup_file} to {target_file}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore from backup: {str(e)}", exc_info=True)
            return False

def load_settings():
    """Load user settings from settings.json."""
    default_settings = {
        "theme": "dark",
        "last_file": None,
        "backup": {
            "max_backups": 5,
            "backup_dir": "./backup",
            "compression_enabled": False,
            "min_backup_interval_minutes": 60
        }
    }
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                
                # Ensure backup settings exist
                if 'backup' not in settings:
                    settings['backup'] = default_settings['backup']
                    
                return settings
        return default_settings
    except Exception as e:
        logging.error("Failed to load settings", exc_info=True)
        return default_settings

def save_settings(settings):
    """Save user settings to settings.json."""
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logging.error("Failed to save settings", exc_info=True)

def handle_error(error, user_message=None):
    """Centralized error handling function."""
    logging.error(str(error), exc_info=True)
    if user_message:
        messagebox.showerror("Error", user_message)
    else:
        messagebox.showerror("Error", str(error))

class ModernTheme:
    """
    A modern theme for Tkinter applications.
    
    This class provides a customizable dark/light theme with a modern look and feel.
    It can be applied to Tkinter and ttk widgets.
    """
    
    def __init__(self, is_dark=True):
        """
        Initialize the ModernTheme.
        
        Args:
            is_dark (bool): Whether to use a dark theme (default: True).
        """
        self.settings = load_settings()
        self.is_dark = self.settings.get("theme", "dark") == "dark" if is_dark is None else is_dark
        self.update_colors()
        self.style = None  # Will be set in apply()
        
        self.fonts = {
            'heading': ('Segoe UI', 11, 'bold'),
            'body': ('Segoe UI', 10),
            'small': ('Segoe UI', 9)
        }

    def update_colors(self):
        """Update the theme colors based on the current mode (dark/light)."""
        if self.is_dark:
            self.colors = {
                'primary': '#2196F3',    # Material Blue
                'secondary': '#FFC107',   # Material Amber
                'background': '#1E1E1E',  # Dark background
                'surface': '#2D2D2D',     # Dark surface
                'text': '#FFFFFF',        # White text
                'text_secondary': '#AAAAAA',  # Light gray text
                'hover': '#3D3D3D',       # Slightly lighter than surface
            }
        else:
            self.colors = {
                'primary': '#2196F3',     # Material Blue
                'secondary': '#FFC107',    # Material Amber
                'background': '#FFFFFF',   # White background
                'surface': '#F5F5F5',     # Light surface
                'text': '#212121',        # Dark text
                'text_secondary': '#757575',  # Gray text
                'hover': '#E0E0E0',       # Light gray hover
            }

    def apply(self, root):
        """
        Apply the theme to a Tkinter application.
        
        Args:
            root (Union[tk.Tk, tk.Toplevel]): The root window of the application.
            
        Returns:
            ttk.Style: The style object with the applied theme.
        """
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure common colors and fonts
        style.configure('.',
            background=self.colors['background'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['surface'],
            font=self.fonts['body']
        )
        
        # Configure specific widget styles
        style.configure('TButton',
            padding=5,
            relief='flat',
            background=self.colors['surface'],
            foreground=self.colors['text']
        )
        
        style.map('TButton',
            relief=[('pressed', 'flat')],
            background=[
                ('pressed', self.colors['primary']),
                ('active', self.colors['hover']),
                ('!active', self.colors['surface'])
            ],
            foreground=[('pressed', '#FFFFFF')]
        )
        
        # Theme toggle button
        style.configure('Toggle.TButton',
            padding=5,
            relief='flat',
            background=self.colors['surface']
        )
        
        style.map('Toggle.TButton',
            relief=[('pressed', 'flat')],
            background=[
                ('pressed', self.colors['secondary']),
                ('active', self.colors['hover'])
            ]
        )
        
        # Entry fields
        style.configure('TEntry',
            padding=5,
            relief='flat',
            fieldbackground=self.colors['surface'],
            selectbackground=self.colors['primary'],
            selectforeground=self.colors['text']
        )
        
        style.map('TEntry',
            relief=[('focus', 'flat')],
            bordercolor=[('focus', self.colors['primary'])]
        )
        
        # Frame and Label
        style.configure('TFrame', background=self.colors['background'])
        style.configure('TLabel', background=self.colors['background'])
        
        # Treeview
        style.configure('Treeview',
            background=self.colors['surface'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['surface'],
            rowheight=25,
            borderwidth=0
        )
        
        style.configure('Treeview.Heading',
            background=self.colors['surface'],
            foreground=self.colors['text'],
            relief='flat',
            borderwidth=0,
            padding=5
        )
        
        style.map('Treeview',
            background=[('selected', self.colors['primary'])],
            foreground=[('selected', '#FFFFFF')]
        )
        
        style.map('Treeview.Heading',
            relief=[('active', 'flat')],
            background=[('active', self.colors['hover'])]
        )
        
        # Scrollbar
        for orient in ['Vertical', 'Horizontal']:
            style.configure(f'{orient}.TScrollbar',
                background=self.colors['surface'],
                troughcolor=self.colors['background'],
                relief='flat',
                borderwidth=0,
                arrowsize=0
            )
            style.map(f'{orient}.TScrollbar',
                relief=[('pressed', 'flat')],
                background=[
                    ('pressed', self.colors['primary']),
                    ('active', self.colors['hover'])
                ]
            )
        
        # Card style for calculator
        style.configure('Card.TFrame',
            background=self.colors['surface'],
            relief='flat',
            borderwidth=1,
            padding=10
        )
        
        # Configure root window
        if isinstance(root, (tk.Tk, tk.Toplevel)):
            root.configure(bg=self.colors['background'])
            
        # Apply theme to all widgets
        self._apply_to_widget(root)
        
        return style
    
    def _apply_to_widget(self, widget):
        """
        Recursively apply the theme to a widget and its children.
        
        Args:
            widget (Union[ttk.Widget, tk.Widget]): The widget to apply the theme to.
        """
        if isinstance(widget, ttk.Widget):
            # TTK widgets use style system
            widget_class = widget.winfo_class()
            if widget_class == 'TButton' and 'Toggle' in str(widget.cget('style')):
                widget.configure(style='Toggle.TButton')
            elif widget_class in ['TFrame', 'TLabelframe']:
                # Skip style application for frames
                pass
            elif widget_class.startswith('T'):
                # For other ttk widgets, use their existing class name
                widget.configure(style=widget_class)
        elif isinstance(widget, tk.Widget):
            # Handle non-TTK widgets
            if isinstance(widget, tk.Canvas):
                widget.configure(
                    bg=self.colors['surface'],
                    highlightthickness=0,
                    bd=0
                )
            elif isinstance(widget, tk.Text):
                widget.configure(
                    bg=self.colors['surface'],
                    fg=self.colors['text'],
                    insertbackground=self.colors['text'],
                    selectbackground=self.colors['primary'],
                    selectforeground=self.colors['text'],
                    font=self.fonts['body']
                )
            elif isinstance(widget, (tk.Tk, tk.Toplevel)):
                widget.configure(bg=self.colors['background'])
        
        # Apply to children
        for child in widget.winfo_children():
            self._apply_to_widget(child)

    def toggle_theme(self):
        """Toggle between dark and light theme modes."""
        self.is_dark = not self.is_dark
        self.update_colors()
        # Save theme preference
        self.settings["theme"] = "dark" if self.is_dark else "light"
        save_settings(self.settings)

class Supplement:
    """
    Represents a supplement.
    
    This class encapsulates the data and behavior of a supplement, including its name,
    counts, cost, tags, link, and daily dose.
    """
    
    def __init__(self, name: str, current_count: int, initial_count: int, 
                 cost: float, tags: List[str], link: str, daily_dose: int, auto_decrement: bool = True):
        """
        Initialize a new Supplement.
        
        Args:
            name (str): The name of the supplement.
            current_count (int): The current count of the supplement.
            initial_count (int): The initial count of the supplement.
            cost (float): The cost of the supplement.
            tags (List[str]): A list of tags associated with the supplement.
            link (str): A link to the supplement (e.g., purchase URL).
            daily_dose (int): The recommended daily dose of the supplement.
            auto_decrement (bool): Whether to automatically decrement the count daily (default: True).
        """
        self.name = name
        self.current_count = current_count
        self.initial_count = initial_count
        self.cost = cost
        self.tags = tags
        self.link = link
        self.daily_dose = daily_dose
        self.auto_decrement = auto_decrement
        self.last_updated = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> Dict:
        """
        Convert the Supplement to a dictionary.
        
        Returns:
            Dict: A dictionary representation of the Supplement.
        """
        return {
            'name': self.name,
            'current_count': self.current_count,
            'initial_count': self.initial_count,
            'cost': self.cost,
            'tags': self.tags,
            'link': self.link,
            'daily_dose': self.daily_dose,
            'auto_decrement': self.auto_decrement,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Create a Supplement from a dictionary.
        
        Args:
            data (Dict): A dictionary containing the Supplement data.
            
        Returns:
            Supplement: A Supplement instance created from the dictionary.
        """
        supplement = cls(
            data['name'],
            data['current_count'],
            data['initial_count'],
            data['cost'],
            data['tags'],
            data['link'],
            data['daily_dose'],
            data.get('auto_decrement', True)  # Default to True for backward compatibility
        )
        supplement.last_updated = data['last_updated']
        return supplement

    def days_remaining(self) -> float:
        """
        Calculate the number of days remaining based on the current count and daily dose.
        
        Returns:
            float: The number of days remaining. Returns infinity if daily dose is zero.
        """
        if self.daily_dose == 0:
            return float('inf')
        return self.current_count / self.daily_dose

    def update_count(self):
        """Update the current count based on the time passed since the last update."""
        if not self.auto_decrement:
            return
            
        last_updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
        days_passed = (datetime.now() - last_updated).days
        doses_taken = days_passed * self.daily_dose
        self.current_count = max(0, self.current_count - doses_taken)
        self.last_updated = datetime.now().strftime("%Y-%m-%d")

class SupplementTracker:
    """
    The main Supplement Tracker application.
    
    This class represents the Supplement Tracker application window and its functionality.
    It allows users to manage their supplement inventory, calculate costs, and more.
    """
    
    def __init__(self, initial_file=None):
        """
        Initialize the SupplementTracker.
        
        Args:
            initial_file (str): The path to the initial supplement data file (default: None).
        """
        try:
            self.root = tk.Tk()
            self.root.title("Supplement Tracker")
            self.root.geometry("1000x700")
            
            # Load settings and apply theme
            self.settings = load_settings()
            self.theme = ModernTheme(is_dark=None)  # Use saved theme preference
            self.style = self.theme.apply(self.root)
            
            # Initialize backup manager
            self.backup_manager = BackupManager(self.settings)
            
            # Set up file association handling
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.createcommand('::tk::mac::OpenDocument', self.open_file_from_system)
            
            self.supplements: List[Supplement] = []
            self.setup_gui()
            
            # Add global keyboard shortcuts with feedback
            self.root.bind("<Control-s>", lambda event: self.save_with_feedback())
            
            # Load initial file or last used file
            if initial_file and os.path.exists(initial_file):
                self.load_supplements(initial_file)
            elif self.settings.get("last_file") and os.path.exists(self.settings["last_file"]):
                self.load_supplements(self.settings["last_file"])
            else:
                self.load_supplements()
        except Exception as e:
            handle_error(e, "Failed to initialize application")
            sys.exit(1)

    def update_title(self, text):
        """
        Update the window title.
        
        Args:
            text (str): The new window title.
        """
        self.root.title(text)

    def on_closing(self):
        """Handle window closing."""
        if self.supplements:
            if messagebox.askyesno("Save Changes", "Would you like to save changes before closing?"):
                # Save with user initiation flag
                self.save_supplements(self.settings.get("last_file", "supplements.sup"), is_user_initiated=True)
            else:
                # Create a backup even if user chooses not to save
                if self.settings.get("last_file"):
                    self.backup_manager.create_backup(self.settings["last_file"], is_auto_save=False)
        self.root.destroy()

    def open_file_from_system(self, filename):
        """
        Handle system file open requests.
        
        Args:
            filename (str): The path to the file to open.
        """
        try:
            self.load_supplements(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def setup_gui(self):
        """Set up the main GUI elements of the application."""
        # Create main frames with padding
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        self.control_frame = ttk.Frame(main_frame, style='TFrame')
        self.control_frame.pack(fill='x', pady=(0, 10))

        # Button frame with modern spacing
        button_frame = ttk.Frame(self.control_frame, style='TFrame')
        button_frame.pack(side='left')

        # Add controls with consistent spacing
        buttons = [
            ("Add Supplement", self.show_add_dialog),
            ("Remove Selected", self.remove_selected),
            ("Cost Calculator", self.show_calculator),
            ("Save As...", self.save_as),
            ("Load File", self.load_file),
            ("Backups", self.show_backups),
            ("Settings", self.show_settings)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.pack(side='left', padx=5)

        # Theme toggle button
        def toggle_theme():
            self.theme.toggle_theme()
            self.style = self.theme.apply(self.root)
            
            # Update theme button text and all windows
            theme_btn.configure(text="🌙 Dark" if not self.theme.is_dark else "☀️ Light")
            for window in self.root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    self.theme._apply_to_widget(window)

        theme_btn = ttk.Button(
            button_frame,
            text="🌙 Dark" if not self.theme.is_dark else "☀️ Light",
            command=toggle_theme,
            style='Toggle.TButton'
        )
        theme_btn.pack(side='left', padx=5)

        # Search frame with modern look
        search_frame = ttk.Frame(self.control_frame)
        search_frame.pack(side='right', padx=5)
        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.update_list())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left')

        # Create treeview with modern styling
        self.list_frame = ttk.Frame(main_frame)
        self.list_frame.pack(fill='both', expand=True)

        # Add scrollbars with modern styling
        tree_scroll_y = ttk.Scrollbar(self.list_frame, orient="vertical", style='Vertical.TScrollbar')
        tree_scroll_y.pack(side='right', fill='y')
        
        tree_scroll_x = ttk.Scrollbar(self.list_frame, orient="horizontal", style='Horizontal.TScrollbar')
        tree_scroll_x.pack(side='bottom', fill='x')

        # Create and configure treeview
        self.tree = ttk.Treeview(self.list_frame, 
            columns=('Name', 'Count', 'Initial', 'Cost', 'Tags', 'Daily', 'Days Left'),
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            style='Treeview'
        )
        
        # Hide the first empty column
        self.tree['show'] = 'headings'
        
        # Configure scrollbars
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Configure column headings with explicit styles
        column_widths = {
            'Name': (150, 100),
            'Count': (70, 50),
            'Initial': (70, 50),
            'Cost': (80, 60),
            'Tags': (150, 100),
            'Daily': (80, 60),
            'Days Left': (80, 60)
        }
        
        for col in column_widths:
            width, minwidth = column_widths[col]
            self.tree.heading(col, text=col, anchor='w')
            self.tree.column(col, width=width, minwidth=minwidth, anchor='w')

        # Configure tag for items with auto-decrement disabled
        self.tree.tag_configure('no_auto_decrement', foreground='#FF6B6B')

        self.tree.pack(fill='both', expand=True)
        
        # Bind right-click event to show context menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Add legend for the asterisk indicator
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill='x', pady=(5, 0))
        legend_label = ttk.Label(
            legend_frame, 
            text="* Items with asterisk have auto-decrement disabled",
            font=self.theme.fonts['small'],
            foreground=self.theme.colors['text_secondary']
        )
        legend_label.pack(side='right', padx=5)

    def show_add_dialog(self):
        """Show the dialog for adding a new supplement."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Supplement")
        dialog.geometry("500x400")
        
        # Apply theme to dialog
        self.theme._apply_to_widget(dialog)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Create entry fields
        entries = {}
        fields = [
            ('name', "Name:"),
            ('count', "Current Count:"),
            ('initial', "Initial Count:"),
            ('cost', "Cost:"),
            ('tags', "Tags (comma-separated):"),
            ('link', "Link:"),
            ('daily', "Daily Dose:")
        ]

        # Calculate maximum label width
        max_label_width = max(len(label) for _, label in fields)

        for key, label in fields:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)
            
            label_widget = ttk.Label(frame, text=label, width=max_label_width + 2)
            label_widget.pack(side='left')
            
            entry = ttk.Entry(frame)
            entry.pack(side='right', expand=True, fill='x', padx=(10, 0))
            entries[key] = entry

        # Add auto-decrement checkbox
        auto_decrement_frame = ttk.Frame(main_frame)
        auto_decrement_frame.pack(fill='x', pady=5)
        
        auto_decrement_var = tk.BooleanVar(value=True)
        auto_decrement_check = ttk.Checkbutton(
            auto_decrement_frame, 
            text="Auto-decrement daily", 
            variable=auto_decrement_var
        )
        auto_decrement_check.pack(side='left')

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=lambda: save()).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)

        def save():
            try:
                supplement = Supplement(
                    entries['name'].get(),
                    int(entries['count'].get()),
                    int(entries['initial'].get()),
                    float(entries['cost'].get()),
                    [tag.strip() for tag in entries['tags'].get().split(',')],
                    entries['link'].get(),
                    int(entries['daily'].get()),
                    auto_decrement_var.get()
                )
                self.supplements.append(supplement)
                self.save_supplements()
                self.update_list()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", "Please check your input values")

    def remove_selected(self):
        """Remove the selected supplement(s) from the list."""
        selected = self.tree.selection()
        if not selected:
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to remove the selected supplement?"):
            for item_id in selected:
                index = int(item_id)
                if 0 <= index < len(self.supplements):
                    del self.supplements[index]
            self.save_supplements()
            self.update_list()

    def show_calculator(self):
        """Show the cost calculator dialog."""
        calc = tk.Toplevel(self.root)
        calc.title("Cost Calculator")
        calc.geometry("800x600")
        calc.configure(bg=self.theme.colors['background'])
        
        # Apply theme to calculator window
        self.theme._apply_to_widget(calc)
        
        # Make calculator modal
        calc.transient(self.root)
        calc.grab_set()

        main_frame = ttk.Frame(calc, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(main_frame, 
            text="Compare Supplement Costs", 
            font=self.theme.fonts['heading'],
            style='TLabel'
        )
        title_label.pack(pady=(0, 20))

        # Create container frame for canvas
        canvas_container = ttk.Frame(main_frame, style='TFrame')
        canvas_container.pack(fill='both', expand=True)
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)

        # Scrollable frame for options
        canvas = tk.Canvas(
            canvas_container,
            bg=self.theme.colors['background'],
            highlightthickness=0,
            bd=0
        )
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview, style='Vertical.TScrollbar')
        options_frame = ttk.Frame(canvas, style='TFrame')
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout for better control
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Create window in canvas
        canvas_frame = canvas.create_window((0, 0), window=options_frame, anchor='nw', width=canvas.winfo_width())

        options = []
        option_frames = []
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_frame, width=event.width)

        canvas.bind('<Configure>', on_configure)
        options_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def add_option():
            option_frame = ttk.Frame(options_frame)
            option_frame.pack(fill='x', pady=5)
            
            entries = {}
            fields_frame = ttk.Frame(option_frame)
            fields_frame.pack(side='left', fill='x', expand=True)
            
            # Add field labels and entries with consistent spacing
            for field in ['Dose Count', 'Price', 'Daily Dose']:
                field_frame = ttk.Frame(fields_frame, style='TFrame')
                field_frame.pack(side='left', padx=10)
                ttk.Label(field_frame, text=field, style='TLabel').pack(side='top')
                entry = ttk.Entry(field_frame, width=15, style='TEntry')
                entry.pack(side='top', pady=(5, 0))
                entries[field] = entry
            
            def remove_this_option():
                if len(options) > 2:
                    options.remove(entries)
                    option_frame.destroy()
                    option_frames.remove(option_frame)
                else:
                    messagebox.showwarning("Warning", "Must keep at least 2 options for comparison")
            
            remove_btn = ttk.Button(option_frame, text="Remove", command=remove_this_option)
            remove_btn.pack(side='right', padx=10)
            
            options.append(entries)
            option_frames.append(option_frame)

        def calculate():
            results = []
            for opt in options:
                try:
                    count = float(opt['Dose Count'].get())
                    price = float(opt['Price'].get())
                    daily = float(opt['Daily Dose'].get())
                    
                    days = count / daily
                    cost_per_day = price / days
                    results.append((cost_per_day, days, price))
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid numbers")
                    return

            # Create results window
            result_window = tk.Toplevel(calc)
            result_window.title("Calculator Results")
            result_window.geometry("400x500")
            result_window.configure(bg=self.theme.colors['background'])
            
            # Make results window modal
            result_window.transient(calc)
            result_window.grab_set()
            
            # Add results in a modern format
            result_frame = ttk.Frame(result_window, padding="20")
            result_frame.pack(fill='both', expand=True)
            
            ttk.Label(result_frame, 
                text="Cost Comparison Results", 
                font=self.theme.fonts['heading']
            ).pack(pady=(0, 20))

            # Create result cards
            for i, (cost_per_day, days, price) in enumerate(sorted(results, key=lambda x: x[0])):
                card = ttk.Frame(result_frame, style='Card.TFrame')
                card.pack(fill='x', pady=5)
                
                ttk.Label(card, 
                    text=f"Option {i+1}", 
                    font=self.theme.fonts['heading']
                ).pack(pady=(5, 0))
                
                ttk.Label(card,
                    text=f"Cost per day: ${cost_per_day:.2f}",
                    font=self.theme.fonts['body']
                ).pack()
                
                ttk.Label(card,
                    text=f"Days supply: {days:.1f}",
                    font=self.theme.fonts['body']
                ).pack()
                
                ttk.Label(card,
                    text=f"Total price: ${price:.2f}",
                    font=self.theme.fonts['body']
                ).pack(pady=(0, 5))

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Add Option", command=add_option).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Calculate", command=calculate).pack(side='left', padx=5)
        
        # Add initial two options
        add_option()
        add_option()

    def update_list(self):
        """Update the supplement list based on the current data and search term."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.search_var.get().lower()
        
        for i, supp in enumerate(self.supplements):
            supp.update_count()
            if search_term and search_term not in supp.name.lower() and \
               not any(search_term in tag.lower() for tag in supp.tags):
                continue
                
            # Determine if we need to add an asterisk for non-auto-decrementing supplements
            days_left_text = f"{supp.days_remaining():.1f}"
            if not supp.auto_decrement:
                days_left_text += "*"
                
            item_id = self.tree.insert('', 'end', iid=str(i), values=(
                supp.name,
                supp.current_count,
                supp.initial_count,
                f"${supp.cost:.2f}",
                ", ".join(supp.tags),
                supp.daily_dose,
                days_left_text
            ))
            
            # Apply the tag for non-auto-decrementing supplements
            if not supp.auto_decrement:
                self.tree.item(item_id, tags=('no_auto_decrement',))

        self.update_days_until_empty()
        
        # Auto-save with backup if we have a last file
        if self.supplements and self.settings.get("last_file"):
            self.save_supplements(self.settings["last_file"], is_user_initiated=False)

    def update_days_until_empty(self):
        """Update the window title with the number of days until a supplement runs out."""
        if not self.supplements:
            self.update_title("Supplement Tracker")
            return

        min_days = float('inf')
        for supp in self.supplements:
            days = supp.days_remaining()
            if days < min_days:
                min_days = days

        if min_days != float('inf'):
            self.update_title(f"Supplement Tracker - Next empty in {min_days:.1f} days")
        else:
            self.update_title("Supplement Tracker")

    def save_as(self):
        """Save the current supplement data to a new file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".sup",
                filetypes=[("Supplement files", "*.sup"), ("All files", "*.*")],
                initialfile="supplements.sup"
            )
            if filename:
                self.save_supplements(filename)
                messagebox.showinfo("Success", f"Data saved to {filename}")
                # Update last file in settings
                self.settings["last_file"] = filename
                save_settings(self.settings)
        except Exception as e:
            handle_error(e, "Failed to save file")

    def load_file(self):
        """Load supplement data from a file."""
        try:
            filename = filedialog.askopenfilename(
                defaultextension=".sup",
                filetypes=[("Supplement files", "*.sup"), ("All files", "*.*")]
            )
            if filename:
                self.load_supplements(filename)
                messagebox.showinfo("Success", f"Data loaded from {filename}")
        except Exception as e:
            handle_error(e, "Failed to load file")

    def save_supplements(self, filename='supplements.sup', is_user_initiated=True):
        """
        Save the current supplement data to a file.
        
        Args:
            filename (str): The path to the file to save the data to (default: 'supplements.sup').
            is_user_initiated (bool): Whether the save was initiated by the user (default: True).
        """
        try:
            data = {
                'supplements': [s.to_dict() for s in self.supplements],
                'save_date': datetime.now().strftime("%Y-%m-%d")
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Update last file in settings
            self.settings["last_file"] = filename
            save_settings(self.settings)
            
            # Create backup if needed
            if not is_user_initiated:
                backup_file = self.backup_manager.create_backup(filename, is_auto_save=True)
                if backup_file:
                    logging.info(f"Created automatic backup: {backup_file}")
            
        except Exception as e:
            handle_error(e, f"Failed to save file: {filename}")

    def load_supplements(self, filename='supplements.sup'):
        """
        Load supplement data from a file.
        
        Args:
            filename (str): The path to the file to load the data from (default: 'supplements.sup').
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.supplements = [Supplement.from_dict(s) for s in data['supplements']]
                
                # Update counts based on time passed since save
                save_date = datetime.strptime(data['save_date'], "%Y-%m-%d")
                days_passed = (datetime.now() - save_date).days
                
                for supplement in self.supplements:
                    # Ensure auto_decrement is set (for backward compatibility)
                    if not hasattr(supplement, 'auto_decrement'):
                        supplement.auto_decrement = True
                        
                    # Update the counts based on days passed if auto_decrement is enabled
                    if supplement.auto_decrement:
                        doses_taken = days_passed * supplement.daily_dose
                        supplement.current_count = max(0, supplement.current_count - doses_taken)
                    
                    supplement.last_updated = datetime.now().strftime("%Y-%m-%d")
                
                self.update_list()
                
                # Update last file in settings
                if filename != 'supplements.sup':  # Don't save default filename
                    self.settings["last_file"] = filename
                    save_settings(self.settings)
        except FileNotFoundError:
            if filename != 'supplements.sup':
                handle_error(FileNotFoundError(f"File not found: {filename}"))
        except json.JSONDecodeError:
            handle_error(ValueError(f"Invalid JSON format in file: {filename}"))
        except KeyError as e:
            handle_error(e, f"Invalid supplement data format in file: {filename}")
        except Exception as e:
            handle_error(e, f"Failed to load file: {filename}")

    def show_context_menu(self, event):
        """
        Show the context menu for the treeview.
        
        Args:
            event: The event that triggered the context menu.
        """
        # Select the item under the cursor
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # If not already selected, select it
            if not self.tree.selection() or item_id not in self.tree.selection():
                self.tree.selection_set(item_id)
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Edit", command=self.edit_selected)
            context_menu.add_command(label="Remove", command=self.remove_selected)
            
            # Display the menu at the cursor position
            context_menu.tk_popup(event.x_root, event.y_root)
            
    def edit_selected(self):
        """Edit the selected supplement."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a supplement to edit")
            return
            
        # Get the selected supplement
        index = int(selected[0])
        if index < 0 or index >= len(self.supplements):
            return
            
        supplement = self.supplements[index]
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Supplement")
        dialog.geometry("500x400")
        
        # Apply theme to dialog
        self.theme._apply_to_widget(dialog)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Create entry fields
        entries = {}
        fields = [
            ('name', "Name:", supplement.name),
            ('count', "Current Count:", str(supplement.current_count)),
            ('initial', "Initial Count:", str(supplement.initial_count)),
            ('cost', "Cost:", str(supplement.cost)),
            ('tags', "Tags (comma-separated):", ", ".join(supplement.tags)),
            ('link', "Link:", supplement.link),
            ('daily', "Daily Dose:", str(supplement.daily_dose))
        ]

        # Calculate maximum label width
        max_label_width = max(len(label) for _, label, _ in fields)

        for key, label, value in fields:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)
            
            label_widget = ttk.Label(frame, text=label, width=max_label_width + 2)
            label_widget.pack(side='left')
            
            entry = ttk.Entry(frame)
            entry.insert(0, value)
            entry.pack(side='right', expand=True, fill='x', padx=(10, 0))
            entries[key] = entry

        # Add auto-decrement checkbox
        auto_decrement_frame = ttk.Frame(main_frame)
        auto_decrement_frame.pack(fill='x', pady=5)
        
        auto_decrement_var = tk.BooleanVar(value=supplement.auto_decrement)
        auto_decrement_check = ttk.Checkbutton(
            auto_decrement_frame, 
            text="Auto-decrement daily", 
            variable=auto_decrement_var
        )
        auto_decrement_check.pack(side='left')

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(
            button_frame, 
            text="Save", 
            command=lambda: self.update_supplement(index, entries, auto_decrement_var, dialog)
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side='left', padx=5)
        
    def update_supplement(self, index, entries, auto_decrement_var, dialog):
        """
        Update a supplement with new values.
        
        Args:
            index (int): The index of the supplement to update.
            entries (Dict): A dictionary of entry widgets containing the new values.
            auto_decrement_var (tk.BooleanVar): The auto-decrement checkbox variable.
            dialog (tk.Toplevel): The dialog window to close after updating.
        """
        try:
            # Create a new supplement with the updated values
            updated_supplement = Supplement(
                entries['name'].get(),
                int(entries['count'].get()),
                int(entries['initial'].get()),
                float(entries['cost'].get()),
                [tag.strip() for tag in entries['tags'].get().split(',')],
                entries['link'].get(),
                int(entries['daily'].get()),
                auto_decrement_var.get()
            )
            
            # Preserve the last_updated date
            updated_supplement.last_updated = self.supplements[index].last_updated
            
            # Update the supplement in the list
            self.supplements[index] = updated_supplement
            
            # Save changes and update the display
            self.save_supplements()
            self.update_list()
            
            # Close the dialog
            dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Error", "Please check your input values")

    def save_with_feedback(self):
        """Save supplements and provide feedback to the user."""
        filename = self.settings.get("last_file", "supplements.sup")
        self.save_supplements(filename, is_user_initiated=True)
        # Show a brief message in the status bar or a small popup
        messagebox.showinfo("Saved", f"File saved to {filename}")
        return "break"  # Prevent the event from propagating

    def show_backups(self):
        """Show the backup management dialog."""
        backups = self.backup_manager.list_backups()
        
        if not backups:
            messagebox.showinfo("Backups", "No backups available.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Backup Management")
        dialog.geometry("700x500")
        
        # Apply theme to dialog
        self.theme._apply_to_widget(dialog)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Backup Management", 
            font=self.theme.fonts['heading']
        ).pack(pady=(0, 20))
        
        # Create treeview for backups
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", style='Vertical.TScrollbar')
        tree_scroll.pack(side='right', fill='y')
        
        backup_tree = ttk.Treeview(
            tree_frame,
            columns=('Filename', 'Date', 'Size', 'Type'),
            yscrollcommand=tree_scroll.set,
            style='Treeview'
        )
        
        # Hide the first empty column
        backup_tree['show'] = 'headings'
        
        # Configure scrollbar
        tree_scroll.config(command=backup_tree.yview)
        
        # Configure column headings
        backup_tree.heading('Filename', text='Filename')
        backup_tree.heading('Date', text='Date')
        backup_tree.heading('Size', text='Size')
        backup_tree.heading('Type', text='Type')
        
        backup_tree.column('Filename', width=250)
        backup_tree.column('Date', width=150)
        backup_tree.column('Size', width=100)
        backup_tree.column('Type', width=100)
        
        backup_tree.pack(fill='both', expand=True)
        
        # Populate treeview
        for i, backup in enumerate(backups):
            # Format date
            try:
                date_obj = datetime.fromisoformat(backup['timestamp'])
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = backup['timestamp']
                
            # Format size
            size_kb = backup['size'] / 1024
            if size_kb < 1000:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
                
            # Type
            type_str = "Automatic" if backup.get('is_auto', True) else "Manual"
            
            backup_tree.insert('', 'end', iid=str(i), values=(
                backup['filename'],
                date_str,
                size_str,
                type_str
            ))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        def restore_backup():
            selected = backup_tree.selection()
            if not selected:
                messagebox.showinfo("Info", "Please select a backup to restore")
                return
                
            index = int(selected[0])
            if index < 0 or index >= len(backups):
                return
                
            backup = backups[index]
            
            if messagebox.askyesno("Confirm Restore", 
                                  f"Are you sure you want to restore from backup: {backup['filename']}?\n\n"
                                  "This will replace your current data."):
                
                # Create a backup of current data before restoring
                if self.settings.get("last_file"):
                    self.backup_manager.create_backup(
                        self.settings["last_file"], 
                        is_auto_save=False
                    )
                
                # Restore from backup
                success = self.backup_manager.restore_from_backup(
                    backup['filename'],
                    self.settings.get("last_file", "supplements.sup")
                )
                
                if success:
                    messagebox.showinfo("Success", "Backup restored successfully")
                    self.load_supplements(self.settings.get("last_file", "supplements.sup"))
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to restore from backup")
        
        ttk.Button(
            button_frame, 
            text="Restore Selected", 
            command=restore_backup
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Close", 
            command=dialog.destroy
        ).pack(side='left', padx=5)

    def show_settings(self):
        """Show the settings dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("550x450")
        
        # Apply theme to dialog
        self.theme._apply_to_widget(dialog)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(
            main_frame, 
            text="Application Settings", 
            font=self.theme.fonts['heading']
        ).pack(pady=(0, 20))
        
        # Create notebook for different settings categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # Backup settings tab
        backup_frame = ttk.Frame(notebook, padding=15)
        notebook.add(backup_frame, text="Backup Settings")
        
        # Get current backup settings
        backup_settings = self.settings.get('backup', {})
        max_backups = backup_settings.get('max_backups', 5)
        backup_dir = backup_settings.get('backup_dir', './backup')
        compression_enabled = backup_settings.get('compression_enabled', False)
        min_backup_interval = backup_settings.get('min_backup_interval_minutes', 60)
        
        # Create variables for settings
        max_backups_var = tk.IntVar(value=max_backups)
        backup_dir_var = tk.StringVar(value=backup_dir)
        compression_var = tk.BooleanVar(value=compression_enabled)
        interval_var = tk.IntVar(value=min_backup_interval)
        
        # Max backups setting
        max_backups_frame = ttk.Frame(backup_frame)
        max_backups_frame.pack(fill='x', pady=10)
        
        ttk.Label(
            max_backups_frame, 
            text="Maximum number of backups:", 
            width=30, 
            anchor='w'
        ).pack(side='left')
        
        max_backups_spinbox = ttk.Spinbox(
            max_backups_frame,
            from_=1,
            to=20,
            textvariable=max_backups_var,
            width=5
        )
        max_backups_spinbox.pack(side='left', padx=(10, 0))
        
        # Backup directory setting
        backup_dir_frame = ttk.Frame(backup_frame)
        backup_dir_frame.pack(fill='x', pady=10)
        
        ttk.Label(
            backup_dir_frame, 
            text="Backup directory:", 
            width=30, 
            anchor='w'
        ).pack(side='left')
        
        backup_dir_entry = ttk.Entry(
            backup_dir_frame,
            textvariable=backup_dir_var,
            width=25
        )
        backup_dir_entry.pack(side='left', padx=(10, 5), fill='x', expand=True)
        
        def browse_backup_dir():
            directory = filedialog.askdirectory(
                initialdir=backup_dir_var.get(),
                title="Select Backup Directory"
            )
            if directory:
                backup_dir_var.set(directory)
        
        browse_button = ttk.Button(
            backup_dir_frame,
            text="Browse...",
            command=browse_backup_dir
        )
        browse_button.pack(side='left')
        
        # Compression setting
        compression_frame = ttk.Frame(backup_frame)
        compression_frame.pack(fill='x', pady=10)
        
        compression_check = ttk.Checkbutton(
            compression_frame,
            text="Enable backup compression (saves disk space)",
            variable=compression_var
        )
        compression_check.pack(side='left')
        
        # Backup interval setting
        interval_frame = ttk.Frame(backup_frame)
        interval_frame.pack(fill='x', pady=10)
        
        ttk.Label(
            interval_frame, 
            text="Minimum time between auto-backups:", 
            width=30, 
            anchor='w'
        ).pack(side='left')
        
        interval_spinbox = ttk.Spinbox(
            interval_frame,
            from_=5,
            to=1440,  # 24 hours in minutes
            textvariable=interval_var,
            width=5
        )
        interval_spinbox.pack(side='left', padx=(10, 5))
        
        ttk.Label(
            interval_frame, 
            text="minutes"
        ).pack(side='left')
        
        # Information section
        info_frame = ttk.Frame(backup_frame)
        info_frame.pack(fill='x', pady=(20, 10))
        
        info_text = (
            "Backups are created automatically when saving supplements.\n"
            "You can view and restore backups using the 'Backups' button."
        )
        
        ttk.Label(
            info_frame,
            text=info_text,
            foreground=self.theme.colors['text_secondary'],
            justify='left',
            wraplength=500
        ).pack(fill='x')
        
        # Current backup stats
        stats_frame = ttk.Frame(backup_frame)
        stats_frame.pack(fill='x', pady=10)
        
        # Count existing backups
        backups = self.backup_manager.list_backups()
        backup_count = len(backups)
        
        # Calculate total size
        total_size = sum(backup.get('size', 0) for backup in backups)
        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size/1024:.1f} KB"
        else:
            size_str = f"{total_size/(1024*1024):.1f} MB"
        
        stats_text = f"Current backups: {backup_count}   Total size: {size_str}"
        
        stats_label = ttk.Label(
            stats_frame,
            text=stats_text,
            foreground=self.theme.colors['text_secondary']
        )
        stats_label.pack(side='left')
        
        # Button to clear all backups
        def clear_all_backups():
            if messagebox.askyesno(
                "Confirm", 
                "Are you sure you want to delete all backups?\nThis action cannot be undone."
            ):
                # Remove all backups from the index
                for backup in self.backup_manager.list_backups():
                    try:
                        backup_path = os.path.join(
                            self.backup_manager.backup_settings['backup_dir'], 
                            backup['filename']
                        )
                        if os.path.exists(backup_path):
                            os.remove(backup_path)
                    except Exception as e:
                        logging.error(f"Failed to remove backup: {str(e)}", exc_info=True)
                
                # Clear the backup index
                self.backup_manager.backup_index['backups'] = []
                self.backup_manager._save_backup_index()
                
                # Update stats
                stats_text = "Current backups: 0   Total size: 0 bytes"
                stats_label.configure(text=stats_text)
                
                messagebox.showinfo("Success", "All backups have been deleted.")
        
        clear_button = ttk.Button(
            stats_frame,
            text="Clear All Backups",
            command=clear_all_backups
        )
        clear_button.pack(side='right')
        
        # Add more settings tabs here if needed
        # For example: general_frame = ttk.Frame(notebook, padding=15)
        # notebook.add(general_frame, text="General Settings")
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def save_settings():
            try:
                # Update backup settings
                self.settings['backup'] = {
                    'max_backups': max_backups_var.get(),
                    'backup_dir': backup_dir_var.get(),
                    'compression_enabled': compression_var.get(),
                    'min_backup_interval_minutes': interval_var.get()
                }
                
                # Save settings to file
                save_settings(self.settings)
                
                # Update backup manager with new settings
                self.backup_manager.backup_settings = self.settings['backup']
                
                # Ensure backup directory exists with new path
                self.backup_manager.ensure_backup_directory()
                
                # Update backup index file path
                self.backup_manager.backup_index_file = os.path.join(
                    self.backup_manager.backup_settings['backup_dir'], 
                    'backup_index.json'
                )
                
                messagebox.showinfo("Success", "Settings saved successfully.")
                dialog.destroy()
                
            except Exception as e:
                handle_error(e, "Failed to save settings")
        
        ttk.Button(
            button_frame, 
            text="Save", 
            command=save_settings
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side='left', padx=5)

    def run(self):
        """Run the main event loop of the application."""
        self.root.mainloop()

def setup_file_association():
    """Set up file association for .sup files on Windows."""
    import winreg
    import sys
    
    try:
        # Register .sup file extension
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.sup") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "SupplementTracker.File")

        # Register application
        app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}" "%1"'
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\SupplementTracker.File") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Supplement Tracker File")
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, app_path)
        
        print("File association setup completed successfully")
        
    except Exception as e:
        error_msg = f"Failed to set up file association: {str(e)}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)
        return False
    
    return True

if __name__ == "__main__":
    # Set up file association (only needs to be done once)
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        success = setup_file_association()
        sys.exit(0 if success else 1)

    # Normal application startup
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = SupplementTracker(initial_file)
    app.run()
