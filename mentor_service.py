import os
import requests
import json
import logging

def get_mentor_response(user_message, topic, location):
    """Get mentorship response from ZO via API"""
    try:
        api_key = os.environ.get('ZO_API_KEY', '').strip()
        
        if not api_key:
            logging.error("ZO_API_KEY not found in environment")
            return None, "Mentor API key not configured"
        
        system_prompt = f"""You are an expert mentor specializing in {topic}. 
Your mentee is located in {location}. 
Provide personalized, actionable mentorship guidance based on their location and the topic of {topic}.
Be encouraging, practical, and specific in your advice.
Keep responses concise but thorough (2-4 paragraphs max). keep it a 100% realistic and brutally honest with suggestions from you"""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json"
        }
        
        payload = {
            "model": os.environ.get("ZO_MODEL", "minimax 2.7"),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7
        }
        
        base_url = os.environ.get("ZO_BASE_URL", "https://api.zo.dev/v1/chat/completions")
        logging.info(f"Calling ZO API with topic={topic}, location={location}")
        
        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logging.info(f"ZO API response status: {response.status_code}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {}).get('message', response.text)
            except:
                error_detail = response.text
            logging.error(f"ZO API Error ({response.status_code}): {error_detail}")
            return None, f"ZO API Error: {response.status_code}"
        
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            logging.error(f"ZO API returned non-JSON response: {content_type} {response.text[:300]}")
            return None, "Mentor service returned an invalid response"

        data = response.json()
        message_text = ""
        if data.get('choices') and len(data['choices']) > 0:
            message_text = data['choices'][0].get('message', {}).get('content', '')
        elif data.get('content') and len(data['content']) > 0:
            message_text = data['content'][0].get('text', '')

        if message_text:
            logging.info(f"ZO response received: {len(message_text)} characters")
            return message_text, None
        else:
            logging.error(f"No content in ZO response: {data}")
            return None, "No response from mentor service"
    
    except requests.exceptions.Timeout:
        logging.error("ZO API request timeout")
        return None, "Request timeout"
    except requests.exceptions.ConnectionError as e:
        logging.error(f"ZO API connection error: {e}")
        return None, "Connection error"
    except Exception as e:
        logging.error(f"Mentor service error: {str(e)}")
        return None, f"Error: {str(e)}"
