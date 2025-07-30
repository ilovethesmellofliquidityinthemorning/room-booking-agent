#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Room Booking with Natural Language Interface
UPDATED: Now uses proper OpenAI parsing instead of primitive regex
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation
from app.agent import RoomBookingAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Fix encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def smart_room_booking_workflow():
    """Smart room booking with OpenAI-powered natural language parsing"""
    
    print("=" * 80)
    print("🏢 SMART ROOM BOOKING ASSISTANT (OpenAI Powered)")
    print("=" * 80)
    print("Tell me what you need and I'll help you book it!")
    print("Now with proper OpenAI date parsing!")
    print()
    
    # Initialize OpenAI agent
    print("🤖 Initializing OpenAI agent...")
    agent = RoomBookingAgent()
    
    if not agent.openai_client:
        print("❌ OpenAI API key not configured!")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    print("✅ OpenAI agent ready!")
    
    # Step 1: Natural Language Input
    booking_request = get_natural_language_request()
    
    # Step 2: Use OpenAI to parse the request
    print(f"\n🔍 Processing with OpenAI: '{booking_request}'")
    print("📡 Sending to OpenAI for intelligent parsing...")
    
    ai_response = agent.process_request(booking_request)
    
    # Debug: Show the raw AI response
    print("\n" + "=" * 60)
    print("🐛 DEBUG: OpenAI Response")
    print("=" * 60)
    print(json.dumps(ai_response, indent=2))
    print("=" * 60)
    
    # Extract booking criteria from AI response
    booking_criteria = extract_criteria_from_ai_response(ai_response, booking_request)
    
    # Display parsed results
    print("\n📋 OpenAI parsed your request as:")
    print(f"   📅 Date: {booking_criteria['date']}")
    print(f"   ⏰ Time: {booking_criteria['start_time']} - {booking_criteria['end_time']}")
    print(f"   👥 Capacity: {booking_criteria['capacity']} people")
    print(f"   📍 Location: {booking_criteria['location'] or 'Any'}")
    print(f"   🛠️  Equipment: {', '.join(booking_criteria['equipment']) if booking_criteria['equipment'] else 'None specified'}")
    
    # Test specifically with 'august 16' input
    if 'august 16' in booking_request.lower():
        expected_date = "2025-08-16"
        actual_date = booking_criteria['date']
        
        print(f"\n🧪 DEBUGGING 'august 16' PARSING:")
        print(f"   Input: '{booking_request}'")
        print(f"   Expected: {expected_date}")
        print(f"   Actual: {actual_date}")
        
        if actual_date == expected_date:
            print("   ✅ DATE PARSING CORRECT!")
        else:
            print("   ❌ DATE PARSING STILL WRONG!")
            print("   🔍 Let's check what OpenAI actually returned...")
            
            # Show extracted details from AI
            extracted = ai_response.get('extracted_details', {})
            print(f"   OpenAI raw date: {extracted.get('date')}")
    
    print()
    confirm = input("✅ Does this look correct? (y/n): ").lower().startswith('y')
    
    if not confirm:
        print("🔄 Let's try again with a more specific request...")
        return smart_room_booking_workflow()
    
    # Step 2: Navigate to Momentus (fixed navigation)
    print("\n" + "=" * 80)
    print("BROWSER AUTOMATION WORKFLOW")
    print("=" * 80)
    print("This workflow will:")
    print("✅ 1. Launch fresh Chrome instance")
    print("✅ 2. Navigate to SharePoint (you handle authentication)")
    print("✅ 3. Find and click Room Reservations link")
    print("✅ 4. Navigate to Momentus (you handle authentication)")
    print("✅ 5. Fill booking form with OpenAI-parsed criteria")
    print("✅ 6. Keep browser open for manual completion")
    print()
    
    # Debug environment loading
    if os.path.exists('.env'):
        print("✅ Found .env file")
        load_dotenv()
        sharepoint_url_check = os.getenv('SHAREPOINT_URL')
        print(f"🔍 Environment check - SHAREPOINT_URL: {sharepoint_url_check}")
    else:
        print("⚠️  No .env file found - using default SharePoint URL")
        load_dotenv()  # Load anyway in case of system env vars
        sharepoint_url_check = os.getenv('SHAREPOINT_URL')
        print(f"🔍 System environment - SHAREPOINT_URL: {sharepoint_url_check}")
    
    print("🚀 Starting Chrome...")
    automation = setup_automation_session()
    
    if not automation:
        print("❌ Failed to set up automation session")
        print("This usually means ChromeDriver or Chrome isn't properly installed")
        return
    
    print("✅ Chrome launched successfully!")
    
    try:
        # Navigate through SharePoint to Momentus (one-time setup)
        momentus_ready = navigate_to_momentus_once(automation)
        
        if not momentus_ready:
            print("❌ Failed to reach Momentus booking interface")
            print("🖥️  Browser will stay open for manual navigation")
            input("Press Enter when you've manually navigated to Momentus booking form...")
            momentus_ready = True  # Continue anyway
        
        # Step 3: Enhanced Momentus form detection and filling
        print("\n📝 Analyzing Momentus booking form...")
        form_elements = detect_momentus_form_elements_enhanced(automation.driver)
        
        if not form_elements:
            print("❌ Could not detect Momentus form elements")
            print("🖥️  Please check the browser - you may need to navigate to the booking form manually")
            input("Press Enter when you're on the booking form...")
            form_elements = detect_momentus_form_elements_enhanced(automation.driver)
        
        if form_elements:
            print("✅ Found Momentus booking form elements!")
            display_form_elements(form_elements)
            
            # Step 4: Fill the form with smart field detection
            print("\n📝 Filling booking form...")
            success = fill_momentus_form_smart(automation.driver, booking_criteria, form_elements)
            
            if success:
                print("✅ Successfully filled booking form!")
                
                # Step 5: Submit and handle results
                print("\n🔍 Submitting search...")
                submit_success = submit_momentus_form_smart(automation.driver, form_elements)
                
                if submit_success:
                    print("✅ Form submitted successfully!")
                    
                    # Wait for results
                    print("⏳ Waiting for search results...")
                    time.sleep(5)
                    
                    # Analyze results
                    results = analyze_search_results(automation.driver)
                    display_booking_results(results)
                    
                else:
                    print("⚠️  Form submission may have failed - check the browser")
            else:
                print("⚠️  Some form fields may not have been filled - check the browser")
        
        # Keep browser open for manual interaction
        print("\n" + "=" * 60)
        print("BOOKING COMPLETE - BROWSER STAYING OPEN")
        print("=" * 60)
        print("🎉 Automation workflow completed successfully!")
        print()
        print("🖥️  Chrome browser will stay open for you to:")
        print("   • Review the search results")
        print("   • Select and book a room manually")
        print("   • Adjust search criteria if needed")
        print("   • Complete any final booking steps")
        print()
        print("⚠️  DO NOT close this terminal until you're done!")
        print("📋 When you've completed your booking, return here")
        print()
        
        input("✅ Press Enter when you're done with the booking (this will close Chrome)...")
        
    except Exception as e:
        print(f"❌ Booking workflow error: {e}")
        print("🖥️  Browser will stay open for manual completion")
        print("You can:")
        print("• Complete the booking manually")
        print("• Navigate to Momentus and try again")
        print("• Debug any issues in the browser")
        print()
        input("Press Enter when you're done or ready to close...")
        
    except KeyboardInterrupt:
        print("\n👋 Workflow interrupted by user")
        print("🖥️  Browser will remain open")
        input("Press Enter to close browser...")
        
    finally:
        try:
            print("🔚 Closing automation session...")
            automation.close()
            print("✅ Booking workflow complete!")
        except:
            print("✅ Workflow complete!")

