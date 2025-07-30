"""
Main agent module for processing natural language requests
and coordinating room booking tasks
"""

import openai
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from .utils import logger

# Ensure environment variables are loaded - look for .env in parent directory
import pathlib
env_path = pathlib.Path(__file__).parent.parent / '.env'

# Load environment variables
load_dotenv(dotenv_path=env_path)

class RoomBookingAgent:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != 'dummy_key_for_testing':
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.openai_client = None
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not configured - AI features disabled")
        self.conversation_history = []
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language input and extract booking requirements
        """
        try:
            if not self.openai_client:
                # Fallback response when OpenAI is not configured
                return {
                    "message": f"Received request: {user_input}",
                    "status": "received",
                    "note": "AI processing disabled - OpenAI API key not configured"
                }
            
            system_prompt = """
            You are a helpful room booking assistant for UT Austin. Your job is to:
            1. Extract specific booking details from user requests
            2. Identify any missing information needed for booking
            3. Provide helpful suggestions and next steps
            
            Extract these details when mentioned:
            - Date (specific date, "tomorrow", "next Monday", etc.)
            - Time (start time, duration, or end time)
            - Capacity (number of people)
            - Location preferences (building, floor, etc.)
            - Equipment needs (projector, whiteboard, etc.)
            - Meeting purpose/type
            
            Respond in JSON format with:
            {
                "extracted_details": {
                    "date": "parsed date or null",
                    "start_time": "parsed time or null", 
                    "duration": "parsed duration or null",
                    "capacity": "number of people or null",
                    "location": "preferred location or null",
                    "equipment": ["list of equipment needed"],
                    "purpose": "meeting purpose or null"
                },
                "missing_info": ["list of missing required details"],
                "suggestions": "helpful suggestions for the user",
                "next_steps": "what should happen next"
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=500
            )
            
            # Parse the response and extract booking parameters
            parsed_request = self._parse_ai_response(response.choices[0].message.content)
            
            logger.info(f"Processed user request: {user_input}")
            return parsed_request
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {"error": f"Failed to process request: {str(e)}"}
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse AI response and structure the booking requirements
        """
        try:
            import json
            # Try to parse as JSON first
            if ai_response.strip().startswith('{'):
                parsed_data = json.loads(ai_response)
                return parsed_data
            else:
                # Fallback for non-JSON responses
                return {
                    "extracted_details": {},
                    "missing_info": [],
                    "suggestions": ai_response,
                    "next_steps": "Please provide more specific details about your booking needs."
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw response
            return {
                "extracted_details": {},
                "missing_info": [],
                "suggestions": ai_response,
                "next_steps": "Please provide more specific details about your booking needs."
            }
    
    def generate_response(self, booking_result: Dict[str, Any]) -> str:
        """
        Generate natural language response based on booking results
        """
        if "error" in booking_result:
            return f"I encountered an issue: {booking_result['error']}"
        
        if "note" in booking_result:
            return f"I received your request: '{booking_result['message']}'. {booking_result['note']}"
        
        # Handle structured AI responses
        if "extracted_details" in booking_result:
            details = booking_result["extracted_details"]
            missing = booking_result.get("missing_info", [])
            suggestions = booking_result.get("suggestions", "")
            next_steps = booking_result.get("next_steps", "")
            
            response_parts = []
            
            # Summarize what was understood
            understood = []
            if details.get("date"):
                understood.append(f"date: {details['date']}")
            if details.get("start_time"):
                understood.append(f"time: {details['start_time']}")
            if details.get("duration"):
                understood.append(f"duration: {details['duration']}")
            if details.get("capacity"):
                understood.append(f"capacity: {details['capacity']} people")
            if details.get("location"):
                understood.append(f"location: {details['location']}")
            if details.get("equipment"):
                understood.append(f"equipment: {', '.join(details['equipment'])}")
            if details.get("purpose"):
                understood.append(f"purpose: {details['purpose']}")
            
            if understood:
                response_parts.append(f"I understand you need a room booking with: {', '.join(understood)}.")
            
            # Mention missing information
            if missing:
                response_parts.append(f"To complete your booking, I still need: {', '.join(missing)}.")
            
            # Add suggestions and next steps
            if suggestions:
                response_parts.append(suggestions)
            if next_steps:
                response_parts.append(next_steps)
            
            return " ".join(response_parts)
        
        # Fallback response
        return "I've processed your request. Please provide more specific details to help me find the perfect room for you."