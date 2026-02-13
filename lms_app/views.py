from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from .models import QuizResult
import google.generativeai as genai
from django.conf import settings
import json
from googleapiclient.discovery import build

genai.configure(api_key=settings.GEMINI_API_KEY)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'lms_app/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'lms_app/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        if topic:
            try:
                print(f"Starting quiz generation for topic: {topic}")
                model = genai.GenerativeModel('gemini-3-flash-preview')
                prompt = f'JSON quiz for "{topic}". Output: {{"notes":"summary","questions":[{{"id":1,"question":"?","options":["A","B","C","D"],"answer":"A"}}]}}. 500 words notes, 30 MCQs.'
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                data = json.loads(response.text)
                
                actual_video_id = None
                try:
                    # Fetch a real YouTube Video ID for the topic using the Provided API Key
                    # Adding videoEmbeddable=True and videoSyndicated=True to fix Error 153
                    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
                    request_yt = youtube.search().list(
                        q=f"{topic} official tutorial",
                        part='snippet',
                        type='video',
                        videoEmbeddable='true',
                        videoSyndicated='true',
                        maxResults=1
                    )
                    response_yt = request_yt.execute()
                    
                    if response_yt.get('items'):
                        actual_video_id = response_yt['items'][0]['id']['videoId']
                except Exception as ve:
                    print(f"YouTube Data API failed: {ve}")
                    actual_video_id = None

                request.session['quiz_questions'] = data.get('questions')
                request.session['quiz_topic'] = topic
                request.session['quiz_notes'] = data.get('notes')
                request.session['quiz_video_id'] = actual_video_id
                return redirect('quiz')
            except Exception as e:
                return render(request, 'lms_app/dashboard.html', {'error': f"Error generating quiz: {str(e)}"})
    
    # Fetch history
    history = QuizResult.objects.filter(user=request.user).order_by('-date_taken')
    return render(request, 'lms_app/dashboard.html', {'history': history})

@login_required
def quiz(request):
    questions = request.session.get('quiz_questions')
    topic = request.session.get('quiz_topic')
    if not questions:
        return redirect('dashboard')
    
    if request.method == 'POST':
        score = 0
        total = len(questions)
        for q in questions:
            user_answer = request.POST.get(str(q['id']))
            if user_answer == q['answer']:
                score += 1
        
        # Save result
        QuizResult.objects.create(
            user=request.user,
            topic=topic,
            score=score,
            total_questions=total
        )
        
        # Clear session
        del request.session['quiz_questions']
        del request.session['quiz_topic']
        
        return render(request, 'lms_app/result.html', {'score': score, 'total': total, 'topic': topic})

    notes = request.session.get('quiz_notes')
    video_id = request.session.get('quiz_video_id')

    return render(request, 'lms_app/quiz.html', {
        'questions': questions, 
        'topic': topic,
        'notes': notes,
        'video_id': video_id
    })
