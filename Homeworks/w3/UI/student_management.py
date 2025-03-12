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
        self.employee_session = EmployeeSession()

        # Store class ID
        self.class_id = class_id

        # Callbacks
        self.on_save = on_save
        self.on_cancel = on_cancel

        # Create form fields
        self._create_fields()

        # Add buttons
        self.create_buttons(self.save, self.cancel)

        # Initially disable fields until add/edit is clicked
        self.set_fields_state("disabled")

    def _create_fields(self):
        """Create the form fields."""
        # Student ID field
        self.add_field('MASV', TextField(
            self, "Mã Sinh Viên *", 1, required=True))

        # Student name field
        self.add_field('HOTEN', TextField(self, "Họ Tên *", 2, required=True))

        # Birth date field
        self.add_field('NGAYSINH', DateField(
            self, "Ngày Sinh *", 3, required=True))

        # Address field
        self.add_field('DIACHI', TextField(self, "Địa Chỉ", 4))

        # Class ID field
        # If class ID is provided, set it as fixed value
        if self.class_id:
            self.add_field('MALOP', TextField(
                self, "Mã Lớp *", 5, required=True, readonly=True))
            self.fields['MALOP'].set_value(self.class_id)
        else:
            # Otherwise, get available classes for the employee
            class_values = self._get_class_values()
            self.add_field('MALOP', ComboBoxField(
                self, "Lớp *", 5, class_values, required=True))

        # Username field (only for new students)
        self.add_field('TENDN', TextField(
            self, "Tên Đăng Nhập *", 6, required=True))

        # Password field (only for new students)
        self.add_field('MATKHAU', TextField(
            self, "Mật Khẩu *", 7, required=True))

    def _get_class_values(self):
        """Get available classes for dropdown."""
        try:
            # Get classes managed by the current employee
            employee_id = self.employee_session.employee_id
            classes = self.db.get_classes_by_employee(employee_id) or []

            # Format for combobox: (display_text, value)
            return [(f"{cls['TENLOP']} ({cls['MALOP']})", cls['MALOP']) for cls in classes]
        except Exception as e:
            logger.error(f"Error loading classes: {str(e)}")
            return []

    def set_fields_state(self, state: str):
        """Enable or disable all fields."""
        for field_id, field in self.fields.items():
            if hasattr(field, "entry"):
                field.entry.configure(state=state)
            elif hasattr(field, "combobox"):
                field.combobox.configure(state=state)

    def enter_edit_mode(self, item_id: str, data: Dict[str, Any]):
        """Enter edit mode with student data."""
        super().enter_edit_mode(item_id, data)

        # Make student ID read-only in edit mode
        if 'MASV' in self.fields:
            self.fields['MASV'].entry.config(state='readonly')
            # Add a note that this field cannot be changed
            self.fields['MASV'].label.config(
                text="Mã Sinh Viên * (không thể thay đổi)")

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
        if 'MASV' in self.fields:
            self.fields['MASV'].entry.config(state='normal')
            self.fields['MASV'].label.config(text="Mã Sinh Viên *")

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
            # Format date properly for SQL Server
            ngaysinh = data['NGAYSINH']
            if ngaysinh and isinstance(ngaysinh, str):
                # Convert from YYYY-MM-DD to SQL Server compatible datetime format
                try:
                    # Parse the date string and format it as SQL Server expects
                    date_obj = datetime.strptime(ngaysinh, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    data['NGAYSINH'] = formatted_date
                except ValueError as e:
                    logger.error(f"Date format error: {e}")
                    MessageDisplay.show_error(
                        "Lỗi", f"Định dạng ngày không hợp lệ: {ngaysinh}. Vui lòng sử dụng định dạng YYYY-MM-DD.")
                    return

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
                    if self.on_save:
                        self.on_save()
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
                    if self.on_save:
                        self.on_save()
                else:
                    MessageDisplay.show_error(
                        "Lỗi", "Không thể thêm sinh viên mới")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when saving student: {str(e)}")

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        super().cancel()
        if self.on_cancel:
            self.on_cancel()


class StudentListScreen(ttk.Frame):
    """Screen for displaying and managing students in a class."""

    def __init__(self, master, class_id: str):
        super().__init__(master)

        # Store class ID
        self.class_id = class_id

        # Database connection
        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()

        # Check if the employee has permission to manage this class
        self.has_permission = self._check_permissions()

        # Create main container with padding
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure grid layout
        self.main_container.columnconfigure(0, weight=1)  # List side
        self.main_container.columnconfigure(1, weight=0)  # Separator
        self.main_container.columnconfigure(2, weight=1)  # Form side
        self.main_container.rowconfigure(0, weight=1)     # Content row

        # Create UI components
        self._create_widgets()

        # Refresh data initially
        self.refresh_data()

        # Show list initially
        self.show_list()

    def _check_permissions(self):
        """Check if the current employee can manage this class."""
        employee_id = self.employee_session.employee_id
        if not employee_id or not self.class_id:
            return False
        return self.db.check_employee_manages_class(employee_id, self.class_id)

    def _create_widgets(self):
        """Create the main UI components."""
        # Left side - student list
        self.list_frame = ttk.Frame(self.main_container)
        self.list_frame.grid(row=0, column=0, sticky='nsew')

        # Add list title with class info
        try:
            # Get class information
            classes = self.db.get_classes()
            class_info = None
            if classes:
                for cls in classes:
                    if cls['MALOP'] == self.class_id:
                        class_info = cls
                        break

            title_text = f"Danh Sách Sinh Viên - Lớp: {class_info['TENLOP'] if class_info else self.class_id}"
        except Exception as e:
            logger.error(f"Error getting class info: {e}")
            title_text = f"Danh Sách Sinh Viên - Lớp: {self.class_id}"

        self.list_title = ttk.Label(self.list_frame, text=title_text,
                                    font=('Arial', 12, 'bold'))
        self.list_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create student table with columns
        student_columns = [
            {'id': 'MASV', 'text': 'Mã SV', 'width': 100},
            {'id': 'HOTEN', 'text': 'Họ Tên', 'width': 200},
            {'id': 'NGAYSINH', 'text': 'Ngày Sinh', 'width': 100},
            {'id': 'DIACHI', 'text': 'Địa Chỉ', 'width': 200}
        ]

        self.students_table = DataTable(
            self.list_frame,
            columns=student_columns,
            on_select=self._on_student_selected
        )

        # Configure table buttons based on permissions
        self.students_table.add_button.configure(
            command=self._on_add_clicked,
            state='normal' if self.has_permission else 'disabled')

        self.students_table.edit_button.configure(
            command=self._on_edit_clicked,
            state='disabled')  # Initially disabled until selection

        self.students_table.delete_button.configure(
            command=self._on_delete_clicked,
            state='disabled')  # Initially disabled until selection

        self.students_table.refresh_button.configure(
            command=self.refresh_data)

        # Add separator
        self.separator = ttk.Separator(self.main_container, orient='vertical')
        self.separator.grid(row=0, column=1, sticky='ns', padx=10)

        # Right side - student form
        self.form_frame = ttk.Frame(self.main_container)
        self.form_frame.grid(row=0, column=2, sticky='nsew')

        # Add form title
        self.form_title = ttk.Label(self.form_frame, text="Thông Tin Sinh Viên",
                                    font=('Arial', 12, 'bold'))
        self.form_title.pack(anchor='w', padx=5, pady=(0, 10))

        # Create student form
        self.student_form = StudentForm(
            self.form_frame,
            on_save=self._on_form_saved,
            on_cancel=self._on_form_cancelled,
            class_id=self.class_id
        )
        self.student_form.pack(fill=tk.BOTH, expand=True)

        # Add a help text for teachers
        if self.has_permission:
            help_frame = ttk.Frame(self.list_frame)
            help_frame.pack(fill=tk.X, pady=10)

            help_text = ttk.Label(help_frame,
                                  text="Hướng dẫn: Nhấn 'Thêm' để thêm sinh viên mới, chọn sinh viên và nhấn 'Sửa' để chỉnh sửa thông tin.",
                                  font=('Arial', 9), foreground='#555555')
            help_text.pack(anchor='w')

    def show_list(self):
        """Show the list view, hide the form."""
        self.refresh_data()
        # No need to adjust layout as both frames are in grid

    def show_form(self):
        """Show the form view, hide the list."""
        # No need to adjust layout as both frames are in grid
        # Just enable form fields
        self.student_form.set_fields_state("normal")

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
                        # Handle different datetime formats
                        if isinstance(ngaysinh, datetime):
                            ngaysinh = ngaysinh.strftime('%Y-%m-%d')
                        elif isinstance(ngaysinh, str):
                            # Try to parse the date string if it's not in the expected format
                            try:
                                # If it's already in YYYY-MM-DD format, keep it
                                if len(ngaysinh) == 10 and ngaysinh[4] == '-' and ngaysinh[7] == '-':
                                    pass
                                else:
                                    # Try to parse with different formats
                                    try:
                                        # Try SQL Server datetime format
                                        date_obj = datetime.strptime(
                                            ngaysinh, '%Y-%m-%d %H:%M:%S')
                                        ngaysinh = date_obj.strftime(
                                            '%Y-%m-%d')
                                    except ValueError:
                                        # Try other common formats
                                        try:
                                            from dateutil import parser
                                            date_obj = parser.parse(ngaysinh)
                                            ngaysinh = date_obj.strftime(
                                                '%Y-%m-%d')
                                        except:
                                            # If all parsing fails, keep original
                                            logger.warning(
                                                f"Could not parse date: {ngaysinh}")
                            except Exception as e:
                                logger.error(f"Error formatting date: {e}")

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
                self.students_table.load_data(table_data)
                logger.info(
                    f"Loaded {len(table_data)} students for class {self.class_id}")
            else:
                # Display a message in the table instead of a popup
                self.students_table.clear_data()  # Clear existing data
                self.students_table.show_message(
                    "Lớp này chưa có sinh viên nào")
                logger.info(f"No students found for class {self.class_id}")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading students: {str(e)}")

    def _on_student_selected(self, student_id):
        """Handle student selection in the table."""
        # Enable edit and delete buttons if has permission
        if self.has_permission:
            self.students_table.edit_button.config(state='normal')
            self.students_table.delete_button.config(state='normal')

    def _on_add_clicked(self):
        """Handle add button click."""
        if not self.has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền thêm sinh viên cho lớp này")
            return

        # Update form title
        self.form_title.configure(text="Thêm Sinh Viên Mới")

        # Show the form in create mode
        self.student_form.enter_create_mode()
        self.show_form()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        if not self.has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền chỉnh sửa sinh viên của lớp này")
            return

        selected_id = self.students_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một sinh viên để chỉnh sửa")
            return

        try:
            # Update form title
            self.form_title.configure(text="Chỉnh Sửa Thông Tin Sinh Viên")

            # Get student by ID (more efficient than getting all students)
            selected_student = self.db.get_student_by_id(selected_id)

            if selected_student:
                # Format date
                ngaysinh = selected_student.get('NGAYSINH', None)
                if ngaysinh:
                    # Handle different datetime formats
                    if isinstance(ngaysinh, datetime):
                        ngaysinh = ngaysinh.strftime('%Y-%m-%d')
                    elif isinstance(ngaysinh, str):
                        # Try to parse the date string if it's not in the expected format
                        try:
                            # If it's already in YYYY-MM-DD format, keep it
                            if len(ngaysinh) == 10 and ngaysinh[4] == '-' and ngaysinh[7] == '-':
                                pass
                            else:
                                # Try to parse with different formats
                                try:
                                    # Try SQL Server datetime format
                                    date_obj = datetime.strptime(
                                        ngaysinh, '%Y-%m-%d %H:%M:%S')
                                    ngaysinh = date_obj.strftime('%Y-%m-%d')
                                except ValueError:
                                    # Try other common formats
                                    try:
                                        from dateutil import parser
                                        date_obj = parser.parse(ngaysinh)
                                        ngaysinh = date_obj.strftime(
                                            '%Y-%m-%d')
                                    except:
                                        # If all parsing fails, keep original
                                        logger.warning(
                                            f"Could not parse date: {ngaysinh}")
                        except Exception as e:
                            logger.error(f"Error formatting date: {e}")

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

        selected_id = self.students_table.get_selected_item()
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
        # Reset form title
        self.form_title.configure(text="Thông Tin Sinh Viên")

        # Refresh the list and show it
        self.refresh_data()
        self.show_list()

    def _on_form_cancelled(self):
        """Handle form cancel event."""
        # Reset form title
        self.form_title.configure(text="Thông Tin Sinh Viên")

        # Just show the list again
        self.show_list()


class StudentManagementScreen(ttk.Frame):
    """Main student management screen with tabbed interface for classes and students."""

    def __init__(self, master):
        super().__init__(master)

        # Database connection
        self.db = DatabaseConnector()
        self.employee_session = EmployeeSession()

        # State tracking
        self.current_view = None  # Can be 'classes' or 'students'
        self.current_class_id = None
        self.student_list_screen = None

        # Create main container with padding
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a header with title and back button
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        self.title_label = ttk.Label(
            self.header_frame, text="Quản lý Sinh Viên", font=('Arial', 14, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        self.back_button = ttk.Button(
            self.header_frame, text="← Quay lại", command=self.show_classes_view)
        self.back_button.pack(side=tk.RIGHT)
        self.back_button.pack_forget()  # Initially hidden

        # Create content frame for both views
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create classes view
        self._create_classes_view()

        # Show classes view initially
        self.show_classes_view()

    def _create_classes_view(self):
        """Create the classes list view."""
        # Create a label for the list
        list_label = ttk.Label(
            self.content_frame, text="Danh Sách Lớp Học", font=('Helvetica', 12, 'bold'))
        list_label.pack(anchor='w', pady=(0, 10))

        # Add description text
        description = ttk.Label(
            self.content_frame,
            text="Chọn một lớp học để quản lý sinh viên. Bạn chỉ có thể quản lý sinh viên trong các lớp mà bạn phụ trách.",
            font=('Arial', 10))
        description.pack(anchor='w', pady=(0, 15))

        # Create class table
        columns = [
            {'id': 'MALOP', 'text': 'Mã Lớp', 'width': 100},
            {'id': 'TENLOP', 'text': 'Tên Lớp', 'width': 250},
            {'id': 'TENNV', 'text': 'Nhân Viên Quản Lý', 'width': 200}
        ]

        self.class_table = DataTable(
            self.content_frame, columns, on_select=None)

        # Hide CRUD buttons, keep only refresh
        self.class_table.add_button.pack_forget()
        self.class_table.edit_button.pack_forget()
        self.class_table.delete_button.pack_forget()

        # Add view students button
        self.view_button = ttk.Button(self.class_table.frame, text="Xem Sinh Viên",
                                      width=15, command=self._on_view_students_clicked)
        self.view_button.pack(side=tk.LEFT, padx=5)
        self.view_button.config(state='disabled')  # Initially disabled

        # Configure refresh button
        self.class_table.refresh_button.configure(command=self.refresh_classes)

        # Configure selection event
        self.class_table.bind(
            "<<TreeviewSelect>>", self._on_class_selected)

        # Double-click to view students
        self.class_table.bind(
            "<Double-1>", self._on_double_click)

        # Load classes
        self.refresh_classes()

    def _on_class_selected(self, event):
        """Handle class selection in the table."""
        selected_id = self.class_table.get_selected_item()
        if selected_id:
            self.view_button.config(state='normal')
        else:
            self.view_button.config(state='disabled')

    def _on_double_click(self, event):
        """Handle double-click event on class table."""
        self._on_view_students_clicked()

    def refresh_classes(self):
        """Refresh the class list."""
        try:
            # Get classes for the current employee
            employee_id = self.employee_session.employee_id
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
                logger.info(
                    f"Loaded {len(table_data)} classes for employee {employee_id}")
            else:
                # Display a message in the table
                self.class_table.clear_data()
                self.class_table.show_message("Bạn không phụ trách lớp nào")
                logger.info(f"No classes found for employee {employee_id}")

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

        # Store the current class ID
        self.current_class_id = selected_id

        # Clear the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create student list screen for the selected class
        self.student_list = StudentListScreen(self.content_frame, selected_id)
        self.student_list.pack(fill=tk.BOTH, expand=True)

        # Update UI for student view
        self.current_view = 'students'
        self.title_label.config(text=f"Quản lý Sinh Viên - Lớp: {selected_id}")
        self.back_button.pack(side=tk.RIGHT)  # Show back button

    def show_classes_view(self):
        """Show the classes view."""
        # Update state
        self.current_view = 'classes'
        self.current_class_id = None

        # Update title
        self.title_label.config(text="Quản lý Sinh Viên")

        # Hide back button
        self.back_button.pack_forget()

        # Clear the content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Recreate classes view
        self._create_classes_view()
