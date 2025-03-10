import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from db_connector import DatabaseConnector
from session import EmployeeSession
from ui_components import Form, TextField, DateField, ComboBoxField, DataTable, MessageDisplay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('student_management')


class StudentForm(Form):
    """Form for creating and editing student information."""

    def __init__(self, master, on_save: callable, on_cancel: callable, class_id: Optional[str] = None):
        super().__init__(master, "Thông Tin Sinh Viên")

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Store class ID
        self.class_id = class_id

        # Callbacks
        self.on_save_callback = on_save
        self.on_cancel_callback = on_cancel

        # Create form fields
        self._create_fields()
        self.create_buttons(self.save, self.cancel)

    def _create_fields(self):
        """Create the form fields."""
        # Student ID field
        self.add_field('MASV', TextField(
            self, "Mã Sinh Viên", 1, required=True))

        # Student name field
        self.add_field('HOTEN', TextField(self, "Họ Tên", 2, required=True))

        # Birth date field
        self.add_field('NGAYSINH', DateField(
            self, "Ngày Sinh", 3, required=True))

        # Address field
        self.add_field('DIACHI', TextField(self, "Địa Chỉ", 4))

        # Class ID field
        # If class ID is provided, set it as fixed value
        if self.class_id:
            self.add_field('MALOP', TextField(
                self, "Mã Lớp", 5, required=True, readonly=True))
            self.fields['MALOP'].set_value(self.class_id)
        else:
            # Otherwise, get available classes for the employee
            class_values = self._get_class_values()
            self.add_field('MALOP', ComboBoxField(
                self, "Lớp", 5, class_values, required=True))

        # Username field (only for new students)
        self.add_field('TENDN', TextField(
            self, "Tên Đăng Nhập", 6, required=True))

        # Password field (only for new students)
        self.add_field('MATKHAU', TextField(
            self, "Mật Khẩu", 7, required=True))

    def _get_class_values(self):
        """Get available classes for dropdown."""
        try:
            # Get classes managed by the current employee
            employee_id = self.session.employee_id
            classes = self.db.get_classes_by_employee(employee_id) or []

            # Format for combobox: (display_text, value)
            return [(f"{cls['TENLOP']} ({cls['MALOP']})", cls['MALOP']) for cls in classes]
        except Exception as e:
            logger.error(f"Error loading classes: {str(e)}")
            return []

    def enter_edit_mode(self, item_id: str, data: Dict[str, Any]):
        """Enter edit mode with student data."""
        super().enter_edit_mode(item_id, data)

        # Make student ID read-only in edit mode
        self.fields['MASV'].entry.config(state='readonly')

        # Hide username and password fields in edit mode
        if 'TENDN' in self.fields:
            self.fields['TENDN'].label.grid_remove()
            self.fields['TENDN'].entry.grid_remove()
            self.fields['TENDN'].error_label.grid_remove()

        if 'MATKHAU' in self.fields:
            self.fields['MATKHAU'].label.grid_remove()
            self.fields['MATKHAU'].entry.grid_remove()
            self.fields['MATKHAU'].error_label.grid_remove()

    def enter_create_mode(self):
        """Enter create mode for a new student."""
        super().enter_create_mode()

        # Make student ID editable in create mode
        self.fields['MASV'].entry.config(state='normal')

        # Show username and password fields in create mode
        if 'TENDN' in self.fields:
            self.fields['TENDN'].label.grid()
            self.fields['TENDN'].entry.grid()
            self.fields['TENDN'].error_label.grid()

        if 'MATKHAU' in self.fields:
            self.fields['MATKHAU'].label.grid()
            self.fields['MATKHAU'].entry.grid()
            self.fields['MATKHAU'].error_label.grid()

    def save(self):
        """Save the student data."""
        # Validate form
        if not self.validate():
            return

        # Get form data
        data = self.get_data()

        try:
            if self.is_edit_mode:
                # Update existing student (no credentials)
                success = self.db.update_student(
                    data['MASV'],
                    data['HOTEN'],
                    data['NGAYSINH'],
                    data['DIACHI'],
                    data['MALOP']
                )

                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Cập nhật thông tin sinh viên thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error(
                        "Lỗi", "Không thể cập nhật thông tin sinh viên")
            else:
                # Add new student (with credentials)
                success = self.db.add_student(
                    data['MASV'],
                    data['HOTEN'],
                    data['NGAYSINH'],
                    data['DIACHI'],
                    data['MALOP'],
                    data['TENDN'],
                    data['MATKHAU']
                )

                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Thêm sinh viên mới thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error(
                        "Lỗi", "Không thể thêm sinh viên mới")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when saving student: {str(e)}")

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        super().cancel()
        if self.on_cancel_callback:
            self.on_cancel_callback()


