# QLSV Nhom - Student Management System

## Overview

QLSV Nhom is a desktop application for managing students, classes, grades, and employees at an educational institution. It features a secure and encrypted database system for storing sensitive information such as employee salaries and student grades.

## Features

- Employee authentication with encrypted credentials
- Class management (create, view, update, delete classes)
- Student management (create, view, update, delete students)
- Grade management with encrypted grade storage
- Employee management with client-side encryption for salaries

## Installation

### Prerequisites

- Windows 10 or newer
- Python 3.8 or newer
- Microsoft SQL Server (local or remote)
- SQL Server drivers for Python (ODBC)

### Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone [repository URL]
   cd [repository-folder]
   ```

2. **Install Dependencies**

   ```bash
   pip install -r UI/requirements.txt
   ```

3. **Database Setup**

   - Open SQL Server Management Studio
   - Run the SQL script `QLSVNhom.sql` to create the database and its tables

4. **Configure Database Connection**

   - Open `UI/db_connector.py`
   - Modify the server, database, username, and password parameters in the DatabaseConnector class initialization if needed

5. **Run the Application**
   ```bash
   cd UI
   python app.py
   ```

## Usage Tutorial

### Login

1. Launch the application with `python app.py`
2. Enter your employee username and password
3. Click "Đăng Nhập" (Login)

### Class Management

#### View Classes

1. After logging in, click on "Quản lý Lớp" (Class Management) in the navigation bar
2. The screen displays all classes, with columns for Class ID, Class Name, and Managing Employee

#### Add a New Class

1. In the Class Management screen, click the "Thêm" (Add) button
2. Fill in the required fields:
   - Mã Lớp (Class ID): A unique identifier for the class
   - Tên Lớp (Class Name): The name of the class
   - Mã Nhân Viên (Employee ID): ID of the employee who will manage the class (pre-filled with your ID)
3. Click "Lưu" (Save) to create the class
4. If successful, a confirmation message will appear

#### Edit a Class

1. In the class list, select the class you want to edit
2. Click the "Sửa" (Edit) button
3. Modify the fields as needed
4. Click "Lưu" (Save) to update the class

#### Delete a Class

1. In the class list, select the class you want to delete
2. Click the "Xóa" (Delete) button
3. Confirm the deletion when prompted

### Student Management

#### View Students in a Class

1. Click on "Quản lý Sinh Viên" (Student Management) in the navigation bar
2. Select a class from the list to view its students
3. Double-click on a class or click the "Xem Sinh Viên" (View Students) button

#### Add a New Student

1. In the Student List screen, click the "Thêm" (Add) button
2. Fill in the required fields:
   - Mã Sinh Viên (Student ID): A unique identifier for the student
   - Họ Tên (Full Name): The student's name
   - Ngày Sinh (Birth Date): The student's date of birth (YYYY-MM-DD format)
   - Địa Chỉ (Address): The student's address (optional)
   - Mã Lớp (Class ID): The class the student belongs to (pre-filled based on selection)
   - Tên Đăng Nhập (Username): A unique username for the student
   - Mật Khẩu (Password): The student's initial password
3. Click "Lưu" (Save) to create the student
4. If successful, a confirmation message will appear

#### Edit a Student

1. In the student list, select the student you want to edit
2. Click the "Sửa" (Edit) button
3. Modify the fields as needed (Note: Username and Password cannot be modified)
4. Click "Lưu" (Save) to update the student

#### Delete a Student

1. In the student list, select the student you want to delete
2. Click the "Xóa" (Delete) button
3. Confirm the deletion when prompted

### Grade Management

#### View Grades for a Class

1. Click on "Quản lý Điểm" (Grade Management) in the navigation bar
2. Select a class from the list to view grades for its students
3. Double-click on a class or click the "Quản Lý Điểm" (Manage Grades) button

#### Add a New Grade

1. In the Grade Management screen, click the "Thêm" (Add) button
2. Fill in the required fields:
   - Sinh Viên (Student): Select a student from the dropdown
   - Học Phần (Course): Select a course from the dropdown
   - Điểm Thi (Grade): Enter a grade between 0 and 10
3. Click "Lưu" (Save) to add the grade
4. If successful, a confirmation message will appear

#### Edit a Grade

1. In the grade list, select the grade you want to edit
2. Click the "Sửa" (Edit) button
3. Modify the grade as needed
4. Click "Lưu" (Save) to update the grade

### Employee Management

#### View Employees

1. Click on "Quản lý Nhân Viên" (Employee Management) in the navigation bar
2. The screen displays all employees, with columns for Employee ID, Name, Email, and Salary
   - Note: For security, you can only see your own salary decrypted, other employees' salaries appear as "\*\*\*"

#### Add a New Employee

1. In the Employee Management screen, click the "Thêm" (Add) button
2. Fill in the required fields:
   - Mã Nhân Viên (Employee ID): A unique identifier for the employee
   - Họ Tên (Full Name): The employee's name
   - Email: The employee's email address (optional)
   - Lương (Salary): The employee's salary (must be a positive integer)
   - Tên Đăng Nhập (Username): A unique username for the employee
   - Mật Khẩu (Password): The employee's initial password
3. Click "Lưu" (Save) to create the employee
4. If successful, a confirmation message will appear

### Logging Out

1. Click "Đăng xuất" (Logout) in the navigation bar
2. Confirm when prompted

## Security Features

- **Password Security**: Passwords are hashed using SHA-1 algorithm
- **Salary Encryption**: Employee salaries are encrypted using asymmetric encryption (RSA-2048)
- **Grade Encryption**: Student grades are encrypted for privacy
- **Access Control**: Employees can only manage and view specific data they have access to

## Troubleshooting

### Connection Issues

- Ensure SQL Server is running
- Verify that the connection string in `db_connector.py` is correct
- Ensure you have the necessary permissions on the database

### Authentication Failures

- Verify username and password
- Check if the employee exists in the database
- Ensure your windows account has permissions to create keys if adding new employees

## Additional Information

### Folder Structure

- `UI/`: Contains the application source code
- `UI/keys/`: Stores encryption keys
- `UI/db_connector.py`: Database connection and queries
- `UI/app.py`: Main application entry point
- `UI/session.py`: Manages user sessions
- `UI/crypto_utils.py`: Cryptographic utilities
- `UI/login_screen.py`: Login interface
- `UI/class_management.py`: Class management interface
- `UI/student_management.py`: Student management interface
- `UI/grade_management.py`: Grade management interface
- `UI/employee_management.py`: Employee management interface
- `UI/ui_components.py`: Reusable UI components
- `QLSVNhom.sql`: Database creation script

## License

[Specify license here]
