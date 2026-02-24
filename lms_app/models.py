from django.db import models
from django.contrib.auth.models import User

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    score = models.IntegerField()
    total_questions = models.IntegerField(default=30)
    results_data = models.TextField(null=True, blank=True)  # JSON stored as text
    is_favorite = models.BooleanField(default=False)
    content_type = models.CharField(max_length=50, default='MCQ') # MCQ, Notes, Visualization
    date_taken = models.DateTimeField(auto_now_add=True)
    time_taken = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.topic} - {self.score}/{self.total_questions}"
