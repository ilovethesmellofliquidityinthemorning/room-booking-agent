#!/usr/bin/env python3
"""
Enhanced test script for the complete SharePoint → Momentus booking flow

This script tests the improved automation with:
- Better navigation handling
- Enhanced form detection and filling
- Robust page transition management
- Complete booking workflow
"""

import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation

def print_test_header():
    print("=" * 60)
    print("ENHANCED SHAREPOINT → MOMENTUS BOOKING TEST")
    print("=" * 60)
    print()
    print("This test will:")
    print("1. Connect to your existing Chrome session")
    print("2. Navigate from SharePoint to Momentus")
    print("3. Fill booking forms with enhanced detection")
    print("4. Complete a sample room booking")
    print()

def print_setup_instructions():
    print("SETUP INSTRUCTIONS:")
    print("-" * 30)
    print("1. Start Chrome with debugging:")
    print("   chrome.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\temp\\chrome_debug\"")
    print()
    print("2. In Chrome, navigate to your UT SharePoint dashboard")
    print("3. Log in with your credentials")
    print("4. Navigate to the room reservations section (if possible)")
    print()
    print("Press Enter when ready to start the test...")
    input()

def test_enhanced_booking():
    """Test the enhanced booking workflow"""
    load_dotenv()
    
    print_test_header()
    print_setup_instructions()
    
    print("🔗 Connecting to Chrome session...")
    
    # Create automation instance that connects to existing session
    automation = MomentusAutomation(
        use_existing_session=True, 
        debug_port=9222,
        headless=False  # Keep visible for debugging
    )
    
    try:
        # Connect to existing session
        automation.setup_driver()
        
        print(f"✅ Connected! Current page: {automation.driver.title}")
        print(f"📍 URL: {automation.driver.current_url}")
        print()
        
        # Test 1: Enhanced Navigation
        print("🧭 TEST 1: Enhanced SharePoint → Momentus Navigation")
        print("-" * 50)
        
        navigation_success = automation.navigate_to_room_reservations()
        
        if navigation_success:
            print("✅ Navigation successful!")
            print(f"📍 Current URL: {automation.driver.current_url}")
            print(f"📄 Page title: {automation.driver.title}")
        else:
            print("⚠️  Automatic navigation failed - this is normal for some SharePoint setups")
            print("Please manually navigate to the Momentus booking system")
            print("Press Enter when you're on the booking page...")
            input()
        
        print()
        
        # Test 2: Enhanced Page Analysis
        print("🔍 TEST 2: Enhanced Momentus Page Analysis")
        print("-" * 50)
        
        page_analysis = automation.analyze_momentus_page()
        
        if page_analysis:
            print("✅ Page analysis complete!")
            print(f"📊 Analysis Summary:")
            print(f"   • Forms: {len(page_analysis.get('forms', []))}")
            print(f"   • Input fields: {len(page_analysis.get('input_fields', []))}")
            print(f"   • Date fields: {len(page_analysis.get('date_fields', []))}")
            print(f"   • Time fields: {len(page_analysis.get('time_fields', []))}")
            print(f"   • Dropdowns: {len(page_analysis.get('select_dropdowns', []))}")
            print(f"   • Buttons: {len(page_analysis.get('buttons', []))}")
            print(f"   • Relevant links: {len(page_analysis.get('links', []))}")
            
            # Show key findings
            if page_analysis.get('date_fields'):
                date_fields = [f"'{f.get('name') or f.get('id')}'" for f in page_analysis['date_fields']]
                print(f"   📅 Date fields: {', '.join(date_fields)}")
            
            if page_analysis.get('time_fields'):
                time_fields = [f"'{f.get('name') or f.get('id')}'" for f in page_analysis['time_fields']]
                print(f"   🕐 Time fields: {', '.join(time_fields)}")
            
            booking_buttons = []
            for btn in page_analysis.get('buttons', []):
                btn_text = btn.get('text', '').lower()
                if any(keyword in btn_text for keyword in ['book', 'reserve', 'search', 'submit']):
                    booking_buttons.append(f"'{btn.get('text')}'")
            
            if booking_buttons:
                print(f"   🎯 Booking buttons: {', '.join(booking_buttons[:5])}")
        
        print()
        
        # Test 3: Enhanced Booking Flow
        print("📝 TEST 3: Enhanced Room Booking")
        print("-" * 50)
        
        # Create sample booking criteria
        tomorrow = datetime.now() + timedelta(days=1)
        booking_criteria = {
            'date': tomorrow.strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00',
            'capacity': 10,
            'location': 'ETC',  # Engineering Teaching Center
            'equipment': ['projector'],
            'purpose': 'Team meeting'
        }
        
        print(f"🎯 Booking criteria:")
        for key, value in booking_criteria.items():
            print(f"   • {key}: {value}")
        print()
        
        print("🚀 Starting enhanced booking process...")
        
        # Use the enhanced search_rooms method which now handles the full booking flow
        result = automation.search_rooms(booking_criteria)
        
        if result:
            if len(result) == 1 and result[0].get('status') == 'booked':
                print("🎉 BOOKING SUCCESS!")
                print("✅ Room has been booked successfully!")
                details = result[0].get('details', {})
                if details:
                    print("📋 Booking details:")
                    for key, value in details.items():
                        print(f"   • {key}: {value}")
            else:
                print(f"🔍 Found {len(result)} available rooms:")
                for i, room in enumerate(result[:5], 1):  # Show first 5 rooms
                    print(f"   {i}. {room}")
                
                if len(result) > 0:
                    print("\n🎯 To book a specific room, you would typically:")
                    print("   1. Present these options to the user")
                    print("   2. Let them select a preferred room")
                    print("   3. Call the book_room() method for the selected room")
        else:
            print("❌ No results returned from booking process")
            print("This could mean:")
            print("   • No rooms available for the criteria")
            print("   • Form couldn't be filled or submitted")
            print("   • Page structure doesn't match expected patterns")
        
        print()
        
        # Test 4: Manual Inspection Time
        print("🕐 TEST 4: Manual Inspection")
        print("-" * 50)
        print("The browser will remain open for 60 seconds for manual inspection.")
        print("You can:")
        print("   • Review the current page state")
        print("   • Check if booking was successful")
        print("   • Navigate to confirmation pages")
        print("   • Test additional functionality manually")
        print()
        
        for i in range(60, 0, -10):
            print(f"⏰ {i} seconds remaining...")
            time.sleep(10)
        
        print("✅ Enhanced booking test completed!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Chrome is running with --remote-debugging-port=9222")
        print("2. Verify you're logged into SharePoint")
        print("3. Check that the room booking system is accessible")
        print("4. Review the logs for detailed error information")
        
    finally:
        # Don't close the driver - leave the browser open for manual use
        print("\n🌐 Browser session remains open for continued manual testing.")
        print("Close this script when you're done.")

def main():
    """Main test execution"""
    test_enhanced_booking()

if __name__ == "__main__":
    main()