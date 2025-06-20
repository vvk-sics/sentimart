from django.urls import path
from .views import chat_api, ChatView  # Add ChatView import

urlpatterns = [
    path('api/', chat_api, name='chat_api'),
    path('', ChatView.as_view(), name='chat_home'),  # Add this line
]