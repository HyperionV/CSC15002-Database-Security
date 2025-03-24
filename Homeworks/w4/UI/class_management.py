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
        super().__init__(master, "")

        # Database connection
        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()

        # Callbacks
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # Create form fields
        self._create_fields()

        # Create buttons but don't pass the callbacks directly
        # We'll handle them in our own save/cancel methods
        self.create_buttons(save_callback=self.save,
                            cancel_callback=self.cancel)

        # Initially disable fields until add/edit is clicked
        self.set_fields_state("disabled")

    def _create_fields(self):
        """Create form fields with proper styling."""
        # Class ID field (required)
        self.malop_field = TextField(
            self, "Mã Lớp *", row=1, required=True, field_width=20)
        self.add_field("MALOP", self.malop_field)

        # Class name field (required)
        self.tenlop_field = TextField(
            self, "Tên Lớp *", row=2, required=True, field_width=30)
        self.add_field("TENLOP", self.tenlop_field)

        # Employee ID field (required) - readonly if current employee is creating a class
        current_employee_id = self.employee_session.employee_id
        readonly = current_employee_id is not None

        self.manv_field = TextField(
            self, "Mã Nhân Viên *", row=3, required=True, field_width=20, readonly=readonly)
        self.add_field("MANV", self.manv_field)

        # Pre-fill current employee's ID
        if current_employee_id:
            self.manv_field.set_value(current_employee_id)

    def set_fields_state(self, state: str):
        """Enable or disable all fields."""
        for field_id, field in self.fields.items():
            if hasattr(field, "entry"):
                field.entry.configure(state=state)
            elif hasattr(field, "combobox"):
                field.combobox.configure(state=state)

    def save(self):
        """Save class data to database."""
        logger.info("Save method called in ClassForm")

        # Validate form data first
        if not self.validate():
            logger.info("Form validation failed, save aborted")
            return

        # Get form data using get_data() method from Form base class
        form_data = self.get_data()
        logger.info(f"Form data: {form_data}")

        malop = form_data.get("MALOP", "")
        tenlop = form_data.get("TENLOP", "")
        manv = form_data.get("MANV", "")

        logger.info(
            f"Attempting to save class data: MALOP={malop}, TENLOP={tenlop}, MANV={manv}, is_edit_mode={self.is_edit_mode}")

        try:
            # If editing existing class
            if self.is_edit_mode:
                try:
                    logger.info(f"Updating class: {malop}")
                    # Update class information
                    self.db.update_class(malop, tenlop, manv)
                    self.show_info_message("Cập nhật lớp thành công!")
                    # Luôn gọi on_save_callback ở đây nếu cập nhật thành công
                    if self.on_save_callback:
                        self.on_save_callback()
                    # Không hủy form, chỉ reset trạng thái
                    self.clear()
                except ValueError as e:
                    logger.error(f"Validation error when updating class: {e}")
                    self.show_warning_message(str(e))
            else:
                # Adding new class
                try:
                    logger.info(f"Adding new class: {malop}")
                    self.db.add_class(malop, tenlop, manv)
                    self.show_info_message("Thêm lớp thành công!")
                    # Luôn gọi on_save_callback ở đây nếu thêm thành công
                    if self.on_save_callback:
                        self.on_save_callback()
                    # Không hủy form, chỉ reset trạng thái
                    self.clear()
                except ValueError as e:
                    logger.error(f"Validation error when adding class: {e}")
                    self.show_warning_message(str(e))
        except Exception as e:
            logger.error(f"Database error: {e}")
            self.show_error_message(f"Lỗi cơ sở dữ liệu: {e}")

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        # First call the base class cancel method to reset fields
        super().cancel()
        # Then call the callback without destroying the form
        if self.on_cancel_callback:
            self.on_cancel_callback()
        # Không hủy form

    def show_info_message(self, message):
        """Show an information message."""
        from tkinter import messagebox
        messagebox.showinfo("Thông báo", message)

    def show_warning_message(self, message):
        """Show a warning message."""
        from tkinter import messagebox
        messagebox.showwarning("Cảnh báo", message)

    def show_error_message(self, message):
        """Show an error message."""
        from tkinter import messagebox
        messagebox.showerror("Lỗi", message)


