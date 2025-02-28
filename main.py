import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import webbrowser
from typing import List, Dict
import sys
import os

class ModernTheme:
    def __init__(self, is_dark=True):
        self.is_dark = is_dark
        self.update_colors()
        
        self.fonts = {
            'heading': ('Segoe UI', 11, 'bold'),
            'body': ('Segoe UI', 10),
            'small': ('Segoe UI', 9)
        }

    def update_colors(self):
        if self.is_dark:
            self.colors = {
                'primary': '#2196F3',  # Material Blue
                'secondary': '#FFC107',  # Material Amber
                'background': '#1E1E1E',  # Dark background
                'surface': '#2D2D2D',    # Dark surface
                'text': '#FFFFFF',       # White text
                'text_secondary': '#AAAAAA',  # Light gray text
                'error': '#F44336',      # Red
                'success': '#4CAF50',    # Green
                'hover': '#3D3D3D',      # Slightly lighter than surface
                'selected': '#404040'    # Selected item background
            }
        else:
            self.colors = {
                'primary': '#2196F3',    # Material Blue
                'secondary': '#FFC107',  # Material Amber
                'background': '#FFFFFF', # White background
                'surface': '#F5F5F5',   # Light surface
                'text': '#212121',      # Dark text
                'text_secondary': '#757575',  # Gray text
                'error': '#F44336',     # Red
                'success': '#4CAF50',   # Green
                'hover': '#E0E0E0',     # Light gray hover
                'selected': '#E8E8E8'   # Selected item background
            }

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.update_colors()

    def apply(self, root):
        style = ttk.Style()
        
        # Configure basic styles
        style.configure('.',
            font=self.fonts['body'],
            background=self.colors['background'],
            foreground=self.colors['text']
        )
        
        # Modern Button
        style.configure('TButton',
            padding=(10, 5),
            font=self.fonts['body'],
            background=self.colors['surface'],
            foreground=self.colors['text']
        )
        
        style.map('TButton',
            background=[('active', self.colors['hover'])],
            foreground=[('active', self.colors['text'])]
        )
        
        # Theme toggle button style
        style.configure('Toggle.TButton',
            padding=(10, 5),
            font=self.fonts['body']
        )
        
        # Entry fields
        style.configure('TEntry',
            padding=5,
            fieldbackground=self.colors['surface'],
            foreground=self.colors['text'],
            insertcolor=self.colors['text']  # Cursor color
        )
        
        # Frame styling
        style.configure('TFrame',
            background=self.colors['background']
        )
        
        # Label styling
        style.configure('TLabel',
            font=self.fonts['body'],
            background=self.colors['background'],
            foreground=self.colors['text']
        )
        
        # Treeview styling
        style.configure('Treeview',
            background=self.colors['surface'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['surface'],
            font=self.fonts['body']
        )
        
        style.configure('Treeview.Heading',
            font=self.fonts['heading'],
            background=self.colors['surface'],
            foreground=self.colors['text']
        )
        
        style.map('Treeview',
            background=[('selected', self.colors['primary'])],
            foreground=[('selected', '#FFFFFF')]
        )
        
        # Scrollbar styling
        style.configure('TScrollbar',
            background=self.colors['surface'],
            troughcolor=self.colors['background'],
            borderwidth=0,
            arrowcolor=self.colors['text']
        )
        
        # Card style for calculator results
        style.configure('Card.TFrame',
            background=self.colors['surface'],
            padding=10
        )
        
        # Remove borders
        style.layout('TEntry', [
            ('Entry.padding', {'sticky': 'nswe', 'children': [
                ('Entry.textarea', {'sticky': 'nswe'})
            ]})
        ])
        
        # Configure root window
        root.configure(bg=self.colors['background'])
        
        return style

class Supplement:
    def __init__(self, name: str, current_count: int, initial_count: int, 
                 cost: float, tags: List[str], link: str, daily_dose: int):
        self.name = name
        self.current_count = current_count
        self.initial_count = initial_count
        self.cost = cost
        self.tags = tags
        self.link = link
        self.daily_dose = daily_dose
        self.last_updated = datetime.now().strftime("%Y-%m-%d")

    def to_dict(self) -> Dict:
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
        if self.daily_dose == 0:
            return float('inf')
        return self.current_count / self.daily_dose

    def update_count(self):
        last_updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
        days_passed = (datetime.now() - last_updated).days
        doses_taken = days_passed * self.daily_dose
        self.current_count = max(0, self.current_count - doses_taken)
        self.last_updated = datetime.now().strftime("%Y-%m-%d")

class SupplementTracker:
    def __init__(self, initial_file=None):
        self.root = tk.Tk()
        self.root.title("Supplement Tracker")
        self.root.geometry("1000x700")  # Larger default size
        
        # Apply modern theme
        self.theme = ModernTheme(is_dark=True)  # Start with dark mode
        self.style = self.theme.apply(self.root)
        
        # Set up file association handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.createcommand('::tk::mac::OpenDocument', self.open_file_from_system)
        
        self.supplements: List[Supplement] = []
        self.setup_gui()
        
        # Load initial file if provided
        if initial_file and os.path.exists(initial_file):
            self.load_supplements(initial_file)
        else:
            self.load_supplements()

    def on_closing(self):
        """Handle window closing"""
        if self.supplements:
            if messagebox.askyesno("Save Changes", "Would you like to save changes before closing?"):
                self.save_supplements()
        self.root.destroy()

    def open_file_from_system(self, filename):
        """Handle system file open requests"""
        try:
            self.load_supplements(filename)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def setup_gui(self):
        # Create main frames with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)

        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.pack(fill='x', pady=(0, 10))

        # Button frame with modern spacing
        button_frame = ttk.Frame(self.control_frame)
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
            # Update all open windows
            for window in self.root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    window.configure(bg=self.theme.colors['background'])
                    for child in window.winfo_children():
                        if isinstance(child, ttk.Frame):
                            child.configure(style='TFrame')

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

        # Add scrollbars
        tree_scroll_y = ttk.Scrollbar(self.list_frame)
        tree_scroll_y.pack(side='right', fill='y')
        
        tree_scroll_x = ttk.Scrollbar(self.list_frame, orient='horizontal')
        tree_scroll_x.pack(side='bottom', fill='x')

        # Create and configure treeview
        self.tree = ttk.Treeview(self.list_frame, 
            columns=('Name', 'Count', 'Initial', 'Cost', 'Tags', 'Daily', 'Days Left'),
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        # Configure scrollbars
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Configure column headings
        self.tree.heading('Name', text='Name', anchor='w')
        self.tree.heading('Count', text='Count', anchor='w')
        self.tree.heading('Initial', text='Initial', anchor='w')
        self.tree.heading('Cost', text='Cost', anchor='w')
        self.tree.heading('Tags', text='Tags', anchor='w')
        self.tree.heading('Daily', text='Daily Dose', anchor='w')
        self.tree.heading('Days Left', text='Days Left', anchor='w')

        # Configure column widths
        self.tree.column('Name', width=150, minwidth=100)
        self.tree.column('Count', width=70, minwidth=50)
        self.tree.column('Initial', width=70, minwidth=50)
        self.tree.column('Cost', width=80, minwidth=60)
        self.tree.column('Tags', width=150, minwidth=100)
        self.tree.column('Daily', width=80, minwidth=60)
        self.tree.column('Days Left', width=80, minwidth=60)

        self.tree.pack(fill='both', expand=True)

    def show_add_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Supplement")
        dialog.geometry("500x400")
        dialog.configure(bg=self.theme.colors['background'])
        
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
        calc = tk.Toplevel(self.root)
        calc.title("Cost Calculator")
        calc.geometry("800x600")
        calc.configure(bg=self.theme.colors['background'])
        
        # Make calculator modal
        calc.transient(self.root)
        calc.grab_set()

        main_frame = ttk.Frame(calc, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Title
        title_label = ttk.Label(main_frame, 
            text="Compare Supplement Costs", 
            font=self.theme.fonts['heading']
        )
        title_label.pack(pady=(0, 20))

        # Scrollable frame for options
        canvas = tk.Canvas(main_frame, bg=self.theme.colors['background'])
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        options_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas
        canvas_frame = canvas.create_window((0, 0), window=options_frame, anchor="nw")

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
                field_frame = ttk.Frame(fields_frame)
                field_frame.pack(side='left', padx=10)
                ttk.Label(field_frame, text=field).pack(side='top')
                entry = ttk.Entry(field_frame, width=15)
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
        if not self.supplements:
            return

        min_days = float('inf')
        for supp in self.supplements:
            days = supp.days_remaining()
            if days < min_days:
                min_days = days

        if min_days != float('inf'):
            self.root.title(f"Supplement Tracker - Next empty in {min_days:.1f} days")
        else:
            self.root.title("Supplement Tracker")

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".sup",
            filetypes=[("Supplement files", "*.sup"), ("All files", "*.*")],
            initialfile="supplements.sup"
        )
        if filename:
            self.save_supplements(filename)
            messagebox.showinfo("Success", f"Data saved to {filename}")

    def load_file(self):
        filename = filedialog.askopenfilename(
            defaultextension=".sup",
            filetypes=[("Supplement files", "*.sup"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.load_supplements(filename)
                messagebox.showinfo("Success", f"Data loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def save_supplements(self, filename='supplements.sup'):
        data = {
            'supplements': [s.to_dict() for s in self.supplements],
            'save_date': datetime.now().strftime("%Y-%m-%d")
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_supplements(self, filename='supplements.sup'):
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
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            raise Exception("Invalid JSON file format")
        except KeyError:
            raise Exception("Invalid supplement data format")

    def run(self):
        self.root.mainloop()

def setup_file_association():
    """Set up file association for .sup files"""
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

    except Exception as e:
        print(f"Failed to set up file association: {e}")

if __name__ == "__main__":
    # Set up file association (only needs to be done once)
    if len(sys.argv) > 1 and sys.argv[1] == "--register":
        setup_file_association()
        sys.exit(0)

    # Normal application startup
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = SupplementTracker(initial_file)
    app.run()