def get_natural_language_request():
    """Get booking request in natural language"""
    
    print("💬 Tell me about your room booking needs.")
    print("Examples:")
    print("• 'I need a conference room for 8 people tomorrow 2-4 PM'")
    print("• 'Book a meeting room for 12 people next Friday morning'")
    print("• 'Small room for 4 people today 3:30-5:00 PM with projector'")
    print("• 'Large conference room Monday 9-11 AM in GSB building'")
    print()
    
    request = input("🗣️  Your booking request: ").strip()
    
    if not request:
        print("Please tell me what you need...")
        return get_natural_language_request()
    
    return request

def extract_criteria_from_ai_response(ai_response, original_request):
    """Extract booking criteria from OpenAI response"""
    
    try:
        # Get extracted details from AI response
        extracted = ai_response.get('extracted_details', {})
        
        # Convert AI response to our expected format
        criteria = {
            'date': None,
            'start_time': None, 
            'end_time': None,
            'capacity': None,
            'location': None,
            'equipment': []
        }
        
        # Parse date from AI response
        ai_date = extracted.get('date')
        if ai_date:
            criteria['date'] = normalize_date(ai_date)
        else:
            # Fallback to today if no date specified
            criteria['date'] = datetime.now().strftime("%Y-%m-%d")
        
        # Parse time from AI response
        ai_start_time = extracted.get('start_time')
        ai_duration = extracted.get('duration')
        
        if ai_start_time:
            criteria['start_time'] = normalize_time(ai_start_time)
            
            # Calculate end time from duration if provided
            if ai_duration:
                end_time = calculate_end_time(criteria['start_time'], ai_duration)
                criteria['end_time'] = end_time
            else:
                # Default to 1 hour if no duration
                end_time = calculate_end_time(criteria['start_time'], "1 hour")
                criteria['end_time'] = end_time
        
        # Parse capacity
        ai_capacity = extracted.get('capacity')
        if ai_capacity:
            try:
                if isinstance(ai_capacity, str):
                    # Extract number from string like "40 people"
                    import re
                    numbers = re.findall(r'\d+', ai_capacity)
                    if numbers:
                        criteria['capacity'] = int(numbers[0])
                else:
                    criteria['capacity'] = int(ai_capacity)
            except (ValueError, TypeError):
                criteria['capacity'] = 8  # Default
        else:
            criteria['capacity'] = 8  # Default
        
        # Parse location
        criteria['location'] = extracted.get('location')
        
        # Parse equipment
        ai_equipment = extracted.get('equipment', [])
        if isinstance(ai_equipment, list):
            criteria['equipment'] = ai_equipment
        else:
            criteria['equipment'] = []
        
        return criteria
        
    except Exception as e:
        print(f"❌ Error extracting criteria from AI response: {e}")
        # Return fallback criteria
        return {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'start_time': "10:00",
            'end_time': "11:00", 
            'capacity': 8,
            'location': None,
            'equipment': []
        }

