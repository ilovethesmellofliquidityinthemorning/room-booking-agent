#!/usr/bin/env python3
"""
Debug script to see what's on the Momentus page
"""

import os
import time
from dotenv import load_dotenv
from app.browser_automation import MomentusAutomation

def debug_page():
    load_dotenv()
    
    print("Opening Momentus page to examine structure...")
    automation = MomentusAutomation(headless=True)  # Use headless for faster debugging
    
    try:
        automation.setup_driver()
        automation.driver.get("https://momentus.utexas.edu/")
        
        time.sleep(3)  # Wait for page to load
        
        print(f"Page title: {automation.driver.title}")
        print(f"Current URL: {automation.driver.current_url}")
        
        try:
            # Look for input fields
            from selenium.webdriver.common.by import By
            inputs = automation.driver.find_elements(By.TAG_NAME, "input")
            print(f"\nFound {len(inputs)} input fields:")
            for i, inp in enumerate(inputs):
                print(f"  {i+1}. ID: '{inp.get_attribute('id')}', Name: '{inp.get_attribute('name')}', Type: '{inp.get_attribute('type')}', Placeholder: '{inp.get_attribute('placeholder')}'")
            
            # Look for buttons
            buttons = automation.driver.find_elements(By.TAG_NAME, "button")
            print(f"\nFound {len(buttons)} buttons:")
            for i, btn in enumerate(buttons):
                print(f"  {i+1}. Text: '{btn.text}', Type: '{btn.get_attribute('type')}', ID: '{btn.get_attribute('id')}'")
            
            # Look for forms
            forms = automation.driver.find_elements(By.TAG_NAME, "form")
            print(f"\nFound {len(forms)} forms:")
            for i, form in enumerate(forms):
                print(f"  {i+1}. Action: '{form.get_attribute('action')}', Method: '{form.get_attribute('method')}'")
            
            # Look for any text containing "login", "sign", etc.
            page_source = automation.driver.page_source.lower()
            keywords = ["login", "sign in", "username", "password", "email"]
            print(f"\nKeyword analysis:")
            for keyword in keywords:
                count = page_source.count(keyword)
                print(f"  '{keyword}': {count} occurrences")
                
            # Save a snippet of page source for analysis
            with open("momentus_page_source.html", "w", encoding="utf-8") as f:
                f.write(automation.driver.page_source)
            print("Page source saved as momentus_page_source.html")
                
        except Exception as debug_e:
            print(f"Debug error: {debug_e}")
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
    finally:
        automation.close()

if __name__ == "__main__":
    debug_page()