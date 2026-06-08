import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

def get_gemini_response(system_instruction, history_messages, user_message):
    """
    history_messages: List of dicts, e.g. [{'sender': 'user', 'content': 'hi'}, {'sender': 'ai', 'content': 'hello'}]
    user_message: string containing the latest user message
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    if not api_key:
        return "I'm sorry, but my Gemini API Key is not configured in this application. Please set the GEMINI_API_KEY environment variable to enable chat responses."

    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        
        contents = []
        for msg in history_messages:
            role = "user" if msg['sender'] == 'user' else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg['content']}]
            })
            
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        response = model.generate_content(contents)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "I received an empty response. Please try sending your message again."
            
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
        err_str = str(e)
        if "429" in err_str or "Quota exceeded" in err_str or "ResourceExhausted" in err_str:
            return (
                "⚠️ **API Rate Limit Exceeded**\n\n"
                "You have reached the free tier limit (5 requests per minute) for your Gemini API key. "
                "Please wait about 20-30 seconds and send your query again. If this happens frequently, consider upgrading your Google AI Studio plan to pay-as-you-go."
            )
        return f"An error occurred while generating a response. Details: {str(e)}"