class StudentListScreen(ttk.Frame):
    """Student list for a specific class."""

    def __init__(self, master, class_id: str):
        super().__init__(master)
        self.master = master
        self.class_id = class_id

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Check permissions
        self._check_permissions()

        # Split the screen into list and form areas
        self._create_widgets()

        # Show the student list initially
        self.show_list()

        # Load data
        self.refresh_data()

    def _check_permissions(self):
        """Check if the current employee can manage this class."""
        employee_id = self.session.employee_id
        self.has_permission = self.db.check_employee_manages_class(
            employee_id, self.class_id)

    def _create_widgets(self):
        """Create the screen widgets."""
        # Create main container with two frames
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame for list
        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                             expand=True, padx=5, pady=5)

        # Get class info
        class_info = "Unknown Class"
        classes = self.db.get_classes()
        if classes:
            for cls in classes:
                if cls['MALOP'] == self.class_id:
                    class_info = f"Danh Sách Sinh Viên - Lớp: {cls['TENLOP']} ({cls['MALOP']})"
                    break

        # Create a label for the list
        list_label = ttk.Label(
            self.list_frame, text=class_info, font=('Helvetica', 14, 'bold'))
        list_label.pack(anchor='w', pady=(0, 10))

        # Create student table
        columns = [
            {'id': 'MASV', 'text': 'Mã SV', 'width': 100},
            {'id': 'HOTEN', 'text': 'Họ Tên', 'width': 200},
            {'id': 'NGAYSINH', 'text': 'Ngày Sinh', 'width': 100},
            {'id': 'DIACHI', 'text': 'Địa Chỉ', 'width': 200}
        ]

        self.student_table = DataTable(
            self.list_frame, columns, on_select=self._on_student_selected)

        # Configure button commands
        self.student_table.add_button.configure(command=self._on_add_clicked)
        self.student_table.edit_button.configure(command=self._on_edit_clicked)
        self.student_table.delete_button.configure(
            command=self._on_delete_clicked)
        self.student_table.refresh_button.configure(command=self.refresh_data)

        # Disable CRUD buttons if no permission
        if not self.has_permission:
            self.student_table.add_button.config(state='disabled')
            self.student_table.edit_button.config(state='disabled')
            self.student_table.delete_button.config(state='disabled')

        # Right frame for form
        self.form_frame = ttk.Frame(self.main_frame)
        self.form_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                             expand=True, padx=5, pady=5)

        # Create student form
        self.student_form = StudentForm(
            self.form_frame,
            self._on_form_saved,
            self._on_form_cancelled,
            class_id=self.class_id
        )
        self.student_form.pack(fill=tk.BOTH, expand=True)

    def show_list(self):
        """Show the student list and hide the form."""
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.form_frame.pack_forget()

    def show_form(self):
        """Show the form and hide the list."""
        self.form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def refresh_data(self):
        """Refresh the student list."""
        try:
            # Get students for this class
            students = self.db.get_students_by_class(self.class_id)

            # Transform data for the table
            table_data = []
            if students:
                for student in students:
                    # Format date
                    ngaysinh = student.get('NGAYSINH', None)
                    if ngaysinh:
                        if isinstance(ngaysinh, datetime):
                            ngaysinh = ngaysinh.strftime('%Y-%m-%d')

                    table_data.append({
                        'id': student['MASV'],  # Use student ID as row ID
                        'MASV': student['MASV'],
                        'HOTEN': student['HOTEN'],
                        'NGAYSINH': ngaysinh,
                        'DIACHI': student.get('DIACHI', ''),
                        'MALOP': student['MALOP'],
                        'TENDN': student.get('TENDN', '')
                    })

            # Load data into table
            self.student_table.load_data(table_data)

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading students: {str(e)}")

    def _on_student_selected(self, student_id):
        """Handle student selection in the table."""
        # Enable edit and delete buttons if has permission
        if self.has_permission:
            self.student_table.edit_button.config(state='normal')
            self.student_table.delete_button.config(state='normal')

    def _on_add_clicked(self):
        """Handle add button click."""
        if not self.has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền thêm sinh viên cho lớp này")
            return

        # Show the form in create mode
        self.student_form.enter_create_mode()
        self.show_form()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        if not self.has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền chỉnh sửa sinh viên của lớp này")
            return

        selected_id = self.student_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một sinh viên để chỉnh sửa")
            return

        try:
            # Get students for this class
            students = self.db.get_students_by_class(self.class_id)

            # Find the selected student
            selected_student = next(
                (s for s in students if s['MASV'] == selected_id), None)

            if selected_student:
                # Format date
                ngaysinh = selected_student.get('NGAYSINH', None)
                if ngaysinh and isinstance(ngaysinh, datetime):
                    ngaysinh = ngaysinh.strftime('%Y-%m-%d')

                # Populate form with student data
                self.student_form.enter_edit_mode(selected_id, {
                    'MASV': selected_student['MASV'],
                    'HOTEN': selected_student['HOTEN'],
                    'NGAYSINH': ngaysinh,
                    'DIACHI': selected_student.get('DIACHI', ''),
                    'MALOP': selected_student['MALOP']
                })

                # Show the form
                self.show_form()
            else:
                MessageDisplay.show_error(
                    "Lỗi", "Không tìm thấy thông tin sinh viên")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(
                f"Database error when loading student details: {str(e)}")

    def _on_delete_clicked(self):
        """Handle delete button click."""
        if not self.has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền xóa sinh viên của lớp này")
            return

        selected_id = self.student_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một sinh viên để xóa")
            return

        # Confirm deletion
        if not MessageDisplay.ask_yes_no("Xác Nhận", "Bạn có chắc chắn muốn xóa sinh viên này?"):
            return

        try:
            # Delete the student
            success = self.db.delete_student(selected_id)

            if success:
                MessageDisplay.show_info(
                    "Thành Công", "Xóa sinh viên thành công")
                self.refresh_data()
            else:
                MessageDisplay.show_error("Lỗi", "Không thể xóa sinh viên")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when deleting student: {str(e)}")

    def _on_form_saved(self):
        """Handle form save event."""
        # Refresh the list and show it
        self.refresh_data()
        self.show_list()

    def _on_form_cancelled(self):
        """Handle form cancel event."""
        # Just show the list again
        self.show_list()


