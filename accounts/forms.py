from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, WhatsAppGroup
from django.contrib.auth.forms import AuthenticationForm
from products.models import Category
from .nigeria_data import NIGERIAN_STATES, get_lgas_for_state, NIGERIAN_LGAS

class PaddieLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style the username field
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Username',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        # Style the password field
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply Paddie styling to all fields
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Your email address',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a password',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm password',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })

class UserProfileForm(forms.ModelForm):
    # Update state field to use Nigerian states
    state = forms.ChoiceField(
        choices=NIGERIAN_STATES,
        required=True
    )
    
    # Make lga a choice field with dynamic population
    lga = forms.CharField(
        max_length=100, 
        required=True,
        help_text="Local Government Area, Neighborhood or Estate",
        widget=forms.Select(choices=[('', '-- Select LGA --')])
    )
    
    categories_of_interest = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    # Flag to indicate if user wants to join WhatsApp groups
    # This will be used to redirect them to the groups page later
    join_whatsapp_group = forms.BooleanField(required=False)

    
    class Meta:
        model = UserProfile
        fields = ['full_name', 'whatsapp_number', 'state', 'lga', 
                  'occupation', 'categories_of_interest', 
                  'preferred_language']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply Paddie styling to text input fields
        self.fields['full_name'].widget.attrs.update({
            'placeholder': 'Enter your full name',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['whatsapp_number'].widget.attrs.update({
            'placeholder': 'e.g. +234 800 000 0000',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['state'].widget.attrs.update({
            'placeholder': 'Select your state',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        # Populate LGA choices based on state (if exists)
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].state:
            state = kwargs['instance'].state
            self.fields['lga'].choices = get_lgas_for_state(state)
        # If form is submitted, get state from POST data
        elif 'data' in kwargs and kwargs['data'].get('state'):
            state = kwargs['data'].get('state')
            self.fields['lga'].choices = get_lgas_for_state(state)
        else:
            # Default to empty list if no state selected yet
            self.fields['lga'].choices = [('', '-- Select LGA --')]
        
        self.fields['lga'].widget.attrs.update({
            'placeholder': 'Select your LGA',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        self.fields['occupation'].widget.attrs.update({
            'placeholder': 'Your profession or occupation',
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        # Style the select dropdown for language preference
        self.fields['preferred_language'].widget.attrs.update({
            'class': 'w-full border border-gray-300 rounded-md py-3 px-4 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent'
        })
        
        # Style checkboxes
        self.fields['categories_of_interest'].widget.attrs.update({
            'class': 'w-4 h-4 text-primary focus:ring-primary rounded border-gray-300'
        })
        
        # Style the join_whatsapp_group checkbox
        if isinstance(self.fields.get('join_whatsapp_group'), forms.BooleanField):
            self.fields['join_whatsapp_group'].widget.attrs.update({
                'class': 'w-4 h-4 text-primary focus:ring-primary rounded border-gray-300'
            })

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get('state')
        lga = cleaned_data.get('lga')
        
        # If both state and LGA are provided, check if LGA is valid for the state
        if state and lga and state in NIGERIAN_LGAS:
            valid_lgas = NIGERIAN_LGAS[state]
            if lga not in valid_lgas:
                self.add_error('lga', f"'{lga}' is not a valid LGA in {state} state.")
        
        return cleaned_data