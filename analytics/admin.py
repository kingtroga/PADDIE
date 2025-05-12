# analytics/admin.py
from django.contrib import admin
from django.db import models
from django.db.models import Count, Q, F, Sum, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django.template.response import TemplateResponse
import datetime
import json

# Import your models
from chatbot.models import ChatSession, ChatMessage
from products.models import Category, Product
from accounts.models import WhatsAppGroup, UserProfile
from django.contrib.auth.models import User

class AnalyticsDashboardModel(models.Model):
    """
    Dummy model for analytics dashboard.
    Not used in database, just for the admin interface.
    """
    class Meta:
        managed = False
        verbose_name_plural = "Analytics Dashboard"
        app_label = 'analytics'
        
    def __str__(self):
        return "Analytics Dashboard"

class AnalyticsDashboardAdmin(admin.ModelAdmin):
    """Admin view for analytics dashboard"""
    change_list_template = 'admin/analytics/dashboard.html'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def changelist_view(self, request, extra_context=None):
        # Get date range from request
        date_range = request.GET.get('date_range', 'month')
        
        # Calculate date ranges
        today = timezone.now().date()
        
        if date_range == 'today':
            start_date = today
            end_date = today
        elif date_range == 'week':
            start_date = today - datetime.timedelta(days=6)
            end_date = today
        elif date_range == 'month':
            start_date = today - datetime.timedelta(days=29)
            end_date = today
        elif date_range == 'custom':
            try:
                start_date = datetime.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                start_date = today - datetime.timedelta(days=29)
                end_date = today
        else:
            start_date = today - datetime.timedelta(days=29)
            end_date = today
        
        # Get date range for charts
        date_range_list = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        date_labels = [d.strftime('%b %d') for d in date_range_list]
        
        # CHAT ANALYTICS
        # Chat session statistics
        chat_sessions = ChatSession.objects.filter(created_at__date__range=(start_date, end_date))
        total_sessions = chat_sessions.count()
        
        # Messages per language
        language_data = chat_sessions.values('language').annotate(count=Count('id')).order_by('-count')
        language_labels = [item.get('language', 'Unknown') for item in language_data]
        language_counts = [item.get('count', 0) for item in language_data]
        
        # Sessions over time
        sessions_by_day = ChatSession.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        sessions_dict = {s['day'].date(): s['count'] for s in sessions_by_day}
        session_counts = [sessions_dict.get(d, 0) for d in date_range_list]
        
        # Chat messages statistics
        chat_messages = ChatMessage.objects.filter(
            timestamp__date__range=(start_date, end_date)
        )
        total_messages = chat_messages.count()
        user_messages = chat_messages.filter(is_user=True).count()
        ai_messages = chat_messages.filter(is_user=False).count()
        
        # Messages with product mentions
        messages_with_products = chat_messages.exclude(product_mentioned__isnull=True).count()
        percent_with_products = round((messages_with_products / total_messages * 100) if total_messages > 0 else 0)
        
        # Average messages per session
        avg_messages = round(total_messages / total_sessions) if total_sessions > 0 else 0
        
        # PRODUCT ANALYTICS
        # Product statistics
        total_products = Product.objects.count()
        products_by_category = list(Product.objects.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        category_names = [item.get('category__name', 'Unknown') for item in products_by_category]
        category_product_counts = [item.get('count', 0) for item in products_by_category]
        
        # Most mentioned products
        top_products = list(Product.objects.annotate(
            mention_count=Count('mentioned_in')
        ).filter(mention_count__gt=0).order_by('-mention_count')[:5].values('name', 'mention_count'))
        
        # USER ANALYTICS
        # WhatsApp group statistics
        total_groups = WhatsAppGroup.objects.count()
        user_profiles = UserProfile.objects.all()
        total_users = User.objects.count()
        
        # User language preferences
        user_language_data = list(user_profiles.values('preferred_language').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        user_language_labels = [item.get('preferred_language', 'Unknown') for item in user_language_data]
        user_language_counts = [item.get('count', 0) for item in user_language_data]
        
        # Users with whatsapp groups
        users_with_groups = user_profiles.filter(joined_whatsapp_group=True).count()
        users_without_groups = user_profiles.filter(joined_whatsapp_group=False).count()
        
        # Category interests
        category_interests = list(Category.objects.annotate(
            interest_count=Count('interested_users')
        ).order_by('-interest_count').values('name', 'interest_count'))
        
        category_interest_names = [item.get('name', 'Unknown') for item in category_interests]
        category_interest_counts = [item.get('interest_count', 0) for item in category_interests]
        
        # Prepare data for template
        context = {
            # Date info
            'selected_range': date_range,
            'start_date': start_date,
            'end_date': end_date,
            'date_labels': json.dumps(date_labels),
            
            # Chat stats
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'messages_with_products': messages_with_products,
            'percent_with_products': percent_with_products,
            'avg_messages_per_session': avg_messages,
            'session_counts': json.dumps(session_counts),
            'language_labels': json.dumps(language_labels),
            'language_counts': json.dumps(language_counts),
            
            # Product stats
            'total_products': total_products,
            'category_names': json.dumps(category_names),
            'category_product_counts': json.dumps(category_product_counts),
            'top_products': top_products,
            
            # User stats
            'total_groups': total_groups,
            'total_users': total_users,
            'users_with_groups': users_with_groups,
            'users_without_groups': users_without_groups,
            'user_language_labels': json.dumps(user_language_labels),
            'user_language_counts': json.dumps(user_language_counts),
            'category_interest_names': json.dumps(category_interest_names),
            'category_interest_counts': json.dumps(category_interest_counts),
            
            # Last updated
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return super().changelist_view(request, extra_context=context)

# Register the admin view
admin.site.register(AnalyticsDashboardModel, AnalyticsDashboardAdmin)