import tkinter as tk
from tkinter import ttk
import logging
from ttkthemes import ThemedTk

from db_connector import DatabaseConnector
from session import EmployeeSession
from login_screen import LoginScreen
from class_management import ClassManagementScreen
from student_management import StudentManagementScreen
from grade_management import GradeManagementScreen
from ui_components import MessageDisplay

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')


class Application:
    """Main application class that integrates all modules."""

    def __init__(self):
        """Initialize the application."""
        # Create themed Tk root
        self.root = ThemedTk(theme="arc")  # Use 'arc' theme for modern look
        self.root.title("Quản Lý Sinh Viên")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)

        # Database connector
        self.db = DatabaseConnector()

        # Session manager
        self.session = EmployeeSession()

        # Set up main container frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create login screen
        self.login_screen = LoginScreen(
            self.main_frame, self._on_login_success)
        self.login_screen.pack(fill=tk.BOTH, expand=True)

        # Create main app frame (hidden initially)
        self.app_frame = ttk.Frame(self.main_frame)

        # Create navigation bar
        self.nav_frame = ttk.Frame(self.app_frame)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.root, textvariable=self.status_var,
            relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create content frame
        self.content_frame = ttk.Frame(self.app_frame)
        self.content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Create navigation buttons and screens (created but not packed yet)
        self._create_navigation()

        # Initialize with login screen
        self._show_login_screen()

    def _create_navigation(self):
        """Create navigation buttons and screen frames."""
        # Create navigation buttons
        self.class_button = ttk.Button(
            self.nav_frame,
            text="Quản lý Lớp",
            command=lambda: self._show_screen('class')
        )
        self.class_button.pack(side=tk.LEFT, padx=5)

        self.student_button = ttk.Button(
            self.nav_frame,
            text="Quản lý Sinh Viên",
            command=lambda: self._show_screen('student')
        )
        self.student_button.pack(side=tk.LEFT, padx=5)

        self.grade_button = ttk.Button(
            self.nav_frame,
            text="Quản lý Điểm",
            command=lambda: self._show_screen('grade')
        )
        self.grade_button.pack(side=tk.LEFT, padx=5)

        # Add logout button on the right
        self.logout_button = ttk.Button(
            self.nav_frame,
            text="Đăng xuất",
            command=self._logout
        )
        self.logout_button.pack(side=tk.RIGHT, padx=5)

        # Create user info label
        self.user_var = tk.StringVar()
        user_label = ttk.Label(self.nav_frame, textvariable=self.user_var)
        user_label.pack(side=tk.RIGHT, padx=15)

        # Create screens (but don't show them yet)
        self.screens = {}

    def _create_screen(self, name):
        """Create a screen if it doesn't exist."""
        if name in self.screens and self.screens[name] is not None:
            return

        # Create the requested screen
        if name == 'class':
            screen = ClassManagementScreen(self.content_frame)
            self.screens[name] = screen
            screen.pack(fill=tk.BOTH, expand=True)
            screen.pack_forget()  # Initially hidden
        elif name == 'student':
            screen = StudentManagementScreen(self.content_frame)
            self.screens[name] = screen
            screen.pack(fill=tk.BOTH, expand=True)
            screen.pack_forget()  # Initially hidden
        elif name == 'grade':
            screen = GradeManagementScreen(self.content_frame)
            self.screens[name] = screen
            screen.pack(fill=tk.BOTH, expand=True)
            screen.pack_forget()  # Initially hidden

    def _show_screen(self, name):
        """Show a specific screen and hide others."""
        # Create the screen if it doesn't exist
        if name not in self.screens or self.screens[name] is None:
            self._create_screen(name)

        # Hide all screens
        for screen_name, screen in self.screens.items():
            if screen is not None:
                screen.pack_forget()

        # Show the requested screen
        if name in self.screens and self.screens[name] is not None:
            self.screens[name].pack(fill=tk.BOTH, expand=True)

            # Update status bar
            status_messages = {
                'class': 'Quản lý lớp học',
                'student': 'Quản lý sinh viên',
                'grade': 'Quản lý điểm số'
            }
            self.status_var.set(status_messages.get(name, ''))

    def _on_login_success(self):
        """Handle successful login."""
        # Hide login screen, show main app
        self.login_screen.pack_forget()
        self.app_frame.pack(fill=tk.BOTH, expand=True)

        # Set user info
        employee = self.session.employee_data
        if employee:
            self.user_var.set(
                f"Xin chào, {employee.get('HOTEN', 'Nhân viên')}")

        # Initialize screens dictionary
        self.screens = {}

        # Show the class management screen by default
        self._show_screen('class')

    def _show_login_screen(self):
        """Show the login screen."""
        # Hide main app, show login
        self.app_frame.pack_forget()
        self.login_screen.pack(fill=tk.BOTH, expand=True)
        self.login_screen.reset_form()

    def _logout(self):
        """Log out the current user."""
        # Ask for confirmation
        if MessageDisplay.ask_yes_no("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            # Reset session
            self.session.logout()

            # Hide all screens first
            for name, screen in self.screens.items():
                if screen is not None:
                    screen.pack_forget()

            # Clear screens dictionary - don't destroy the widgets
            self.screens = {}

            # Clear the content frame
            for widget in self.content_frame.winfo_children():
                if widget.winfo_exists():
                    widget.destroy()

            # Show login screen
            self._show_login_screen()

    def run(self):
        """Run the application."""
        try:
            # Test database connection
            if not self.db.connect():
                MessageDisplay.show_error(
                    "Lỗi Kết Nối",
                    "Không thể kết nối đến cơ sở dữ liệu. Vui lòng kiểm tra cài đặt và thử lại."
                )
                return False

            # Show the UI
            self.root.mainloop()
            return True

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            MessageDisplay.show_error("Lỗi Ứng Dụng", str(e))
            return False
        finally:
            # Ensure database connection is closed
            if self.db:
                self.db.disconnect()


if __name__ == "__main__":
    app = Application()
    app.run()
