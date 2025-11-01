# Graderific - Web-Based Assignment Grading System

A full-stack web application for managing course assignments, submissions, and grading. Built with Django, this platform provides role-based access for students, teaching assistants, and administrators to streamline the assignment submission and grading workflow.

## 🎯 Project Overview

Graderific is a comprehensive grading management system that allows:
- **Students** to view assignments, submit work, and track their grades
- **Teaching Assistants** to grade assigned submissions and provide feedback
- **Administrators** to manage all aspects of the course and grading

The application features automatic TA assignment distribution, real-time grade calculations, and an intuitive interface for all user types.

## ✨ Key Features

### For Students
- View all course assignments with due dates and point values
- Submit assignments (PDF files) with validation
- Track submission status (submitted, graded, missing)
- View grades and percentage scores
- Calculate projected final grades with hypothetical scores
- Resubmit assignments before deadline

### For Teaching Assistants
- Automated assignment of submissions for balanced workload
- Grade interface for assigned submissions
- Bulk grade submission with validation
- View grading progress across assignments

### For Administrators
- Full access to all submissions and grades
- User management (students, TAs)
- Assignment creation and management
- Override capabilities for all grading operations

### Technical Features
- **Authentication & Authorization**: Django's built-in auth system with role-based permissions
- **File Upload System**: Secure PDF validation and storage
- **Asynchronous Forms**: AJAX-based file uploads with status feedback
- **Dynamic Sorting**: Client-side table sorting for assignments and grades
- **Grade Calculation**: Weighted grade computation with deadline awareness
- **Responsive Design**: Clean, accessible interface that works on all devices

## 🛠️ Technologies Used

### Backend
- **Framework**: Django 5.1.4
- **Database**: SQLite (Django ORM)
- **Language**: Python 3.x
- **Authentication**: Django contrib.auth

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Custom styling with flexbox
- **JavaScript (ES6+)**: Async/await, Fetch API
- **Responsive Design**: Mobile-friendly layouts

### Security
- CSRF protection on all forms
- Permission-based view access
- File validation (type, size, content)
- Object-level permissions

## 📦 Project Structure

```
graderific/
├── graderific/          # Project configuration
│   ├── settings.py      # Django settings
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI configuration
├── grades/              # Main application
│   ├── models.py        # Database models (Assignment, Submission)
│   ├── views.py         # View logic and controllers
│   ├── templates/       # HTML templates
│   └── migrations/      # Database migrations
├── static/              # Static files (CSS, JS)
│   ├── main.css         # Stylesheet
│   └── main.js          # Client-side JavaScript
├── uploads/             # User-uploaded files
├── manage.py            # Django management script
└── makedata.py          # Sample data generator
```

## 🚀 How to Run

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/graderific.git
   cd graderific
   ```

2. **Install dependencies**
   ```bash
   pip install django --break-system-packages
   # or use a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install django
   ```

3. **Set up the database**
   ```bash
   python manage.py migrate
   ```

4. **Create sample data (optional)**
   ```bash
   python makedata.py
   ```
   
   This creates test users:
   - **Admin**: username: `david`, password: `david`
   - **TA 1**: username: `g`, password: `g`
   - **TA 2**: username: `h`, password: `h`
   - **Student 1**: username: `a`, password: `a`
   - **Student 2**: username: `b`, password: `b`
   - **Student 3**: username: `c`, password: `c`
   - **Student 4**: username: `d`, password: `d`

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Open your browser to: `http://localhost:8000`
   - Log in with one of the test accounts

## 🎓 What I Learned

### Backend Development
- **Django framework fundamentals**: Models, Views, Templates (MVT pattern)
- **Database design**: Relational data modeling with foreign keys
- **ORM queries**: Complex database queries with Django QuerySet API
- **User authentication**: Session management and permission systems
- **File handling**: Secure file uploads with validation

### Frontend Development
- **Asynchronous JavaScript**: Fetch API for AJAX requests
- **DOM manipulation**: Dynamic content updates without page reloads
- **Event handling**: Interactive user interfaces
- **Form validation**: Client-side and server-side validation

### Software Engineering Practices
- **MVC/MVT architecture**: Separation of concerns
- **Security best practices**: CSRF protection, input validation, permission checks
- **Error handling**: Graceful error management and user feedback
- **RESTful design**: Clean URL patterns and HTTP methods

### AWS Deployment (Homework 7)
- EC2 instance setup and configuration
- Web server configuration (Nginx)
- Production deployment considerations
- Security groups and networking

## 🔒 Security Features

- **CSRF Protection**: All forms include CSRF tokens
- **Permission Checks**: Role-based access control at view level
- **File Validation**: 
  - Type checking (PDF only)
  - Size limits (64 MiB max)
  - Content verification (magic bytes)
- **Object-Level Permissions**: Users can only access their own submissions
- **SQL Injection Prevention**: Django ORM parameterized queries

## 🎨 Key Implementation Highlights

### Auto-Assignment Algorithm
TAs are automatically assigned submissions based on current workload to ensure balanced distribution:
```python
def pick_grader(assignment):
    """Returns the TA with the fewest assigned submissions."""
    tas = ta_group.user_set.annotate(
        total_assigned=Count('graded_set')
    ).order_by('total_assigned')
    return tas.first()
```

### Grade Calculation System
Weighted grade computation considering only graded assignments past their due date:
```python
def compute_grade(user):
    """Compute student's current grade based on graded assignments."""
    # Calculates percentage based on weighted assignments
    # Only includes past-due, graded submissions
```

### Permission-Based File Access
Submissions can only be viewed by authorized users (author, grader, or admin):
```python
def view_submission(self, user):
    """Check permissions before allowing file access."""
    if user.is_superuser or user == self.author or user == self.grader:
        return self.file
    raise PermissionDenied()
```

## 📊 Database Schema

### Assignment Model
- title, description, deadline, weight, points

### Submission Model
- assignment (FK), author (FK), grader (FK), file, score
- Enforces business rules through model methods

## 🌐 Deployment

This application was deployed to AWS EC2 as part of CS 3550 coursework, including:
- Ubuntu server configuration
- Nginx web server setup
- Static file serving
- Security hardening

## 🔮 Future Enhancements

- Email notifications for new assignments and graded submissions
- Rubric-based grading with detailed feedback
- Support for multiple file types
- Peer review functionality
- Analytics dashboard for instructors
- Export grades to CSV
- Discussion forums for assignments

## 👨‍💻 Development

**Developer**: Kellen Auth  
**GitHub**: [@KellenAuth](https://github.com/KellenAuth)  
**Course**: CS 3550 - Web Software Architecture, University of Utah  
**Semester**: Fall 2024

## 📄 Course Context

This project was developed across 7 homework assignments covering:
1. HTML and basic web structure
2. CSS styling and responsive design
3. Django models and database design
4. Controllers and business logic
5. User authentication and permissions
6. JavaScript and asynchronous operations
7. AWS deployment

## 🙏 Acknowledgments

Built as part of CS 3550 at the University of Utah. Thanks to Professor David Johnson and the teaching staff for guidance throughout the course.

---

*A comprehensive web application demonstrating full-stack development skills from database design to deployment.*
