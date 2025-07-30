#!/usr/bin/env python3
"""
Test script for Momentus login functionality
"""

import os
import time
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation

def test_login():
    """Test the Momentus login functionality"""
    load_dotenv()
    
    username = os.getenv('MOMENTUS_USERNAME')
    password = os.getenv('MOMENTUS_PASSWORD')
    
    if not username or not password:
        print("ERROR: MOMENTUS_USERNAME and MOMENTUS_PASSWORD must be set in .env file")
        return
    
    print(f"Testing Momentus login with username: {username}")
    print(f"Momentus URL: {os.getenv('MOMENTUS_BASE_URL', 'https://utexas.momentus.io/')}")
    print("Starting browser automation (non-headless for debugging)...")
    
    # Create automation instance (connect to existing Chrome debug session)
    automation = MomentusAutomation(headless=False, use_existing_session=True, debug_port=9222)
    
    try:
        # Test login
        print("Attempting login...")
        success = automation.login(username, password)
        
        if success:
            print("SUCCESS: Login successful!")
            
            # Wait a bit to see the result
            print("Waiting 5 seconds to observe result...")
            time.sleep(5)
            
        else:
            print("ERROR: Login failed!")
            print("Check the browser window for details...")
            time.sleep(3)
            
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        time.sleep(3)
        
    finally:
        automation.close()
        print("Browser closed.")

if __name__ == "__main__":
    test_login()