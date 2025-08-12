#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Room Booking Script - Full Momentus Workflow
Builds on the working date parsing and navigation to complete the full booking flow
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
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

# Fix encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def complete_room_booking_workflow():
    """Complete room booking with full Momentus form handling"""
    
    print("=" * 80)
    print("🏢 COMPLETE ROOM BOOKING ASSISTANT")
    print("=" * 80)
    print("Full workflow: SharePoint → Momentus → Form Filling → Room Selection")
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
    print(f"\n🔍 Processing: '{booking_request}'")
    ai_response = agent.process_request(booking_request)
    
    # Extract booking criteria
    booking_criteria = extract_criteria_from_ai_response(ai_response, booking_request)
    
    # Display parsed results
    print("\n📋 Parsed booking request:")
    print(f"   📅 Date: {booking_criteria['date']}")
    print(f"   ⏰ Time: {booking_criteria['start_time']} - {booking_criteria['end_time']}")
    print(f"   👥 Capacity: {booking_criteria['capacity']} people")
    print(f"   📍 Location: {booking_criteria['location'] or 'Any'}")
    print(f"   🛠️  Equipment: {', '.join(booking_criteria['equipment']) if booking_criteria['equipment'] else 'None specified'}")
    
    print()
    confirm = input("✅ Proceed with booking? (y/n): ").lower().startswith('y')
    
    if not confirm:
        print("🔄 Let's try again...")
        return complete_room_booking_workflow()
    
    # Step 3: Browser Automation
    print("\n" + "=" * 80)
    print("STARTING BROWSER AUTOMATION")
    print("=" * 80)
    
    load_dotenv()
    sharepoint_url = os.getenv('SHAREPOINT_URL', 'https://utexas.sharepoint.com/sites/McCombs-DepartmentofFinance/SitePages/CollabHome.aspx')
    
    print("🚀 Launching Chrome...")
    automation = setup_automation_session()
    
    if not automation:
        print("❌ Failed to set up automation session")
        return
    
    print("✅ Chrome launched successfully!")
    
    try:
        # Navigate to Momentus
        momentus_ready = navigate_to_momentus_complete(automation, sharepoint_url)
        
        if not momentus_ready:
            print("❌ Failed to reach Momentus")
            input("Press Enter when you've manually navigated to Momentus...")
        
        # Step 4: Complete form filling with all fields
        print("\n📝 Filling Momentus booking form...")
        form_success = fill_momentus_form_complete(automation.driver, booking_criteria)
        
        if form_success:
            print("✅ Form filled successfully!")
            
            # Step 5: Submit search and handle results
            print("\n🔍 Searching for available rooms...")
            search_success = submit_and_search_rooms(automation.driver)
            
            if search_success:
                # Step 6: Analyze and select rooms
                print("\n📊 Analyzing search results...")
                rooms = analyze_room_results_complete(automation.driver)
                
                if rooms:
                    print(f"\n✅ Found {len(rooms)} available rooms!")
                    display_available_rooms(rooms)
                    
                    # Auto-select best room or let user choose
                    selected_room = select_best_room(rooms, booking_criteria)
                    if selected_room:
                        print(f"\n🎯 Selecting room: {selected_room['name']}")
                        book_room(automation.driver, selected_room)
                else:
                    print("⚠️  No rooms found. Try different criteria.")
        
        # Keep browser open
        print("\n" + "=" * 60)
        print("AUTOMATION COMPLETE - BROWSER OPEN")
        print("=" * 60)
        print("🖥️  Review and complete booking manually if needed")
        print()
        input("✅ Press Enter when done (closes browser)...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
    finally:
        automation.close()

def get_natural_language_request():
    """Get booking request in natural language"""
    
    print("💬 Describe your room booking needs:")
    print("Examples:")
    print("• 'Conference room for 10 people tomorrow 2-4 PM'")
    print("• 'Small study room today 3:30-5:00 PM'")
    print("• 'Large room Monday morning with projector'")
    print()
    
    request = input("🗣️  Your request: ").strip()
    
    if not request:
        print("Please tell me what you need...")
        return get_natural_language_request()
    
    return request

def extract_criteria_from_ai_response(ai_response, original_request):
    """Extract booking criteria from OpenAI response"""
    
    try:
        extracted = ai_response.get('extracted_details', {})
        
        criteria = {
            'date': None,
            'start_time': None, 
            'end_time': None,
            'capacity': None,
            'location': None,
            'equipment': []
        }
        
        # Parse date
        ai_date = extracted.get('date')
        if ai_date:
            criteria['date'] = normalize_date(ai_date)
        else:
            criteria['date'] = datetime.now().strftime("%Y-%m-%d")
        
        # Parse time
        ai_start_time = extracted.get('start_time')
        ai_duration = extracted.get('duration')
        
        if ai_start_time:
            criteria['start_time'] = normalize_time(ai_start_time)
            
            if ai_duration:
                end_time = calculate_end_time(criteria['start_time'], ai_duration)
                criteria['end_time'] = end_time
            else:
                end_time = calculate_end_time(criteria['start_time'], "1 hour")
                criteria['end_time'] = end_time
        else:
            # Default times
            criteria['start_time'] = "10:00"
            criteria['end_time'] = "11:00"
        
        # Parse capacity
        ai_capacity = extracted.get('capacity')
        if ai_capacity:
            try:
                if isinstance(ai_capacity, str):
                    import re
                    numbers = re.findall(r'\d+', ai_capacity)
                    if numbers:
                        criteria['capacity'] = int(numbers[0])
                else:
                    criteria['capacity'] = int(ai_capacity)
            except:
                criteria['capacity'] = 8
        else:
            criteria['capacity'] = 8
        
        criteria['location'] = extracted.get('location')
        
        ai_equipment = extracted.get('equipment', [])
        if isinstance(ai_equipment, list):
            criteria['equipment'] = ai_equipment
        
        return criteria
        
    except Exception as e:
        print(f"❌ Error extracting criteria: {e}")
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
        if not date_string or date_string.lower() in ['null', 'none']:
            return datetime.now().strftime("%Y-%m-%d")
        
        # If already in correct format
        if len(date_string) == 10 and date_string.count('-') == 2:
            try:
                datetime.strptime(date_string, "%Y-%m-%d")
                return date_string
            except ValueError:
                pass
        
        # Try various formats
        date_formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
            "%B %d, %Y", "%B %d", "%b %d, %Y", "%b %d"
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                
                if parsed_date < datetime.now():
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                    if parsed_date < datetime.now():
                        parsed_date = parsed_date.replace(year=datetime.now().year + 1)
                
                return parsed_date.strftime("%Y-%m-%d")
                
            except ValueError:
                continue
        
        print(f"⚠️  Could not parse date '{date_string}', using today")
        return datetime.now().strftime("%Y-%m-%d")
        
    except Exception as e:
        print(f"❌ Date error: {e}")
        return datetime.now().strftime("%Y-%m-%d")

def normalize_time(time_string):
    """Normalize time string to HH:MM format"""
    
    try:
        if not time_string:
            return "10:00"
        
        time_formats = [
            "%H:%M", "%I:%M %p", "%I %p", "%H"
        ]
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(time_string, fmt)
                return parsed_time.strftime("%H:%M")
            except ValueError:
                continue
        
        # Regex fallback
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
        
        return "10:00"
        
    except Exception as e:
        print(f"❌ Time error: {e}")
        return "10:00"

def calculate_end_time(start_time, duration_string):
    """Calculate end time from start time and duration"""
    
    try:
        start_hour, start_min = map(int, start_time.split(':'))
        
        duration_minutes = 60  # Default
        
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
        
        total_minutes = start_hour * 60 + start_min + duration_minutes
        end_hour = (total_minutes // 60) % 24
        end_min = total_minutes % 60
        
        return f"{end_hour:02d}:{end_min:02d}"
        
    except:
        try:
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour = (start_hour + 1) % 24
            return f"{end_hour:02d}:{start_min:02d}"
        except:
            return "11:00"

def setup_automation_session():
    """Set up automation session"""
    
    try:
        automation = MomentusAutomation(
            headless=False,
            use_existing_session=False
        )
        automation.setup_driver()
        automation.driver.execute_script("document.charset = 'UTF-8';")
        return automation
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None

def navigate_to_momentus_complete(automation, sharepoint_url):
    """Complete navigation to Momentus"""
    
    try:
        print(f"🌐 Navigating to SharePoint...")
        automation.driver.get(sharepoint_url)
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("SHAREPOINT AUTHENTICATION")
        print("=" * 60)
        print("👤 Complete authentication in Chrome")
        print("🖥️  Switch to Chrome window")
        print()
        input("✅ Press Enter when on SharePoint dashboard...")
        
        print("🔍 Looking for Room Reservations link...")
        
        # Find the link with multiple strategies
        room_link = find_room_link_complete(automation.driver)
        
        if room_link:
            print(f"✅ Found: {room_link['text']}")
            click_element_safe(automation.driver, room_link['element'])
            time.sleep(5)
            
            # Handle new window/tab
            handle_new_window(automation.driver)
            
            # Check if Momentus auth needed
            current_url = automation.driver.current_url.lower()
            if 'momentus' not in current_url:
                print("\n🔐 Momentus authentication required")
                input("✅ Press Enter when Momentus is loaded...")
            
            print("✅ Momentus ready!")
            return True
        else:
            print("❌ Room Reservations link not found")
            return False
            
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return False

def find_room_link_complete(driver):
    """Find room reservations link with multiple strategies"""
    
    selectors = [
        "//a[contains(text(), 'Room Reservations')]",
        "//a[contains(text(), 'ROOM RESERVATIONS')]",
        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]",
        "//a[contains(@href, 'momentus')]",
        "//a[contains(@href, 'room')]",
        "//*[contains(text(), 'Room')]//ancestor::a",
        "//span[contains(text(), 'Room')]//ancestor::a"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    text = element.text.strip() or element.get_attribute('aria-label') or 'Room Link'
                    return {
                        'element': element,
                        'text': text,
                        'href': element.get_attribute('href') or ''
                    }
        except:
            continue
    
    return None

def click_element_safe(driver, element):
    """Safely click element"""
    
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        
        try:
            element.click()
        except:
            driver.execute_script("arguments[0].click();", element)
        
        time.sleep(2)
    except Exception as e:
        print(f"⚠️  Click warning: {e}")

def handle_new_window(driver):
    """Handle new window/tab"""
    
    windows = driver.window_handles
    if len(windows) > 1:
        driver.switch_to.window(windows[-1])
        print(f"📑 Switched to new tab/window")

def fill_momentus_form_complete(driver, criteria):
    """Complete Momentus form filling"""
    
    try:
        time.sleep(2)
        
        success_count = 0
        
        # 1. Fill Date
        print("📅 Filling date field...")
        if fill_date_field_complete(driver, criteria['date']):
            success_count += 1
            print(f"   ✅ Date: {criteria['date']}")
        
        # 2. Fill Time
        print("⏰ Filling time fields...")
        if fill_time_fields_complete(driver, criteria['start_time'], criteria['end_time']):
            success_count += 1
            print(f"   ✅ Time: {criteria['start_time']} - {criteria['end_time']}")
        
        # 3. Fill Capacity
        print("👥 Filling capacity field...")
        if fill_capacity_field_complete(driver, criteria['capacity']):
            success_count += 1
            print(f"   ✅ Capacity: {criteria['capacity']} people")
        
        # 4. Fill Location if specified
        if criteria.get('location'):
            print("📍 Filling location field...")
            if fill_location_field_complete(driver, criteria['location']):
                success_count += 1
                print(f"   ✅ Location: {criteria['location']}")
        
        print(f"\n✅ Form filling complete: {success_count} fields filled")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Form filling error: {e}")
        return False

def fill_date_field_complete(driver, date_value):
    """Fill date field with multiple strategies"""
    
    # Format date for different input types
    date_formats = {
        'yyyy-mm-dd': date_value,
        'mm/dd/yyyy': datetime.strptime(date_value, "%Y-%m-%d").strftime("%m/%d/%Y"),
        'mm-dd-yyyy': datetime.strptime(date_value, "%Y-%m-%d").strftime("%m-%d-%Y")
    }
    
    date_selectors = [
        "//input[@type='date']",
        "//input[contains(@name, 'date') or contains(@id, 'date')]",
        "//input[contains(@placeholder, 'date')]",
        "//input[contains(@class, 'date')]",
        "//*[@data-date-format]//input"
    ]
    
    for selector in date_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    elem.clear()
                    
                    # Try different date formats
                    for format_name, formatted_date in date_formats.items():
                        elem.clear()
                        elem.send_keys(formatted_date)
                        elem.send_keys(Keys.TAB)  # Trigger change event
                        
                        # Check if value was accepted
                        if elem.get_attribute('value'):
                            return True
        except:
            continue
    
    # JavaScript fallback
    try:
        driver.execute_script(f"""
            var dateInputs = document.querySelectorAll('input[type="date"], input[name*="date"], input[id*="date"]');
            if (dateInputs.length > 0) {{
                dateInputs[0].value = '{date_value}';
                dateInputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        """)
        return True
    except:
        pass
    
    return False

def fill_time_fields_complete(driver, start_time, end_time):
    """Fill time fields completely"""
    
    success = False
    
    # Convert times to different formats
    start_formats = {
        '24h': start_time,
        '12h': convert_to_12h(start_time)
    }
    end_formats = {
        '24h': end_time,
        '12h': convert_to_12h(end_time)
    }
    
    # Start time
    start_selectors = [
        "//input[@name='start_time' or @id='start_time']",
        "//input[contains(@name, 'start') and (contains(@name, 'time') or @type='time')]",
        "//select[contains(@name, 'start')]",
        "//input[@type='time'][1]"
    ]
    
    for selector in start_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    if elem.tag_name == 'select':
                        success = fill_time_select(elem, start_time)
                    else:
                        for format_name, formatted_time in start_formats.items():
                            elem.clear()
                            elem.send_keys(formatted_time)
                            if elem.get_attribute('value'):
                                success = True
                                break
                    if success:
                        break
        except:
            continue
    
    # End time
    end_selectors = [
        "//input[@name='end_time' or @id='end_time']",
        "//input[contains(@name, 'end') and (contains(@name, 'time') or @type='time')]",
        "//select[contains(@name, 'end')]",
        "//input[@type='time'][2]"
    ]
    
    for selector in end_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    if elem.tag_name == 'select':
                        success = fill_time_select(elem, end_time) or success
                    else:
                        for format_name, formatted_time in end_formats.items():
                            elem.clear()
                            elem.send_keys(formatted_time)
                            if elem.get_attribute('value'):
                                success = True
                                break
                    if success:
                        break
        except:
            continue
    
    return success

def convert_to_12h(time_24h):
    """Convert 24-hour time to 12-hour format"""
    try:
        hour, minute = map(int, time_24h.split(':'))
        period = 'AM' if hour < 12 else 'PM'
        hour_12 = hour % 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"
    except:
        return time_24h

def fill_time_select(select_elem, time_value):
    """Fill time select dropdown"""
    try:
        select = Select(select_elem)
        
        # Try exact match
        for option in select.options:
            if time_value in option.text or time_value == option.get_attribute('value'):
                select.select_by_visible_text(option.text)
                return True
        
        # Try partial match
        time_hour = time_value.split(':')[0]
        for option in select.options:
            if time_hour in option.text:
                select.select_by_visible_text(option.text)
                return True
    except:
        pass
    return False

def fill_capacity_field_complete(driver, capacity):
    """Fill capacity field completely"""
    
    capacity_str = str(capacity)
    
    # Try selects
    select_selectors = [
        "//select[contains(@name, 'capacity') or contains(@id, 'capacity')]",
        "//select[contains(@name, 'people') or contains(@id, 'people')]",
        "//select[contains(@name, 'size') or contains(@id, 'size')]"
    ]
    
    for selector in select_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    if fill_capacity_select(elem, capacity):
                        return True
        except:
            continue
    
    # Try inputs
    input_selectors = [
        "//input[contains(@name, 'capacity') or contains(@id, 'capacity')]",
        "//input[contains(@name, 'people') or contains(@id, 'people')]",
        "//input[@type='number']"
    ]
    
    for selector in input_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    elem.clear()
                    elem.send_keys(capacity_str)
                    if elem.get_attribute('value'):
                        return True
        except:
            continue
    
    return False

def fill_capacity_select(select_elem, capacity):
    """Fill capacity select dropdown"""
    try:
        select = Select(select_elem)
        capacity_str = str(capacity)
        
        # Exact match
        for option in select.options:
            if capacity_str in option.text or capacity_str == option.get_attribute('value'):
                select.select_by_visible_text(option.text)
                return True
        
        # Range match
        import re
        for option in select.options:
            range_match = re.search(r'(\d+)\s*-\s*(\d+)', option.text)
            if range_match:
                min_cap = int(range_match.group(1))
                max_cap = int(range_match.group(2))
                if min_cap <= capacity <= max_cap:
                    select.select_by_visible_text(option.text)
                    return True
        
        # Select closest higher option
        best_option = None
        best_diff = float('inf')
        for option in select.options:
            try:
                option_cap = int(re.search(r'\d+', option.text).group())
                if option_cap >= capacity and option_cap - capacity < best_diff:
                    best_option = option
                    best_diff = option_cap - capacity
            except:
                continue
        
        if best_option:
            select.select_by_visible_text(best_option.text)
            return True
    except:
        pass
    return False

def fill_location_field_complete(driver, location):
    """Fill location field"""
    
    location_selectors = [
        "//input[contains(@name, 'location') or contains(@id, 'location')]",
        "//select[contains(@name, 'building') or contains(@id, 'building')]",
        "//select[contains(@name, 'location')]"
    ]
    
    for selector in location_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    if elem.tag_name == 'select':
                        select = Select(elem)
                        for option in select.options:
                            if location.lower() in option.text.lower():
                                select.select_by_visible_text(option.text)
                                return True
                    else:
                        elem.clear()
                        elem.send_keys(location)
                        if elem.get_attribute('value'):
                            return True
        except:
            continue
    
    return False

def submit_and_search_rooms(driver):
    """Submit form and search"""
    
    try:
        submit_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(text(), 'Search')]",
            "//button[contains(text(), 'Find')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]"
        ]
        
        submit_button = None
        for selector in submit_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        submit_button = elem
                        break
                if submit_button:
                    break
            except:
                continue
        
        if submit_button:
            print(f"🔘 Found submit button")
            click_element_safe(driver, submit_button)
            time.sleep(5)
            return True
        else:
            print("⌨️  Trying Enter key...")
            active = driver.switch_to.active_element
            active.send_keys(Keys.RETURN)
            time.sleep(5)
            return True
        
    except Exception as e:
        print(f"❌ Submit error: {e}")
    
    return False

