from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, F, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.http import url_has_allowed_host_and_scheme
from . import models

# Helper functions for user roles
def is_student(user):
    return user.groups.filter(name="Students").exists()

def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()

def pick_grader(assignment):
    """Returns the TA with the fewest assigned submissions for this assignment."""
    ta_group = models.Group.objects.get(name="Teaching Assistants")
    
    # Get all TAs, annotated with their submission count for this assignment
    tas = ta_group.user_set.annotate(
        total_assigned=Count('graded_set', filter=models.Q(graded_set__assignment=assignment))
    ).order_by('total_assigned')
    
    # Return the TA with the fewest assignments
    return tas.first()

def is_pdf(file):
    """Check if a file is a valid PDF by extension and header."""
    # Check file extension
    if not file.name.lower().endswith('.pdf'):
        return False
    
    # Check file header (magic bytes)
    try:
        file.seek(0)
        header = next(file.chunks()).startswith(b'%PDF-')
        file.seek(0)  # Reset file pointer
        return header
    except:
        return False

def compute_grade(user):
    """Compute a student's current grade."""
    assignments = models.Assignment.objects.all()
    available_points = 0
    earned_points = 0
    
    for assignment in assignments:
        submission = assignment.submission_set.filter(author=user).first()
        
        # Assignment is past due date
        if assignment.deadline < timezone.now():
            available_points += assignment.weight
            
            # If student has a graded submission
            if submission and submission.score is not None:
                percentage = submission.score / assignment.points
                earned_points += percentage * assignment.weight
                
        # Assignment isn't past due and isn't graded - ignore
    
    # Calculate percentage (prevent division by zero)
    if available_points > 0:
        grade_percentage = (earned_points / available_points) * 100
    else:
        grade_percentage = 100  # No assignments due yet
        
    return {
        'percentage': round(grade_percentage, 1),
        'available_points': available_points,
        'earned_points': round(earned_points, 1)
    }

@login_required
def index(request):
    assignments = models.Assignment.objects.all().order_by('deadline')
    return render(request, "index.html", {
        'title': 'Assignments - CS 3550',
        'assignments': assignments,
        'user': request.user
    })

@login_required
def assignment(request, assignment_id):
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    user = request.user
    is_authenticated = user.is_authenticated
    is_student_user = is_student(user) or not is_authenticated
    is_ta_user = is_ta(user)
    is_admin = user.is_superuser
    
    # Count submissions based on user type
    total_submissions = assignment.submission_set.count()
    total_students = models.Group.objects.get(name="Students").user_set.count()
    
    if is_admin:
        # Admin sees all submissions
        your_submissions = total_submissions
    else:
        # TAs see their assigned submissions
        your_submissions = assignment.submission_set.filter(grader=user).count()
    
    # Get the user's own submission if they're a student
    user_submission = None
    submission_status = "No current submission"
    past_due = assignment.deadline < timezone.now()
    file_error = None
    
    if is_authenticated and is_student_user:
        user_submission = assignment.submission_set.filter(author=user).first()
        
        if user_submission:
            if user_submission.score is not None and past_due:
                # Graded submission
                percentage = (user_submission.score / assignment.points) * 100
                submission_status = f"Your submission, {user_submission.file.name.split('/')[-1]}, received {user_submission.score}/{assignment.points} points ({percentage:.1f}%)"
            elif past_due:
                # Submitted but not graded, past due
                submission_status = f"Your submission, {user_submission.file.name.split('/')[-1]}, is being graded"
            else:
                # Submitted, not due
                submission_status = f"Your current submission is {user_submission.file.name.split('/')[-1]}"
        elif past_due:
            # Not submitted, past due
            submission_status = "You did not submit this assignment and received 0 points"
        else:
            # Not submitted, not due
            submission_status = "No current submission"
    
    # Handle file upload
    if request.method == "POST" and request.FILES and is_authenticated:
        # Get the submitted file
        uploaded_file = request.FILES.get('submission_file')
        
        # Check if deadline has passed
        #if past_due:
            #return HttpResponseBadRequest("Deadline has passed. Cannot submit.")
        
        if uploaded_file and is_student_user:
            # Check file size (64 MiB = 64 * 1024 * 1024 bytes)
            max_size = 64 * 1024 * 1024
            if uploaded_file.size > max_size:
                file_error = "File is too large. Maximum size is 64 MiB."
            # Check file extension
            elif not uploaded_file.name.lower().endswith('.pdf'):
                file_error = "Only PDF files are accepted."
            # Check file content
            elif not next(uploaded_file.chunks()).startswith(b'%PDF-'):
                uploaded_file.seek(0)  # Reset file pointer
                file_error = "The file is not a valid PDF."
            else:
                uploaded_file.seek(0)  # Reset file pointer
                if user_submission:
                    # Update existing submission - keep the same grader
                    user_submission.file = uploaded_file
                    user_submission.save()
                else:
                    # Create new submission for the current user
                    grader = pick_grader(assignment)
                    
                    user_submission = models.Submission.objects.create(
                        assignment=assignment,
                        author=user,
                        grader=grader,
                        score=None,
                        file=uploaded_file
                    )
                
                # Redirect back to assignment page
                return redirect(f"/{assignment_id}/")
    
    context = {
        'title': f'{assignment.title} - CS 3550',
        'assignment': assignment,
        'total_submissions': total_submissions,
        'your_submissions': your_submissions,
        'total_students': total_students,
        'user_submission': user_submission,
        'submission_status': submission_status,
        'past_due': past_due,
        'file_error': file_error,
        'user': user,
        'is_student': is_student_user,
        'is_ta': is_ta_user,
        'is_admin': is_admin
    }
    return render(request, "assignment.html", context)

