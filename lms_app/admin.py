from django.contrib import admin
from .models import QuizResult

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'score', 'total_questions', 'date_taken')
    list_filter = ('topic', 'date_taken')
    search_fields = ('user__username', 'topic')
