from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'), # Make dashboard the home page
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('quiz/', views.quiz, name='quiz'),
    path('history/', views.history_list, name='history_list'),
    path('history/<int:result_id>/', views.view_history, name='view_history'),
    path('delete-result/<int:result_id>/', views.delete_result, name='delete_result'),
    path('toggle-favorite/<int:result_id>/', views.toggle_favorite, name='toggle_favorite'),
]
