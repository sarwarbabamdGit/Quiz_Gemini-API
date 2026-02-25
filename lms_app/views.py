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
        mode = request.POST.get('mode', 'MCQ') # MCQ, Notes, Visualization
        if topic:
            try:
                print(f"Starting {mode} generation for topic: {topic}")
                model = genai.GenerativeModel('gemini-3-flash-preview')
                # model = genai.GenerativeModel('gemini-3-flash')
                
                if 'exam' in topic.lower():
                    prompt = f'Provide the latest syllabus, exam pattern, and direct PDF links to the previous 3 year question papers for "{topic}". Also generate 30 previously asked and expected MCQs for the same. For each question, provide a brief explanation for the correct answer. Format: {{"notes":"# Syllabus & Pattern...","questions":[{{"id":1,"question":"","options":["","","",""],"answer":"","explanation":""}}]}}. JSON only.'
                elif mode == 'Notes':
                    prompt = f'Provide comprehensive 1000-word study notes on "{topic}". Output as JSON: {{"notes":"...", "questions":[]}}. JSON only.'
                elif mode == 'Visualization':
                    prompt = f'Provide a visual learning guide for "{topic}". Include a Mermaid.js graph/diagram code block. Output as JSON: {{"notes":"# Visual Roadmap\\n```mermaid\\n...\\n```\\nDescription...", "questions":[]}}. JSON only.'
                else: # MCQ
                    prompt = f'JSON quiz on "{topic}". Include "Important Points to Remember" in the notes. Generate 30 previously asked and expected MCQs. For each question, provide a brief explanation for the correct answer. Format: {{"notes":"","questions":[{{"id":1,"question":"","options":["","","",""],"answer":"","explanation":""}}]}}. JSON only.'
                
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                data = json.loads(response.text)
                
                videos = []
                try:
                    youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
                    request_yt = youtube.search().list(
                        q=f"{topic} syllabus and paper guide" if mode == 'Exam' else f"{topic} official tutorial",
                        part='snippet',
                        type='video',
                        videoEmbeddable='true',
                        videoSyndicated='true',
                        maxResults=3
                    )
                    response_yt = request_yt.execute()
                    
                    for item in response_yt.get('items', []):
                        videos.append({
                            'id': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'thumbnail': item['snippet']['thumbnails']['high']['url']
                        })
                except Exception as ve:
                    print(f"YouTube Data API failed: {ve}")

                request.session['quiz_questions'] = data.get('questions', [])
                request.session['quiz_topic'] = topic
                request.session['quiz_notes'] = data.get('notes')
                request.session['quiz_videos'] = videos
                request.session['quiz_mode'] = mode
                
                if data.get('questions'):
                    request.session['quiz_mode'] = 'MCQ' if mode == 'MCQ' else mode
                    return redirect('quiz')
                
                result = QuizResult.objects.create(
                    user=request.user,
                    topic=topic,
                    score=0,
                    total_questions=0,
                    results_data=data.get('notes'),
                    content_type=mode
                )
                return redirect('view_history', result_id=result.id)
            except Exception as e:
                return render(request, 'lms_app/dashboard.html', {'error': f"Error: {str(e)}"})
    
    # Fetch only favorites for dashboard
    favorites = QuizResult.objects.filter(user=request.user, is_favorite=True).order_by('-date_taken')
    return render(request, 'lms_app/dashboard.html', {'favorites': favorites})

@login_required
def history_list(request):
    history = QuizResult.objects.filter(user=request.user).order_by('-date_taken')
    return render(request, 'lms_app/history.html', {'history': history})

@login_required
def delete_result(request, result_id):
    result = QuizResult.objects.get(id=result_id, user=request.user)
    result.delete()
    return redirect('history_list')

@login_required
def toggle_favorite(request, result_id):
    result = QuizResult.objects.get(id=result_id, user=request.user)
    result.is_favorite = not result.is_favorite
    result.save()
    return redirect('history_list')

@login_required
def quiz(request):
    questions = request.session.get('quiz_questions')
    topic = request.session.get('quiz_topic')
    if not questions:
        return redirect('dashboard')
    
    if request.method == 'POST':
        score = 0
        total = len(questions)
        results = []
        for q in questions:
            user_answer = request.POST.get(str(q['id']))
            is_correct = user_answer == q['answer']
            if is_correct:
                score += 1
            results.append({
                'question': q['question'],
                'options': q['options'],
                'user_answer': user_answer,
                'correct_answer': q['answer'],
                'is_correct': is_correct,
                'explanation': q.get('explanation', 'No explanation provided.')
            })
        
        # Save result
        mode = request.session.get('quiz_mode', 'MCQ')
        try:
            time_taken = int(request.POST.get('time_taken', 0))
        except (ValueError, TypeError):
            time_taken = 0
        
        result = QuizResult.objects.create(
            user=request.user,
            topic=topic,
            score=score,
            total_questions=total,
            results_data=json.dumps(results),
            content_type=mode,
            time_taken=time_taken
        )
        
        # Clear session
        del request.session['quiz_questions']
        del request.session['quiz_topic']
        
        return redirect('view_history', result_id=result.id)

    notes = request.session.get('quiz_notes')
    videos = request.session.get('quiz_videos', [])

    return render(request, 'lms_app/quiz.html', {
        'questions': questions, 
        'topic': topic,
        'notes': notes,
        'videos': videos
    })

@login_required
def view_history(request, result_id):
    result = QuizResult.objects.get(id=result_id, user=request.user)
    
    # Check if the data is a JSON list of results
    is_quiz_result = False
    try:
        results = json.loads(result.results_data)
        if isinstance(results, list):
            is_quiz_result = True
            notes_content = None
        else:
            is_quiz_result = False
            notes_content = result.results_data
    except:
        is_quiz_result = False
        notes_content = result.results_data

    return render(request, 'lms_app/result.html', {
        'score': result.score,
        'total': result.total_questions,
        'topic': result.topic,
        'results': results if is_quiz_result else [],
        'date_taken': result.date_taken,
        'time_taken_formatted': f"{result.time_taken // 60}:{result.time_taken % 60:02d}",
        'is_review': True,
        'is_favorite': result.is_favorite,
        'result_id': result.id,
        'notes': notes_content,
        'content_type': result.content_type,
        'is_quiz_result': is_quiz_result
    })
