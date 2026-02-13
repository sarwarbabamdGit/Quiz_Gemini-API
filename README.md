# LMS Project

This project is a Learning Management System (LMS) built with Django, HTML, CSS, JavaScript, and SQLite3.

## Features

- **User Authentication**: Registration and Login.
- **Subject Selection**: Enter any topic to generate a quiz.
- **AI-Powered Quizzes**: Uses Google Gemini API to generate 30 multiple-choice questions.
- **Scoring**: Calculates score out of 30.
- **History Tracking**: Stores quiz results for each user.
- **Interactive UI**: Responsive design with animations.

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install django google-generativeai
   ```

2. **Run Migrations**:
   ```bash
   python manage.py makemigrations lms_app
   python manage.py migrate
   ```

3. **Create Superuser (Optional)**:
   This allows you to view quiz results in the admin panel.
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Server**:
   ```bash
   python manage.py runserver
   ```

5. **Access App**:
   Open browser at: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Usage

1. **Register** a new account.
2. **Login** with your credentials.
3. On the **Dashboard**, enter a topic (e.g., "Python Programming", "World History").
4. Click **Start Quiz** and wait for the AI to generate questions.
5. Answer the **30 questions** and submit.
6. View your **Score** and see your **History** on the dashboard.

## Notes

- Ensure you have internet connection for the Gemini API to work.
- The API Key is configured in `settings.py`.
