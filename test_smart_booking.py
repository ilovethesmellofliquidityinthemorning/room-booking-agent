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
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation
from app.agent import RoomBookingAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Fix encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class AIDropdownMatcher:
    """AI-powered dropdown option matcher"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def match_dropdown_options(self, user_intent, dropdown_options, field_type):
        """Use OpenAI to match user intent with dropdown options"""
        
        try:
            # Create a prompt for OpenAI to match options
            prompt = f"""
You are helping with room booking automation. The user said: "{user_intent}"

I need to select from these {field_type} options in a dropdown:
{json.dumps(dropdown_options, indent=2)}

Based on the user's request, which option would be the BEST match?

Rules:
1. Return ONLY the exact option text from the list
2. If multiple good matches, return the BEST one
3. If no good match, return "NONE"
4. Consider context (e.g., "exam review" suggests academic space, "projector" suggests AV equipment)

Your response should be just the option text, nothing else.
"""
            
            response = self.agent.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            selected_option = response.choices[0].message.content.strip()
            
            # Validate the response is actually in our options
            if selected_option in dropdown_options:
                return selected_option
            elif selected_option == "NONE":
                return None
            else:
                # Try partial matching
                for option in dropdown_options:
                    if selected_option.lower() in option.lower() or option.lower() in selected_option.lower():
                        return option
                return None
                
        except Exception as e:
            print(f"⚠️  AI matching error for {field_type}: {e}")
            return None
    
    def interpret_capacity_requirement(self, user_intent, available_capacities):
        """Interpret capacity needs and match to available options"""
        
        try:
            prompt = f"""
The user said: "{user_intent}"

Available capacity options:
{json.dumps(available_capacities, indent=2)}

What capacity does the user need?

Rules:
1. Extract the number of people from the user's request
2. If they said "small group" assume 4-6 people
3. If they said "large group" assume 12-20 people
4. If they said "conference" assume 8-15 people
5. Return the BEST matching option from the available list
6. If no clear capacity mentioned, return option for 8-10 people

