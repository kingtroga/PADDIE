#chatbot/microservices/chatbot.py
import requests
import os
from .utils import get_products_and_categories_json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_chat_completion_from_openrouter(user_message, history=None):
    """
    Sends a message to OpenRouter using the deepseek-chat model with PADDIE system prompt
    and returns the assistant's reply.
    
    Args:
        user_message (str): The current user message
        history (list, optional): List of previous message objects with role and content
    """

    # Get dynamic product and category JSON
    product_json = get_products_and_categories_json()

    system_prompt = f"""
You are PADDIE, a friendly and professional Nigerian safety assistant. Your job is to answer only safety-related questions clearly, accurately, and in a localized tone (English, Pidgin, or Nigerian-accented English when appropriate).

🎯 Rules for every reply:

- Focus only on safety advice (e.g., road, fire, home, workplace, child, food, event, first-aid).
- When a user's question relates to a product (e.g., fire extinguisher, first-aid kit, reflective jacket, PPE), recommend a SafetyPlus product clearly and naturally.
  → Example: "For that kind situation, you fit use the SafetyPlus fire extinguisher. It's portable and easy to use. [Link or placeholder for product]"
- If the user says something unrelated to safety, politely say: "Sorry, I can only answer safety-related questions. Please ask me something about safety."
- If it's an emergency (e.g., snake bite, accident, bleeding), give urgent steps and tell the user to call a medical professional immediately.
- If the user asks in Pidgin English, reply in simple Pidgin.
- Keep responses clear, practical, and sometimes slightly conversational to build trust.

🛍️ Below is a list of SafetyPlus products and categories for reference when recommending items:
{product_json}

IMPORTANT: Always return your answers in plain text e.g return 
'Safety refers to the state of being protected from harm, danger, or injury. It involves taking precautions to prevent accidents, hazards, or risks in various environments—such as at home, on the road, in the workplace, or during emergencies.  

Key aspects of safety include:  
- Prevention (e.g., using protective gear, following safety guidelines).  
- Preparedness (e.g., having fire extinguishers, first-aid kits).  
- Awareness (e.g., recognizing hazards and responding appropriately).'

instead of 
'**Safety** refers to the state of being protected from harm, danger, or injury. It involves taking precautions to prevent accidents, hazards, or risks in various environments—such as at home, on the road, in the workplace, or during emergencies.  

Key aspects of safety include:  
- **Prevention** (e.g., using protective gear, following safety guidelines).  
- **Preparedness** (e.g., having fire extinguishers, first-aid kits).  
- **Awareness** (e.g., recognizing hazards and responding appropriately).  '
NO USING OF DOUBLE ** to show important words or phrases.
"""

    # Initialize messages with system prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    # If history is provided, add it to messages
    if history and isinstance(history, list):
        # Filter out any system messages from history (we'll use our own)
        filtered_history = [msg for msg in history if msg.get("role") != "system"]
        messages.extend(filtered_history)
    else:
        # If no history or invalid history, just add the current user message
        messages.append({"role": "user", "content": user_message})

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324:free", # Nice model but slow # deepseek/deepseek-prover-v2:free # Fast model but Neutral 
        "messages": messages,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://safetyplusone.com",  # change to your real domain
        "X-Title": "Paddie Safety Assistant"
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return "Sorry, something went wrong while contacting the safety server."



def extract_product_id_with_ai(message_text):
    """
    Uses OpenRouter AI to extract product IDs mentioned in a message.
    
    Args:
        message_text (str): The message text to analyze for product mentions
        
    Returns:
        int or None: The ID of the mentioned product, or None if no products were mentioned
    """
    import requests
    import os
    import json
    from .utils import get_products_and_categories_json
    
    # Get OpenRouter API key from environment
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Get product JSON data
    product_json = get_products_and_categories_json()
    
    # Create a focused system prompt specifically for product extraction
    system_prompt = f"""
    You are a product extraction assistant. Your only job is to identify if a SafetyPlus product 
    is mentioned in the given message, and extract its product ID.
    
    Here is a JSON of all SafetyPlus products in the database:
    {product_json}
    
    RULES:
    1. Examine the message carefully for any explicit mention of a SafetyPlus product by name.
    2. If a product is mentioned, return ONLY the product ID as a number.
    3. If no product is mentioned, return ONLY the word "None".
    4. If multiple products are mentioned, return ONLY the ID of the first product mentioned.
    5. Your response must be just the ID number or "None", nothing else.
    """
    
    payload = {
        "model": "deepseek/deepseek-prover-v2:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract product ID from this message: {message_text}"}
        ],
        "temperature": 0.1  # Low temperature for more deterministic results
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://safetyplusone.com",
        "X-Title": "Product Extraction Assistant"
    }
    
    try:
        # Make the API call to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            # Extract the response
            ai_response = response.json()["choices"][0]["message"]["content"].strip()
            
            # Process the response
            if ai_response.lower() == "none":
                return None
                
            try:
                # Try to convert the response to an integer (product ID)
                product_id = int(ai_response)
                return product_id
            except ValueError:
                # If conversion fails, return None
                return None
        else:
            return None
    except Exception:
        return None