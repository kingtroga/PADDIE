from django.db import models
import uuid
from products.models import Product

# Create your models here.
class ChatSession(models.Model):
    """Model for storing chat sessions"""
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, 
                                choices=[('en', 'English'), 
                                         ('pcm', 'Pidgin'), 
                                         ('yo', 'Yoruba'), 
                                         ('ha', 'Hausa'),
                                         ('ig', 'Igbo')],
                                default='en')
    
    def __str__(self):
        return f"Chat {self.session_id} - {self.user_name or 'Anonymous'}"

class ChatMessage(models.Model):
    """Model for storing individual chat messages"""
    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    is_user = models.BooleanField(default=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    product_mentioned = models.ForeignKey(Product, on_delete=models.SET_NULL, 
                                         null=True, blank=True, 
                                         related_name="mentioned_in")
    
    def __str__(self):
        return f"{'User' if self.is_user else 'PADDIE'}: {self.content[:50]}..."

    class Meta:
        ordering = ['timestamp']