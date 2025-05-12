from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm
from .models import WhatsAppGroup
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import json

@require_http_methods(["GET", "POST"])
def custom_logout(request):
    # Get the user before logout for the message
    was_logged_in = request.user.is_authenticated
    
    # Properly log the user out
    logout(request)
    
    # Clear session data
    request.session.flush()
    
    # Delete the session cookie
    response = redirect('login')
    response.delete_cookie('sessionid')
    
    # Add a success message if they were logged in
    if was_logged_in:
        messages.success(request, 'You have been successfully logged out.')
    
    # Redirect to login page
    return response

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            # Update the user's profile
            user.profile.full_name = profile_form.cleaned_data.get('full_name')
            user.profile.whatsapp_number = profile_form.cleaned_data.get('whatsapp_number')
            user.profile.state = profile_form.cleaned_data.get('state')
            user.profile.lga = profile_form.cleaned_data.get('lga')
            user.profile.occupation = profile_form.cleaned_data.get('occupation')
            user.profile.preferred_language = profile_form.cleaned_data.get('preferred_language')
            
            # Save the profile to apply the changes
            user.save()
            
            # Now use the profile form's save method to handle M2M fields
            profile_form = UserProfileForm(request.POST, instance=user.profile)
            profile = profile_form.save()
            
            # Check if user wants to join WhatsApp groups
            join_whatsapp = profile_form.cleaned_data.get('join_whatsapp_group')
            
            messages.success(request, 'Account created successfully!')
            
            # Authenticate the user
            from django.contrib.auth import login
            login(request, user)
            
            # Redirect to WhatsApp groups page if requested
            if join_whatsapp:
                return redirect('whatsapp_groups')
            else:
                return redirect('profile')  # or any other default redirect
    else:
        user_form = UserRegisterForm()
        profile_form = UserProfileForm()
    
    return render(request, 'accounts/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        
        if profile_form.is_valid():
            profile = profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=request.user.profile)
    
    # Display WhatsApp groups if user has joined any
    whatsapp_groups = None
    if request.user.profile.joined_whatsapp_group:
        whatsapp_groups = request.user.profile.whatsapp_groups.all()
    
    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'whatsapp_groups': whatsapp_groups
    })

@login_required
def whatsapp_groups(request):
    """Display available WhatsApp groups for the user to join"""
    user_state = request.user.profile.state
    user_lga = request.user.profile.lga
    
    # Get relevant groups
    local_groups = WhatsAppGroup.objects.filter(
        state__iexact=user_state
    ).order_by('name')
    
    # Get more specific groups for user's LGA if available
    lga_groups = local_groups.filter(
        lga__iexact=user_lga
    )
    
    # Get national groups
    national_groups = WhatsAppGroup.objects.filter(
        is_national=True
    ).order_by('name')
    
    # Update the user's joined_whatsapp_group flag if they view this page
    if not request.user.profile.joined_whatsapp_group:
        request.user.profile.joined_whatsapp_group = True
        request.user.profile.save()
    
    return render(request, 'accounts/whatsapp_groups.html', {
        'lga_groups': lga_groups,
        'local_groups': local_groups.exclude(id__in=lga_groups.values_list('id', flat=True)),
        'national_groups': national_groups
    })

@login_required
@require_POST
@csrf_protect
def join_whatsapp_group(request):
    """Add a WhatsApp group to the user's profile"""
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        # Get the group
        group = WhatsAppGroup.objects.get(id=group_id)
        
        # Add it to user's profile if not already added
        if group not in request.user.profile.whatsapp_groups.all():
            request.user.profile.whatsapp_groups.add(group)
            request.user.profile.joined_whatsapp_group = True
            request.user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'You have joined the group successfully!'
        })
    except WhatsAppGroup.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Group not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    return render(request, 'errors/400.html', status=400)