def normalize_date(date_string):
    """Normalize date string to YYYY-MM-DD format"""
    
    try:
        # Handle various date formats that OpenAI might return
        if not date_string or date_string.lower() in ['null', 'none']:
            return datetime.now().strftime("%Y-%m-%d")
        
        # If already in YYYY-MM-DD format
        if len(date_string) == 10 and date_string.count('-') == 2:
            try:
                datetime.strptime(date_string, "%Y-%m-%d")
                return date_string
            except ValueError:
                pass
        
        # Parse common date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y", 
            "%m-%d-%Y",
            "%B %d, %Y",  # August 16, 2025
            "%B %d",      # August 16
            "%b %d, %Y",  # Aug 16, 2025  
            "%b %d"       # Aug 16
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                
                # If year not specified, assume current year
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                
                # If date is in the past, assume next year
                if parsed_date < datetime.now():
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                    if parsed_date < datetime.now():  # Still in past, use next year
                        parsed_date = parsed_date.replace(year=datetime.now().year + 1)
                
                return parsed_date.strftime("%Y-%m-%d")
                
            except ValueError:
                continue
        
        # If all parsing fails, return today
        print(f"⚠️  Could not parse date '{date_string}', using today")
        return datetime.now().strftime("%Y-%m-%d")
        
    except Exception as e:
        print(f"❌ Date normalization error: {e}")
        return datetime.now().strftime("%Y-%m-%d")

def normalize_time(time_string):
    """Normalize time string to HH:MM format"""
    
    try:
        if not time_string:
            return "10:00"
        
        # Handle various time formats
        time_formats = [
            "%H:%M",      # 14:30
            "%I:%M %p",   # 2:30 PM
            "%I %p",      # 2 PM
            "%H"          # 14
        ]
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_string, fmt)
                return parsed_time.strftime("%H:%M")
            except ValueError:
                continue
        
        # Extract time with regex as fallback
        import re
        time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?', time_string.lower())
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        return "10:00"  # Default
        
    except Exception as e:
        print(f"❌ Time normalization error: {e}")
        return "10:00"