Return ONLY the exact option text from the list.
"""
            
            response = self.agent.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            selected_capacity = response.choices[0].message.content.strip()
            
            if selected_capacity in available_capacities:
                return selected_capacity
            else:
                # Try to find partial match
                for option in available_capacities:
                    if selected_capacity.lower() in option.lower():
                        return option
                
                # Default to medium capacity
                for option in available_capacities:
                    if any(size in option.lower() for size in ['8', '10', '12']):
                        return option
                
                return available_capacities[0] if available_capacities else None
                
        except Exception as e:
            print(f"⚠️  AI capacity matching error: {e}")
            return None

def smart_room_booking_workflow():
    """Smart room booking with OpenAI-powered natural language parsing"""
    
    print("=" * 80)
    print("🤖 AI-ENHANCED ROOM BOOKING ASSISTANT")
    print("=" * 80)
    print("Uses AI to interpret your needs AND intelligently select dropdown options!")
    print("Now with AI-powered form field mapping!")
    print()
    
    # Initialize OpenAI agent
    print("🤖 Initializing OpenAI agent...")
    agent = RoomBookingAgent()
    
    if not agent.openai_client:
        print("❌ OpenAI API key not configured!")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    print("✅ OpenAI agent ready!")
    
    # Initialize AI dropdown matcher
    dropdown_matcher = AIDropdownMatcher(agent)
    
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
        
        # Step 3: AI-Enhanced Momentus form analysis
        print("\n🧠 AI-Enhanced form analysis...")
        form_elements = detect_momentus_form_with_ai(automation.driver, booking_request, dropdown_matcher)
        
        if not form_elements:
            print("❌ Could not detect Momentus form elements")
            print("🖥️  Please check the browser - you may need to navigate to the booking form manually")
            input("Press Enter when you're on the booking form...")
            form_elements = detect_momentus_form_with_ai(automation.driver, booking_request, dropdown_matcher)
        
        if form_elements:
            print("✅ Found and analyzed Momentus booking form!")
            
            # Step 4: Fill the form with AI-selected options
            print("\n📝 Filling booking form with AI selections...")
            success = fill_momentus_form_with_ai(automation.driver, booking_criteria, form_elements, booking_request)
            
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
                    
                    # Analyze results with AI
                    results = analyze_search_results_with_ai(automation.driver, booking_request, dropdown_matcher)
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
    """Get detailed booking request in natural language"""
    
    print("💬 Tell me about your room booking needs in detail:")
    print("Examples:")
    print("• 'Conference room for exam review with projector tomorrow 2-4 PM'")
    print("• 'Small study room in GSB building for group project today 3:30 PM'")
    print("• 'Large presentation room with AV equipment and whiteboard Friday morning'")
    print("• 'Classroom for teaching session with computer and screen Monday 9-11 AM'")
    print("• 'Meeting space for 15 people in McCombs building with video conferencing'")
    print()
    print("💡 Include: space type, capacity, equipment needs, building preference, purpose")
    print()
    
    request = input("🗣️  Your detailed booking request: ").strip()
    
    if not request:
        print("Please tell me what you need...")
        return get_natural_language_request()
    
    return request

def extract_criteria_from_ai_response(ai_response, original_request):
    """Extract booking criteria from AI response with enhanced time parsing"""
    
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
        
        # Enhanced time parsing - handle ranges like "10-11am"
        print(f"\n🕒 DEBUG: Time parsing from AI response...")
        ai_start_time = extracted.get('start_time')
        ai_end_time = extracted.get('end_time')
        ai_duration = extracted.get('duration')
        
        print(f"   AI start_time: '{ai_start_time}'")
        print(f"   AI end_time: '{ai_end_time}'")
        print(f"   AI duration: '{ai_duration}'")
        print(f"   Original request: '{original_request}'")
        
        # Try to parse time range from original request if AI parsing is insufficient
        time_range_patterns = [
            r'(\d{1,2})\s*-\s*(\d{1,2})\s*(am|pm)',  # "10-11am"
            r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*(am|pm)',  # "10:00-11:00am"
            r'(\d{1,2})\s*(am|pm)\s*-\s*(\d{1,2})\s*(am|pm)',  # "10am-11am"
        ]
        
        time_range_found = False
        for pattern in time_range_patterns:
            match = re.search(pattern, original_request.lower())
            if match:
                print(f"   ✅ Found time range pattern: {match.group(0)}")
                
                if len(match.groups()) == 3:  # "10-11am"
                    start_hour = int(match.group(1))
                    end_hour = int(match.group(2))
                    period = match.group(3).lower()
                    
                    # Convert to 24-hour format
                    if period == 'pm' and start_hour != 12:
                        start_hour += 12
                        end_hour += 12
                    elif period == 'am' and start_hour == 12:
                        start_hour = 0
                    elif period == 'am' and end_hour == 12:
                        end_hour = 0
                    
                    criteria['start_time'] = f"{start_hour:02d}:00"
                    criteria['end_time'] = f"{end_hour:02d}:00"
                    time_range_found = True
                    
                    print(f"   ✅ Parsed time range: {criteria['start_time']} - {criteria['end_time']}")
                    break
        
        # If no time range found, use AI response or fallback
        if not time_range_found:
            if ai_start_time:
                criteria['start_time'] = normalize_time(ai_start_time)
                print(f"   Using AI start time: {criteria['start_time']}")
                
                if ai_end_time:
                    criteria['end_time'] = normalize_time(ai_end_time)
                    print(f"   Using AI end time: {criteria['end_time']}")
                elif ai_duration:
                    criteria['end_time'] = calculate_end_time(criteria['start_time'], ai_duration)
                    print(f"   Calculated end time from duration: {criteria['end_time']}")
                else:
                    # Default to 1 hour
                    criteria['end_time'] = calculate_end_time(criteria['start_time'], "1 hour")
                    print(f"   Default 1-hour duration: {criteria['end_time']}")
            else:
                # Complete fallback
                criteria['start_time'] = "10:00"
                criteria['end_time'] = "11:00"
                print(f"   Using fallback times: {criteria['start_time']} - {criteria['end_time']}")
        
        # Enhanced capacity parsing
        print(f"\n👥 DEBUG: Capacity parsing...")
        ai_capacity = extracted.get('capacity')
        print(f"   AI capacity: '{ai_capacity}'")
        
        if ai_capacity:
            try:
                if isinstance(ai_capacity, str):
                    # Extract number from string like "40 people"
                    numbers = re.findall(r'\d+', ai_capacity)
                    if numbers:
                        criteria['capacity'] = int(numbers[0])
                        print(f"   ✅ Extracted capacity from string: {criteria['capacity']}")
                else:
                    criteria['capacity'] = int(ai_capacity)
                    print(f"   ✅ Used AI capacity directly: {criteria['capacity']}")
            except (ValueError, TypeError):
                criteria['capacity'] = 8  # Default
                print(f"   ⚠️  Capacity parsing failed, using default: {criteria['capacity']}")
        else:
            # Try to extract from original request
            capacity_match = re.search(r'(\d+)\s*(?:people|attendees|participants)', original_request.lower())
            if capacity_match:
                criteria['capacity'] = int(capacity_match.group(1))
                print(f"   ✅ Extracted capacity from original request: {criteria['capacity']}")
            else:
                criteria['capacity'] = 8  # Default
                print(f"   ⚠️  No capacity found, using default: {criteria['capacity']}")
        
        # Parse location
        criteria['location'] = extracted.get('location')
        
        # Parse equipment
        ai_equipment = extracted.get('equipment', [])
        if isinstance(ai_equipment, list):
            criteria['equipment'] = ai_equipment
        else:
            criteria['equipment'] = []
        
        print(f"\n📋 Final parsed criteria:")
        print(f"   📅 Date: {criteria['date']}")
        print(f"   ⏰ Start Time: {criteria['start_time']}")
        print(f"   ⏰ End Time: {criteria['end_time']}")
        print(f"   👥 Capacity: {criteria['capacity']}")
        print(f"   📍 Location: {criteria['location']}")
        print(f"   🛠️ Equipment: {criteria['equipment']}")
        
        return criteria
        
    except Exception as e:
        print(f"❌ Error extracting criteria from AI response: {e}")
        import traceback
        traceback.print_exc()
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

def detect_momentus_form_with_ai(driver, user_request, dropdown_matcher):
    """AI-enhanced detection and analysis of Momentus form elements with comprehensive debugging"""
    
    print("🔍 Scanning Momentus form with comprehensive debugging...")
    
    form_elements = {
        'date_fields': [],
        'time_fields': [],
        'ai_dropdowns': [],
        'buttons': [],
        'form': None
    }
    
    try:
        # First, let's see what page we're actually on
        print(f"\n📄 DEBUG: Current page info:")
        print(f"   URL: {driver.current_url}")
        print(f"   Title: {driver.title}")
        
        # Wait for page to be fully loaded - Ungerboeck system needs more time
        print(f"⏳ Waiting for Ungerboeck/Momentus page to fully load...")
        time.sleep(5)
        
        # Check if we're on the right page
        if 'ungerboeck' in driver.current_url.lower():
            print(f"✅ Detected Ungerboeck system - using enhanced loading strategy...")
            
            # Wait for dynamic content to load
            wait = WebDriverWait(driver, 20)
            try:
                # Wait for common Ungerboeck form elements to appear
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
                print(f"   Form detected, waiting for dropdowns...")
                time.sleep(3)
            except TimeoutException:
                print(f"   No forms detected within 20 seconds")
                
            # Trigger any lazy loading by scrolling
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
        
        # Check if there are any forms at all
        all_forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"\n📋 Found {len(all_forms)} form(s) on page")
        
        for i, form in enumerate(all_forms):
            try:
                form_id = form.get_attribute('id')
                form_class = form.get_attribute('class')
                form_action = form.get_attribute('action')
                print(f"   Form {i+1}: id='{form_id}', class='{form_class}', action='{form_action}'")
                if i == 0:
                    form_elements['form'] = form
            except:
                continue
        
        # Let's try MUCH broader selectors for date fields
        print(f"\n📅 DEBUG: Searching for date fields...")
        
        all_date_selectors = [
            "//input[@type='date']",
            "//input[contains(@name, 'date')]",
            "//input[contains(@id, 'date')]",
            "//input[contains(@class, 'date')]",
            "//input[contains(@placeholder, 'date')]",
            "//input[contains(@ng-model, 'date')]",
            "//input[contains(@data-date, '')]",
            "//*[@data-testid='date']//input",
            "//*[contains(@class, 'datepicker')]//input",
            "//input[contains(@aria-label, 'date')]",
            "//div[contains(@class, 'date')]//input"
        ]
        
        all_date_inputs = []
        for selector in all_date_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    elem_info = f"type='{elem.get_attribute('type')}' name='{elem.get_attribute('name')}' id='{elem.get_attribute('id')}'"
                    print(f"   Found date field: {elem_info}")
                    if elem.is_displayed() and elem not in all_date_inputs:
                        form_elements['date_fields'].append(elem)
                        all_date_inputs.append(elem)
            except Exception as e:
                print(f"   Date selector failed: {selector} - {e}")
        
        # If no date fields found, let's look for ANY input that might be a date
        if not form_elements['date_fields']:
            print(f"   ⚠️  No date fields found with standard selectors, trying all inputs...")
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            print(f"   Found {len(all_inputs)} total input elements")
            
            for i, inp in enumerate(all_inputs[:10]):  # Check first 10
                try:
                    if inp.is_displayed():
                        inp_type = inp.get_attribute('type')
                        inp_name = inp.get_attribute('name')
                        inp_id = inp.get_attribute('id')
                        inp_class = inp.get_attribute('class')
                        inp_placeholder = inp.get_attribute('placeholder')
                        
                        print(f"   Input {i+1}: type='{inp_type}', name='{inp_name}', id='{inp_id}', class='{inp_class}', placeholder='{inp_placeholder}'")
                        
                        # Check if this looks like a date field
                        date_indicators = ['date', 'calendar', 'day', 'month', 'year']
                        field_text = f"{inp_name} {inp_id} {inp_class} {inp_placeholder}".lower()
                        
                        if any(indicator in field_text for indicator in date_indicators):
                            print(f"   ✅ Potential date field found: {inp_name or inp_id}")
                            form_elements['date_fields'].append(inp)
                except:
                    continue
        
        # Let's try broader selectors for time fields including custom dropdowns
        print(f"\n⏰ DEBUG: Searching for time fields...")
        
        all_time_selectors = [
            "//input[@type='time']",
            "//select[contains(@name, 'time')]",
            "//select[contains(@id, 'time')]",
            "//select[contains(@class, 'time')]",
            "//select[contains(@name, 'hour')]",
            "//select[contains(@name, 'minute')]",
            "//select[contains(@id, 'hour')]",
            "//select[contains(@id, 'minute')]",
            "//select[contains(@name, 'start')]",
            "//select[contains(@name, 'end')]",
            "//input[contains(@name, 'time')]",
            "//input[contains(@id, 'time')]",
            # Add custom dropdown patterns for time
            "//*[contains(@class, 'time') and contains(@class, 'select')]",
            "//*[contains(@class, 'time') and contains(@class, 'dropdown')]",
            "//*[@role='combobox' and contains(@aria-label, 'time')]",
            "//*[contains(text(), 'Start Time')]//following-sibling::*//select",
            "//*[contains(text(), 'End Time')]//following-sibling::*//select",
            "//*[contains(text(), 'start time')]//following-sibling::*//select",
            "//*[contains(text(), 'end time')]//following-sibling::*//select",
            "//label[contains(text(), 'Start')]//following-sibling::select",
            "//label[contains(text(), 'End')]//following-sibling::select"
        ]
        
        all_time_fields = []
        for selector in all_time_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    elem_info = f"tag='{elem.tag_name}' name='{elem.get_attribute('name')}' id='{elem.get_attribute('id')}' class='{elem.get_attribute('class')}'"
                    print(f"   Found time field: {elem_info}")
                    if elem.is_displayed() and elem not in all_time_fields:
                        form_elements['time_fields'].append(elem)
                        all_time_fields.append(elem)
            except Exception as e:
                print(f"   Time selector failed: {selector} - {e}")
        
        # If no time fields found, look for ALL select elements and check if any might be time-related
        if not all_time_fields:
            print(f"   ⚠️  No time fields found with standard selectors, checking all selects for time-related options...")
            all_selects_for_time = driver.find_elements(By.TAG_NAME, "select")
            
            for select_elem in all_selects_for_time:
                try:
                    if select_elem.is_displayed():
                        select_obj = Select(select_elem)
                        options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                        
                        # Check if options look like times
                        has_time_options = any(
                            re.search(r'\d{1,2}:\d{2}', option) or 
                            re.search(r'\d{1,2}\s*(AM|PM|am|pm)', option) for option in options
                        )
                        
                        if has_time_options:
                            select_name = select_elem.get_attribute('name') or select_elem.get_attribute('id') or 'time_select'
                            print(f"   ✅ Found potential time dropdown: {select_name}")
                            print(f"      Sample options: {options[:3]}")
                            form_elements['time_fields'].append(select_elem)
                            all_time_fields.append(select_elem)
                except Exception as e:
                    print(f"   Error checking select for time options: {e}")
        
        # Search for attendees/capacity input field
        print(f"\n👥 DEBUG: Searching for attendees/capacity input field...")
        
        attendees_selectors = [
            "//input[contains(@name, 'attendee')]",
            "//input[contains(@id, 'attendee')]",
            "//input[contains(@placeholder, 'attendee')]",
            "//input[contains(@name, 'capacity')]",
            "//input[contains(@id, 'capacity')]",
            "//input[contains(@placeholder, 'capacity')]",
            "//input[contains(@name, 'people')]",
            "//input[contains(@id, 'people')]",
            "//input[contains(@name, 'participants')]",
            "//input[contains(@id, 'participants')]",
            "//input[@type='number']",
            "//*[contains(text(), 'Attendees')]//following-sibling::input",
            "//*[contains(text(), 'attendees')]//following-sibling::input",
            "//*[contains(text(), 'Of Attendees')]//following-sibling::input",
            "//label[contains(text(), 'Attendees')]//following-sibling::input"
        ]
        
        attendees_fields = []
        for selector in attendees_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        elem_info = f"type='{elem.get_attribute('type')}' name='{elem.get_attribute('name')}' id='{elem.get_attribute('id')}' placeholder='{elem.get_attribute('placeholder')}'"
                        print(f"   Found attendees field: {elem_info}")
                        if elem not in attendees_fields:
                            attendees_fields.append(elem)
            except Exception as e:
                print(f"   Attendees selector failed: {selector} - {e}")
        
        form_elements['attendees_fields'] = attendees_fields
        
        # Let's examine ALL select elements on the page with better filtering
        print(f"\n📋 DEBUG: Examining ALL select dropdowns...")
        
        # Try multiple times with increasing waits for dynamic content
        all_selects = []
        for attempt in range(3):
            all_selects = driver.find_elements(By.TAG_NAME, "select")
            print(f"   Attempt {attempt + 1}: Found {len(all_selects)} select elements")
            
            if len(all_selects) > 0:
                break
            elif attempt < 2:  # Don't wait on last attempt
                print(f"   Waiting for more select elements to load...")
                time.sleep(3)
        
        print(f"   FINAL: Found {len(all_selects)} total select elements")
        
        # If no selects found, try alternative approaches
        if len(all_selects) == 0:
            print(f"\n🚨 NO SELECT ELEMENTS FOUND! Trying alternative detection methods...")
            
            # Check if dropdowns are in iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"   Found {len(iframes)} iframes on page")
            
            # Check for custom dropdown implementations
            custom_dropdown_selectors = [
                "//*[@role='combobox']",
                "//*[@role='listbox']",
                "//*[contains(@class, 'dropdown')]",
                "//*[contains(@class, 'select')]",
                "//*[contains(@class, 'picker')]",
                "//*[contains(@aria-label, 'dropdown')]",
                "//*[contains(@aria-label, 'select')]",
                "//*[@data-toggle='dropdown']",
                "//div[contains(@class, 'ui-selectmenu')]",
                "//div[contains(@class, 'chosen')]",
                "//div[contains(@class, 'multiselect')]"
            ]
            
            for selector in custom_dropdown_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} custom dropdowns with selector: {selector}")
                        for elem in elements[:3]:  # Show first 3
                            print(f"      Custom dropdown: class='{elem.get_attribute('class')}', role='{elem.get_attribute('role')}'")
                except:
                    continue
            
            # Check if we need to wait longer or scroll
            print(f"\n🔄 Waiting longer and trying to trigger dropdown loading...")
            time.sleep(5)
            
            # Try scrolling to bottom to load dynamic content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Try again after scrolling
            all_selects = driver.find_elements(By.TAG_NAME, "select")
            print(f"   After scrolling and waiting: Found {len(all_selects)} select elements")
        
        # Wait a bit more for dynamic selects to load
        time.sleep(2)
        
        for i, select_elem in enumerate(all_selects):
            try:
                select_name = select_elem.get_attribute('name')
                select_id = select_elem.get_attribute('id')
                select_class = select_elem.get_attribute('class')
                
                print(f"\n   Select {i+1}: name='{select_name}', id='{select_id}', class='{select_class}'")
                
                # Check if element is actually in the DOM and visible
                try:
                    is_displayed = select_elem.is_displayed()
                    is_enabled = select_elem.is_enabled()
                    print(f"      Displayed: {is_displayed}, Enabled: {is_enabled}")
                except:
                    print(f"      Element state check failed")
                    continue
                
                if is_displayed and is_enabled:
                    try:
                        # Scroll element into view to ensure it's accessible
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_elem)
                        time.sleep(0.5)
                        
                        select_obj = Select(select_elem)
                        options = []
                        
                        # Get options with error handling
                        try:
                            raw_options = select_obj.options
                            options = [opt.text.strip() for opt in raw_options if opt.text.strip()]
                            print(f"      Options: {len(options)} total")
                        except Exception as opt_error:
                            print(f"      Error getting options: {opt_error}")
                            continue
                        
                        # Only process dropdowns with meaningful options
                        if len(options) > 1 and not all(opt.lower() in ['', 'select', 'choose', 'none'] for opt in options):
                            print(f"      First 5 options: {options[:5]}")
                            
                            # Categorize this dropdown based on its options and context
                            field_context = f"{select_name} {select_id} {select_class}".lower()
                            dropdown_category = categorize_dropdown_by_content(field_context, options)
                            
                            print(f"      Categorized as: {dropdown_category}")
                            
                            # Handle time dropdowns specially but don't skip them
                            if dropdown_category in ['start_time', 'end_time']:
                                if dropdown_category == 'start_time':
                                    form_elements['start_time_dropdown'] = select_elem
                                elif dropdown_category == 'end_time':  
                                    form_elements['end_time_dropdown'] = select_elem
                                # Also add to time_fields for backward compatibility
                                if select_elem not in form_elements['time_fields']:
                                    form_elements['time_fields'].append(select_elem)
                            
                            # Skip generic time fields to avoid duplicates, but process start/end specifically
                            if dropdown_category == 'time_generic':
                                print(f"      Skipped: Generic time dropdown (looking for start/end specific)")
                                continue
                            
                            # Use AI to analyze this dropdown
                            try:
                                selected_option = analyze_dropdown_with_ai(
                                    dropdown_matcher, 
                                    user_request, 
                                    select_name or select_id or f'dropdown_{i+1}', 
                                    options
                                )
                                
                                dropdown_info = {
                                    'element': select_elem,
                                    'name': select_name or select_id or f'dropdown_{i+1}',
                                    'options': options,
                                    'ai_selection': selected_option
                                }
                                
                                form_elements['ai_dropdowns'].append(dropdown_info)
                                
                                if selected_option:
                                    print(f"      🤖 AI selected: '{selected_option}'")
                                else:
                                    print(f"      ⚠️  No AI selection made")
                                    
                            except Exception as ai_error:
                                print(f"      AI analysis error: {ai_error}")
                        else:
                            print(f"      Skipped: Too few meaningful options ({len(options)})")
                            if options:
                                print(f"      Options were: {options}")
                                
                    except Exception as e:
                        print(f"      Error analyzing dropdown: {e}")
                else:
                    print(f"      Skipped: Not displayed or not enabled")
                    
            except Exception as e:
                print(f"   Select {i+1} error: {e}")
        
        # Look for submit buttons with broader search
        print(f"\n🔘 DEBUG: Searching for submit buttons...")
        
        button_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Search')]",
            "//button[contains(text(), 'Find')]",
            "//button[contains(text(), 'Submit')]",
            "//button[contains(@class, 'submit')]",
            "//input[@value='Search']",
            "//input[@value='Find']"
        ]
        
        for selector in button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        button_text = elem.text or elem.get_attribute('value')
                        print(f"   Found button: '{button_text}'")
                        form_elements['buttons'].append(elem)
            except:
                continue
        
        # If still no buttons, look at all buttons
        if not form_elements['buttons']:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"   Found {len(all_buttons)} total buttons, checking first 5...")
            for i, btn in enumerate(all_buttons[:5]):
                try:
                    if btn.is_displayed():
                        btn_text = btn.text
                        btn_type = btn.get_attribute('type')
                        print(f"   Button {i+1}: '{btn_text}' (type: {btn_type})")
                        
                        # Look for likely submit buttons
                        if any(word in btn_text.lower() for word in ['search', 'find', 'submit', 'go']):
                            form_elements['buttons'].append(btn)
                except:
                    continue
        
        print(f"\n📊 FINAL Form detection results:")
        print(f"   📅 Date fields: {len(form_elements['date_fields'])}")
        print(f"   ⏰ Time fields: {len(form_elements['time_fields'])}")
        print(f"   👥 Attendees fields: {len(form_elements.get('attendees_fields', []))}")
        print(f"   🧠 AI-analyzed dropdowns: {len(form_elements['ai_dropdowns'])}")
        print(f"   🔘 Submit buttons: {len(form_elements['buttons'])}")
        
        # If dropdown detection failed completely, do comprehensive element analysis
        if len(form_elements['ai_dropdowns']) == 0:
            print(f"\n🔍 COMPREHENSIVE ELEMENT ANALYSIS (No dropdowns detected)...")
            
            try:
                # Look for ANY interactive elements
                print(f"   Analyzing all interactive elements...")
                
                # Check all elements by tag
                element_counts = {}
                for tag in ['input', 'select', 'button', 'div', 'span', 'a']:
                    elements = driver.find_elements(By.TAG_NAME, tag)
                    element_counts[tag] = len(elements)
                    print(f"   {tag.upper()}: {len(elements)} elements")
                
                # Look specifically for elements with dropdown-like classes or attributes
                dropdown_indicators = [
                    ('class*=dropdown', "//*[contains(@class, 'dropdown')]"),
                    ('class*=select', "//*[contains(@class, 'select')]"),
                    ('role=combobox', "//*[@role='combobox']"),
                    ('role=listbox', "//*[@role='listbox']"),
                    ('data-toggle', "//*[@data-toggle]"),
                    ('aria-expanded', "//*[@aria-expanded]")
                ]
                
                for desc, selector in dropdown_indicators:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        if elements:
                            print(f"   {desc}: {len(elements)} elements")
                            for i, elem in enumerate(elements[:2]):  # Show first 2
                                print(f"      {i+1}. class='{elem.get_attribute('class')}', id='{elem.get_attribute('id')}'")
                    except:
                        continue
                
                # Save comprehensive debug information
                debug_info = {
                    'url': driver.current_url,
                    'title': driver.title,
                    'element_counts': element_counts,
                    'window_size': driver.get_window_size(),
                    'timestamp': datetime.now().isoformat()
                }
                
                with open("momentus_element_debug.json", "w", encoding="utf-8") as f:
                    json.dump(debug_info, f, indent=2)
                print(f"   Element analysis saved: momentus_element_debug.json")
                
            except Exception as e:
                print(f"   Error in element analysis: {e}")
        
        # If we still found nothing, let's save a screenshot for debugging
        if (len(form_elements['date_fields']) == 0 and 
            len(form_elements['time_fields']) == 0 and 
            len(form_elements['ai_dropdowns']) == 0):
            
            print(f"\n🚨 NO FORM ELEMENTS FOUND! Saving screenshot for debugging...")
            try:
                screenshot_path = "momentus_debug_screenshot.png"
                driver.save_screenshot(screenshot_path)
                print(f"   Screenshot saved: {screenshot_path}")
                
                # Also save page source
                with open("momentus_debug_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"   Page source saved: momentus_debug_source.html")
                
                print(f"\n💡 DEBUG TIPS:")
                print(f"   1. Check the screenshot to see what's actually on the page")
                print(f"   2. Look at the HTML source to find the actual element structure")
                print(f"   3. The dropdowns might be custom components, iframes, or dynamically loaded")
                print(f"   4. You may need to wait longer or trigger specific events to load the form")
                
            except Exception as e:
                print(f"   Could not save debug files: {e}")
        
        return form_elements
        
    except Exception as e:
        print(f"❌ Form detection error: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_dropdown_with_ai(dropdown_matcher, user_request, field_name, options):
    """Use AI to analyze a dropdown and select appropriate option"""
    
    try:
        # Determine dropdown type based on field name and options
        dropdown_type = categorize_dropdown(field_name, options)
        
        if dropdown_type == 'capacity':
            return dropdown_matcher.interpret_capacity_requirement(user_request, options)
        else:
            # Use generic matching with context
            field_context = f"{dropdown_type} (field: {field_name})"
            return dropdown_matcher.match_dropdown_options(user_request, options, field_context)
    
    except Exception as e:
        print(f"   ⚠️  AI analysis error: {e}")
        return None

def categorize_dropdown(field_name, options):
    """Categorize dropdown based on field name and options"""
    
    field_lower = field_name.lower()
    options_text = ' '.join(options).lower()
    
    # Space type indicators
    if any(keyword in field_lower for keyword in ['space', 'room', 'type']):
        return 'space type'
    if any(keyword in options_text for keyword in ['conference', 'classroom', 'study', 'meeting']):
        return 'space type'
    
    # Building indicators
    if any(keyword in field_lower for keyword in ['building', 'location', 'where']):
        return 'building/location'
    if any(keyword in options_text for keyword in ['hall', 'building', 'center']):
        return 'building/location'
    
    # Capacity indicators
    if any(keyword in field_lower for keyword in ['capacity', 'people', 'size']):
        return 'capacity'
    if any(re.search(r'\d+.*people', option.lower()) for option in options):
        return 'capacity'
    
    # Duration indicators
    if any(keyword in field_lower for keyword in ['duration', 'length', 'time']):
        return 'duration/length'
    if any(keyword in options_text for keyword in ['hour', 'minute', 'hrs']):
        return 'duration/length'
    
    # Features indicators
    if any(keyword in field_lower for keyword in ['feature', 'equipment', 'amenity']):
        return 'features/equipment'
    if any(keyword in options_text for keyword in ['projector', 'whiteboard', 'computer', 'screen']):
        return 'features/equipment'
    
    return f'form field ({field_name})'

def categorize_dropdown_by_content(field_context, options):
    """Enhanced dropdown categorization based on field context and option content"""
    
    options_text = ' '.join(options).lower()
    
    # Time detection - check if options look like times
    has_time_pattern = any(
        re.search(r'\d{1,2}:\d{2}', option) or 
        re.search(r'\d{1,2}\s*(am|pm)', option.lower()) for option in options
    )
    
    if has_time_pattern:
        # Try to distinguish start vs end time based on context
        if any(word in field_context for word in ['start', 'from', 'begin']):
            return 'start_time'
        elif any(word in field_context for word in ['end', 'to', 'until', 'finish']):
            return 'end_time'
        else:
            return 'time_generic'
    
    # Space type detection
    if any(keyword in options_text for keyword in ['conference', 'classroom', 'meeting', 'study', 'lab', 'auditorium']):
        return 'space_type'
    
    # Venue/Building detection
    if any(keyword in options_text for keyword in ['hall', 'building', 'center', 'room', 'floor']):
        return 'venue'
    
    # Features detection
    if any(keyword in options_text for keyword in ['projector', 'whiteboard', 'screen', 'computer', 'microphone', 'audio']):
        return 'features'
    
    # Capacity detection
    if any(re.search(r'\d+.*people', option.lower()) for option in options):
        return 'capacity'
    
    return 'unknown'

def display_form_elements(form_elements):
    """Display detected form elements"""
    
    print("📋 Detected form elements:")
    print(f"   📅 Date fields: {len(form_elements['date_fields'])}")
    print(f"   ⏰ Time fields: {len(form_elements['time_fields'])}")
    print(f"   📋 Dropdowns: {len(form_elements['select_fields'])}")
    print(f"   🔘 Buttons: {len(form_elements['buttons'])}")

def fill_momentus_form_with_ai(driver, criteria, form_elements, user_request):
    """Fill form using AI-selected dropdown options and criteria"""
    
    success_count = 0
    total_attempts = 0
    
    try:
        print(f"\n🔧 DEBUG: Starting form filling...")
        print(f"   Date fields available: {len(form_elements.get('date_fields', []))}")
        print(f"   Time fields available: {len(form_elements.get('time_fields', []))}")
        print(f"   Attendees fields available: {len(form_elements.get('attendees_fields', []))}")
        print(f"   AI dropdowns available: {len(form_elements.get('ai_dropdowns', []))}")
        
        # Fill date fields with enhanced debugging
        if criteria.get('date') and form_elements.get('date_fields'):
            print(f"\n📅 Attempting to fill date: {criteria['date']}")
            for i, date_field in enumerate(form_elements['date_fields']):
                try:
                    total_attempts += 1
                    print(f"   Trying date field {i+1}...")
                    
                    # Scroll into view first
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_field)
                    time.sleep(0.5)
                    
                    # Check if field is interactable
                    if not date_field.is_displayed():
                        print(f"   ❌ Date field {i+1} not visible")
                        continue
                        
                    if not date_field.is_enabled():
                        print(f"   ❌ Date field {i+1} not enabled")
                        continue
                    
                    # Try multiple date formats
                    date_formats = [
                        criteria['date'],  # YYYY-MM-DD
                        datetime.strptime(criteria['date'], "%Y-%m-%d").strftime("%m/%d/%Y"),  # MM/DD/YYYY
                        datetime.strptime(criteria['date'], "%Y-%m-%d").strftime("%m-%d-%Y")   # MM-DD-YYYY
                    ]
                    
                    for date_format in date_formats:
                        try:
                            date_field.clear()
                            time.sleep(0.2)
                            date_field.send_keys(date_format)
                            time.sleep(0.5)
                            
                            # Trigger change event
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", date_field)
                            
                            # Check if value was set
                            current_value = date_field.get_attribute('value')
                            if current_value:
                                print(f"✅ Filled date field {i+1}: {date_format} (value: {current_value})")
                                success_count += 1
                                break
                        except Exception as inner_e:
                            print(f"   ⚠️  Date format {date_format} failed: {inner_e}")
                    
                    if success_count > 0:
                        break
                        
                except Exception as e:
                    print(f"⚠️  Date field {i+1} failed: {e}")
        else:
            print(f"⚠️  Skipping date: criteria has date = {criteria.get('date')}, fields = {len(form_elements.get('date_fields', []))}")
        
        # Fill start time dropdown specifically
        if criteria.get('start_time') and form_elements.get('start_time_dropdown'):
            print(f"\n⏰ Attempting to fill START TIME dropdown: {criteria['start_time']}")
            total_attempts += 1
            
            try:
                start_dropdown = form_elements['start_time_dropdown']
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_dropdown)
                time.sleep(0.5)
                
                if start_dropdown.is_displayed() and start_dropdown.is_enabled():
                    select_obj = Select(start_dropdown)
                    print(f"   Start time dropdown has {len(select_obj.options)} options")
                    
                    # Try multiple time format matches
                    time_formats_to_try = [
                        criteria['start_time'],  # 10:00
                        convert_to_12h_format(criteria['start_time']),  # 10:00 AM
                        criteria['start_time'].replace(':', ''),  # 1000
                        criteria['start_time'].lstrip('0'),  # 10:00 if was 010:00
                    ]
                    
                    start_matched = False
                    for time_format in time_formats_to_try:
                        for option in select_obj.options:
                            option_text = option.text.strip()
                            if (time_format in option_text or 
                                option_text.replace(':', '').replace(' ', '').lower() == time_format.replace(':', '').replace(' ', '').lower()):
                                
                                select_obj.select_by_visible_text(option_text)
                                print(f"✅ Selected START TIME: {option_text}")
                                success_count += 1
                                start_matched = True
                                break
                        if start_matched:
                            break
                    
                    if not start_matched:
                        print(f"   ⚠️  No matching start time found for {criteria['start_time']}")
                        print(f"   Available options: {[opt.text[:15] for opt in select_obj.options[:5]]}")
                        
            except Exception as e:
                print(f"⚠️  Start time dropdown failed: {e}")
        
        # Fill end time dropdown specifically  
        if criteria.get('end_time') and form_elements.get('end_time_dropdown'):
            print(f"\n⏰ Attempting to fill END TIME dropdown: {criteria['end_time']}")
            total_attempts += 1
            
            try:
                end_dropdown = form_elements['end_time_dropdown']
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", end_dropdown)
                time.sleep(0.5)
                
                if end_dropdown.is_displayed() and end_dropdown.is_enabled():
                    select_obj = Select(end_dropdown)
                    print(f"   End time dropdown has {len(select_obj.options)} options")
                    
                    # Try multiple time format matches
                    time_formats_to_try = [
                        criteria['end_time'],  # 11:00
                        convert_to_12h_format(criteria['end_time']),  # 11:00 AM
                        criteria['end_time'].replace(':', ''),  # 1100
                        criteria['end_time'].lstrip('0'),  # 11:00 if was 011:00
                    ]
                    
                    end_matched = False
                    for time_format in time_formats_to_try:
                        for option in select_obj.options:
                            option_text = option.text.strip()
                            if (time_format in option_text or 
                                option_text.replace(':', '').replace(' ', '').lower() == time_format.replace(':', '').replace(' ', '').lower()):
                                
                                select_obj.select_by_visible_text(option_text)
                                print(f"✅ Selected END TIME: {option_text}")
                                success_count += 1
                                end_matched = True
                                break
                        if end_matched:
                            break
                    
                    if not end_matched:
                        print(f"   ⚠️  No matching end time found for {criteria['end_time']}")
                        print(f"   Available options: {[opt.text[:15] for opt in select_obj.options[:5]]}")
                        
            except Exception as e:
                print(f"⚠️  End time dropdown failed: {e}")
        
        # Fallback: Fill any remaining time fields if specific dropdowns weren't found
        remaining_time_fields = [f for f in form_elements.get('time_fields', []) 
                               if f != form_elements.get('start_time_dropdown') 
                               and f != form_elements.get('end_time_dropdown')]
        
        if remaining_time_fields and (criteria.get('start_time') or criteria.get('end_time')):
            print(f"\n⏰ Filling {len(remaining_time_fields)} remaining time fields...")
            for i, time_field in enumerate(remaining_time_fields[:2]):  # Limit to 2
                try:
                    total_attempts += 1
                    time_value = criteria.get('start_time') if i == 0 else criteria.get('end_time')
                    if not time_value:
                        continue
                        
                    print(f"   Trying remaining time field {i+1}: {time_value}")
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", time_field)
                    time.sleep(0.5)
                    
                    if time_field.is_displayed() and time_field.is_enabled() and time_field.tag_name == 'select':
                        select_obj = Select(time_field)
                        
                        time_matched = False
                        for option in select_obj.options:
                            if (time_value in option.text or 
                                convert_to_12h_format(time_value) in option.text):
                                
                                select_obj.select_by_visible_text(option.text)
                                print(f"✅ Selected time in field {i+1}: {option.text}")
                                success_count += 1
                                time_matched = True
                                break
                        
                        if not time_matched:
                            print(f"   ⚠️  No match in remaining field {i+1}")
                    
                except Exception as e:
                    print(f"⚠️  Remaining time field {i+1} failed: {e}")
        
        # Status check
        if not form_elements.get('start_time_dropdown') and not form_elements.get('end_time_dropdown'):
            print(f"⚠️  No specific start/end time dropdowns found, using generic time fields")
        
        # Fill attendees/capacity fields
        attendees_fields = form_elements.get('attendees_fields', [])
        if criteria.get('capacity') and attendees_fields:
            print(f"\n👥 Attempting to fill attendees: {criteria['capacity']}")
            for i, attendees_field in enumerate(attendees_fields):
                try:
                    total_attempts += 1
                    print(f"   Trying attendees field {i+1}...")
                    
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", attendees_field)
                    time.sleep(0.5)
                    
                    if not attendees_field.is_displayed() or not attendees_field.is_enabled():
                        print(f"   ❌ Attendees field {i+1} not interactable")
                        continue
                    
                    # Clear and fill
                    attendees_field.clear()
                    time.sleep(0.2)
                    attendees_field.send_keys(str(criteria['capacity']))
                    time.sleep(0.5)
                    
                    # Trigger change event
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", attendees_field)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", attendees_field)
                    
                    # Verify value was set
                    current_value = attendees_field.get_attribute('value')
                    if current_value == str(criteria['capacity']):
                        print(f"✅ Filled attendees field {i+1}: {criteria['capacity']} (verified)")
                        success_count += 1
                        break
                    else:
                        print(f"   ⚠️  Value verification failed: expected {criteria['capacity']}, got {current_value}")
                    
                except Exception as e:
                    print(f"⚠️  Attendees field {i+1} failed: {e}")
        else:
            print(f"⚠️  Skipping attendees: criteria has capacity = {criteria.get('capacity')}, fields = {len(attendees_fields)}")
        
        # Fill AI-analyzed dropdowns with enhanced debugging
        ai_dropdowns = form_elements.get('ai_dropdowns', [])
        if ai_dropdowns:
            print(f"\n🧠 Attempting to fill {len(ai_dropdowns)} AI-analyzed dropdowns...")
            for i, dropdown_info in enumerate(ai_dropdowns):
                try:
                    total_attempts += 1
                    field_name = dropdown_info.get('name', f'dropdown_{i+1}')
                    ai_selection = dropdown_info.get('ai_selection')
                    
                    print(f"   Dropdown {i+1} ({field_name}): AI wants to select '{ai_selection}'")
                    
                    if not ai_selection:
                        print(f"   ⚠️  No AI selection for {field_name}")
                        continue
                    
                    element = dropdown_info.get('element')
                    if not element:
                        print(f"   ❌ No element for {field_name}")
                        continue
                    
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    
                    if not element.is_displayed() or not element.is_enabled():
                        print(f"   ❌ Dropdown {field_name} not interactable")
                        continue
                    
                    select_obj = Select(element)
                    
                    # Try exact match first
                    selection_made = False
                    for option in select_obj.options:
                        if option.text.strip() == ai_selection:
                            select_obj.select_by_visible_text(option.text)
                            print(f"✅ AI selected '{option.text}' for {field_name} (exact match)")
                            success_count += 1
                            selection_made = True
                            break
                    
                    # Try partial match if exact failed
                    if not selection_made:
                        for option in select_obj.options:
                            if (ai_selection.lower() in option.text.lower() or 
                                option.text.lower() in ai_selection.lower()):
                                select_obj.select_by_visible_text(option.text)
                                print(f"✅ AI selected '{option.text}' for {field_name} (partial match)")
                                success_count += 1
                                selection_made = True
                                break
                    
                    if not selection_made:
                        print(f"   ⚠️  Could not find option '{ai_selection}' in {field_name}")
                        available_options = [opt.text for opt in select_obj.options[:5]]
                        print(f"   Available: {available_options}")
                        
                except Exception as e:
                    print(f"⚠️  Dropdown {field_name} selection error: {e}")
        else:
            print(f"⚠️  No AI dropdowns to fill")
        
        print(f"\n📊 Form filling results:")
        print(f"   ✅ Successfully filled: {success_count} fields")
        print(f"   ⚠️  Total attempts: {total_attempts}")
        print(f"   📈 Success rate: {(success_count/max(total_attempts, 1)*100):.1f}%")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Form filling error: {e}")
        import traceback
        traceback.print_exc()
        return False

def convert_to_12h_format(time_24h):
    """Convert 24-hour time to 12-hour format for matching"""
    try:
        hour, minute = map(int, time_24h.split(':'))
        period = 'AM' if hour < 12 else 'PM'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"
    except:
        return time_24h

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

def analyze_search_results_with_ai(driver, user_request, dropdown_matcher):
    """Analyze search results using AI to recommend best options"""
    
    try:
        # Wait for results to load
        time.sleep(3)
        
        current_title = driver.title
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
        
        rooms = []
        for selector in room_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements[:5]:  # Limit to first 5 results
                    try:
                        room_text = elem.text
                        if room_text and len(room_text) > 10:  # Skip empty or very short text
                            rooms.append(room_text)
                    except:
                        continue
            except:
                continue
        
        if rooms:
            print(f"✅ Found {len(rooms)} room results!")
            
            # Use AI to recommend the best room
            print("\n🤖 AI analyzing room options...")
            best_room = dropdown_matcher.match_dropdown_options(
                user_request,
                rooms,
                "available room (which room best matches the user's needs)"
            )
            
            if best_room:
                print(f"\n🎯 AI recommends: {best_room[:100]}...")
                
                # Try to find and highlight the recommended room
                for elem in driver.find_elements(By.XPATH, "//*[contains(text(), '" + best_room.split('\n')[0][:20] + "')]"):
                    try:
                        driver.execute_script("arguments[0].style.border='3px solid red';", elem)
                        break
                    except:
                        continue
            
            print("\n📋 All available options:")
            for i, room in enumerate(rooms, 1):
                print(f"   {i}. {room[:100]}...")
            
            return {
                'rooms_found': len(rooms),
                'rooms': rooms,
                'ai_recommendation': best_room
            }
        else:
            print("⚠️  No rooms found with current criteria")
            return {'rooms_found': 0}
        
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