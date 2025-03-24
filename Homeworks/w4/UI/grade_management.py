import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Optional, Tuple

from db_connector import DatabaseConnector
from session import EmployeeSession
from ui_components import Form, TextField, ComboBoxField, DataTable, MessageDisplay
from crypto_utils import CryptoManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('grade_management')


class GradeForm(Form):
    """Form for entering and editing grades."""

    def __init__(self, master, on_save: callable, on_cancel: callable, class_id: str):
        super().__init__(master, "Nhập Điểm Sinh Viên")

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.employee_session = EmployeeSession()

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
        # Student field (dropdown)
        student_values = self._get_student_values()
        self.add_field('MASV', ComboBoxField(
            self, "Sinh Viên", 1, student_values, required=True))

        # Course field (dropdown)
        course_values = self._get_course_values()
        self.add_field('MAHP', ComboBoxField(
            self, "Học Phần", 2, course_values, required=True))

        # Grade field
        def grade_validator(value):
            try:
                grade = float(value)
                if grade < 0 or grade > 10:
                    return False, "Điểm phải từ 0 đến 10"
                return True, ""
            except:
                return False, "Điểm phải là số"

        self.add_field('DIEMTHI', TextField(self, "Điểm Thi", 3,
                       required=True, validator=grade_validator))

    def _get_student_values(self):
        """Get students for dropdown."""
        try:
            # Get students in this class
            students = self.db.get_students_by_class(self.class_id) or []

            # Format for combobox: (display_text, value)
            return [(f"{s['HOTEN']} ({s['MASV']})", s['MASV']) for s in students]
        except Exception as e:
            logger.error(f"Error loading students: {str(e)}")
            return []

    def _get_course_values(self):
        """Get courses for dropdown."""
        try:
            # Execute a query to get courses
            query = "SELECT MAHP, TENHP FROM HOCPHAN"
            courses = self.db.execute_query(query) or []

            # Format for combobox: (display_text, value)
            return [(f"{c['TENHP']} ({c['MAHP']})", c['MAHP']) for c in courses]
        except Exception as e:
            logger.error(f"Error loading courses: {str(e)}")
            return []

    def save(self):
        """Save the grade data with client-side encryption."""
        # Validate form
        if not self.validate():
            return

        # Get form data
        data = self.get_data()

        try:
            # Get the employee ID for encryption
            manv = self.employee_session.employee_id
            if not manv:
                MessageDisplay.show_error(
                    "Lỗi", "Không tìm thấy thông tin nhân viên đăng nhập")
                return

            # Convert grade to float
            diemthi = float(data['DIEMTHI'])

            # Get the employee session
            employee_data = self.employee_session.employee_data

            # Check if we have the public key
            if not employee_data or 'PUBKEY' not in employee_data:
                MessageDisplay.show_error(
                    "Lỗi", "Không tìm thấy khóa công khai của nhân viên")
                return

            # Create crypto manager
            crypto_mgr = CryptoManager()

            # Encrypt the grade using the employee's public key
            encrypted_grade = crypto_mgr.encrypt_data(
                employee_data['PUBKEY'],
                str(diemthi)
            )

            # Encode the encrypted grade for database storage
            encoded_grade = crypto_mgr.encode_for_db(encrypted_grade)

            if self.is_edit_mode:
                # Update grade with client-side encryption
                success = self.db.update_grade_with_client_encryption(
                    data['MASV'], data['MAHP'], encoded_grade, manv)
                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Cập nhật điểm thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error("Lỗi", "Không thể cập nhật điểm")
            else:
                # Add new grade with client-side encryption
                success = self.db.add_grade_with_client_encryption(
                    data['MASV'], data['MAHP'], encoded_grade, manv)
                if success:
                    MessageDisplay.show_info(
                        "Thành Công", "Thêm điểm mới thành công")
                    if self.on_save_callback:
                        self.on_save_callback()
                else:
                    MessageDisplay.show_error("Lỗi", "Không thể thêm điểm mới")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when saving grade: {str(e)}")

    def cancel(self):
        """Cancel the form and call the cancel callback."""
        super().cancel()
        if self.on_cancel_callback:
            self.on_cancel_callback()


