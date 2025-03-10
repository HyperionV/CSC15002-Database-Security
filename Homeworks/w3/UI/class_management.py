import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Tuple

from db_connector import DatabaseConnector
from session import EmployeeSession
from ui_components import Form, TextField, DataTable, MessageDisplay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('class_management')


class ClassForm(Form):
    """Form for creating and editing class information."""

    def __init__(self, master, on_save: callable, on_cancel: callable):
        super().__init__(master, "Thông Tin Lớp")

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Callbacks
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # Create form fields
        self._create_fields()
        self.create_buttons(self.save, self.cancel)

    def _create_fields(self):
        """Create the form fields."""
        # Class ID field
        self.add_field('MALOP', TextField(self, "Mã Lớp", 1, required=True))

        # Class name field
        self.add_field('TENLOP', TextField(self, "Tên Lớp", 2, required=True))

        # Employee ID field (read-only)
        employee_id = self.session.employee_id or ''
        self.add_field('MANV', TextField(
            self, "Mã Nhân Viên", 3, required=True, readonly=True))
        self.fields['MANV'].set_value(employee_id)

    def save(self):
        """Save the class data."""
        # Validate form
        if not self.validate():
            return

        # Get form data
        data = self.get_data()

        try:
            if self.is_edit_mode:
                # Update existing class
                success = self.db.update_class(
                    data['MALOP'], data['TENLOP'], data['MANV'])
                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Cập nhật thông tin lớp thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error(
                        "Lỗi", "Không thể cập nhật thông tin lớp")
            else:
                # Add new class
                success = self.db.add_class(
                    data['MALOP'], data['TENLOP'], data['MANV'])
                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Thêm lớp mới thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error("Lỗi", "Không thể thêm lớp mới")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when saving class: {str(e)}")

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        super().cancel()
        if self.on_cancel_callback:
            self.on_cancel_callback()


class ClassManagementScreen(ttk.Frame):
    """Class management screen with list and CRUD operations."""

    def __init__(self, master):
        super().__init__(master)
        self.master = master

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Split the screen into list and form areas
        self._create_widgets()

        # Show the class list initially
        self.show_list()

        # Load data
        self.refresh_data()

    def _create_widgets(self):
        """Create the screen widgets."""
        # Create main container with two frames
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame for list
        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                             expand=True, padx=5, pady=5)

        # Create a label for the list
        list_label = ttk.Label(
            self.list_frame, text="Danh Sách Lớp", font=('Helvetica', 14, 'bold'))
        list_label.pack(anchor='w', pady=(0, 10))

        # Create class table
        columns = [
            {'id': 'MALOP', 'text': 'Mã Lớp', 'width': 100},
            {'id': 'TENLOP', 'text': 'Tên Lớp', 'width': 250},
            {'id': 'TENNV', 'text': 'Nhân Viên Quản Lý', 'width': 200}
        ]

        self.class_table = DataTable(
            self.list_frame, columns, on_select=self._on_class_selected)

        # Configure button commands
        self.class_table.add_button.configure(command=self._on_add_clicked)
        self.class_table.edit_button.configure(command=self._on_edit_clicked)
        self.class_table.delete_button.configure(
            command=self._on_delete_clicked)
        self.class_table.refresh_button.configure(command=self.refresh_data)

        # Right frame for form
        self.form_frame = ttk.Frame(self.main_frame)
        self.form_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                             expand=True, padx=5, pady=5)

        # Create class form
        self.class_form = ClassForm(
            self.form_frame, self._on_form_saved, self._on_form_cancelled)
        self.class_form.pack(fill=tk.BOTH, expand=True)

    def show_list(self):
        """Show the class list and hide the form."""
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.form_frame.pack_forget()

    def show_form(self):
        """Show the form and hide the list."""
        self.form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def refresh_data(self):
        """Refresh the class list."""
        try:
            # Get classes managed by the current employee
            employee_id = self.session.employee_id
            if employee_id:
                # Get classes managed by this employee
                classes = self.db.get_classes_by_employee(employee_id)

                # Transform data for the table
                table_data = []
                if classes:
                    for cls in classes:
                        table_data.append({
                            'id': cls['MALOP'],  # Use class ID as row ID
                            'MALOP': cls['MALOP'],
                            'TENLOP': cls['TENLOP'],
                            'TENNV': cls['TENNV'] if 'TENNV' in cls else ''
                        })

                # Load data into table
                self.class_table.load_data(table_data)
            else:
                MessageDisplay.show_error(
                    "Lỗi", "Không có thông tin nhân viên đăng nhập")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading classes: {str(e)}")

    def _on_class_selected(self, class_id):
        """Handle class selection in the table."""
        # Enable edit and delete buttons
        self.class_table.edit_button.config(state='normal')
        self.class_table.delete_button.config(state='normal')

    def _on_add_clicked(self):
        """Handle add button click."""
        # Show the form in create mode
        self.class_form.enter_create_mode()
        self.show_form()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        selected_id = self.class_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để chỉnh sửa")
            return

        try:
            # Get classes managed by the current employee
            employee_id = self.session.employee_id
            classes = self.db.get_classes_by_employee(employee_id)

            # Find the selected class
            selected_class = next(
                (cls for cls in classes if cls['MALOP'] == selected_id), None)

            if selected_class:
                # Populate form with class data
                self.class_form.enter_edit_mode(selected_id, {
                    'MALOP': selected_class['MALOP'],
                    'TENLOP': selected_class['TENLOP'],
                    'MANV': selected_class['MANV']
                })

                # Make class ID read-only in edit mode
                self.class_form.fields['MALOP'].entry.config(state='readonly')

                # Show the form
                self.show_form()
            else:
                MessageDisplay.show_error(
                    "Lỗi", "Không tìm thấy thông tin lớp")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(
                f"Database error when loading class details: {str(e)}")

    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected_id = self.class_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để xóa")
            return

        # Confirm deletion
        if not MessageDisplay.ask_yes_no("Xác Nhận", "Bạn có chắc chắn muốn xóa lớp này?"):
            return

        try:
            # Delete the class
            success = self.db.delete_class(selected_id)

            if success:
                MessageDisplay.show_info("Thành Công", "Xóa lớp thành công")
                self.refresh_data()
            else:
                MessageDisplay.show_error("Lỗi", "Không thể xóa lớp")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when deleting class: {str(e)}")

    def _on_form_saved(self):
        """Handle form save event."""
        # Refresh the list and show it
        self.refresh_data()
        self.show_list()

    def _on_form_cancelled(self):
        """Handle form cancel event."""
        # Just show the list again
        self.show_list()