@login_required
def submissions(request, assignment_id):
    user = request.user
    is_admin = user.is_superuser
    
    # Check if user is a TA or admin
    if not (is_ta(user) or is_admin):
        raise PermissionDenied("Only TAs can access the submissions page")
    
    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    
    # Get submissions based on user type
    if is_admin:
        # Admin sees all submissions
        submissions = assignment.submission_set.all().order_by('author__username')
    else:
        # TAs see only their assigned submissions
        submissions = assignment.submission_set.filter(
            grader=user
        ).order_by('author__username')
    
    errors = {}  # Dictionary to store errors for each submission
    general_errors = []  # List for errors with invalid submission IDs
    
    if request.method == "POST":
        # Process submitted grades
        submissions_to_update = []
        
        for key in request.POST:
            # Skip any keys that don't start with 'grade-'
            if not key.startswith('grade-'):
                continue
            
            try:
                # Extract the submission ID from the key
                submission_id = int(key.removeprefix('grade-'))
                
                # Get the submission object and verify it belongs to this assignment
                try:
                    submission = models.Submission.objects.get(id=submission_id)
                    
                    # Check if submission belongs to this assignment
                    if submission.assignment.id != assignment.id:
                        general_errors.append(f"Submission {submission_id} does not belong to this assignment")
                        continue
                    
                    # Get the score value
                    score_value = request.POST[key].strip()
                    
                    if score_value == '':
                        # Empty string means no grade
                        try:
                            submission.change_grade(user, None)
                            submissions_to_update.append(submission)
                        except PermissionDenied:
                            general_errors.append(f"You are not authorized to grade submission {submission_id}")
                    else:
                        try:
                            # Convert to Decimal
                            score = Decimal(score_value)
                            
                            # Validate the score range
                            if score < 0:
                                if submission_id not in errors:
                                    errors[submission_id] = []
                                errors[submission_id].append("Grade cannot be negative")
                                continue
                                
                            if score > assignment.points:
                                if submission_id not in errors:
                                    errors[submission_id] = []
                                errors[submission_id].append(f"Grade cannot exceed {assignment.points} points")
                                continue
                            
                            # Use the permission-checked method
                            try:
                                submission.change_grade(user, score)
                                submissions_to_update.append(submission)
                            except PermissionDenied:
                                general_errors.append(f"You are not authorized to grade submission {submission_id}")
                            
                        except (InvalidOperation, ValueError):
                            # Handle invalid decimal values
                            if submission_id not in errors:
                                errors[submission_id] = []
                            errors[submission_id].append("Grade must be a valid number")
                            continue
                    
                except models.Submission.DoesNotExist:
                    general_errors.append(f"Submission ID {submission_id} does not exist")
                    continue
                    
            except ValueError:
                # Handle case where ID is not a valid integer
                general_errors.append(f"Invalid submission ID format in {key}")
                continue
        
        # Save all valid changes at once using bulk_update
        if submissions_to_update:
            models.Submission.objects.bulk_update(submissions_to_update, ['score'])
            
        # If no errors, redirect back to the page
        if not errors and not general_errors:
            return redirect(f"/{assignment_id}/submissions/")
        
        # If there are errors, add error information to submissions for display
        for submission in submissions:
            submission.error_messages = errors.get(submission.id, [])
    
    return render(request, "submissions.html", {
        'title': f'{assignment.title} - CS 3550',
        'assignment': assignment,
        'submissions': submissions,
        'general_errors': general_errors,
        'user': user,
        'is_admin': is_admin
    })

