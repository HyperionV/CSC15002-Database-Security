import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any, Optional, Tuple
import re
from datetime import datetime
from dateutil import parser


class FormField:
    """Base class for form fields with validation."""

    def __init__(self, master, label_text: str, row: int,
                 required: bool = False, validator: Optional[Callable] = None,
                 field_width: int = 30):
        self.master = master
        self.label_text = label_text
        self.required = required
        self.validator = validator
        self.field_width = field_width

        # Create label
        self.label = ttk.Label(master, text=label_text +
                               (' *' if required else ''))
        self.label.grid(row=row, column=0, sticky='w', padx=5, pady=5)

        # Value variable and error message
        self.value_var = None  # To be set by subclass
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(
            master, textvariable=self.error_var, foreground='red')
        self.error_label.grid(row=row, column=2, sticky='w', padx=5, pady=5)

    def validate(self) -> bool:
        """Validate the field value."""
        value = self.get_value()

        # Check required
        if self.required and (value is None or value == ''):
            self.error_var.set(f"{self.label_text} is required")
            return False

        # Run custom validator if provided
        if value and self.validator:
            is_valid, error_msg = self.validator(value)
            if not is_valid:
                self.error_var.set(error_msg)
                return False

        # Clear any previous error
        self.error_var.set('')
        return True

    def get_value(self):
        """Get the field value. To be implemented by subclass."""
        raise NotImplementedError

    def set_value(self, value):
        """Set the field value. To be implemented by subclass."""
        raise NotImplementedError

    def clear(self):
        """Clear the field value and error."""
        self.error_var.set('')


class TextField(FormField):
    """Text field with validation."""

    def __init__(self, master, label_text: str, row: int,
                 required: bool = False, validator: Optional[Callable] = None,
                 field_width: int = 30, readonly: bool = False):
        super().__init__(master, label_text, row, required, validator, field_width)

        # Create entry widget
        self.value_var = tk.StringVar()
        state = 'readonly' if readonly else 'normal'
        self.entry = ttk.Entry(
            master, textvariable=self.value_var, width=field_width, state=state)
        self.entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)

    def get_value(self) -> str:
        """Get the text value."""
        return self.value_var.get()

    def set_value(self, value: str) -> None:
        """Set the text value."""
        self.value_var.set(value if value is not None else '')

    def clear(self) -> None:
        """Clear the text field and error."""
        super().clear()
        self.value_var.set('')


class DateField(FormField):
    """Date field with validation."""

    def __init__(self, master, label_text: str, row: int,
                 required: bool = False, field_width: int = 20):
        # Date validator
        def date_validator(value):
            try:
                parser.parse(value)
                return True, ''
            except:
                return False, "Invalid date format (e.g., YYYY-MM-DD)"

        super().__init__(master, label_text, row, required, date_validator, field_width)

        # Create entry widget
        self.value_var = tk.StringVar()
        self.entry = ttk.Entry(
            master, textvariable=self.value_var, width=field_width)
        self.entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)

        # Create calendar button (placeholder - could be extended with a date picker)
        self.cal_button = ttk.Button(master, text="📅", width=3)
        self.cal_button.grid(row=row, column=1, sticky='e', padx=5, pady=5)

    def get_value(self) -> str:
        """Get the date value as string."""
        return self.value_var.get()

    def set_value(self, value) -> None:
        """Set the date value."""
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%d')
        self.value_var.set(value if value is not None else '')

    def clear(self) -> None:
        """Clear the date field and error."""
        super().clear()
        self.value_var.set('')


