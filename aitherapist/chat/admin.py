from django.contrib import admin

# Register your models here.
from .models import TherapySession, ChatMessage, MoodEntry

admin.site.register(TherapySession)
admin.site.register(ChatMessage)
admin.site.register(MoodEntry)