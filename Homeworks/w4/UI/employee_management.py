import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Tuple

from db_connector import DatabaseConnector
from session import EmployeeSession
from ui_components import Form, TextField, DataTable, MessageDisplay
from crypto_utils import CryptoManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('employee_management')


class EmployeeForm(Form):
    """Form for creating and editing employee information with client-side encryption."""

    def __init__(self, master, on_save: callable, on_cancel: callable):
        super().__init__(master, "")

        # Database connection
        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()
        self.crypto_mgr = CryptoManager()

        # Callbacks
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # Create form fields
        self._create_fields()

        # Create buttons
        self.create_buttons(save_callback=self.save,
                            cancel_callback=self.cancel)

        # Initially disable fields until add/edit is clicked
        self.set_fields_state("disabled")

    def _create_fields(self):
        """Create form fields with proper styling."""
        # Employee ID field (required)
        self.manv_field = TextField(
            self, "Mã Nhân Viên", row=1, required=True, field_width=20)
        self.add_field("MANV", self.manv_field)

        # Employee name field (required)
        self.hoten_field = TextField(
            self, "Họ Tên", row=2, required=True, field_width=30)
        self.add_field("HOTEN", self.hoten_field)

        # Email field
        self.email_field = TextField(
            self, "Email", row=3, field_width=30)
        self.add_field("EMAIL", self.email_field)

        # Salary field (required)
        def salary_validator(value):
            try:
                salary = int(value)
                if salary <= 0:
                    return False, "Lương phải lớn hơn 0"
                return True, ""
            except ValueError:
                return False, "Lương phải là số nguyên"

        self.luong_field = TextField(
            self, "Lương", row=4, required=True, validator=salary_validator, field_width=20)
        self.add_field("LUONG", self.luong_field)

        # Username field (required)
        self.tendn_field = TextField(
            self, "Tên Đăng Nhập", row=5, required=True, field_width=20)
        self.add_field("TENDN", self.tendn_field)

        # Password field (required)
        self.matkhau_field = TextField(
            self, "Mật Khẩu", row=6, required=True, field_width=20)
        self.add_field("MATKHAU", self.matkhau_field)

    def set_fields_state(self, state: str):
        """Enable or disable all fields."""
        for field_id, field in self.fields.items():
            if hasattr(field, "entry"):
                field.entry.configure(state=state)
            elif hasattr(field, "combobox"):
                field.combobox.configure(state=state)

    def save(self):
        """Save employee data to database with client-side encryption."""
        logger.info("Save method called in EmployeeForm")

        # Validate form data first
        if not self.validate():
            logger.info("Form validation failed, save aborted")
            return

        # Get form data
        form_data = self.get_data()
        logger.info(f"Form data: {form_data}")

        manv = form_data.get("MANV", "")
        hoten = form_data.get("HOTEN", "")
        email = form_data.get("EMAIL", "")
        luong = form_data.get("LUONG", "0")
        tendn = form_data.get("TENDN", "")
        matkhau = form_data.get("MATKHAU", "")

        try:
            # Convert salary to integer
            luong_int = int(luong)

            # If editing existing employee
            if self.is_edit_mode:
                # Editing functionality would go here
                # This is more complex as we'd need to handle key management
                MessageDisplay.show_error(
                    "Không hỗ trợ", "Chức năng chỉnh sửa nhân viên chưa được hỗ trợ trong phiên bản này")
            else:
                # Adding new employee with client-side encryption
                success = self.db.add_employee_with_client_encryption(
                    manv, hoten, email, luong_int, tendn, matkhau
                )

                if success:
                    MessageDisplay.show_info(
                        "Thành công", "Thêm nhân viên mới thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                    self.clear()
                else:
                    MessageDisplay.show_error(
                        "Lỗi", "Không thể thêm nhân viên mới")

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            MessageDisplay.show_warning("Lỗi dữ liệu", str(e))
        except Exception as e:
            logger.error(f"Database error: {e}")
            MessageDisplay.show_error("Lỗi cơ sở dữ liệu", str(e))

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        super().cancel()
        if self.on_cancel_callback:
            self.on_cancel_callback()


class EmployeeManagementScreen(ttk.Frame):
    """Employee management screen."""

    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()
        self.crypto_mgr = CryptoManager()

        self._create_widgets()
        self._load_employee_list()
        self._hide_form()

    def _create_widgets(self):
        """Create the main UI components."""
        # Create a main container with padding
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure grid to expand appropriately
        self.main_container.columnconfigure(0, weight=1)  # Left side (list)
        self.main_container.columnconfigure(1, weight=0)  # Separator
        self.main_container.columnconfigure(2, weight=1)  # Right side (form)
        self.main_container.rowconfigure(0, weight=1)

        # Create left side (list view)
        self.list_frame = ttk.Frame(self.main_container)
        self.list_frame.grid(row=0, column=0, sticky='nsew')

        # Add section title
        self.list_title = ttk.Label(self.list_frame, text="Danh Sách Nhân Viên",
                                    font=('Arial', 12, 'bold'))
        self.list_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create data table for employees
        employee_columns = [
            {'id': 'MANV', 'text': 'Mã NV', 'width': 100},
            {'id': 'HOTEN', 'text': 'Họ Tên', 'width': 200},
            {'id': 'EMAIL', 'text': 'Email', 'width': 150},
            {'id': 'LUONG', 'text': 'Lương', 'width': 100}
        ]

        self.employees_table = DataTable(
            self.list_frame,
            columns=employee_columns,
            on_select=self._on_employee_selected
        )

        # Add buttons to the DataTable
        self.employees_table.add_button.configure(command=self._on_add_clicked)
        # Disable edit and delete for now as they require more complex key management
        self.employees_table.edit_button.configure(state='disabled')
        self.employees_table.delete_button.configure(state='disabled')
        self.employees_table.refresh_button.configure(
            command=self._load_employee_list)

        # Create separator between list and form
        self.separator = ttk.Separator(self.main_container, orient='vertical')
        self.separator.grid(row=0, column=1, sticky='ns', padx=10)

        # Create right side (form)
        self.form_frame = ttk.Frame(self.main_container)
        self.form_frame.grid(row=0, column=2, sticky='nsew')

        # Add section title
        self.form_title = ttk.Label(self.form_frame, text="Thông Tin Nhân Viên",
                                    font=('Arial', 12, 'bold'))
        self.form_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create form
        self.employee_form = EmployeeForm(
            self.form_frame,
            on_save=self._on_form_saved,
            on_cancel=self._on_form_cancelled
        )
        self.employee_form.pack(fill=tk.BOTH, expand=True)

    def _load_employee_list(self):
        """Load employee list data from database."""
        try:
            # Get all employees
            employees = self.db.get_employees()

            # Transform data for the table
            table_data = []
            if employees:
                for emp in employees:
                    # Decrypt salary if possible and if current user has permission
                    salary_display = "***"  # Default to hidden

                    # Only the employee themselves can see their own salary
                    if self.employee_session.employee_id == emp['MANV']:
                        try:
                            decrypted_salary = self.db.decrypt_employee_salary(
                                emp, self.employee_session.password)
                            if decrypted_salary is not None:
                                salary_display = f"{decrypted_salary:,}"
                        except Exception as e:
                            logger.error(f"Failed to decrypt salary: {e}")

                    table_data.append({
                        'id': emp['MANV'],  # Use employee ID as row ID
                        'MANV': emp['MANV'],
                        'HOTEN': emp['HOTEN'],
                        'EMAIL': emp.get('EMAIL', ''),
                        'LUONG': salary_display
                    })

                # Load data into table
                self.employees_table.load_data(table_data)
                logger.info(f"Loaded {len(table_data)} employees")
            else:
                # Display a message in the table instead of a popup
                self.employees_table.clear_data()  # Clear existing data
                self.employees_table.show_message(
                    "Không có nhân viên nào được tìm thấy")
                logger.info("No employees found")

        except Exception as e:
            logger.error(f"Database error when loading employees: {e}")
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))

    def _hide_form(self):
        """Hide the form view."""
        self.form_frame.grid_remove()
        self.list_frame.grid(row=0, column=0, columnspan=3, sticky='nsew')
        self.separator.grid_remove()

    def _show_form(self):
        """Show the form view."""
        self.form_frame.grid()
        self.list_frame.grid(row=0, column=0, columnspan=1, sticky='nsew')
        self.separator.grid()
        # Enable form fields
        self.employee_form.set_fields_state("normal")

    def _on_employee_selected(self, employee_id):
        """Handle employee selection in the table."""
        # Enable edit and delete buttons
        # For now, we'll keep these disabled as they require more complex key management
        pass

    def _on_add_clicked(self):
        """Handle add button click."""
        # Update form title
        self.form_title.configure(text="Thêm Nhân Viên Mới")
        logger.info("Showing Add Employee form")

        # Prepare form for adding new employee
        self.employee_form.enter_create_mode()

        # Show the form
        self._show_form()

    def _on_form_saved(self):
        """Handle form saved event."""
        logger.info("Form saved successfully, updating UI")
        # Restore original title
        self.form_title.configure(text="Thông Tin Nhân Viên")
        # Reload employee list
        self._load_employee_list()
        # Hide form
        self._hide_form()
        # Reset form to initial state
        self.employee_form.enter_create_mode()

    def _on_form_cancelled(self):
        """Handle form cancel event."""
        logger.info("Form cancelled by user")
        # Restore original title
        self.form_title.configure(text="Thông Tin Nhân Viên")
        # Hide form
        self._hide_form()
        # Reset form to initial state
        self.employee_form.enter_create_mode()
