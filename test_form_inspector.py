#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intelligent Form Inspector for Momentus
Analyzes the actual form structure and maps fields intelligently
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

# Fix encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class FormInspector:
    """Intelligent form field inspector and mapper"""
    
    def __init__(self, driver):
        self.driver = driver
        self.form_fields = []
        self.field_mappings = {}
        
    def inspect_form(self):
        """Comprehensively inspect all form elements on the page"""
        
        print("\n" + "=" * 80)
        print("🔍 FORM INSPECTION STARTING")
        print("=" * 80)
        
        # Find all forms on the page
        forms = self.driver.find_elements(By.TAG_NAME, "form")
        print(f"\n📋 Found {len(forms)} form(s) on the page")
        
        # Inspect all input elements
        self._inspect_inputs()
        
        # Inspect all select dropdowns
        self._inspect_selects()
        
        # Inspect all textareas
        self._inspect_textareas()
        
        # Inspect all buttons
        self._inspect_buttons()
        
        # Find labels and associate with fields
        self._associate_labels()
        
        return self.form_fields
    
    def _inspect_inputs(self):
        """Inspect all input fields"""
        
        print("\n📝 Inspecting INPUT fields...")
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        
        for idx, input_elem in enumerate(inputs):
            try:
                if not input_elem.is_displayed():
                    continue
                    
                field_info = {
                    'element': input_elem,
                    'tag': 'input',
                    'type': input_elem.get_attribute('type') or 'text',
                    'name': input_elem.get_attribute('name'),
                    'id': input_elem.get_attribute('id'),
                    'placeholder': input_elem.get_attribute('placeholder'),
                    'value': input_elem.get_attribute('value'),
                    'class': input_elem.get_attribute('class'),
                    'required': input_elem.get_attribute('required') is not None,
                    'label': None,
                    'nearby_text': self._get_nearby_text(input_elem)
                }
                
                # Skip hidden and submit/button types
                if field_info['type'] in ['hidden', 'submit', 'button']:
                    continue
                
                self.form_fields.append(field_info)
                
                # Print field details
                self._print_field_info(field_info, idx + 1)
                
            except Exception as e:
                continue
    
    def _inspect_selects(self):
        """Inspect all select dropdowns"""
        
        print("\n📋 Inspecting SELECT dropdowns...")
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        
        for idx, select_elem in enumerate(selects):
            try:
                if not select_elem.is_displayed():
                    continue
                
                select_obj = Select(select_elem)
                options = [opt.text for opt in select_obj.options[:10]]  # First 10 options
                
                field_info = {
                    'element': select_elem,
                    'tag': 'select',
                    'type': 'select',
                    'name': select_elem.get_attribute('name'),
                    'id': select_elem.get_attribute('id'),
                    'class': select_elem.get_attribute('class'),
                    'required': select_elem.get_attribute('required') is not None,
                    'options': options,
                    'option_count': len(select_obj.options),
                    'label': None,
                    'nearby_text': self._get_nearby_text(select_elem)
                }
                
                self.form_fields.append(field_info)
                
                # Print field details
                self._print_select_info(field_info, idx + 1)
                
            except Exception as e:
                continue
    
    def _inspect_textareas(self):
        """Inspect all textarea fields"""
        
        print("\n📄 Inspecting TEXTAREA fields...")
        textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
        
        for idx, textarea_elem in enumerate(textareas):
            try:
                if not textarea_elem.is_displayed():
                    continue
                
                field_info = {
                    'element': textarea_elem,
                    'tag': 'textarea',
                    'type': 'textarea',
                    'name': textarea_elem.get_attribute('name'),
                    'id': textarea_elem.get_attribute('id'),
                    'placeholder': textarea_elem.get_attribute('placeholder'),
                    'class': textarea_elem.get_attribute('class'),
                    'required': textarea_elem.get_attribute('required') is not None,
                    'label': None,
                    'nearby_text': self._get_nearby_text(textarea_elem)
                }
                
                self.form_fields.append(field_info)
                
                # Print field details
                self._print_field_info(field_info, idx + 1)
                
            except Exception as e:
                continue
    
    def _inspect_buttons(self):
        """Inspect all buttons"""
        
        print("\n🔘 Inspecting BUTTONS...")
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        submit_inputs = self.driver.find_elements(By.XPATH, "//input[@type='submit']")
        
        all_buttons = buttons + submit_inputs
        
        for idx, button_elem in enumerate(all_buttons):
            try:
                if not button_elem.is_displayed():
                    continue
                
                button_text = button_elem.text or button_elem.get_attribute('value') or ''
                
                button_info = {
                    'element': button_elem,
                    'tag': button_elem.tag_name,
                    'type': 'button',
                    'text': button_text,
                    'name': button_elem.get_attribute('name'),
                    'id': button_elem.get_attribute('id'),
                    'class': button_elem.get_attribute('class'),
                    'onclick': button_elem.get_attribute('onclick')
                }
                
                print(f"   Button {idx + 1}: '{button_text}' "
                      f"(id: {button_info['id'] or 'none'}, "
                      f"name: {button_info['name'] or 'none'})")
                
            except Exception as e:
                continue
    
    def _get_nearby_text(self, element):
        """Get text near the element for context"""
        
        try:
            # Try to get parent element's text
            parent = element.find_element(By.XPATH, "..")
            parent_text = parent.text[:100] if parent.text else ""
            
            # Try to get preceding sibling text
            try:
                preceding = element.find_element(By.XPATH, "preceding-sibling::*[1]")
                preceding_text = preceding.text[:50] if preceding.text else ""
            except:
                preceding_text = ""
            
            return {
                'parent': parent_text,
                'preceding': preceding_text
            }
        except:
            return {'parent': '', 'preceding': ''}
    
    def _associate_labels(self):
        """Associate labels with form fields"""
        
        labels = self.driver.find_elements(By.TAG_NAME, "label")
        
        for label in labels:
            try:
                label_for = label.get_attribute('for')
                label_text = label.text
                
                if label_for:
                    # Find field with matching id
                    for field in self.form_fields:
                        if field.get('id') == label_for:
                            field['label'] = label_text
                            break
                else:
                    # Try to find field within label
                    try:
                        input_in_label = label.find_element(By.TAG_NAME, "input")
                        for field in self.form_fields:
                            if field.get('element') == input_in_label:
                                field['label'] = label_text
                                break
                    except:
                        pass
            except:
                continue
    
    def _print_field_info(self, field_info, num):
        """Print detailed field information"""
        
        print(f"\n   Field {num}: {field_info['type'].upper()}")
        print(f"      Name: {field_info.get('name') or 'none'}")
        print(f"      ID: {field_info.get('id') or 'none'}")
        
        if field_info.get('placeholder'):
            print(f"      Placeholder: {field_info['placeholder']}")
        
        if field_info.get('label'):
            print(f"      Label: {field_info['label']}")
        
        if field_info.get('value'):
            print(f"      Current value: {field_info['value']}")
        
        if field_info.get('required'):
            print(f"      Required: Yes")
        
        if field_info.get('nearby_text', {}).get('parent'):
            print(f"      Context: {field_info['nearby_text']['parent'][:50]}...")
    
    def _print_select_info(self, field_info, num):
        """Print detailed select field information"""
        
        print(f"\n   Select {num}: DROPDOWN")
        print(f"      Name: {field_info.get('name') or 'none'}")
        print(f"      ID: {field_info.get('id') or 'none'}")
        print(f"      Options ({field_info['option_count']} total):")
        
        for i, option in enumerate(field_info['options'][:5]):
            print(f"         - {option}")
        
        if field_info['option_count'] > 5:
            print(f"         ... and {field_info['option_count'] - 5} more")
        
        if field_info.get('label'):
            print(f"      Label: {field_info['label']}")
        
        if field_info.get('required'):
            print(f"      Required: Yes")
    
    def analyze_and_map_fields(self):
        """Intelligently map form fields to booking requirements"""
        
        print("\n" + "=" * 80)
        print("🧠 INTELLIGENT FIELD MAPPING")
        print("=" * 80)
        
        # Keywords for each field type
        field_patterns = {
            'date': {
                'keywords': ['date', 'day', 'when', 'calendar'],
                'types': ['date', 'text'],
                'found': None
            },
            'start_time': {
                'keywords': ['start', 'from', 'begin', 'starting'],
                'types': ['time', 'select', 'text'],
                'found': None
            },
            'end_time': {
                'keywords': ['end', 'to', 'until', 'ending', 'finish'],
                'types': ['time', 'select', 'text'],
                'found': None
            },
            'duration': {
                'keywords': ['duration', 'length', 'hours', 'minutes'],
                'types': ['select', 'text', 'number'],
                'found': None
            },
            'capacity': {
                'keywords': ['capacity', 'people', 'attendees', 'size', 'occupancy', 'seats'],
                'types': ['number', 'select', 'text'],
                'found': None
            },
            'location': {
                'keywords': ['location', 'building', 'where', 'place', 'room'],
                'types': ['select', 'text'],
                'found': None
            },
            'purpose': {
                'keywords': ['purpose', 'reason', 'description', 'title', 'event', 'meeting'],
                'types': ['text', 'textarea'],
                'found': None
            }
        }
        
        # Analyze each field
        for field in self.form_fields:
            field_text = self._get_field_text(field).lower()
            
            # Check each pattern
            for req_type, pattern in field_patterns.items():
                if pattern['found']:
                    continue  # Already found this field
                
                # Check if field matches this requirement
                score = self._calculate_match_score(field, field_text, pattern)
                
                if score > 0.5:  # Threshold for match
                    pattern['found'] = field
                    self.field_mappings[req_type] = field
                    print(f"\n✅ Mapped '{req_type}' to field:")
                    print(f"   Name: {field.get('name')}")
                    print(f"   ID: {field.get('id')}")
                    print(f"   Type: {field.get('type')}")
                    if field.get('label'):
                        print(f"   Label: {field.get('label')}")
        
        # Report unmapped requirements
        print("\n" + "-" * 40)
        unmapped = []
        for req_type, pattern in field_patterns.items():
            if not pattern['found']:
                unmapped.append(req_type)
                print(f"❓ Could not auto-map: {req_type}")
        
        # Report unidentified fields
        mapped_fields = set(id(f['element']) for f in self.field_mappings.values())
        unidentified = []
        
        print("\n" + "-" * 40)
        print("📋 Unidentified fields:")
        for field in self.form_fields:
            if id(field['element']) not in mapped_fields:
                unidentified.append(field)
                print(f"   - {field.get('type')} field: "
                      f"name='{field.get('name')}', "
                      f"id='{field.get('id')}'")
                if field.get('label'):
                    print(f"     Label: {field.get('label')}")
        
        return self.field_mappings, unmapped, unidentified
    
    def _get_field_text(self, field):
        """Get all text associated with a field for matching"""
        
        texts = []
        
        if field.get('name'):
            texts.append(field['name'])
        if field.get('id'):
            texts.append(field['id'])
        if field.get('placeholder'):
            texts.append(field['placeholder'])
        if field.get('label'):
            texts.append(field['label'])
        if field.get('class'):
            texts.append(field['class'])
        if field.get('nearby_text', {}).get('parent'):
            texts.append(field['nearby_text']['parent'])
        
        return ' '.join(texts)
    
    def _calculate_match_score(self, field, field_text, pattern):
        """Calculate how well a field matches a pattern"""
        
        score = 0.0
        
        # Check keywords
        for keyword in pattern['keywords']:
            if keyword in field_text:
                score += 0.3
        
        # Check field type
        if field.get('type') in pattern['types']:
            score += 0.3
        
        # Special checks for specific fields
        if field.get('type') == 'date':
            score += 0.4
        elif field.get('type') == 'time':
            score += 0.3
        elif field.get('type') == 'number' and 'capacity' in pattern['keywords']:
            score += 0.2
        
        # Check for select options that match
        if field.get('options'):
            option_text = ' '.join(field['options']).lower()
            for keyword in pattern['keywords']:
                if keyword in option_text:
                    score += 0.2
                    break
        
        return min(score, 1.0)  # Cap at 1.0
    
    def interactive_mapping(self, unmapped, unidentified):
        """Interactively map remaining fields"""
        
        if not unmapped:
            return
        
        print("\n" + "=" * 80)
        print("🤝 INTERACTIVE FIELD MAPPING")
        print("=" * 80)
        print("Help me map the remaining fields...")
        
        for req_type in unmapped:
            print(f"\n❓ Looking for field: {req_type.upper()}")
            print("Available unidentified fields:")
            
            for idx, field in enumerate(unidentified, 1):
                print(f"{idx}. {field.get('type')} - "
                      f"name: {field.get('name')}, "
                      f"id: {field.get('id')}")
                if field.get('label'):
                    print(f"   Label: {field.get('label')}")
            
            print("0. Skip this field")
            
            choice = input(f"\nWhich field is for {req_type}? (0-{len(unidentified)}): ")
            
            try:
                choice_idx = int(choice)
                if 0 < choice_idx <= len(unidentified):
                    selected_field = unidentified[choice_idx - 1]
                    self.field_mappings[req_type] = selected_field
                    print(f"✅ Mapped {req_type} to field {selected_field.get('name')}")
                elif choice_idx == 0:
                    print(f"⏭️  Skipping {req_type}")
            except:
                print(f"⏭️  Skipping {req_type}")


