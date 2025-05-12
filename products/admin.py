# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin
from .models import Product

# Unregister the default Group admin
admin.site.unregister(Group)

class ProductInline(admin.TabularInline):
    """Inline admin for Product model"""
    model = Product
    extra = 1
    fields = ('name', 'description', 'link')

class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model"""
    list_display = ('name', 'category', 'description_preview', 'view_link')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    
    def description_preview(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + "..."
        return obj.description
    description_preview.short_description = "Description"
    
    def view_link(self, obj):
        return format_html('<a href="{}" target="_blank">View</a>', obj.link)
    view_link.short_description = "Link"

# Register models with admin site
admin.site.register(Product, ProductAdmin)
admin.site.site_header = "AskPaddie Admin"
