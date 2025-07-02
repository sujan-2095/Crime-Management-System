README - Crime Record Management System (CRMS)

📌 Project Overview

Crime is a critical concern, and effective crime data management is essential for public safety. This project implements a Crime Record Management System (CRMS) using Flask (Python) and SQLite that supports centralized, structured, and role-based access to case information for law enforcement.

🎯 Key Objectives

- Digitize and streamline crime record keeping.
- Enable secure and role-specific access.
- Maintain integrity, confidentiality, and quick retrieval of data.
- Support crime tracking, offender profiling, legal proceedings, and analytics.
  
🛠️ Tech Stack

Layer	Technology
Frontend	HTML, CSS, JavaScript, Bootstrap
Backend	Python (Flask)
Database	SQLite
Authentication	Flask-Login, RBAC

🔐 Core Modules

1. User Authentication
Secure login for admins and officers. Role-based access control. Logs user activities.
2. Crime Report Management
Enter, update, view crime records. Real-time case status tracking.
3. Offender Management
Maintain offender profiles. Link offenders to multiple cases. View biometric and background data.
4. Legal Proceedings
Track court hearings, verdicts, sentencing. Store legal documents and updates.
5. Investigation
Log investigation steps and officer actions. Collaborate and track case progress.
6. Search & Reports
Filter crimes, offenders, and legal data. Generate reports (e.g., crime trends, unresolved cases).

📊 DBMS Concepts Applied

- ER Modeling
- Normalization
- ACID Transactions
- Triggers & Constraints
- SQL Query Optimization
- RBAC (Role-Based Access Control)

⚙️ How to Run the Project

1. Clone the repository:
   git clone https://github.com/<your-username>/Crime-Management-System.git
   cd Crime-Management-System

2. Set up a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Run the app:
   python main.py

5. Open in browser:
   http://localhost:5000

🧪 Sample Credentials

Role	Username	Password
Admin	admin	admin123
> You can configure more users via the database or UI.

🎓 Academic Use

This project was developed as part of the Database Management Systems (CGB1221) course under the guidance of Dr. R. Bharathi, M.E., Ph.D., at M. Kumarasamy College of Engineering, Karur.

📚 References

- Elmasri & Navathe – Fundamentals of Database Systems
- Silberschatz, Korth & Sudarshan – Database System Concepts
- Flask Documentation – https://flask.palletsprojects.com
- SQLite Documentation – https://www.sqlite.org/docs.html
- Bootstrap – https://getbootstrap.com

👨‍💻 Developed By

Sujan P
927623BIT117
Department of Information Technology
M.Kumarasamy College of Engineering
