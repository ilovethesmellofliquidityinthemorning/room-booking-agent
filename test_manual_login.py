#!/usr/bin/env python3
"""
Manual login test script - launches its own Chrome, waits for manual login,
then continues with automation
"""

import os
import time
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation

def test_manual_login_workflow():
    """Test workflow with manual login step"""
    load_dotenv()
    
    # Get SharePoint URL from environment (default to UT Finance SharePoint)
    sharepoint_url = os.getenv('SHAREPOINT_URL', 'https://utexas.sharepoint.com/sites/McCombs-DepartmentofFinance/SitePages/CollabHome.aspx')
    
    if not sharepoint_url:
        print("ERROR: SharePoint URL is required")
        return
    
    print("=" * 60)
    print("MANUAL LOGIN WORKFLOW")
    print("=" * 60)
    print(f"SharePoint URL: {sharepoint_url}")
    print()
    print("This script will:")
    print("1. Launch a fresh Chrome instance")
    print("2. Navigate to your SharePoint URL")
    print("3. Wait for you to manually complete login")
    print("4. Continue with room booking automation")
    print()
    
    input("Press Enter to start...")
    
    # Create automation instance with fresh Chrome (no existing session)
    print("\n🚀 Starting fresh Chrome instance...")
    automation = MomentusAutomation(
        headless=False,           # Keep visible for manual login
        use_existing_session=False  # Start fresh instance
    )
    
    try:
        # Navigate to SharePoint
        print(f"🌐 Navigating to SharePoint: {sharepoint_url}")
        automation.setup_driver()  # Initialize the driver
        automation.driver.get(sharepoint_url)
        
        # Wait for page to load
        time.sleep(3)
        print(f"📄 Current page: {automation.driver.title}")
        
        # Manual login pause
        print("\n" + "=" * 60)
        print("MANUAL LOGIN REQUIRED")
        print("=" * 60)
        print("👤 Please complete your login in the Chrome window:")
        print("   1. Enter your credentials")
        print("   2. Complete any 2FA/MFA steps")
        print("   3. Navigate to your dashboard/home page")
        print("   4. When ready, return here and press Enter")
        print()
        
        input("✅ Press Enter when you have successfully logged in...")
        
        # Verify login success
        print("\n🔍 Verifying login status...")
        current_url = automation.driver.current_url
        current_title = automation.driver.title
        
        print(f"📍 Current URL: {current_url}")
        print(f"📄 Current Title: {current_title}")
        
        # Check for common login indicators
        page_source = automation.driver.page_source.lower()
        login_indicators = [
            'dashboard', 'welcome', 'logout', 'sign out', 
            'profile', 'menu', 'nav', 'home'
        ]
        
        found_indicators = [indicator for indicator in login_indicators if indicator in page_source]
        
        if found_indicators:
            print(f"✅ Login appears successful! Found indicators: {', '.join(found_indicators)}")
        else:
            print("⚠️  Login status unclear, but continuing...")
        
        # Now try to find room reservations
        print("\n🏢 Searching for room reservation system...")
        
        success = automation.navigate_to_room_reservations()
        
        if success:
            print("✅ Successfully found room reservation system!")
            
            # Analyze the page to see what we can do
            print("\n📊 Analyzing the room booking interface...")
            page_analysis = automation.analyze_momentus_page()
            
            print("\n" + "=" * 60)
            print("NEXT STEPS")
            print("=" * 60)
            print("The automation has successfully:")
            print("✅ Launched Chrome")
            print("✅ Navigated to SharePoint")
            print("✅ Waited for manual login")
            print("✅ Found the room reservation system")
            print()
            print("You can now:")
            print("1. Test room booking with specific criteria")
            print("2. Explore the booking interface manually")
            print("3. Run the full booking automation")
            print()
            
            # Keep browser open for further testing
            print("Browser will stay open for 30 seconds for you to explore...")
            print("Press Ctrl+C to close immediately, or wait for auto-close.")
            
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 Closing browser...")
                
        else:
            print("❌ Could not find room reservation system")
            print("The browser will stay open for you to manually navigate")
            print("Press Enter when ready to close...")
            input()
            
    except KeyboardInterrupt:
        print("\n👋 Script interrupted by user")
        
    except Exception as e:
        print(f"❌ Error during workflow: {e}")
        print("Browser will stay open for debugging...")
        input("Press Enter to close...")
        
    finally:
        automation.close()
        print("🔚 Browser closed. Workflow complete.")

def test_room_booking_with_criteria():
    """Test room booking with specific criteria after manual login"""
    print("\n" + "=" * 60)
    print("ROOM BOOKING TEST")
    print("=" * 60)
    
    # Get booking criteria from user
    date = input("Enter booking date (YYYY-MM-DD) [today]: ").strip()
    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
    
    start_time = input("Enter start time (HH:MM) [09:00]: ").strip() or "09:00"
    end_time = input("Enter end time (HH:MM) [10:00]: ").strip() or "10:00"
    capacity = input("Enter required capacity [5]: ").strip() or "5"
    location = input("Enter preferred location/building []: ").strip()
    
    criteria = {
        'date': date,
        'start_time': start_time,
        'end_time': end_time,
        'capacity': int(capacity),
        'location': location
    }
    
    print(f"\n🔍 Searching for rooms with criteria: {criteria}")
    
    # This assumes we already have an active session from the manual login
    # You would call this after running test_manual_login_workflow()
    print("Note: Run this as part of the manual login workflow")

if __name__ == "__main__":
    try:
        test_manual_login_workflow()
        
        # Optional: Ask if user wants to test booking
        if input("\nWould you like to test room booking now? (y/n): ").lower().startswith('y'):
            test_room_booking_with_criteria()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Script failed: {e}")