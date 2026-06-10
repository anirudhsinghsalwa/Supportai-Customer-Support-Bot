import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import ChatSession, ChatMessage, UserProfile
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .gemini_service import get_gemini_response

def register_view(request):
    if request.user.is_authenticated:
        return redirect('chatbot:chat_home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Customer Support.")
            return redirect('chatbot:chat_home')
    else:
        form = UserRegistrationForm()
    return render(request, 'chatbot/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('chatbot:chat_home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('chatbot:chat_home')
    else:
        form = AuthenticationForm()
        
    # Inject classes into authentication form manually for styling consistency
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-800 dark:text-slate-100 transition duration-200',
            'placeholder': field.label
        })
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('chatbot:login')

@login_required
def chat_home(request):
    sessions = ChatSession.objects.filter(user=request.user)
    latest_session = sessions.first()
    
    if latest_session:
        return redirect('chatbot:chat_session_detail', session_id=latest_session.id)
        
    return render(request, 'chatbot/chat.html', {
        'sessions': sessions,
        'active_session': None,
        'messages': []
    })

@login_required
def chat_session_detail(request, session_id):
    sessions = ChatSession.objects.filter(user=request.user)
    active_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    chat_messages = active_session.messages.all()
    
    return render(request, 'chatbot/chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'chat_messages': chat_messages
    })

@login_required
def create_session(request):
    session = ChatSession.objects.create(user=request.user, title="New Conversation")
    return redirect('chatbot:chat_session_detail', session_id=session.id)

@login_required
@require_POST
def delete_session(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    messages.success(request, "Conversation deleted.")
    return redirect('chatbot:chat_home')

@login_required
@require_POST
def send_message_api(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    try:
        # Accept either JSON or standard POST parameters
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user_message_content = data.get('message', '').strip()
        else:
            user_message_content = request.POST.get('message', '').strip()
            
        if not user_message_content:
            return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
            
        user_msg = ChatMessage.objects.create(
            session=session,
            sender='user',
            content=user_message_content
        )
        
        # If it was the default title, rename the conversation title based on the first message
        if session.title == "New Conversation" and session.messages.filter(sender='user').count() == 1:
            title = user_message_content[:40]
            if len(user_message_content) > 40:
                title += "..."
            session.title = title
            session.save()
            
        history_msgs = []
        for msg in session.messages.exclude(id=user_msg.id):
            history_msgs.append({
                'sender': msg.sender,
                'content': msg.content
            })
            
        system_instruction = (
            "You are a friendly, highly professional, and empathetic AI Customer Support Agent. "
            "Your goal is to assist the user with their queries accurately, politely, and cleanly. "
            "Structure your output using markdown for readability if needed (e.g. lists, bold text, code snippets). "
            "Always maintain a helpful corporate support persona, but keep your responses natural and engaging."
        )
        
        ai_response_content = get_gemini_response(system_instruction, history_msgs, user_message_content)
        
        ai_msg = ChatMessage.objects.create(
            session=session,
            sender='ai',
            content=ai_response_content
        )
        
        return JsonResponse({
            'status': 'success',
            'session_title': session.title,
            'user_msg': {
                'content': user_msg.content,
                'timestamp': timezone.localtime(user_msg.timestamp).strftime('%I:%M %p')
            },
            'ai_msg': {
                'content': ai_msg.content,
                'timestamp': timezone.localtime(ai_msg.timestamp).strftime('%I:%M %p')
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('chatbot:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=user_profile)
        
    return render(request, 'chatbot/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })
