#!/usr/bin/env python3
"""
Room Booking Agent for UT Austin
Entry point for the application
"""

import os
from dotenv import load_dotenv
from app.web_interface import create_app

def main():
    load_dotenv()
    
    app = create_app()
    
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()