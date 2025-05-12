from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, fields, BooleanField
from django.db.models.functions import TruncDay
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db import models  # Added this import for the Django models
import datetime
import json
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    """Inline admin for chat messages within a session"""
    model = ChatMessage
    extra = 0
    readonly_fields = ('timestamp', 'get_sender', 'content_preview', 'product_link')
    fields = ('get_sender', 'content_preview', 'timestamp', 'product_link')
    ordering = ('timestamp',)
    can_delete = False
    show_change_link = True
    max_num = 0  # Prevents adding new messages from the admin
    
    def get_sender(self, obj):
        return "User" if obj.is_user else "PADDIE"
    get_sender.short_description = "Sender"
    
    def content_preview(self, obj):
        # Show the first 100 characters of the content
        preview = obj.content[:100]
        if len(obj.content) > 100:
            preview += "..."
        return preview
    content_preview.short_description = "Message"
    
    def product_link(self, obj):
        if obj.product_mentioned:
            url = reverse('admin:products_product_change', args=[obj.product_mentioned.id])
            return format_html('<a href="{}">{}</a>', url, obj.product_mentioned.name)
        return "-"
    product_link.short_description = "Product Mentioned"

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin configuration for ChatSession model"""
    list_display = ('session_id_short', 'user_name', 'language', 'created_at', 'message_count', 'last_activity')
    list_filter = ('language', 'created_at')
    search_fields = ('user_name', 'session_id')
    readonly_fields = ('session_id', 'created_at')
    inlines = [ChatMessageInline]
    date_hierarchy = 'created_at'
    
    def session_id_short(self, obj):
        # Display shortened session ID for readability
        return str(obj.session_id)[:8] + "..."
    session_id_short.short_description = "Session ID"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Add annotation to count messages in each session
        return qs.annotate(message_count_annotation=Count('messages'))
    
    def message_count(self, obj):
        return obj.message_count_annotation
    message_count.admin_order_field = 'message_count_annotation'
    message_count.short_description = "Messages"
    
    def last_activity(self, obj):
        last_message = ChatMessage.objects.filter(chat=obj).order_by('-timestamp').first()
        if last_message:
            return last_message.timestamp
        return obj.created_at
    last_activity.short_description = "Last Activity"
    
    def has_add_permission(self, request):
        # Prevent creating sessions directly in admin - they should be created by the app
        return False

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ChatMessage model"""
    list_display = ('id', 'get_session_user', 'sender_type', 'content_preview', 'timestamp', 'has_product')
    list_filter = ('is_user', 'timestamp', ('product_mentioned', admin.EmptyFieldListFilter))  # Fixed list_filter syntax
    search_fields = ('content', 'chat__user_name')
    readonly_fields = ('timestamp', 'chat_link')
    date_hierarchy = 'timestamp'
    fieldsets = (
        (None, {
            'fields': ('chat_link', 'is_user', 'timestamp')
        }),
        ('Message Content', {
            'fields': ('content',)
        }),
        ('Product Information', {
            'fields': ('product_mentioned',),
            'classes': ('collapse',),
            'description': 'Product mentioned in this message'
        }),
    )
    
    def get_session_user(self, obj):
        return obj.chat.user_name or f"Anonymous ({str(obj.chat.session_id)[:8]})"
    get_session_user.admin_order_field = 'chat__user_name'
    get_session_user.short_description = "User"
    
    def sender_type(self, obj):
        return "User" if obj.is_user else "PADDIE"
    sender_type.admin_order_field = 'is_user'
    sender_type.short_description = "Sender"
    
    def content_preview(self, obj):
        # Show the first 50 characters of the content
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += "..."
        return preview
    content_preview.short_description = "Message"
    
    def has_product(self, obj):
        return obj.product_mentioned is not None
    has_product.boolean = True
    has_product.admin_order_field = 'product_mentioned__isnull'
    has_product.short_description = "Product"
    
    def chat_link(self, obj):
        url = reverse('admin:chatbot_chatsession_change', args=[obj.chat.id])
        return format_html('<a href="{}">{} ({})</a>', 
                           url, 
                           obj.chat.user_name or "Anonymous",
                           str(obj.chat.session_id)[:8])
    chat_link.short_description = "Chat Session"
    
    def has_add_permission(self, request):
        # Prevent creating messages directly in admin - they should be created by the app
        return False

