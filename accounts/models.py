from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Category


class WhatsAppGroup(models.Model):
    name = models.CharField(max_length=100)
    link = models.URLField(help_text="WhatsApp group invite link")
    description = models.TextField()
    is_national = models.BooleanField(default=False, help_text="Is this group for all states?")
    state = models.CharField(max_length=50, blank=True)
    lga = models.CharField(max_length=100, blank=True, help_text="Local Government Area or neighborhood")
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)
    whatsapp_number = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    lga = models.CharField(max_length=100, help_text="Local Government Area, Neighborhood or Estate")
    occupation = models.CharField(max_length=100)
    categories_of_interest = models.ManyToManyField(Category, related_name="interested_users")
    language_choices = [
        ('en', 'English'),
        ('yo', 'Yoruba'),
        ('pcm', 'Pidgin'),
        ('ha', 'Hausa'),
        ('ig', 'Igbo'),
    ]
    preferred_language = models.CharField(max_length=3, choices=language_choices, default='en')
    joined_whatsapp_group = models.BooleanField(default=False)
    # Change from ForeignKey to ManyToManyField
    whatsapp_groups = models.ManyToManyField(WhatsAppGroup, blank=True, related_name="whatsapp_groups_joined")
    
    def __str__(self):
        return self.full_name

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()