@login_required
def profile(request):
    user = request.user
    is_authenticated = user.is_authenticated
    is_student_user = is_student(user) or not is_authenticated
    is_ta_user = is_ta(user)
    is_admin = user.is_superuser
    
    assignments = models.Assignment.objects.all().order_by('deadline')
    current_grade = None
    
    if is_student_user and is_authenticated:
        # For students, show submission status and grades
        for assignment in assignments:
            submission = assignment.submission_set.filter(author=user).first()
            past_due = assignment.deadline < timezone.now()
            
            if submission and submission.score is not None:
                # Graded submission
                percentage = (submission.score / assignment.points) * 100
                assignment.status = f"{percentage:.1f}%"
            elif submission and past_due:
                # Submitted, not graded, past due
                assignment.status = "Ungraded"
            elif submission:
                # Submitted, not due
                assignment.status = "Submitted"
            elif past_due:
                # Not submitted, past due
                assignment.status = "Missing"
            else:
                # Not submitted, not due
                assignment.status = "Not Due"
        
        # Compute the student's current grade
        current_grade = compute_grade(user)
    else:
        # For TAs or admin, show grading progress
        for assignment in assignments:
            if is_admin:
                # Admin sees all submissions
                assigned = assignment.submission_set.count()
                graded = assignment.submission_set.filter(score__isnull=False).count()
            elif is_ta_user and is_authenticated:
                # TAs see their assigned submissions
                assigned = assignment.submission_set.filter(grader=user).count()
                graded = assignment.submission_set.filter(grader=user, score__isnull=False).count()
            else:
                # Anonymous users see nothing
                assigned = 0
                graded = 0
            
            assignment.graded_count = f"{graded}/{assigned}"
    
    return render(request, "profile.html", {
        'title': 'Your Grades - CS 3550',
        'assignments': assignments,
        'user': user,
        'is_student': is_student_user,
        'is_ta': is_ta_user,
        'is_admin': is_admin,
        'current_grade': current_grade
    })

@login_required
def show_upload(request, filename):
    try:
        # Look for the submission with this filename
        # Try to find the submission by matching the end of the file path
        submission = models.Submission.objects.filter(file__endswith=filename).first()
        
        if not submission:
            raise Http404(f"File {filename} not found")
        
        # Check permissions
        try:
            file = submission.view_submission(request.user)
        except PermissionDenied:
            raise PermissionDenied("You are not authorized to view this file")
        
        # Verify it's a PDF
        if not is_pdf(file):
            raise Http404("Invalid PDF file")
        
        # Open the file and return its contents
        file_content = file.open()
        
        # Create response with proper headers
        response = HttpResponse(file_content)
        response['Content-Type'] = 'application/pdf'
        response['Content-Disposition'] = f'attachment; filename="{file.name.split("/")[-1]}"'
        
        return response
        
    except Exception as e:
        raise Http404(f"Error retrieving file: {str(e)}")

def login_form(request):
    # Default next URL if not provided
    next_url = request.GET.get('next', '/profile/')
    error = None
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/profile/')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Check if next URL is safe before redirecting
            if url_has_allowed_host_and_scheme(next_url, None):
                return redirect(next_url)
            else:
                return redirect('/')
        else:
            error = "Username and password do not match"
    
    return render(request, "login.html", {
        'title': 'Log in - CS 3550',
        'next': next_url,
        'error': error
    })

def logout_form(request):
    logout(request)
    return redirect('/profile/login/')