# Analytics Dashboard View
class ChatAnalyticsDashboard(admin.ModelAdmin):
    """Admin dashboard for chat analytics"""
    change_list_template = 'admin/chatbot/analytics_dashboard.html'

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True  # Need True to view the page
    
    def changelist_view(self, request, extra_context=None):
        # Get date range from request
        date_range = request.GET.get('date_range', 'month')
        
        # Calculate date ranges
        today = timezone.now().date()
        
        if date_range == 'today':
            start_date = today
            end_date = today
            prev_start_date = today - datetime.timedelta(days=1)
            prev_end_date = prev_start_date
        elif date_range == 'week':
            start_date = today - datetime.timedelta(days=6)
            end_date = today
            prev_start_date = start_date - datetime.timedelta(days=7)
            prev_end_date = start_date - datetime.timedelta(days=1)
        elif date_range == 'month':
            start_date = today - datetime.timedelta(days=29)
            end_date = today
            prev_start_date = start_date - datetime.timedelta(days=30)
            prev_end_date = start_date - datetime.timedelta(days=1)
        elif date_range == 'custom':
            try:
                start_date = datetime.datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
                date_diff = (end_date - start_date).days + 1
                prev_start_date = start_date - datetime.timedelta(days=date_diff)
                prev_end_date = start_date - datetime.timedelta(days=1)
            except (ValueError, TypeError):
                # Default to last 30 days if custom range is invalid
                start_date = today - datetime.timedelta(days=29)
                end_date = today
                prev_start_date = start_date - datetime.timedelta(days=30)
                prev_end_date = start_date - datetime.timedelta(days=1)
        else:
            start_date = today - datetime.timedelta(days=29)
            end_date = today
            prev_start_date = start_date - datetime.timedelta(days=30)
            prev_end_date = start_date - datetime.timedelta(days=1)
        
        # Query current period sessions
        period_sessions = ChatSession.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Query previous period sessions for comparison
        prev_period_sessions = ChatSession.objects.filter(
            created_at__date__gte=prev_start_date,
            created_at__date__lte=prev_end_date
        )
        
        # Calculate key metrics
        total_sessions = period_sessions.count()
        prev_total_sessions = prev_period_sessions.count()
        
        # Calculate percentage increase in sessions
        if prev_total_sessions > 0:
            new_sessions_percent = round(((total_sessions - prev_total_sessions) / prev_total_sessions) * 100)
        else:
            new_sessions_percent = 100 if total_sessions > 0 else 0
        
        # Get messages for current period
        period_messages = ChatMessage.objects.filter(
            chat__in=period_sessions
        )
        
        total_messages = period_messages.count()
        
        # Average messages per session
        messages_per_session = round(total_messages / total_sessions) if total_sessions > 0 else 0
        
        # Count unique users
        active_users = period_sessions.values('user_name').distinct().count()
        
        # Count new users (not in previous period)
        prev_users = set(prev_period_sessions.values_list('user_name', flat=True).distinct())
        current_users = set(period_sessions.values_list('user_name', flat=True).distinct())
        new_users = len(current_users - prev_users)
        
        # Product mentions
        products_mentioned = period_messages.exclude(product_mentioned__isnull=True).count()
        sessions_with_products = period_messages.exclude(product_mentioned__isnull=True).values('chat').distinct().count()
        
        # Get sessions by day for chart
        date_range_list = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        date_labels = [d.strftime('%b %d') for d in date_range_list]
        
        # Count sessions per day
        sessions_by_day = period_sessions.annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Create a dict with dates as keys and counts as values
        sessions_dict = {s['day'].date(): s['count'] for s in sessions_by_day}
        
        # Fill in the session counts for the chart
        session_counts = [sessions_dict.get(d, 0) for d in date_range_list]
        
        # Message types count
        user_messages = period_messages.filter(is_user=True).count()
        ai_messages = period_messages.filter(is_user=False).count()
        
        # Language distribution
        language_data = period_sessions.values('language').annotate(count=Count('id')).order_by('-count')
        language_labels = [item['language'] for item in language_data]
        language_counts = [item['count'] for item in language_data]
        
        # Session duration distribution (approximation based on first and last message)
        duration_counts = [0, 0, 0, 0, 0]  # <1min, 1-5min, 5-15min, 15-30min, >30min
        
        for session in period_sessions:
            messages = ChatMessage.objects.filter(chat=session).order_by('timestamp')
            if messages.count() < 2:  # Skip sessions with less than 2 messages
                continue
                
            first_msg = messages.first()
            last_msg = messages.last()
            
            if first_msg and last_msg:
                # Calculate duration in minutes
                duration = (last_msg.timestamp - first_msg.timestamp).total_seconds() / 60
                
                # Increment appropriate duration bucket
                if duration < 1:
                    duration_counts[0] += 1
                elif duration < 5:
                    duration_counts[1] += 1
                elif duration < 15:
                    duration_counts[2] += 1
                elif duration < 30:
                    duration_counts[3] += 1
                else:
                    duration_counts[4] += 1
        
        # Top products mentioned
        from products.models import Product
        top_products_data = ChatMessage.objects.filter(
            chat__in=period_sessions
        ).exclude(product_mentioned__isnull=True).values(
            'product_mentioned'
        ).annotate(
            count=Count('product_mentioned')
        ).order_by('-count')[:5]
        
        top_products = []
        for item in top_products_data:
            try:
                product = Product.objects.get(id=item['product_mentioned'])
                top_products.append({
                    'name': product.name,
                    'count': item['count']
                })
            except Product.DoesNotExist:
                continue
        
        # Most active users
        top_users_data = period_sessions.values('user_name').annotate(
            sessions=Count('id')
        ).order_by('-sessions')[:5]
        
        top_users = [{
            'name': item['user_name'] or 'Anonymous',
            'sessions': item['sessions']
        } for item in top_users_data]
        
        # Context to send to template
        context = {
            'total_sessions': total_sessions,
            'new_sessions_percent': new_sessions_percent,
            'total_messages': total_messages,
            'messages_per_session': messages_per_session,
            'active_users': active_users,
            'new_users': new_users,
            'products_mentioned': products_mentioned,
            'sessions_with_products': sessions_with_products,
            'date_labels': json.dumps(date_labels),
            'session_counts': json.dumps(session_counts),
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'language_labels': json.dumps(language_labels),
            'language_counts': json.dumps(language_counts),
            'duration_counts': json.dumps(duration_counts),
            'top_products': top_products,
            'top_users': top_users,
            'selected_range': date_range,
            'start_date': start_date,
            'end_date': end_date,
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return super().changelist_view(request, extra_context=context)

# Create a dummy model to register with the admin
class ChatAnalyticsDashboardModel(models.Model):
    """
    Dummy model for the analytics dashboard.
    This model is never used in the database, it just exists
    so we can register our admin view.
    """
    class Meta:
        managed = False  # No database table creation or deletion operations will be performed for this model
        verbose_name_plural = "Chat Analytics Dashboard"
        app_label = 'chatbot'  # Must match your app name
        
    def __str__(self):
        return "Chat Analytics Dashboard"

# Register the dashboard with the admin site
admin.site.register(ChatAnalyticsDashboardModel, ChatAnalyticsDashboard)