def calculate_end_time(start_time, duration_string):
    """Calculate end time from start time and duration"""
    
    try:
        start_hour, start_min = map(int, start_time.split(':'))
        
        # Parse duration
        duration_minutes = 60  # Default 1 hour
        
        if 'minute' in duration_string:
            import re
            minutes = re.findall(r'\d+', duration_string)
            if minutes:
                duration_minutes = int(minutes[0])
        elif 'hour' in duration_string:
            import re
            hours = re.findall(r'\d+', duration_string)
            if hours:
                duration_minutes = int(hours[0]) * 60
        
        # Calculate end time
        total_minutes = start_hour * 60 + start_min + duration_minutes
        end_hour = (total_minutes // 60) % 24
        end_min = total_minutes % 60
        
        return f"{end_hour:02d}:{end_min:02d}"
        
    except Exception as e:
        print(f"❌ End time calculation error: {e}")
        # Default to 1 hour later
        try:
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour = (start_hour + 1) % 24
            return f"{end_hour:02d}:{start_min:02d}"
        except:
            return "11:00"


def setup_automation_session():
    """Set up automation session with proper encoding handling"""
    
    load_dotenv()
    sharepoint_url = os.getenv('SHAREPOINT_URL', 'https://utexas.sharepoint.com/sites/McCombs-DepartmentofFinance/SitePages/CollabHome.aspx')
    
    try:
        # Create fresh automation instance
        automation = MomentusAutomation(
            headless=False,
            use_existing_session=False
        )
        
        print("🚀 Launching Chrome...")
        automation.setup_driver()
        
        # Set encoding to handle Unicode properly
        automation.driver.execute_script("document.charset = 'UTF-8';")
        
        return automation
        
    except Exception as e:
        print(f"❌ Failed to set up automation: {e}")
        return None

def navigate_to_momentus_once(automation):
    """Navigate to Momentus one time and stay there"""
    
    load_dotenv()
    sharepoint_url = os.getenv('SHAREPOINT_URL')
    
    # Debug URL loading
    print(f"🔍 DEBUG: Loaded SharePoint URL: {sharepoint_url}")
    
    # Provide fallback URL if not loaded from environment
    if not sharepoint_url:
        sharepoint_url = 'https://utexas.sharepoint.com/sites/McCombs-DepartmentofFinance/SitePages/CollabHome.aspx'
        print(f"⚠️  SHAREPOINT_URL not found in .env, using default: {sharepoint_url}")
    
    try:
        # Validate URL format
        if not sharepoint_url.startswith(('http://', 'https://')):
            sharepoint_url = 'https://' + sharepoint_url
            print(f"🔧 Fixed URL format: {sharepoint_url}")
        
        print(f"🌐 Navigating to SharePoint: {sharepoint_url}")
        automation.driver.get(sharepoint_url)
        time.sleep(3)
        
        # Verify navigation succeeded
        current_url = automation.driver.current_url
        current_title = automation.driver.title
        print(f"✅ Navigation complete!")
        print(f"   Current URL: {current_url}")
        print(f"   Page Title: {current_title}")
        
        # Check if we got an error page
        if 'error' in current_title.lower() or '404' in current_title or 'not found' in current_title.lower():
            print(f"⚠️  Possible navigation error - check the URL and try again")
            print(f"   If this URL is wrong, update SHAREPOINT_URL in your .env file")
        
        print("\n" + "=" * 60)
        print("STEP 1: SHAREPOINT AUTHENTICATION")
        print("=" * 60)
        print("👤 Please complete SharePoint/UT authentication:")
        print("   • Enter your UT EID and password")
        print("   • Complete any DUO/2FA authentication")
        print("   • Wait until you reach your SharePoint dashboard")
        print("   • Look for 'Room Reservations' or similar text/links")
        print()
        print("🖥️  Switch to the Chrome window to complete authentication")
        print("📋 When you see your dashboard, return here and press Enter")
        print()
        input("✅ Press Enter when you're authenticated and on the SharePoint dashboard...")
        
        print("🔍 Looking for Room Reservations link...")
        
        # Find and click Room Reservations (one time only)
        room_link = find_room_reservations_link_smart(automation.driver)
        
        if room_link:
            print(f"✅ Found: {room_link['text']}")
            click_element_once(automation.driver, room_link['element'])
            time.sleep(5)
            
            # Check if we need Momentus authentication
            current_url = automation.driver.current_url.lower()
            if 'momentus' not in current_url:
                print("\n" + "=" * 60)
                print("STEP 2: MOMENTUS AUTHENTICATION")
                print("=" * 60)
                print("🔐 Momentus authentication required!")
                print()
                print("👤 Please complete Momentus authentication:")
                print("   • Enter your UT EID credentials again if prompted")
                print("   • Complete any additional authentication steps")
                print("   • Wait for the Momentus room booking interface to load")
                print("   • Look for date/time fields, room selection, etc.")
                print()
                print("🖥️  Switch to Chrome to complete Momentus authentication")
                print("📋 When you see the room booking interface, return here and press Enter")
                print()
                input("✅ Press Enter when Momentus booking interface is loaded...")
            else:
                print("✅ Already in Momentus system!")
            
            print("✅ Momentus booking interface ready!")
            return True
        else:
            print("❌ Could not find Room Reservations link")
            return False
            
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return False

def find_room_reservations_link_smart(driver):
    """Smart Room Reservations link detection"""
    
    selectors = [
        "//a[contains(text(), 'Room Reservations')]",
        "//a[contains(text(), 'ROOM RESERVATIONS')]",
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room reserv')]",
        "//a[contains(@href, 'momentus')]",
        "//a[contains(@href, 'room')]",
        "//*[contains(text(), 'Room Reservations')]//ancestor::a"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return {
                        'element': element,
                        'text': element.text.strip(),
                        'href': element.get_attribute('href') or ''
                    }
        except:
            continue
    
    return None

def click_element_once(driver, element):
    """Click element once and handle new windows"""
    
    original_windows = driver.window_handles
    
    try:
        driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)
        element.click()
        time.sleep(3)
        
        # Handle new window
        new_windows = driver.window_handles
        if len(new_windows) > len(original_windows):
            for window in new_windows:
                if window not in original_windows:
                    driver.switch_to.window(window)
                    break
        
    except Exception as e:
        print(f"Click warning: {e}")

def detect_momentus_form_elements_enhanced(driver):
    """Enhanced detection of Momentus form elements with multiple strategies"""
    
    print("🔍 Scanning for Momentus form elements...")
    
    form_elements = {
        'date_fields': [],
        'time_fields': [],
        'select_fields': [],
        'input_fields': [],
        'buttons': [],
        'form': None
    }
    
    try:
        # Find the main form
        forms = driver.find_elements(By.TAG_NAME, "form")
        if forms:
            form_elements['form'] = forms[0]
            print(f"✅ Found form: {forms[0].get_attribute('id') or 'unnamed'}")
        
        # Enhanced date field detection
        date_selectors = [
            "//input[@type='date']",
            "//input[contains(@name, 'date')]",
            "//input[contains(@id, 'date')]",
            "//input[contains(@placeholder, 'date')]",
            "//input[contains(@class, 'date')]",
            "//*[contains(@class, 'datepicker')]//input",
            "//*[contains(@id, 'calendar')]//input"
        ]
        
        for selector in date_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        form_elements['date_fields'].append({
                            'element': elem,
                            'name': elem.get_attribute('name'),
                            'id': elem.get_attribute('id'),
                            'type': elem.get_attribute('type')
                        })
            except:
                continue
        
        # Enhanced time field detection
        time_selectors = [
            "//input[@type='time']",
            "//select[contains(@name, 'time')]",
            "//select[contains(@id, 'time')]",
            "//input[contains(@name, 'time')]",
            "//input[contains(@id, 'time')]",
            "//select[contains(@name, 'hour')]",
            "//select[contains(@name, 'minute')]",
            "//input[contains(@placeholder, 'time')]"
        ]
        
        for selector in time_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        form_elements['time_fields'].append({
                            'element': elem,
                            'name': elem.get_attribute('name'),
                            'id': elem.get_attribute('id'),
                            'type': elem.get_attribute('type'),
                            'tag': elem.tag_name
                        })
            except:
                continue
        
        # Enhanced dropdown detection
        select_selectors = [
            "//select",
            "//*[@role='combobox']",
            "//*[@role='listbox']"
        ]
        
        for selector in select_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        options = []
                        if elem.tag_name == 'select':
                            option_elements = elem.find_elements(By.TAG_NAME, "option")
                            options = [opt.text for opt in option_elements[:10]]
                        
                        form_elements['select_fields'].append({
                            'element': elem,
                            'name': elem.get_attribute('name'),
                            'id': elem.get_attribute('id'),
                            'options': options
                        })
            except:
                continue
        
        # Button detection
        button_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'find')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book')]"
        ]
        
        for selector in button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        form_elements['buttons'].append({
                            'element': elem,
                            'text': elem.text,
                            'type': elem.get_attribute('type'),
                            'id': elem.get_attribute('id')
                        })
            except:
                continue
        
        return form_elements
        
    except Exception as e:
        print(f"❌ Form detection error: {e}")
        return None

