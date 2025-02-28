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

# Set up logging
logging.basicConfig(
    filename='supplement_tracker.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_settings():
    """Load user settings from settings.json."""
    default_settings = {
        "theme": "dark",
        "last_file": None
    }
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                return json.load(f)
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
                 cost: float, tags: List[str], link: str, daily_dose: int):
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
        """
        self.name = name
        self.current_count = current_count
        self.initial_count = initial_count
        self.cost = cost
        self.tags = tags
        self.link = link
        self.daily_dose = daily_dose
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
            data['daily_dose']
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
            
            # Set up file association handling
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.createcommand('::tk::mac::OpenDocument', self.open_file_from_system)
            
            self.supplements: List[Supplement] = []
            self.setup_gui()
            
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
                self.save_supplements()
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
            ("Load File", self.load_file)
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

        self.tree.pack(fill='both', expand=True)

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
                    int(entries['daily'].get())
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
                
            self.tree.insert('', 'end', iid=str(i), values=(
                supp.name,
                supp.current_count,
                supp.initial_count,
                f"${supp.cost:.2f}",
                ", ".join(supp.tags),
                supp.daily_dose,
                f"{supp.days_remaining():.1f}"
            ))

        self.update_days_until_empty()

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

    def save_supplements(self, filename='supplements.sup'):
        """
        Save the current supplement data to a file.
        
        Args:
            filename (str): The path to the file to save the data to (default: 'supplements.sup').
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
                    # Update the counts based on days passed
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
