# VIT Bhopal Central Library Management System

## Overview
A modern desktop application designed to streamline operations at the VIT Bhopal Central Library. Built with Python and CustomTkinter, this system provides dedicated portals for students, faculty, and librarians to track books, manage issues, and calculate fines seamlessly.

## Features
* **Role-Based Portals:** Secure logins for Students, Faculty, and Librarians, each with custom permissions.
* **Catalogue Management:** Search, add, update, and remove books.
* **Circulation System:** Issue, return, and renew books with automated due-date and fine calculations.
* **Reservation Queue:** Reserve books that are currently out on loan and receive notifications when they return.
* **Admin Dashboard & Reports:** Visual analytics and one-click Excel report generation for library statistics.
* **Dark/Light Mode UI:** A clean, responsive, and modern interface built using CustomTkinter.

## Technologies Used
* **Frontend:** CustomTkinter (Python)
* **Backend Logic:** Python
* **Database:** SQLite3
* **Data Visualization:** Matplotlib
* **Reporting:** OpenPyXL (Excel exports)

## Installation & Setup
1. Clone this repository to your local machine.
2. Ensure you have Python installed.
3. Install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```
*(Note: The SQLite database `library.db` will automatically initialize with demo seed data on the first launch).*

## Testing Instructions
You can test the system using the following pre-loaded seed accounts:
* **Librarian Login:** `LIB001` / Password: `admin123`
* **Student Login:** `22BEC10145` / Password: `student123`
* **Faculty Login:** `EMP1042` / Password: `faculty123`

## Screenshots

**Login Screen**
![Login Screen](login.png)

**Librarian Dashboard**
![Librarian Dashboard](librarian_dash.png)

**Student Portal**
![Student Portal](student_portal.png)