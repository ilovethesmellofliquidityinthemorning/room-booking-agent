#!/usr/bin/env python3
"""
Test script for session-based room booking automation

Instructions:
1. First, start Chrome with remote debugging:
   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug"

2. Manually log into your UT SharePoint dashboard

3. Run this script to test the automation
"""

import os
import time
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation

def print_instructions():
    print("=== Session-Based Room Booking Test ===")
    print()
    print("STEP 1: Start Chrome with remote debugging")
    print("Run this command in Command Prompt:")
    print('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
    print()
    print("STEP 2: Manually log into your UT SharePoint dashboard")
    print("Navigate to your room reservation system and log in")
    print()
    print("STEP 3: Press Enter here to start automation...")
    input()

def test_session_automation():
    """Test the session-based automation"""
    load_dotenv()
    
    print("=== Session-Based Room Booking Test ===")
    print("Connecting to your existing Chrome session...")
    
    # Create automation instance that connects to existing session
    automation = MomentusAutomation(use_existing_session=True, debug_port=9222)
    
    try:
        # Connect to existing session
        automation.setup_driver()
        
        print(f"Connected! Current page: {automation.driver.title}")
        print(f"URL: {automation.driver.current_url}")
        
        # Test navigation to room reservations
        print("\n--- Testing Room Reservation Navigation ---")
        success = automation.navigate_to_room_reservations()
        
        if success:
            print("SUCCESS: Successfully navigated to room reservations!")
            print(f"Current URL: {automation.driver.current_url}")
            
            # Wait a moment for the page to fully load
            time.sleep(3)
            
            # Analyze the Momentus page
            print("\n--- Analyzing Momentus Interface ---")
            page_analysis = automation.analyze_momentus_page()
            
            if page_analysis:
                print(f"✓ Page analysis complete!")
                print(f"  Title: {page_analysis['title']}")
                print(f"  Forms found: {len(page_analysis['forms'])}")
                print(f"  Input fields: {len(page_analysis['input_fields'])}")
                print(f"  Buttons: {len(page_analysis['buttons'])}")
                print(f"  Date fields: {len(page_analysis['date_fields'])}")
                print(f"  Time fields: {len(page_analysis['time_fields'])}")
                print(f"  Select dropdowns: {len(page_analysis['select_dropdowns'])}")
                print(f"  Relevant links: {len(page_analysis['links'])}")
                
                # Show key booking-related elements found
                if page_analysis['date_fields']:
                    print(f"  📅 Date fields available: {[f['name'] or f['id'] for f in page_analysis['date_fields']]}")
                if page_analysis['time_fields']:
                    print(f"  🕐 Time fields available: {[f['name'] or f['id'] for f in page_analysis['time_fields']]}")
                if any('room' in str(btn).lower() or 'book' in str(btn).lower() for btn in page_analysis['buttons']):
                    booking_buttons = [btn['text'] for btn in page_analysis['buttons'] if 'room' in btn['text'].lower() or 'book' in btn['text'].lower() or 'search' in btn['text'].lower()]
                    if booking_buttons:
                        print(f"  🎯 Booking buttons found: {booking_buttons}")
            
            # Test room search with sample criteria (now with detailed analysis)
            print("\n--- Testing Room Search with Enhanced Analysis ---")
            search_criteria = {
                'date': '2025-01-27',  # Tomorrow
                'start_time': '14:00',
                'end_time': '16:00', 
                'capacity': 10,
                'location': 'ETC',
                'equipment': ['projector']
            }
            
            print(f"Searching for rooms with criteria: {search_criteria}")
            rooms = automation.search_rooms(search_criteria)
            
            if rooms:
                print(f"Found {len(rooms)} available rooms:")
                for i, room in enumerate(rooms, 1):
                    print(f"  {i}. {room}")
            else:
                print("No rooms found - analyzing why...")
                if page_analysis:
                    if not page_analysis['date_fields'] and not page_analysis['input_fields']:
                        print("  → No input fields found on the page")
                    elif not page_analysis['forms']:
                        print("  → No forms found on the page")
                    else:
                        print("  → Forms and fields exist but selectors need customization")
                        print("  → This is normal for the initial setup")
        else:
            print("Could not navigate to room reservations automatically")
            print("This is normal - each SharePoint setup is different")
            
        print("\n--- Current Page Analysis ---")
        
        # Analyze current page for debugging
        from selenium.webdriver.common.by import By
        
        # Look for forms
        forms = automation.driver.find_elements(By.TAG_NAME, "form")
        print(f"Found {len(forms)} forms on the page")
        
        # Look for inputs
        inputs = automation.driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} input fields:")
        for i, inp in enumerate(inputs[:10]):  # Show first 10
            print(f"  {i+1}. Type: {inp.get_attribute('type')}, Name: {inp.get_attribute('name')}, ID: {inp.get_attribute('id')}")
        
        # Look for buttons
        buttons = automation.driver.find_elements(By.TAG_NAME, "button")
        print(f"Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:5]):  # Show first 5
            print(f"  {i+1}. Text: '{btn.text}', ID: {btn.get_attribute('id')}")
        
        print("\n--- Manual Testing Time ---")
        print("The automation is now connected to your browser session.")
        print("You can:")
        print("1. Manually navigate to room reservations if automation didn't find it")
        print("2. Observe the page structure for customizing selectors")
        print("3. Test booking flows manually")
        print()
        print("Browser will stay open for 30 seconds for inspection...")
        time.sleep(30)
        
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Chrome is running with --remote-debugging-port=9222")
        print("2. Verify you're logged into SharePoint")
        print("3. Check that no other automation is using the same Chrome instance")
        
    finally:
        # Don't close the driver - leave the browser open for manual use
        print("Test completed. Your browser session remains open.")

if __name__ == "__main__":
    test_session_automation()