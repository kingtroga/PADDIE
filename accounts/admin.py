from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, WhatsAppGroup, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    filter_horizontal = ('categories_of_interest',)

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name', 'get_whatsapp', 'get_state')
    
    def get_full_name(self, obj):
        return obj.profile.full_name
    get_full_name.short_description = 'Full Name'
    
    def get_whatsapp(self, obj):
        return obj.profile.whatsapp_number
    get_whatsapp.short_description = 'WhatsApp'
    
    def get_state(self, obj):
        return obj.profile.state
    get_state.short_description = 'State'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'interested_users_count')
    prepopulated_fields = {'slug': ('name',)}
    
    def interested_users_count(self, obj):
        return obj.interested_users.count()
    interested_users_count.short_description = 'Users Interested'

@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'lga', 'members_count', 'is_national')
    list_filter = ('state', 'is_national')
    search_fields = ('name', 'state', 'lga')
    
    def members_count(self, obj):
        return obj.whatsapp_groups_joined.count()
    members_count.short_description = 'Members'