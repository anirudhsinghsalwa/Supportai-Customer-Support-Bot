import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import ChatSession, ChatMessage

def ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def chat_home(request):
    session_key = ensure_session_key(request)
    sessions = ChatSession.objects.filter(session_key=session_key)
    latest_session = sessions.first()
    
    if latest_session:
        return redirect('chatbot:chat_session_detail', session_id=latest_session.id)
        
    return render(request, 'chatbot/chat.html', {
        'sessions': sessions,
        'active_session': None,
        'chat_messages': []
    })

def chat_session_detail(request, session_id):
    session_key = ensure_session_key(request)
    sessions = ChatSession.objects.filter(session_key=session_key)
    active_session = get_object_or_404(ChatSession, id=session_id, session_key=session_key)
    chat_messages = active_session.messages.all()
    
    return render(request, 'chatbot/chat.html', {
        'sessions': sessions,
        'active_session': active_session,
        'chat_messages': chat_messages
    })

def create_session(request):
    session_key = ensure_session_key(request)
    session = ChatSession.objects.create(session_key=session_key, title="New Conversation")
    return redirect('chatbot:chat_session_detail', session_id=session.id)

@require_POST
def delete_session(request, session_id):
    session_key = ensure_session_key(request)
    session = get_object_or_404(ChatSession, id=session_id, session_key=session_key)
    session.delete()
    messages.success(request, "Conversation deleted.")
    return redirect('chatbot:chat_home')

@require_POST
def send_message_api(request, session_id):
    session_key = ensure_session_key(request)
    session = get_object_or_404(ChatSession, id=session_id, session_key=session_key)
    
    try:
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