class ComboBoxField(FormField):
    """Dropdown field with validation."""

    def __init__(self, master, label_text: str, row: int, values: List[Tuple[str, str]],
                 required: bool = False, field_width: int = 30):
        super().__init__(master, label_text, row, required, None, field_width)

        # Store values
        self.values = values
        self.display_values = [display for display,
                               _ in values] if values else []
        self.value_map = {display: value for display,
                          value in values} if values else {}

        # Create combobox widget
        self.value_var = tk.StringVar()
        self.combobox = ttk.Combobox(master, textvariable=self.value_var,
                                     values=self.display_values, width=field_width)
        self.combobox.grid(row=row, column=1, sticky='w', padx=5, pady=5)

        # Set state to readonly to prevent direct editing
        self.combobox['state'] = 'readonly'

    def get_value(self) -> str:
        """Get the selected value (not display text)."""
        display_text = self.value_var.get()
        return self.value_map.get(display_text, '')

    def get_display_value(self) -> str:
        """Get the display text."""
        return self.value_var.get()

    def set_value(self, value: str) -> None:
        """Set the value by internal value (will map to display text)."""
        for display, val in self.values:
            if val == value:
                self.value_var.set(display)
                break

    def set_values(self, values: List[Tuple[str, str]]) -> None:
        """Update the list of values."""
        self.values = values
        self.display_values = [display for display,
                               _ in values] if values else []
        self.value_map = {display: value for display,
                          value in values} if values else {}
        self.combobox['values'] = self.display_values

    def clear(self) -> None:
        """Clear the selection and error."""
        super().clear()
        self.value_var.set('')


class DataTable(ttk.Treeview):
    """Enhanced treeview for displaying tabular data."""

    def __init__(self, master, columns: List[Dict[str, Any]], data: List[Dict] = None,
                 on_select: Optional[Callable] = None, height: int = 10,
                 show_buttons: bool = True):
        """
        Initialize a data table.

        Args:
            master: Parent widget
            columns: List of column definitions. Each column should have:
                     - 'id': Column ID
                     - 'text': Column header text
                     - 'width': Column width
                     - 'anchor': Text anchor (optional)
            data: Initial data as list of dictionaries
            on_select: Callback function when a row is selected
            height: Number of rows to display
            show_buttons: Whether to show action buttons
        """
        # Configure column ids and display columns
        self.column_ids = ['#0'] + [col['id'] for col in columns]
        self.display_columns = [col['id'] for col in columns]

        # Initialize treeview
        super().__init__(master, columns=self.display_columns,
                         show='headings', height=height)

        # Configure columns
        for col in columns:
            self.heading(col['id'], text=col['text'])
            self.column(col['id'], width=col.get('width', 100),
                        anchor=col.get('anchor', 'w'))

        # Create a frame for the treeview with a scrollbar
        self.frame = ttk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.configure(yscrollcommand=scrollbar.set)
        self.pack(in_=self.frame, fill=tk.BOTH, expand=True)

        # Store callback
        self.on_select = on_select

        # Bind selection event
        self.bind('<<TreeviewSelect>>', self._on_row_selected)

        # Add action buttons if requested
        if show_buttons:
            button_frame = ttk.Frame(self.frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            self.add_button = ttk.Button(button_frame, text="Add", width=10)
            self.add_button.pack(side=tk.LEFT, padx=5)

            self.edit_button = ttk.Button(button_frame, text="Edit", width=10)
            self.edit_button.pack(side=tk.LEFT, padx=5)

            self.delete_button = ttk.Button(
                button_frame, text="Delete", width=10)
            self.delete_button.pack(side=tk.LEFT, padx=5)

            self.refresh_button = ttk.Button(
                button_frame, text="Refresh", width=10)
            self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Load initial data if provided
        if data:
            self.load_data(data)

    def load_data(self, data: List[Dict]) -> None:
        """Load data into the table."""
        # Clear existing data
        for i in self.get_children():
            self.delete(i)

        # Insert new data
        for item in data:
            values = [item.get(col_id, '') for col_id in self.display_columns]
            self.insert('', tk.END, values=values, iid=str(item.get('id', '')))

    def get_selected_item(self) -> Optional[str]:
        """Get the selected item ID."""
        selection = self.selection()
        if selection:
            return selection[0]
        return None

    def _on_row_selected(self, event) -> None:
        """Handle row selection event."""
        if self.on_select:
            selected_item = self.get_selected_item()
            if selected_item:
                self.on_select(selected_item)


class Form(ttk.Frame):
    """Base form with validation and CRUD operations."""

    def __init__(self, master, title: str):
        super().__init__(master)
        self.master = master

        # Set form title
        self.title_label = ttk.Label(
            self, text=title, font=('Helvetica', 14, 'bold'))
        self.title_label.grid(row=0, column=0, columnspan=3,
                              sticky='w', padx=10, pady=10)

        # Fields storage
        self.fields = {}
        self.current_row = 1

        # Buttons frame
        self.buttons_frame = ttk.Frame(self)

        # Form state
        self._edit_mode = False
        self._current_id = None

    def add_field(self, field_id: str, field: FormField) -> None:
        """Add a field to the form."""
        self.fields[field_id] = field

    def create_buttons(self, save_callback: Optional[Callable] = None,
                       cancel_callback: Optional[Callable] = None,
                       position: int = None) -> None:
        """Create form buttons."""
        row = position if position is not None else self.current_row

        self.buttons_frame.grid(
            row=row, column=0, columnspan=3, sticky='w', padx=5, pady=10)

        self.save_button = ttk.Button(self.buttons_frame, text="Save",
                                      command=save_callback if save_callback else self.save)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.buttons_frame, text="Cancel",
                                        command=cancel_callback if cancel_callback else self.cancel)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.current_row = row + 1

    def validate(self) -> bool:
        """Validate all form fields."""
        is_valid = True
        for field in self.fields.values():
            if not field.validate():
                is_valid = False
        return is_valid

    def get_data(self) -> Dict[str, Any]:
        """Get data from all fields as a dictionary."""
        data = {}
        for field_id, field in self.fields.items():
            data[field_id] = field.get_value()
        return data

    def set_data(self, data: Dict[str, Any]) -> None:
        """Set form data from a dictionary."""
        for field_id, value in data.items():
            if field_id in self.fields:
                self.fields[field_id].set_value(value)

    def clear(self) -> None:
        """Clear all form fields."""
        for field in self.fields.values():
            field.clear()

    def enter_edit_mode(self, item_id: str, data: Dict[str, Any]) -> None:
        """Enter edit mode for an existing item."""
        self._edit_mode = True
        self._current_id = item_id
        self.set_data(data)
        self.save_button.configure(text="Update")

    def enter_create_mode(self) -> None:
        """Enter create mode for a new item."""
        self._edit_mode = False
        self._current_id = None
        self.clear()
        self.save_button.configure(text="Save")

    @property
    def is_edit_mode(self) -> bool:
        """Check if form is in edit mode."""
        return self._edit_mode

    @property
    def current_id(self) -> Optional[str]:
        """Get the ID of the item being edited."""
        return self._current_id

    def save(self) -> None:
        """Default save method to be overridden."""
        pass

    def cancel(self) -> None:
        """Default cancel method."""
        self.clear()
        self.enter_create_mode()


