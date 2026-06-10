import logging
from django.conf import settings
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

def get_gemini_response(system_instruction, history_messages, user_message):
    """
    Query the Gemini API using the new google-genai SDK.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    if not api_key:
        return "I'm sorry, but my Gemini API Key is not configured in this application. Please set the GEMINI_API_KEY environment variable to enable chat responses."

    try:
        # Initialize client with the API key
        client = genai.Client(api_key=api_key)
        
        # Build types.Content list for conversation history
        contents = []
        for msg in history_messages:
            role = "user" if msg['sender'] == 'user' else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg['content'])]
                )
            )
            
        # Append the new user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            )
        )
        
        # Request generation using gemini-2.5-flash with system instruction config
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return "I received an empty response. Please try sending your message again."
            
    except APIError as e:
        logger.error(f"Gemini APIError: {str(e)}", exc_info=True)
        err_str = str(e)
        if e.code == 429 or "Quota exceeded" in err_str or "ResourceExhausted" in err_str:
            return (
                "⚠️ **API Rate Limit Exceeded (429)**\n\n"
                "You have reached the free tier limit (5 requests per minute) for your Gemini API key. "
                "Please wait about 20-30 seconds and send your query again. If this happens frequently, consider upgrading your Google AI Studio plan to pay-as-you-go."
            )
        elif e.code == 403 or "denied access" in err_str or "PERMISSION_DENIED" in err_str:
            return (
                "⚠️ **API Key Permission Denied (403)**\n\n"
                "Google has denied access to this API key or project. This is a common issue when a Google AI Studio project is flagged, suspended, or "
                "when using a Google Workspace account that restricts external API usage.\n\n"
                "**To fix this:** Please create a new API key in Google AI Studio using a standard personal `@gmail.com` account and update the `GEMINI_API_KEY` on Render."
            )
        return f"An API error occurred while generating a response. Details: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error calling Gemini API: {str(e)}", exc_info=True)
        return f"An unexpected error occurred while generating a response. Details: {str(e)}"
