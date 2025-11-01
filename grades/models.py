from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    weight = models.IntegerField()
    points = models.IntegerField()
    
    def __str__(self):
        return self.title

class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submission_set'
    )
    grader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_set'
    )
    file = models.FileField(upload_to='submissions/')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.author}'s submission for {self.assignment}"
    
    def change_grade(self, user, grade):
        """
        Updates the submission's grade if the user has permission.
        Raises PermissionDenied if user is not authorized to grade this submission.
        """
        # Admin can change any grade
        if user.is_superuser:
            self.score = grade
            return
        
        # TA can only change grades for submissions assigned to them
        if user == self.grader:
            self.score = grade
            return
        
        # Otherwise, user is not authorized
        raise PermissionDenied("You are not authorized to grade this submission")
        
    def view_submission(self, user):
        """
        Check if user has permission to view this submission.
        Raises PermissionDenied if not authorized.
        Returns the file if authorized.
        """
        # Admin can view any submission
        if user.is_superuser:
            return self.file
        
        # Author can view their own submission
        if user == self.author:
            return self.file
        
        # Grader can view submissions assigned to them
        if user == self.grader:
            return self.file
        
        # Otherwise, user is not authorized
        raise PermissionDenied("You are not authorized to view this submission")