class StudentManagementScreen(ttk.Frame):
    """Student management screen that shows classes first, then students."""

    def __init__(self, master):
        super().__init__(master)
        self.master = master

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create frames for each view
        self.classes_frame = ttk.Frame(self.main_frame)
        self.students_frame = ttk.Frame(self.main_frame)

        # Create the classes view
        self._create_classes_view()

        # Show classes view initially
        self.show_classes_view()

    def _create_classes_view(self):
        """Create the classes list view."""
        # Create a label for the list
        list_label = ttk.Label(
            self.classes_frame, text="Lớp Học", font=('Helvetica', 14, 'bold'))
        list_label.pack(anchor='w', pady=(0, 10))

        # Create class table
        columns = [
            {'id': 'MALOP', 'text': 'Mã Lớp', 'width': 100},
            {'id': 'TENLOP', 'text': 'Tên Lớp', 'width': 250},
            {'id': 'TENNV', 'text': 'Nhân Viên Quản Lý', 'width': 200}
        ]

        self.class_table = DataTable(
            self.classes_frame, columns, on_select=None)

        # Hide CRUD buttons, keep only refresh
        self.class_table.add_button.pack_forget()
        self.class_table.edit_button.pack_forget()
        self.class_table.delete_button.pack_forget()

        # Add view students button
        view_button = ttk.Button(self.class_table.frame, text="Xem Sinh Viên",
                                 width=15, command=self._on_view_students_clicked)
        view_button.pack(side=tk.LEFT, padx=5)

        # Configure refresh button
        self.class_table.refresh_button.configure(command=self.refresh_classes)

        # Double-click to view students
        self.class_table.bind(
            "<Double-1>", lambda event: self._on_view_students_clicked())

        # Load classes
        self.refresh_classes()

    def refresh_classes(self):
        """Refresh the class list."""
        try:
            # Get classes for the current employee
            employee_id = self.session.employee_id
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

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading classes: {str(e)}")

    def _on_view_students_clicked(self):
        """Handle view students button click."""
        selected_id = self.class_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để xem sinh viên")
            return

        # Create student list screen for the selected class
        self.student_list = StudentListScreen(self.students_frame, selected_id)
        self.student_list.pack(fill=tk.BOTH, expand=True)

        # Show students view
        self.show_students_view()

    def show_classes_view(self):
        """Show the classes view."""
        # Remove any existing widgets in the students frame
        for widget in self.students_frame.winfo_children():
            widget.destroy()

        # Hide students frame, show classes frame
        self.students_frame.pack_forget()
        self.classes_frame.pack(fill=tk.BOTH, expand=True)

    def show_students_view(self):
        """Show the students view."""
        # Hide classes frame, show students frame
        self.classes_frame.pack_forget()
        self.students_frame.pack(fill=tk.BOTH, expand=True)

        # Add back button
        back_button = ttk.Button(self.students_frame, text="← Quay Lại Danh Sách Lớp",
                                 command=self.show_classes_view)
        back_button.pack(anchor='w', padx=10, pady=10)
