from django.contrib import admin
from .models import ChatSession, ChatMessage, UserProfile

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'user__username')
    ordering = ('-created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'content_snippet', 'timestamp')
    list_filter = ('sender', 'timestamp')
    search_fields = ('content', 'session__title', 'session__user__username')
    ordering = ('timestamp',)

    def content_snippet(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_snippet.short_description = 'Content'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    search_fields = ('user__username', 'phone', 'address')