def display_form_elements(form_elements):
    """Display detected form elements"""
    
    print("📋 Detected form elements:")
    print(f"   📅 Date fields: {len(form_elements['date_fields'])}")
    print(f"   ⏰ Time fields: {len(form_elements['time_fields'])}")
    print(f"   📋 Dropdowns: {len(form_elements['select_fields'])}")
    print(f"   🔘 Buttons: {len(form_elements['buttons'])}")

def fill_momentus_form_smart(driver, criteria, form_elements):
    """Smart form filling with enhanced field detection"""
    
    success_count = 0
    total_attempts = 0
    
    try:
        # Fill date fields
        if criteria['date'] and form_elements['date_fields']:
            for date_field in form_elements['date_fields']:
                try:
                    element = date_field['element']
                    element.clear()
                    element.send_keys(criteria['date'])
                    print(f"✅ Filled date: {criteria['date']}")
                    success_count += 1
                    break
                except Exception as e:
                    print(f"⚠️  Date field failed: {e}")
                total_attempts += 1
        
        # Fill time fields (enhanced)
        time_fields = form_elements['time_fields']
        if criteria['start_time'] and time_fields:
            # Look for start time field
            for time_field in time_fields:
                field_name = (time_field['name'] or time_field['id'] or '').lower()
                if any(keyword in field_name for keyword in ['start', 'begin', 'from']):
                    try:
                        element = time_field['element']
                        if element.tag_name == 'select':
                            select = Select(element)
                            # Try to find matching time option
                            for option in select.options:
                                if criteria['start_time'] in option.text:
                                    select.select_by_visible_text(option.text)
                                    print(f"✅ Selected start time: {option.text}")
                                    success_count += 1
                                    break
                        else:
                            element.clear()
                            element.send_keys(criteria['start_time'])
                            print(f"✅ Filled start time: {criteria['start_time']}")
                            success_count += 1
                        break
                    except Exception as e:
                        print(f"⚠️  Start time field failed: {e}")
                    total_attempts += 1
        
        # Fill end time
        if criteria['end_time'] and time_fields:
            for time_field in time_fields:
                field_name = (time_field['name'] or time_field['id'] or '').lower()
                if any(keyword in field_name for keyword in ['end', 'finish', 'to', 'until']):
                    try:
                        element = time_field['element']
                        if element.tag_name == 'select':
                            select = Select(element)
                            for option in select.options:
                                if criteria['end_time'] in option.text:
                                    select.select_by_visible_text(option.text)
                                    print(f"✅ Selected end time: {option.text}")
                                    success_count += 1
                                    break
                        else:
                            element.clear()
                            element.send_keys(criteria['end_time'])
                            print(f"✅ Filled end time: {criteria['end_time']}")
                            success_count += 1
                        break
                    except Exception as e:
                        print(f"⚠️  End time field failed: {e}")
                    total_attempts += 1
        
        # Fill capacity (look in both selects and inputs)
        if criteria['capacity']:
            capacity_filled = False
            
            # Try dropdowns first
            for select_field in form_elements['select_fields']:
                field_name = (select_field['name'] or select_field['id'] or '').lower()
                if any(keyword in field_name for keyword in ['capacity', 'people', 'size', 'attendee']):
                    try:
                        select = Select(select_field['element'])
                        capacity_str = str(criteria['capacity'])
                        
                        # Try exact match first
                        for option in select.options:
                            if capacity_str in option.text or capacity_str == option.get_attribute('value'):
                                select.select_by_visible_text(option.text)
                                print(f"✅ Selected capacity: {option.text}")
                                success_count += 1
                                capacity_filled = True
                                break
                        
                        if capacity_filled:
                            break
                            
                    except Exception as e:
                        print(f"⚠️  Capacity dropdown failed: {e}")
                    total_attempts += 1
            
            # Try input fields if dropdown didn't work
            if not capacity_filled:
                capacity_inputs = driver.find_elements(By.XPATH, "//input[contains(@name, 'capacity') or contains(@id, 'capacity') or contains(@placeholder, 'capacity')]")
                for input_elem in capacity_inputs:
                    try:
                        if input_elem.is_displayed():
                            input_elem.clear()
                            input_elem.send_keys(str(criteria['capacity']))
                            print(f"✅ Filled capacity: {criteria['capacity']}")
                            success_count += 1
                            break
                    except Exception as e:
                        print(f"⚠️  Capacity input failed: {e}")
                    total_attempts += 1
        
        print(f"📊 Form filling result: {success_count}/{total_attempts + 1} fields successful")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Form filling error: {e}")
        return False