class MessageDisplay:
    """Utility class for displaying messages."""

    @staticmethod
    def show_info(title: str, message: str) -> None:
        """Show an information message."""
        messagebox.showinfo(title, message)

    @staticmethod
    def show_error(title: str, message: str) -> None:
        """Show an error message."""
        messagebox.showerror(title, message)

    @staticmethod
    def show_warning(title: str, message: str) -> None:
        """Show a warning message."""
        messagebox.showwarning(title, message)

    @staticmethod
    def ask_yes_no(title: str, message: str) -> bool:
        """Ask a yes/no question."""
        return messagebox.askyesno(title, message)


class ApplicationWindow:
    """Base application window with navigation."""

    def __init__(self, title: str, width: int = 800, height: int = 600):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        # Set up the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Set up a frame for the navigation bar
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)

        # Set up a frame for the content
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Dictionary to store content frames
        self.frames = {}

        # Set up status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var,
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def add_nav_button(self, text: str, command: Callable) -> None:
        """Add a button to the navigation bar."""
        button = ttk.Button(self.nav_frame, text=text, command=command)
        button.pack(side=tk.LEFT, padx=5, pady=5)

    def add_frame(self, name: str, frame: ttk.Frame) -> None:
        """Add a content frame."""
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()  # Hide the frame initially

    def show_frame(self, name: str) -> None:
        """Show a specific content frame."""
        # Hide all frames
        for frame in self.frames.values():
            frame.grid_remove()

        # Show the requested frame
        if name in self.frames:
            self.frames[name].grid()

    def set_status(self, message: str) -> None:
        """Set the status bar message."""
        self.status_var.set(message)

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()

    def close(self) -> None:
        """Close the application."""
        self.root.destroy()