class ClassManagementScreen(ttk.Frame):
    """Class management screen."""

    def __init__(self, master):
        super().__init__(master)
        self.master = master

        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()

        self._create_widgets()

        self._load_class_list()
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
        self.list_title = ttk.Label(self.list_frame, text="Danh Sách Lớp",
                                    font=('Arial', 12, 'bold'))
        self.list_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create data table for classes
        class_columns = [
            {'id': 'MALOP', 'text': 'Mã Lớp', 'width': 100},
            {'id': 'TENLOP', 'text': 'Tên Lớp', 'width': 200},
            {'id': 'TENNV', 'text': 'Nhân Viên Quản Lý', 'width': 200}
        ]

        self.classes_table = DataTable(
            self.list_frame,
            columns=class_columns,
            on_select=self._on_class_selected
        )

        # Add buttons to the DataTable
        self.classes_table.add_button.configure(command=self._on_add_clicked)
        self.classes_table.edit_button.configure(command=self._on_edit_clicked)
        self.classes_table.delete_button.configure(
            command=self._on_delete_clicked)
        self.classes_table.refresh_button.configure(
            command=self._load_class_list)

        # Create separator between list and form
        self.separator = ttk.Separator(self.main_container, orient='vertical')
        self.separator.grid(row=0, column=1, sticky='ns', padx=10)

        # Create right side (form)
        self.form_frame = ttk.Frame(self.main_container)
        self.form_frame.grid(row=0, column=2, sticky='nsew')

        # Add section title
        self.form_title = ttk.Label(self.form_frame, text="Thông Tin Lớp",
                                    font=('Arial', 12, 'bold'))
        self.form_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create form
        self.class_form = ClassForm(
            self.form_frame,
            on_save=self._on_form_saved,
            on_cancel=self._on_form_cancelled
        )
        self.class_form.pack(fill=tk.BOTH, expand=True)

    def _load_class_list(self):
        """Load class list data from database."""
        try:
            # Get classes managed by the current employee
            employee_id = self.employee_session.employee_id

            if employee_id:
                # Sử dụng SP_SEL_LOP_BY_MANV cho lấy danh sách lớp của nhân viên
                classes = self.db.get_classes_by_employee(employee_id)
            else:
                # Sử dụng SP_SEL_LOP cho lấy tất cả các lớp
                classes = self.db.get_classes()

            # Transform data for the table
            table_data = []
            if classes:
                for cls in classes:
                    table_data.append({
                        'id': cls['MALOP'],  # Use class ID as row ID
                        'MALOP': cls['MALOP'],
                        'TENLOP': cls['TENLOP'],
                        'MANV': cls.get('MANV', ''),
                        'TENNV': cls.get('TENNV', '')
                    })

                # Load data into table
                self.classes_table.load_data(table_data)
                logger.info(f"Loaded {len(table_data)} classes")
            else:
                # Display a message in the table instead of a popup
                if employee_id:
                    message = "Nhân viên này hiện không quản lý lớp nào"
                else:
                    message = "Không có lớp nào được tìm thấy"
                self.classes_table.clear_data()  # Clear existing data
                self.classes_table.show_message(message)
                logger.info(f"No classes found, displaying message: {message}")

        except Exception as e:
            logger.error(f"Database error when loading classes: {e}")
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
        self.class_form.set_fields_state("normal")

    def _on_class_selected(self, class_id):
        """Handle class selection in the table."""
        # Enable edit and delete buttons
        self.classes_table.edit_button.config(state='normal')
        self.classes_table.delete_button.config(state='normal')

    def _on_add_clicked(self):
        """Handle add button click."""
        # Đổi tiêu đề form
        self.form_title.configure(text="Thêm Lớp Mới")
        logger.info("Showing Add Class form")

        # Chuẩn bị form để thêm mới
        self.class_form.enter_create_mode()

        # Hiển thị form
        self._show_form()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        selected_id = self.classes_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để chỉnh sửa")
            return

        try:
            # Đổi tiêu đề form
            self.form_title.configure(text="Chỉnh Sửa Lớp")
            logger.info(f"Editing class with ID: {selected_id}")

            # Sử dụng stored procedure để lấy thông tin chính xác từ database
            employee_id = self.employee_session.employee_id

            # Sử dụng SP_SEL_LOP để lấy thông tin chi tiết của lớp đã chọn
            classes = self.db.get_classes()
            if not classes:
                logger.error("No classes found in database")
                MessageDisplay.show_error(
                    "Lỗi", "Không thể tải danh sách lớp từ cơ sở dữ liệu")
                return

            # Tìm lớp đã chọn trong danh sách
            selected_class = None
            for cls in classes:
                if cls['MALOP'] == selected_id:
                    selected_class = cls
                    break

            if not selected_class:
                logger.error(
                    f"Class with ID {selected_id} not found in database")
                MessageDisplay.show_error(
                    "Lỗi", "Không tìm thấy thông tin lớp")
                return

            # Populate form với dữ liệu
            logger.info(f"Populating form with class data: {selected_class}")

            # Chuẩn bị dữ liệu cho form
            form_data = {
                'MALOP': selected_class.get('MALOP', ''),
                'TENLOP': selected_class.get('TENLOP', ''),
                'MANV': selected_class.get('MANV', employee_id or '')
            }

            # Đặt form vào chế độ chỉnh sửa
            self.class_form.enter_edit_mode(selected_id, form_data)

            # Đặt mã lớp thành readonly trong chế độ chỉnh sửa
            if 'MALOP' in self.class_form.fields:
                self.class_form.fields['MALOP'].entry.config(state='readonly')

            # Hiển thị form
            self._show_form()

        except Exception as e:
            logger.error(f"Error when preparing edit form: {e}")
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(
                f"Database error when loading class details: {str(e)}")

    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected_id = self.classes_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để xóa")
            return

        # Xác nhận xóa
        if not MessageDisplay.ask_yes_no("Xác Nhận", "Bạn có chắc chắn muốn xóa lớp này?"):
            return

        try:
            logger.info(f"Deleting class with ID: {selected_id}")
            # Sử dụng SP_DEL_LOP để xóa lớp
            success = self.db.delete_class(selected_id)

            if success:
                logger.info(f"Successfully deleted class: {selected_id}")
                MessageDisplay.show_info("Thành Công", "Xóa lớp thành công")
                # Tải lại danh sách lớp sau khi xóa
                self._load_class_list()
            else:
                logger.error(f"Failed to delete class: {selected_id}")
                MessageDisplay.show_error("Lỗi", "Không thể xóa lớp")

        except Exception as e:
            logger.error(f"Error when deleting class {selected_id}: {e}")
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when deleting class: {str(e)}")

    def _on_form_saved(self):
        """Handle form saved event."""
        logger.info("Form saved successfully, updating UI")
        # Khôi phục lại tiêu đề gốc
        self.form_title.configure(text="Thông Tin Lớp")
        # Tải lại danh sách lớp sau khi lưu
        self._load_class_list()
        # Ẩn form
        self._hide_form()
        # Đảm bảo form được reset về trạng thái ban đầu
        self.class_form.enter_create_mode()

    def _on_form_cancelled(self):
        """Handle form cancel event."""
        logger.info("Form cancelled by user")
        # Khôi phục lại tiêu đề gốc
        self.form_title.configure(text="Thông Tin Lớp")
        # Ẩn form
        self._hide_form()
        # Đảm bảo form được reset về trạng thái ban đầu
        self.class_form.enter_create_mode()
