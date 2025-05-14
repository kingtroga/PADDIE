from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, WhatsAppGroup, UserProfile
from django import forms
from .nigeria_data import NIGERIAN_STATES, get_lgas_for_state, NIGERIAN_LGAS

# Create a custom form for WhatsAppGroup
class WhatsAppGroupForm(forms.ModelForm):
    state = forms.ChoiceField(choices=NIGERIAN_STATES, required=False)
    lga = forms.ChoiceField(choices=[], required=False)
    
    class Meta:
        model = WhatsAppGroup
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(WhatsAppGroupForm, self).__init__(*args, **kwargs)
        
        # If instance exists and has state, populate LGAs for that state
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].state:
            state = kwargs['instance'].state
            self.fields['lga'].choices = get_lgas_for_state(state)
        # If form is submitted, get state from POST data
        elif args and args[0] and 'state' in args[0]:
            state = args[0].get('state')
            self.fields['lga'].choices = get_lgas_for_state(state)
        else:
            # Default to empty list if no state selected yet
            self.fields['lga'].choices = [('', '-- Select LGA --')]
        
        # If is_national is checked, make state and lga not required
        if args and args[0] and args[0].get('is_national'):
            self.fields['state'].required = False
            self.fields['lga'].required = False

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

# Fixed WhatsAppGroupAdmin - only register once and use the custom form
@admin.register(WhatsAppGroup)
class WhatsAppGroupAdmin(admin.ModelAdmin):
    form = WhatsAppGroupForm  # Use the custom form
    list_display = ('name', 'state', 'lga', 'members_count', 'is_national')
    list_filter = ('state', 'is_national')
    search_fields = ('name', 'state', 'lga')
    
    def members_count(self, obj):
        return obj.whatsapp_groups_joined.count()
    members_count.short_description = 'Members'
    
    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.min.js',  # Django admin's jQuery
            'admin/js/jquery.init.js',  # Initializes django.jQuery
            'js/lga_dropdown.js',
        )