def intelligent_form_booking_workflow():
    """Complete booking workflow with intelligent form inspection"""
    
    print("=" * 80)
    print("🔍 INTELLIGENT FORM BOOKING ASSISTANT")
    print("=" * 80)
    print("This version inspects and understands the actual Momentus form")
    print()
    
    # Initialize OpenAI agent
    print("🤖 Initializing OpenAI agent...")
    agent = RoomBookingAgent()
    
    if not agent.openai_client:
        print("❌ OpenAI API key not configured!")
        return
    
    print("✅ OpenAI agent ready!")
    
    # Get booking request
    booking_request = get_natural_language_request()
    
    # Parse with OpenAI
    print(f"\n🔍 Processing: '{booking_request}'")
    ai_response = agent.process_request(booking_request)
    booking_criteria = extract_criteria_from_ai_response(ai_response)
    
    # Display parsed request
    print("\n📋 Parsed booking request:")
    print(f"   📅 Date: {booking_criteria['date']}")
    print(f"   ⏰ Time: {booking_criteria['start_time']} - {booking_criteria['end_time']}")
    print(f"   👥 Capacity: {booking_criteria['capacity']} people")
    
    confirm = input("\n✅ Proceed? (y/n): ").lower().startswith('y')
    if not confirm:
        return
    
    # Setup browser
    print("\n🚀 Launching Chrome...")
    automation = setup_automation_session()
    if not automation:
        print("❌ Failed to setup browser")
        return
    
    try:
        # Navigate to Momentus
        load_dotenv()
        sharepoint_url = os.getenv('SHAREPOINT_URL', 'https://utexas.sharepoint.com/sites/McCombs-DepartmentofFinance/SitePages/CollabHome.aspx')
        
        print(f"🌐 Navigating to SharePoint...")
        automation.driver.get(sharepoint_url)
        time.sleep(3)
        
        print("\n👤 Complete SharePoint authentication in Chrome")
        input("✅ Press Enter when on SharePoint dashboard...")
        
        # Find and click Room Reservations
        print("🔍 Looking for Room Reservations link...")
        room_link = find_room_reservations_link(automation.driver)
        
        if room_link:
            print(f"✅ Found: {room_link['text']}")
            room_link['element'].click()
            time.sleep(5)
            
            # Handle new window
            windows = automation.driver.window_handles
            if len(windows) > 1:
                automation.driver.switch_to.window(windows[-1])
            
            # Wait for Momentus
            print("\n🔐 Complete Momentus authentication if needed")
            input("✅ Press Enter when Momentus form is visible...")
        else:
            print("❌ Room link not found")
            input("Navigate manually and press Enter when ready...")
        
        # INSPECT THE FORM
        print("\n" + "=" * 80)
        print("🔬 ANALYZING MOMENTUS FORM STRUCTURE")
        print("=" * 80)
        
        inspector = FormInspector(automation.driver)
        
        # Inspect all form elements
        form_fields = inspector.inspect_form()
        
        print(f"\n📊 Found {len(form_fields)} form fields total")
        
        # Analyze and map fields
        field_mappings, unmapped, unidentified = inspector.analyze_and_map_fields()
        
        # Interactive mapping for unmapped fields
        if unmapped:
            inspector.interactive_mapping(unmapped, unidentified)
        
        # Now fill the form with mapped fields
        print("\n" + "=" * 80)
        print("📝 FILLING FORM WITH MAPPED FIELDS")
        print("=" * 80)
        
        success = fill_form_with_mappings(
            automation.driver,
            inspector.field_mappings,
            booking_criteria
        )
        
        if success:
            print("\n✅ Form filled successfully!")
            
            # Find and click submit
            print("\n🔍 Looking for submit button...")
            submit_button = find_submit_button(automation.driver)
            
            if submit_button:
                print(f"🔘 Found submit button: '{submit_button.text or submit_button.get_attribute('value')}'")
                confirm_submit = input("Submit the form? (y/n): ").lower().startswith('y')
                
                if confirm_submit:
                    submit_button.click()
                    print("✅ Form submitted!")
                    time.sleep(5)
                    
                    # Check for results
                    print("\n📊 Checking for room results...")
                    analyze_results_page(automation.driver)
        
        print("\n🖥️  Browser staying open for manual completion")
        input("Press Enter when done...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
    finally:
        automation.close()


def get_natural_language_request():
    """Get booking request"""
    
    print("💬 Describe your room booking needs:")
    print("Examples:")
    print("• 'Conference room for 10 people tomorrow 2-4 PM'")
    print("• 'Small room today 3:30 PM for 1 hour'")
    print()
    
    request = input("🗣️  Your request: ").strip()
    return request if request else get_natural_language_request()


def extract_criteria_from_ai_response(ai_response):
    """Extract criteria from AI response"""
    
    try:
        extracted = ai_response.get('extracted_details', {})
        
        criteria = {
            'date': normalize_date(extracted.get('date')) if extracted.get('date') else datetime.now().strftime("%Y-%m-%d"),
            'start_time': normalize_time(extracted.get('start_time')) if extracted.get('start_time') else "10:00",
            'end_time': None,
            'capacity': 8,
            'location': extracted.get('location'),
            'purpose': extracted.get('purpose', 'Meeting')
        }
        
        # Calculate end time
        if extracted.get('duration'):
            criteria['end_time'] = calculate_end_time(criteria['start_time'], extracted.get('duration'))
        else:
            criteria['end_time'] = calculate_end_time(criteria['start_time'], "1 hour")
        
        # Parse capacity
        if extracted.get('capacity'):
            try:
                if isinstance(extracted['capacity'], str):
                    numbers = re.findall(r'\d+', extracted['capacity'])
                    if numbers:
                        criteria['capacity'] = int(numbers[0])
                else:
                    criteria['capacity'] = int(extracted['capacity'])
            except:
                pass
        
        return criteria
        
    except Exception as e:
        print(f"Error parsing: {e}")
        return {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'start_time': "10:00",
            'end_time': "11:00",
            'capacity': 8,
            'location': None,
            'purpose': 'Meeting'
        }


def normalize_date(date_string):
    """Normalize date to YYYY-MM-DD"""
    
    if not date_string:
        return datetime.now().strftime("%Y-%m-%d")
    
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
        "%B %d, %Y", "%B %d", "%b %d, %Y", "%b %d"
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_string, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.strftime("%Y-%m-%d")
        except:
            continue
    
    return datetime.now().strftime("%Y-%m-%d")


def normalize_time(time_string):
    """Normalize time to HH:MM"""
    
    if not time_string:
        return "10:00"
    
    formats = ["%H:%M", "%I:%M %p", "%I %p"]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(time_string, fmt)
            return parsed.strftime("%H:%M")
        except:
            continue
    
    return "10:00"


def calculate_end_time(start_time, duration):
    """Calculate end time"""
    
    try:
        start_hour, start_min = map(int, start_time.split(':'))
        
        duration_min = 60
        if 'hour' in duration:
            match = re.search(r'(\d+)', duration)
            if match:
                duration_min = int(match.group(1)) * 60
        elif 'minute' in duration:
            match = re.search(r'(\d+)', duration)
            if match:
                duration_min = int(match.group(1))
        
        total_min = start_hour * 60 + start_min + duration_min
        return f"{(total_min // 60) % 24:02d}:{total_min % 60:02d}"
    except:
        return "11:00"


def setup_automation_session():
    """Setup browser"""
    
    try:
        automation = MomentusAutomation(headless=False, use_existing_session=False)
        automation.setup_driver()
        return automation
    except Exception as e:
        print(f"Setup error: {e}")
        return None


def find_room_reservations_link(driver):
    """Find room reservations link"""
    
    selectors = [
        "//a[contains(text(), 'Room Reservations')]",
        "//a[contains(text(), 'ROOM RESERVATIONS')]",
        "//a[contains(@href, 'momentus')]",
        "//a[contains(@href, 'room')]"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    return {
                        'element': elem,
                        'text': elem.text or 'Room Link'
                    }
        except:
            continue
    
    return None


def fill_form_with_mappings(driver, mappings, criteria):
    """Fill form using discovered mappings"""
    
    success_count = 0
    
    # Fill date
    if 'date' in mappings and criteria.get('date'):
        field = mappings['date']
        try:
            elem = field['element']
            elem.clear()
            elem.send_keys(criteria['date'])
            print(f"✅ Filled date: {criteria['date']}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill date: {e}")
    
    # Fill start time
    if 'start_time' in mappings and criteria.get('start_time'):
        field = mappings['start_time']
        try:
            if field['tag'] == 'select':
                select = Select(field['element'])
                # Find matching option
                for option in select.options:
                    if criteria['start_time'] in option.text:
                        select.select_by_visible_text(option.text)
                        print(f"✅ Selected start time: {option.text}")
                        success_count += 1
                        break
            else:
                elem = field['element']
                elem.clear()
                elem.send_keys(criteria['start_time'])
                print(f"✅ Filled start time: {criteria['start_time']}")
                success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill start time: {e}")
    
    # Fill end time
    if 'end_time' in mappings and criteria.get('end_time'):
        field = mappings['end_time']
        try:
            if field['tag'] == 'select':
                select = Select(field['element'])
                for option in select.options:
                    if criteria['end_time'] in option.text:
                        select.select_by_visible_text(option.text)
                        print(f"✅ Selected end time: {option.text}")
                        success_count += 1
                        break
            else:
                elem = field['element']
                elem.clear()
                elem.send_keys(criteria['end_time'])
                print(f"✅ Filled end time: {criteria['end_time']}")
                success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill end time: {e}")
    
    # Fill capacity
    if 'capacity' in mappings and criteria.get('capacity'):
        field = mappings['capacity']
        try:
            if field['tag'] == 'select':
                select = Select(field['element'])
                capacity_str = str(criteria['capacity'])
                
                # Find best matching option
                best_option = None
                for option in select.options:
                    if capacity_str in option.text:
                        best_option = option
                        break
                    # Check for range
                    range_match = re.search(r'(\d+)\s*-\s*(\d+)', option.text)
                    if range_match:
                        min_cap = int(range_match.group(1))
                        max_cap = int(range_match.group(2))
                        if min_cap <= criteria['capacity'] <= max_cap:
                            best_option = option
                            break
                
                if best_option:
                    select.select_by_visible_text(best_option.text)
                    print(f"✅ Selected capacity: {best_option.text}")
                    success_count += 1
            else:
                elem = field['element']
                elem.clear()
                elem.send_keys(str(criteria['capacity']))
                print(f"✅ Filled capacity: {criteria['capacity']}")
                success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill capacity: {e}")
    
    # Fill location
    if 'location' in mappings and criteria.get('location'):
        field = mappings['location']
        try:
            if field['tag'] == 'select':
                select = Select(field['element'])
                for option in select.options:
                    if criteria['location'].lower() in option.text.lower():
                        select.select_by_visible_text(option.text)
                        print(f"✅ Selected location: {option.text}")
                        success_count += 1
                        break
            else:
                elem = field['element']
                elem.clear()
                elem.send_keys(criteria['location'])
                print(f"✅ Filled location: {criteria['location']}")
                success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill location: {e}")
    
    # Fill purpose
    if 'purpose' in mappings and criteria.get('purpose'):
        field = mappings['purpose']
        try:
            elem = field['element']
            elem.clear()
            elem.send_keys(criteria['purpose'])
            print(f"✅ Filled purpose: {criteria['purpose']}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to fill purpose: {e}")
    
    print(f"\n📊 Filled {success_count} fields successfully")
    return success_count > 0


def find_submit_button(driver):
    """Find submit button"""
    
    selectors = [
        "//button[@type='submit']",
        "//input[@type='submit']",
        "//button[contains(text(), 'Search')]",
        "//button[contains(text(), 'Find')]",
        "//button[contains(text(), 'Submit')]"
    ]
    
    for selector in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    return elem
        except:
            continue
    
    return None


def analyze_results_page(driver):
    """Analyze results after form submission"""
    
    try:
        # Look for common result indicators
        page_text = driver.page_source.lower()
        
        if 'no results' in page_text or 'no rooms' in page_text:
            print("❌ No rooms found with current criteria")
        elif 'available' in page_text or 'book' in page_text:
            print("✅ Found available rooms!")
            
            # Count book buttons
            book_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Book')] | //a[contains(text(), 'Book')]")
            if book_buttons:
                print(f"📊 Found {len(book_buttons)} bookable rooms")
        else:
            print("📄 Results page loaded - check browser for details")
    except Exception as e:
        print(f"Error analyzing results: {e}")


if __name__ == "__main__":
    try:
        intelligent_form_booking_workflow()
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")