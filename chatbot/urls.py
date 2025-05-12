# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('send_message/', views.send_message, name='send_message'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('chat/<uuid:session_id>/', views.view_chat, name='view_chat'),
    path('delete_chat/<uuid:session_id>/', views.delete_chat, name='delete_chat'),
    path('update_language/', views.update_language, name='update_language'),
]