class GradeManagementScreen(ttk.Frame):
    """Grade management screen with list and entry form."""

    def __init__(self, master):
        super().__init__(master)

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.employee_session = EmployeeSession()

        # Create main container with padding
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a header with title and back button
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        self.title_label = ttk.Label(
            self.header_frame, text="Quản lý Điểm", font=('Arial', 14, 'bold'))
        self.title_label.pack(side=tk.LEFT)

        self.back_button = ttk.Button(
            self.header_frame, text="Quay lại", command=self.show_classes_view)
        self.back_button.pack(side=tk.RIGHT)
        self.back_button.pack_forget()  # Initially hidden

        # Create content frame for both views
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create the classes view
        self._create_classes_view()

        # Show classes view initially
        self.show_classes_view()

    def _create_classes_view(self):
        """Create the classes list view."""
        # Create a label for the list
        list_label = ttk.Label(
            self.content_frame, text="Lớp Học", font=('Helvetica', 14, 'bold'))
        list_label.pack(anchor='w', pady=(0, 10))

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

        # Add view grades button
        view_button = ttk.Button(self.class_table.frame, text="Quản Lý Điểm",
                                 width=15, command=self._on_view_grades_clicked)
        view_button.pack(side=tk.LEFT, padx=5)

        # Configure refresh button
        self.class_table.refresh_button.configure(command=self.refresh_classes)

        # Double-click to view grades
        self.class_table.bind(
            "<Double-1>", lambda event: self._on_view_grades_clicked())

        # Load classes
        self.refresh_classes()

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

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading classes: {str(e)}")

    def _on_view_grades_clicked(self):
        """Handle view grades button click."""
        selected_id = self.class_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một lớp để quản lý điểm")
            return

        # Check if employee can manage this class
        employee_id = self.employee_session.employee_id
        has_permission = self.db.check_employee_manages_class(
            employee_id, selected_id)

        if not has_permission:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Bạn không có quyền quản lý điểm cho lớp này")
            return

        # Create grade screen for the selected class
        self._create_grades_view(selected_id)

        # Show grades view
        self.show_grades_view()

    def _create_grades_view(self, class_id):
        """Create the grades view for a class."""
        # Clear any existing widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Create back button
        back_button = ttk.Button(self.content_frame, text="Quay Lại Danh Sách Lớp",
                                 command=self.show_classes_view)
        back_button.pack(anchor='w', padx=10, pady=10)

        # Get class info
        class_info = "Unknown Class"
        classes = self.db.get_classes()
        if classes:
            for cls in classes:
                if cls['MALOP'] == class_id:
                    class_info = f"Quản Lý Điểm - Lớp: {cls['TENLOP']} ({cls['MALOP']})"
                    break

        # Create title
        title_label = ttk.Label(
            self.content_frame, text=class_info, font=('Helvetica', 14, 'bold'))
        title_label.pack(anchor='w', padx=10, pady=(0, 10))

        # Create container for grades list and form
        content_frame = ttk.Frame(self.content_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Split into left and right panes
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=5, pady=5)

        form_frame = ttk.Frame(content_frame)
        form_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                        expand=True, padx=5, pady=5)

        # Create grades table
        columns = [
            {'id': 'MASV', 'text': 'Mã SV', 'width': 80},
            {'id': 'TENSV', 'text': 'Tên Sinh Viên', 'width': 150},
            {'id': 'MAHP', 'text': 'Mã HP', 'width': 80},
            {'id': 'TENHP', 'text': 'Tên Học Phần', 'width': 150},
            {'id': 'DIEMTHI', 'text': 'Điểm Thi', 'width': 80}
        ]

        grades_label = ttk.Label(
            list_frame, text="Danh Sách Điểm", font=('Helvetica', 12, 'bold'))
        grades_label.pack(anchor='w', pady=(0, 10))

        self.grades_table = DataTable(
            list_frame, columns, on_select=self._on_grade_selected)

        # Configure button commands
        self.grades_table.add_button.configure(
            command=lambda: self._on_add_grade_clicked(class_id))
        self.grades_table.edit_button.configure(
            command=self._on_edit_grade_clicked)
        self.grades_table.delete_button.pack_forget()  # Hide delete button
        self.grades_table.refresh_button.configure(
            command=lambda: self.refresh_grades(class_id))

        # Create grade form
        self.grade_form = GradeForm(
            form_frame,
            lambda: self.refresh_grades(class_id),
            lambda: self.hide_grade_form(),
            class_id=class_id
        )

        # Hide form initially
        self.grade_form.pack_forget()

        # Load grades
        self.refresh_grades(class_id)

    def show_classes_view(self):
        """Show the classes view."""
        # Instead of destroying all widgets, which might affect other screens,
        # just hide the current content frame and recreate our own classes view

        # First hide the current content frame
        self.content_frame.pack_forget()

        # Create a new content frame
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Recreate the classes view in the new frame
        self._create_classes_view()

        # Refresh the class data
        self.refresh_classes()

    def show_grades_view(self):
        """Show the grades view."""
        self.content_frame.pack_forget()
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def show_grade_form(self):
        """Show the grade form."""
        self.grade_form.pack(fill=tk.BOTH, expand=True)

    def hide_grade_form(self):
        """Hide the grade form."""
        self.grade_form.pack_forget()

    def refresh_grades(self, class_id):
        """Refresh the grade list for a class with client-side decryption."""
        try:
            # Get grades for this class with encrypted data
            grades = self.db.get_grades_with_client_encryption(class_id)

            # Transform data for the table
            table_data = []
            if grades:
                for grade in grades:
                    # Try to decrypt the grade if we have the private key
                    diemthi_display = "***"  # Default to hidden

                    if 'ENCRYPTED_DIEMTHI' in grade and grade['ENCRYPTED_DIEMTHI']:
                        try:
                            # Check if we have the private key loaded
                            if self.employee_session.private_key:
                                # Decrypt the grade
                                decrypted_grade = self.employee_session.decrypt_data(
                                    grade['ENCRYPTED_DIEMTHI']
                                )
                                if decrypted_grade:
                                    diemthi_display = float(decrypted_grade)
                        except Exception as e:
                            logger.error(f"Error decrypting grade: {e}")

                    table_data.append({
                        # Composite key
                        'id': f"{grade['MASV']}_{grade['MAHP']}",
                        'MASV': grade['MASV'],
                        'TENSV': grade['TENSV'],
                        'MAHP': grade['MAHP'],
                        'TENHP': grade['TENHP'],
                        'DIEMTHI': diemthi_display
                    })

                # Load data into table
                self.grades_table.load_data(table_data)

            else:
                # No grades found
                self.grades_table.clear_data()
                self.grades_table.show_message(
                    "Không có điểm nào được tìm thấy")

        except Exception as e:
            MessageDisplay.show_error("Lỗi Cơ Sở Dữ Liệu", str(e))
            logger.error(f"Database error when loading grades: {str(e)}")

    def _on_grade_selected(self, grade_id):
        """Handle grade selection in the table."""
        # Enable edit button
        self.grades_table.edit_button.config(state='normal')

    def _on_add_grade_clicked(self, class_id):
        """Handle add grade button click."""
        # Show the form in create mode
        self.grade_form.enter_create_mode()
        self.show_grade_form()

    def _on_edit_grade_clicked(self):
        """Handle edit grade button click."""
        selected_id = self.grades_table.get_selected_item()
        if not selected_id:
            MessageDisplay.show_warning(
                "Cảnh Báo", "Vui lòng chọn một điểm để chỉnh sửa")
            return

        try:
            # Split the composite key
            masv, mahp = selected_id.split('_')

            # Get the selected row data
            selection = self.grades_table.selection()
            if selection:
                item = self.grades_table.item(selection[0])
                values = item['values']

                # Get column indices
                columns = self.grades_table['columns']
                idx_masv = columns.index('MASV')
                idx_mahp = columns.index('MAHP')
                idx_diemthi = columns.index('DIEMTHI')

                # Get values from the selected row
                masv = values[idx_masv]
                mahp = values[idx_mahp]
                diemthi = values[idx_diemthi]

                # Populate form with grade data
                self.grade_form.enter_edit_mode(selected_id, {
                    'MASV': masv,
                    'MAHP': mahp,
                    'DIEMTHI': diemthi
                })

                # Make student and course fields read-only in edit mode
                self.grade_form.fields['MASV'].combobox.config(
                    state='disabled')
                self.grade_form.fields['MAHP'].combobox.config(
                    state='disabled')

                # Show the form
                self.show_grade_form()

        except Exception as e:
            MessageDisplay.show_error(
                "Lỗi", f"Không thể tải thông tin điểm: {str(e)}")
            logger.error(f"Error loading grade details: {str(e)}")
