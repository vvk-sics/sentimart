from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ChatSession, ChatMessage
from .utils import ChatbotEngine
import json

@login_required
def chat_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        # Get or create chat session
        session, created = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True
        )
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            message=message,
            is_bot=False
        )
        
        # Get bot response
        bot = ChatbotEngine(request.user)
        bot_response = bot.process_message(message)
        
        # Save bot response
        ChatMessage.objects.create(
            session=session,
            message=bot_response,
            is_bot=True
        )
        
        return JsonResponse({'response': bot_response})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.views.generic import TemplateView

class ChatView(TemplateView):
    template_name = 'chatbot/chat.html'