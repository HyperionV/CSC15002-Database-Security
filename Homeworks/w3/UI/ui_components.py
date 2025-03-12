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
                               (' *' if required else ''), width=15, anchor='e')
        self.label.grid(row=row, column=0, sticky='e', padx=(10, 5), pady=8)

        # Value variable and error message
        self.value_var = None  # To be set by subclass
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(
            master, textvariable=self.error_var, foreground='red')
        self.error_label.grid(
            row=row, column=2, sticky='w', padx=(5, 10), pady=8)

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
    """Text input field."""

    def __init__(self, master, label_text: str, row: int,
                 required: bool = False, validator: Optional[Callable] = None,
                 field_width: int = 30, readonly: bool = False):
        super().__init__(master, label_text, row, required, validator, field_width)
        self.readonly = readonly

        # Create entry field with value variable
        self.value_var = tk.StringVar()
        self.entry = ttk.Entry(
            master, textvariable=self.value_var, width=field_width)

        if readonly:
            self.entry.configure(state='readonly')

        # Apply consistent styling
        self.entry.grid(row=row, column=1, sticky='ew', padx=(0, 5))

        # Configure column to expand
        if row == 0:  # Only need to configure once
            master.columnconfigure(1, weight=1)

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
    """Date input field with validation."""

    def __init__(self, master, label_text: str, row: int,
                 required: bool = False, field_width: int = 20):
        # Date validator
        def date_validator(value):
            try:
                # Try to parse the date in the expected format
                datetime.strptime(value, '%Y-%m-%d')
                return True, ""
            except ValueError:
                return False, "Invalid date format. Use YYYY-MM-DD"

        super().__init__(master, label_text, row, required, date_validator, field_width)

        # Create date entry with value variable
        self.value_var = tk.StringVar()
        self.entry = ttk.Entry(
            master, textvariable=self.value_var, width=field_width)

        # Add placeholder text
        self.entry.insert(0, "YYYY-MM-DD")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)

        # Apply consistent styling
        self.entry.grid(row=row, column=1, sticky='ew', padx=(0, 5))

    def _clear_placeholder(self, event):
        if self.entry.get() == "YYYY-MM-DD":
            self.entry.delete(0, tk.END)

    def _restore_placeholder(self, event):
        if self.entry.get() == "":
            self.entry.insert(0, "YYYY-MM-DD")

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
    """Dropdown selection field."""

    def __init__(self, master, label_text: str, row: int, values: List[Tuple[str, str]],
                 required: bool = False, field_width: int = 30):
        super().__init__(master, label_text, row, required, None, field_width)

        # Store the value-display mapping
        self.values = values
        self.display_map = {display: value for display, value in values}
        self.value_map = {value: display for display, value in values}

        # Get only display values for the dropdown
        display_values = [display for display, _ in values]

        # Create combobox with display values
        self.value_var = tk.StringVar()
        self.combobox = ttk.Combobox(
            master, textvariable=self.value_var, values=display_values,
            width=field_width, state="readonly")

        # Apply consistent styling
        self.combobox.grid(row=row, column=1, sticky='ew', padx=(0, 5))

    def get_value(self) -> str:
        """Get the selected value (not display text)."""
        display_text = self.value_var.get()
        return self.display_map.get(display_text, '')

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
        self.display_map = {display: value for display,
                            value in values} if values else {}
        self.value_map = {value: display for display,
                          value in values} if values else {}
        self.combobox['values'] = self.display_values

    def clear(self) -> None:
        """Clear the selection and error."""
        super().clear()
        self.value_var.set('')


