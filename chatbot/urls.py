from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Chat Dashboard
    path('', views.chat_home, name='chat_home'),
    path('chat/<int:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('chat/new/', views.create_session, name='create_session'),
    path('chat/delete/<int:session_id>/', views.delete_session, name='delete_session'),
    
    # API endpoints
    path('chat/send/<int:session_id>/', views.send_message_api, name='send_message_api'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
]
