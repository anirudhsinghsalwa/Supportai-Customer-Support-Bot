from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Chat Dashboard
    path('', views.chat_home, name='chat_home'),
    path('chat/<int:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('chat/new/', views.create_session, name='create_session'),
    path('chat/delete/<int:session_id>/', views.delete_session, name='delete_session'),
    
    # API endpoints
    path('chat/send/<int:session_id>/', views.send_message_api, name='send_message_api'),
]
