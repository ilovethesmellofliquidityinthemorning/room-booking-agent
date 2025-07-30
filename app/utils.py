"""
Utility functions and configurations for the room booking agent
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

# Configure logging
def setup_logger():
    """Set up application logger"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler('room_booking_agent.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('room_booking_agent')

logger = setup_logger()

class DateTimeHelper:
    """Helper class for date and time operations"""
    
    @staticmethod
    def parse_natural_time(time_str: str) -> Optional[datetime]:
        """Parse natural language time expressions"""
        # This would contain logic to parse expressions like:
        # "tomorrow at 2pm", "next Tuesday 10am", "in 2 hours"
        # For now, return None - implement based on requirements
        return None
    
    @staticmethod
    def format_time_for_momentus(dt: datetime) -> str:
        """Format datetime for Momentus system"""
        return dt.strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_business_hours() -> Dict[str, str]:
        """Return standard business hours"""
        return {
            'start': '08:00',
            'end': '18:00'
        }

class ValidationHelper:
    """Helper class for validating booking data"""
    
    @staticmethod
    def validate_booking_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate booking request data"""
        errors = []
        
        # Check required fields
        required_fields = ['date', 'start_time', 'end_time']
        for field in required_fields:
            if field not in request_data or not request_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate date format
        try:
            if 'date' in request_data:
                datetime.strptime(request_data['date'], '%Y-%m-%d')
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD")
        
        # Validate time format
        try:
            if 'start_time' in request_data:
                datetime.strptime(request_data['start_time'], '%H:%M')
            if 'end_time' in request_data:
                datetime.strptime(request_data['end_time'], '%H:%M')
        except ValueError:
            errors.append("Invalid time format. Use HH:MM")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class ConfigHelper:
    """Helper class for configuration management"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'momentus_base_url': os.getenv('MOMENTUS_BASE_URL', 'https://utexas.momentus.io/'),
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'port': int(os.getenv('PORT', 5000)),
            'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
    
    @staticmethod
    def validate_config() -> Dict[str, Any]:
        """Validate that required configuration is present"""
        config = ConfigHelper.get_config()
        errors = []
        
        if not config['openai_api_key']:
            errors.append("OPENAI_API_KEY environment variable is required")
        
        if config['secret_key'] == 'dev-secret-key':
            errors.append("SECRET_KEY should be set to a secure value in production")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'config': config
        }

def load_room_mappings() -> Dict[str, Any]:
    """Load room mappings and metadata"""
    # This could load from a JSON file containing room information
    # For now, return empty dict
    return {}

def save_booking_history(booking_data: Dict[str, Any]) -> None:
    """Save booking to history file"""
    try:
        history_file = 'booking_history.json'
        
        # Load existing history
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add timestamp to booking data
        booking_data['timestamp'] = datetime.now().isoformat()
        
        # Append new booking
        history.append(booking_data)
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
        logger.info("Booking saved to history")
        
    except Exception as e:
        logger.error(f"Failed to save booking history: {str(e)}")