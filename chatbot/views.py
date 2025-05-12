# chatbot/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
import uuid
from .models import ChatSession, ChatMessage
from products.models import Product
from .microservices.chatbot import get_chat_completion_from_openrouter, extract_product_id_with_ai

@login_required
def chat_home(request):
    """Render the main chat interface, requiring authentication"""
    # Create a new chat session or get an existing one
    session_id = request.session.get('chat_session_id')
    
    if session_id:
        try:
            # If we have a session ID, try to get the existing chat session
            chat_session = ChatSession.objects.get(session_id=session_id, user_name=request.user.username)
            # We'll keep the language that's already set in the chat session
        except ChatSession.DoesNotExist:
            # If session doesn't exist, create new with user's preferred language as fallback
            chat_session = ChatSession.objects.create(
                user_name=request.user.username,
                language=request.user.profile.preferred_language
            )
            request.session['chat_session_id'] = str(chat_session.session_id)
    else:
        # If no session at all, create new with user's preferred language as fallback
        chat_session = ChatSession.objects.create(
            user_name=request.user.username,
            language=request.user.profile.preferred_language
        )
        request.session['chat_session_id'] = str(chat_session.session_id)
    
    # Get previous messages for this session
    messages = ChatMessage.objects.filter(chat=chat_session)
    
    # Get all chat sessions for this user
    user_chat_sessions = ChatSession.objects.filter(user_name=request.user.username).order_by('-created_at')
    
    context = {
        'chat_session': chat_session,
        'messages': messages,
        'chat_sessions': user_chat_sessions,
        'language_choices': dict(ChatSession._meta.get_field('language').choices)
    }
    
    return render(request, 'chatbot/chat.html', context)

@login_required
@csrf_exempt
@require_POST
def send_message(request):
    """Process user message and get AI response"""
    data = json.loads(request.body)
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id')
    
    if not user_message or not session_id:
        return JsonResponse({'error': 'Message and session ID are required'}, status=400)
    
    try:
        # Get the chat session and verify it belongs to the current user
        chat_session = ChatSession.objects.get(session_id=session_id, user_name=request.user.username)
        
        # Save user message
        user_chat_message = ChatMessage.objects.create(
            chat=chat_session,
            is_user=True,
            content=user_message
        )
        
        # Get all previous messages in this chat session
        previous_messages = ChatMessage.objects.filter(chat=chat_session).order_by('timestamp')
        
        # Format the message history for the AI
        chat_history = []
        
        # Add previous messages to the history (except the one we just saved)
        for msg in previous_messages:
            if msg.id != user_chat_message.id:  # Skip the message we just added
                role = "user" if msg.is_user else "assistant"
                chat_history.append({"role": role, "content": msg.content})
        
        # Append the current user message with language instruction
        language_instruction = f"I want your response in {chat_session.language} language."
        current_message = f"{user_message}\n\n{language_instruction}"
        chat_history.append({"role": "user", "content": current_message})
        
        # Get response from AI with chat history
        ai_response = get_chat_completion_from_openrouter(current_message, history=chat_history)
        
        # Extract product ID from the AI's response
        product_id = extract_product_id_with_ai(ai_response)
        
        # Create AI message with product mention if applicable
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                ai_chat_message = ChatMessage.objects.create(
                    chat=chat_session,
                    is_user=False,
                    content=ai_response,
                    product_mentioned=product
                )
            except Product.DoesNotExist:
                ai_chat_message = ChatMessage.objects.create(
                    chat=chat_session,
                    is_user=False,
                    content=ai_response
                )
        else:
            ai_chat_message = ChatMessage.objects.create(
                chat=chat_session,
                is_user=False,
                content=ai_response
            )
        
        return JsonResponse({
            'success': True,
            'message_id': str(ai_chat_message.id),
            'response': ai_response,
            'timestamp': ai_chat_message.timestamp.strftime('%H:%M')
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Invalid session'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def new_chat(request):
    """Start a new chat session"""
    # Create a new session with the user's preferred language
    user_language = request.user.profile.preferred_language
    chat_session = ChatSession.objects.create(
        user_name=request.user.username,
        language=user_language
    )
    request.session['chat_session_id'] = str(chat_session.session_id)
    
    return redirect('chat_home')

@login_required
def view_chat(request, session_id):
    """Load a specific chat session"""
    try:
        # Verify the chat session belongs to the current user
        chat_session = ChatSession.objects.get(session_id=session_id, user_name=request.user.username)
        request.session['chat_session_id'] = str(chat_session.session_id)
        return redirect('chat_home')
    except ChatSession.DoesNotExist:
        return redirect('chat_home')

@login_required
@csrf_exempt
@require_POST
def update_language(request):
    """Update the language preference for a chat session"""
    data = json.loads(request.body)
    session_id = data.get('session_id')
    language = data.get('language')
    
    if not session_id or not language:
        return JsonResponse({'error': 'Session ID and language are required'}, status=400)
    
    try:
        # Verify the chat session belongs to the current user
        chat_session = ChatSession.objects.get(session_id=session_id, user_name=request.user.username)
        chat_session.language = language
        chat_session.save()
        
        return JsonResponse({
            'success': True,
            'language': language
        })
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Invalid session'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_chat(request, session_id):
    """Delete a chat session"""
    try:
        # Verify the chat session belongs to the current user
        chat_session = ChatSession.objects.get(session_id=session_id, user_name=request.user.username)
        chat_session.delete()
        
        # If the deleted session was the current one, create a new session
        if request.session.get('chat_session_id') == str(session_id):
            # Create new session with user's preferred language
            user_language = request.user.profile.preferred_language
            new_session = ChatSession.objects.create(
                user_name=request.user.username,
                language=user_language
            )
            request.session['chat_session_id'] = str(new_session.session_id)
        
        return redirect('chat_home')
    except ChatSession.DoesNotExist:
        return redirect('chat_home')