def analyze_room_results_complete(driver):
    """Analyze room results"""
    
    rooms = []
    
    try:
        time.sleep(2)
        
        room_selectors = [
            "//div[contains(@class, 'room')]",
            "//tr[contains(@class, 'room')]",
            "//div[contains(@class, 'result')]",
            "//table[@class='results']//tr[position()>1]"
        ]
        
        for selector in room_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    for elem in elements[:10]:
                        room_info = extract_room_info(elem)
                        if room_info:
                            rooms.append(room_info)
                    if rooms:
                        break
            except:
                continue
        
        # Find book buttons if no structured results
        if not rooms:
            book_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Book')] | //a[contains(text(), 'Book')]")
            for idx, button in enumerate(book_buttons[:5]):
                rooms.append({
                    'name': f"Room Option {idx + 1}",
                    'capacity': 'Unknown',
                    'book_button': button
                })
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
    
    return rooms

def extract_room_info(element):
    """Extract room info"""
    
    try:
        text = element.text
        
        room_info = {
            'name': text.split('\n')[0] if text else 'Unknown Room',
            'capacity': None,
            'book_button': None,
            'element': element
        }
        
        # Find capacity
        import re
        cap_match = re.search(r'(\d+)\s*(?:people|persons|capacity)', text, re.I)
        if cap_match:
            room_info['capacity'] = cap_match.group(1)
        
        # Find book button
        try:
            book_btn = element.find_element(By.XPATH, ".//button[contains(text(), 'Book')] | .//a[contains(text(), 'Book')]")
            room_info['book_button'] = book_btn
        except:
            pass
        
        return room_info if room_info['name'] else None
        
    except:
        return None

def display_available_rooms(rooms):
    """Display rooms"""
    
    print("\n📋 Available Rooms:")
    print("-" * 50)
    
    for idx, room in enumerate(rooms, 1):
        print(f"{idx}. {room['name']}")
        if room['capacity']:
            print(f"   Capacity: {room['capacity']}")

def select_best_room(rooms, criteria):
    """Select best room"""
    
    for room in rooms:
        if room.get('book_button'):
            return room
    
    return rooms[0] if rooms else None

def book_room(driver, room):
    """Book room"""
    
    try:
        if room.get('book_button'):
            print("📝 Booking room...")
            click_element_safe(driver, room['book_button'])
            time.sleep(3)
            print("✅ Room booking initiated!")
            return True
        else:
            print("⚠️  No book button found")
            return False
            
    except Exception as e:
        print(f"❌ Booking error: {e}")
        return False

if __name__ == "__main__":
    try:
        complete_room_booking_workflow()
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")