def submit_momentus_form_smart(driver, form_elements):
    """Smart form submission"""
    
    try:
        # Find the best submit button
        submit_button = None
        
        for button in form_elements['buttons']:
            button_text = button['text'].lower()
            if any(keyword in button_text for keyword in ['search', 'find', 'submit', 'go']):
                submit_button = button['element']
                print(f"🔘 Found submit button: '{button['text']}'")
                break
        
        if not submit_button and form_elements['buttons']:
            submit_button = form_elements['buttons'][0]['element']
            print(f"🔘 Using first button: '{form_elements['buttons'][0]['text']}'")
        
        if submit_button:
            driver.execute_script("arguments[0].scrollIntoView();", submit_button)
            time.sleep(1)
            submit_button.click()
            print("✅ Form submitted!")
            return True
        else:
            print("❌ No submit button found")
            return False
            
    except Exception as e:
        print(f"❌ Submit error: {e}")
        return False

def analyze_search_results(driver):
    """Analyze search results page"""
    
    try:
        # Wait for results to load
        time.sleep(3)
        
        current_title = driver.title
        current_url = driver.current_url
        
        print(f"📄 Results page: {current_title}")
        
        # Look for room results
        room_selectors = [
            "//div[contains(@class, 'room')]",
            "//tr[contains(@class, 'room')]",
            "//div[contains(@class, 'result')]",
            "//div[contains(@class, 'available')]",
            "//*[contains(text(), 'Available')]",
            "//*[contains(text(), 'Book')]"
        ]
        
        rooms_found = 0
        for selector in room_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                rooms_found += len(elements)
            except:
                continue
        
        return {
            'rooms_found': rooms_found,
            'title': current_title,
            'url': current_url
        }
        
    except Exception as e:
        print(f"❌ Results analysis error: {e}")
        return {'rooms_found': 0}

def display_booking_results(results):
    """Display booking results"""
    
    rooms_found = results.get('rooms_found', 0)
    
    if rooms_found > 0:
        print(f"✅ Found {rooms_found} potential room matches!")
        print("🖥️  Check the browser to:")
        print("   • Review available rooms")
        print("   • Select your preferred room")
        print("   • Complete the booking")
    else:
        print("⚠️  No rooms found with current criteria")
        print("💡 Try:")
        print("   • Different time slots")
        print("   • Smaller capacity requirements")
        print("   • Different dates")
        print("   • Manual search refinement in browser")

if __name__ == "__main__":
    try:
        smart_room_booking_workflow()
    except KeyboardInterrupt:
        print("\n👋 Booking cancelled by user")
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        input("Press Enter to exit...")