from django.db import models

# Create your models here.
class ChatMessage(models.Model):
    content = models.TextField()
    role = models.CharField(max_length=10)