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
        self.session = EmployeeSession()

        # Create the login form
        self._create_widgets()

    def _create_widgets(self):
        """Create and layout the login form widgets."""
        # Main frame for login
        self.login_frame = ttk.Frame(self)
        self.login_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Title
        title_label = ttk.Label(self.login_frame, text="Đăng Nhập Hệ Thống",
                                font=('Helvetica', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        # Username field
        username_frame = ttk.Frame(self.login_frame)
        username_frame.pack(fill=tk.X, pady=10)

        username_label = ttk.Label(
            username_frame, text="Tên đăng nhập:", width=15)
        username_label.pack(side=tk.LEFT)

        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(
            username_frame, textvariable=self.username_var, width=30)
        username_entry.pack(side=tk.LEFT, padx=5)

        # Password field
        password_frame = ttk.Frame(self.login_frame)
        password_frame.pack(fill=tk.X, pady=10)

        password_label = ttk.Label(password_frame, text="Mật khẩu:", width=15)
        password_label.pack(side=tk.LEFT)

        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var,
                                   show="*", width=30)
        password_entry.pack(side=tk.LEFT, padx=5)

        # Error message
        self.error_var = tk.StringVar()
        error_label = ttk.Label(self.login_frame, textvariable=self.error_var,
                                foreground='red')
        error_label.pack(pady=10)

        # Login button
        login_button = ttk.Button(self.login_frame, text="Đăng Nhập",
                                  command=self._login, width=20)
        login_button.pack(pady=10)

        # Bind Enter key to login button
        password_entry.bind("<Return>", lambda event: self._login())

        # Focus on username field
        username_entry.focus_set()

    def _login(self):
        """Handle login button click."""
        # Clear previous error
        self.error_var.set("")

        # Get username and password
        username = self.username_var.get()
        password = self.password_var.get()

        # Validate input
        if not username or not password:
            self.error_var.set("Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        # Attempt to authenticate
        try:
            employee = self.db.authenticate_employee(username, password)

            if employee:
                # Login successful
                self.session.login(employee)
                logger.info(f"Login successful for user: {username}")

                # Clear form
                self.username_var.set("")
                self.password_var.set("")

                # Call success callback
                if self.on_login_success:
                    self.on_login_success()
            else:
                # Login failed
                self.error_var.set("Tên đăng nhập hoặc mật khẩu không đúng")
                logger.warning(f"Login failed for user: {username}")

        except Exception as e:
            # Handle connection error
            self.error_var.set("Lỗi kết nối đến cơ sở dữ liệu")
            logger.error(f"Database error during login: {str(e)}")

    def reset_form(self):
        """Reset the login form."""
        self.username_var.set("")
        self.password_var.set("")
        self.error_var.set("")
