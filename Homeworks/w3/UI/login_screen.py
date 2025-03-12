import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, Optional

from db_connector import DatabaseConnector
from session import EmployeeSession
from ui_components import MessageDisplay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('login_screen')


class LoginScreen(ttk.Frame):
    """Login screen for employee authentication."""

    def __init__(self, master, on_login_success: Optional[Callable] = None):
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success

        # Database connection
        self.db = DatabaseConnector()

        # Session manager
        self.employee_session = EmployeeSession()

        # Create the login form
        self._create_widgets()

        # Styling
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=('Arial', 18, 'bold'))
        self.style.configure("Error.TLabel", foreground='red')
        self.style.configure("Login.TButton", font=('Arial', 10, 'bold'))

    def _create_widgets(self):
        """Create and layout the login form widgets."""
        # Main container with padding and border
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # Center login frame
        self.login_frame = ttk.Frame(
            self.main_container, padding=20, relief="ridge", borderwidth=1)
        self.login_frame.place(
            relx=0.5, rely=0.5, anchor="center", width=400, height=350)

        # Title with icon
        title_frame = ttk.Frame(self.login_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        app_icon = ttk.Label(title_frame, text="🎓", font=('Arial', 24))
        app_icon.pack()

        title_label = ttk.Label(title_frame, text="Đăng Nhập Hệ Thống",
                                style="Title.TLabel")
        title_label.pack(pady=(5, 10))

        subtitle_label = ttk.Label(
            title_frame, text="Nhập thông tin đăng nhập để tiếp tục")
        subtitle_label.pack(pady=(0, 10))

        # Username field with icon
        username_frame = ttk.Frame(self.login_frame)
        username_frame.pack(fill=tk.X, pady=10)

        username_icon = ttk.Label(username_frame, text="👤")
        username_icon.pack(side=tk.LEFT, padx=(0, 5))

        username_label = ttk.Label(
            username_frame, text="Tên đăng nhập:", width=15)
        username_label.pack(side=tk.LEFT)

        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(
            username_frame, textvariable=self.username_var, width=30)
        self.username_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Password field with icon
        password_frame = ttk.Frame(self.login_frame)
        password_frame.pack(fill=tk.X, pady=10)

        password_icon = ttk.Label(password_frame, text="🔒")
        password_icon.pack(side=tk.LEFT, padx=(0, 5))

        password_label = ttk.Label(password_frame, text="Mật khẩu:", width=15)
        password_label.pack(side=tk.LEFT)

        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(password_frame, textvariable=self.password_var,
                                        show="*", width=30)
        self.password_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Error message
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(self.login_frame, textvariable=self.error_var,
                                     style="Error.TLabel", wraplength=350)
        self.error_label.pack(pady=10)

        # Tạo frame container với pack để căn giữa nút
        button_container = ttk.Frame(self.login_frame)
        button_container.pack(pady=10)

        # Nút đăng nhập
        self.login_button = ttk.Button(
            button_container,
            text="Đăng Nhập",
            command=self._login,
            style="Login.TButton",
            width=20
        )
        self.login_button.pack()

        # Bind Enter key to login button
        self.password_entry.bind("<Return>", lambda event: self._login())
        self.username_entry.bind(
            "<Return>", lambda event: self.password_entry.focus())

        # Focus on username field
        self.username_entry.focus_set()

        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self.login_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)

    def _login(self):
        """Handle login button click."""
        # Clear previous error
        self.error_var.set("")
        self.status_var.set("Đang xác thực...")
        self.update()  # Update UI to show status immediately

        # Disable login button during authentication
        self.login_button.configure(state="disabled")

        # Get username and password
        username = self.username_var.get()
        password = self.password_var.get()

        # Validate input
        if not username or not password:
            self.error_var.set("Vui lòng nhập tên đăng nhập và mật khẩu")
            self.status_var.set("")
            self.login_button.configure(state="normal")
            return

        # Attempt to authenticate
        try:
            employee = self.db.authenticate_employee(username, password)

            logger.info(f"Employee: {employee}")

            if employee:
                # Login successful
                self.employee_session.login(employee)
                logger.info(f"Login successful for user: {username}")

                # Show success message
                self.status_var.set(
                    f"Đăng nhập thành công! Xin chào {employee.get('HOTEN', '')}")
                self.update()  # Update UI to show status

                # Clear form
                self.username_var.set("")
                self.password_var.set("")

                # Call success callback after a short delay to show the success message
                self.after(1000, self._complete_login)
            else:
                # Login failed
                self.error_var.set("Tên đăng nhập hoặc mật khẩu không đúng")
                self.status_var.set("")
                logger.warning(f"Login failed for user: {username}")
                self.login_button.configure(state="normal")

        except Exception as e:
            # Handle connection error
            self.error_var.set(f"Lỗi kết nối đến cơ sở dữ liệu: {str(e)}")
            self.status_var.set("")
            logger.error(f"Database error during login: {str(e)}")
            self.login_button.configure(state="normal")

    def _complete_login(self):
        """Complete the login process after showing success message."""
        # Call success callback
        if self.on_login_success:
            self.on_login_success()
        self.login_button.configure(state="normal")

    def reset_form(self):
        """Reset the login form."""
        self.username_var.set("")
        self.password_var.set("")
        self.error_var.set("")
        self.status_var.set("")
        self.login_button.configure(state="normal")
        # Focus on username field
        if hasattr(self, 'username_entry'):
            self.username_entry.focus_set()