class DataTable(ttk.Treeview):
    """Enhanced treeview for tabular data display."""

    def __init__(self, master, columns: List[Dict[str, Any]], data: List[Dict] = None,
                 on_select: Optional[Callable] = None, height: int = 10,
                 show_buttons: bool = True):
        """
        Initialize a data table with columns configuration.

        columns: List of dictionaries with 'id', 'text', and 'width' keys
        data: Optional initial data to display
        on_select: Callback when a row is selected
        height: Number of rows to display
        show_buttons: Whether to show the action buttons
        """
        self.master = master
        self.columns = columns
        self.on_select = on_select
        self.show_buttons = show_buttons

        # Create a frame to hold the table and scrollbar
        self.frame = ttk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure column IDs and displayable columns
        column_ids = [col['id'] for col in columns]

        # Initialize treeview with columns
        super().__init__(
            self.frame,
            columns=column_ids,
            show='headings',
            height=height,
            selectmode='browse'
        )

        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=self.scrollbar.set)

        # Layout table and scrollbar
        self.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure columns
        for col in columns:
            self.heading(col['id'], text=col['text'], anchor=tk.W)
            self.column(col['id'], width=col['width'],
                        anchor=col.get('anchor', tk.W))

        # Set up selection event
        self.bind('<<TreeviewSelect>>', self._on_row_selected)

        # Add alternating row colors for better readability
        self.tag_configure('odd', background='#f5f5f5')
        self.tag_configure('even', background='white')

        # Add buttons if needed
        if show_buttons:
            self.button_frame = ttk.Frame(master)
            self.button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            # Style for consistent button appearance
            self.add_button = ttk.Button(
                self.button_frame, text="Add", width=10)
            self.edit_button = ttk.Button(
                self.button_frame, text="Edit", width=10)
            self.delete_button = ttk.Button(
                self.button_frame, text="Delete", width=10)
            self.refresh_button = ttk.Button(
                self.button_frame, text="Refresh", width=10)

            # Pack buttons with consistent spacing
            self.add_button.pack(side=tk.LEFT, padx=(0, 5))
            self.edit_button.pack(side=tk.LEFT, padx=5)
            self.delete_button.pack(side=tk.LEFT, padx=5)
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
        for i, item in enumerate(data):
            # Get values for all columns
            values = []
            for col in self.columns:
                col_id = col['id']
                values.append(item.get(col_id, ''))

            # Apply alternating row colors
            row_tag = 'even' if i % 2 == 0 else 'odd'

            # Get the unique ID for this row if available
            item_id = str(item.get('id', i))

            # Insert the row with appropriate tag
            self.insert('', tk.END, values=values,
                        iid=item_id, tags=(row_tag,))

        # Enable or disable buttons based on data
        if self.show_buttons:
            has_data = len(data) > 0
            self.edit_button.configure(
                state="normal" if has_data else "disabled")
            self.delete_button.configure(
                state="normal" if has_data else "disabled")

    def clear_data(self) -> None:
        """Clear all data from the table."""
        for i in self.get_children():
            self.delete(i)

        # Disable edit and delete buttons
        if self.show_buttons:
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

    def show_message(self, message: str) -> None:
        """Show a message in the table when there's no data."""
        self.clear_data()
        # Insert a dummy row with the message spanning all columns
        self.insert('', tk.END, values=[message] + [''] * (len(self.columns) - 1),
                    tags=('message',))
        # Style the message row
        self.tag_configure('message', background='#f0f0f0',
                           foreground='#555555', font=('Arial', 10, 'italic'))

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
    """Base form class with field management and validation."""

    def __init__(self, master, title: str):
        """
        Initialize a form with a title.

        master: Parent widget
        title: Form title text
        """
        super().__init__(master)

        # Create a styled frame with padding and border
        self.configure(padding=10)

        # Add a distinctive border
        self.style = ttk.Style()
        self.style.configure('Form.TFrame', borderwidth=1, relief='solid')

        # Add form title
        self.title_label = ttk.Label(
            self, text=title, font=('Arial', 12, 'bold'))
        self.title_label.grid(row=0, column=0, columnspan=3,
                              sticky='w', padx=5, pady=(5, 15))

        # Store fields and form state
        self.fields = {}
        self._item_id = None
        self._is_edit_mode = False

        # Configure the grid to make the form responsive
        self.columnconfigure(1, weight=1)  # Make field column expandable

    def add_field(self, field_id: str, field: FormField) -> None:
        """Add a field to the form."""
        self.fields[field_id] = field

    def create_buttons(self, save_callback: Optional[Callable] = None,
                       cancel_callback: Optional[Callable] = None,
                       position: int = None) -> None:
        """
        Add save and cancel buttons to the form.

        save_callback: Function to call when save button is clicked
        cancel_callback: Function to call when cancel button is clicked
        position: Row position for buttons (default: after all fields)
        """
        if position is None:
            # If there are fields, place buttons after the last field
            # Otherwise, place them after the title
            position = max(field.label.grid_info()[
                           'row'] for field in self.fields.values()) + 1 if self.fields else 1

        # Create a button frame with padding
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=position, column=0, columnspan=3,
                                sticky='e', padx=5, pady=15)

        # Create styled buttons
        self.save_button = ttk.Button(
            self.buttons_frame, text="Save", command=save_callback or self.save, width=10)
        self.cancel_button = ttk.Button(
            self.buttons_frame, text="Cancel", command=cancel_callback or self.cancel, width=10)

        # Pack buttons with consistent spacing
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        self.cancel_button.pack(side=tk.LEFT)

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
        """Enter edit mode with the given item ID and data."""
        self._item_id = item_id
        self._is_edit_mode = True
        self.set_data(data)
        if hasattr(self, 'save_button'):
            self.save_button.configure(text="Update")

    def enter_create_mode(self) -> None:
        """Enter create mode with empty form."""
        self._item_id = None
        self._is_edit_mode = False
        self.clear()
        if hasattr(self, 'save_button'):
            self.save_button.configure(text="Save")

    @property
    def is_edit_mode(self) -> bool:
        """Check if the form is in edit mode."""
        return self._is_edit_mode

    @property
    def current_id(self) -> Optional[str]:
        """Get the current item ID being edited."""
        return self._item_id

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
    """Main application window with navigation and content frames."""

    def __init__(self, title: str, width: int = 1000, height: int = 700):
        """Initialize the main application window."""
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        # Add styling
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure(
            "TLabel", background="#f0f0f0", font=('Arial', 10))
        self.style.configure("TButton", font=('Arial', 10))
        self.style.configure("Heading.TLabel", font=('Arial', 12, 'bold'))
        self.style.configure("Nav.TButton", font=('Arial', 10, 'bold'))

        # Create header frame
        self.header_frame = ttk.Frame(self.root, padding=10)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        # Application title
        self.title_label = ttk.Label(
            self.header_frame, text=title, font=('Arial', 14, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=10)

        # Navigation buttons
        self.nav_frame = ttk.Frame(self.header_frame)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)

        # User info and login/logout on right side
        self.user_frame = ttk.Frame(self.header_frame)
        self.user_frame.pack(side=tk.RIGHT, padx=10)

        self.user_label = ttk.Label(self.user_frame, text="")
        self.user_label.pack(side=tk.LEFT, padx=(0, 10))

        self.logout_button = ttk.Button(
            self.user_frame, text="Đăng xuất", style="Nav.TButton")
        self.logout_button.pack(side=tk.LEFT)

        # Add a separator
        self.separator = ttk.Separator(self.root, orient='horizontal')
        self.separator.pack(fill=tk.X, padx=5, pady=2)

        # Main content area
        self.content_frame = ttk.Frame(self.root, padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Status bar at bottom
        self.status_frame = ttk.Frame(self.root, padding=(10, 5))
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)

        # Store frames
        self.frames = {}

    def add_nav_button(self, text: str, command: Callable) -> None:
        """Add a button to the navigation bar."""
        button = ttk.Button(self.nav_frame, text=text,
                            command=command, style="Nav.TButton")
        button.pack(side=tk.LEFT, padx=5)

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
        self.status_label.config(text=message)

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()

    def close(self) -> None:
        """Close the application."""
        self.root.destroy()
