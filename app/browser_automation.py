"""
Browser automation module for interacting with the Momentus system
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from .utils import logger

# Load environment variables
load_dotenv()

class MomentusAutomation:
    def __init__(self, headless: bool = True, use_existing_session: bool = False, debug_port: int = 9222):
        self.driver = None
        self.headless = headless
        self.wait_timeout = 10
        self.base_url = os.getenv('MOMENTUS_BASE_URL', 'https://momentus.utexas.edu/')
        self.use_existing_session = use_existing_session
        self.debug_port = debug_port
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.use_existing_session:
            # Connect to existing Chrome instance with remote debugging
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            logger.info(f"Connecting to existing Chrome session on port {self.debug_port}")
        else:
            # Standard setup for new browser instance
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki-list')
            chrome_options.add_argument('--ignore-ssl-errors-list')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver manager to automatically download and manage ChromeDriver
        try:
            # Try to get the latest version compatible with current Chrome
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            logger.warning(f"Failed to use webdriver manager: {e}")
            # Fallback to system ChromeDriver
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                logger.error(f"Failed to initialize Chrome driver: {e2}")
                raise e2
        
        if not self.use_existing_session:
            # Execute script to prevent detection (only for new sessions)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver initialized")
    
    def login(self, username: str, password: str) -> bool:
        """Login to the Momentus system"""
        try:
            if not self.driver:
                self.setup_driver()
            
            logger.info(f"Navigating to Momentus login: {self.base_url}")
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Take screenshot for debugging
            if not self.headless:
                self.driver.save_screenshot("momentus_initial_page.png")
                logger.info("Screenshot saved: momentus_initial_page.png")
            
            # Log current page title and URL
            logger.info(f"Page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Try multiple common selectors for username field
            username_field = None
            username_selectors = [
                (By.ID, "username"),
                (By.ID, "user"),
                (By.ID, "login"),
                (By.ID, "email"),
                (By.NAME, "username"),
                (By.NAME, "user"),
                (By.NAME, "login"),
                (By.NAME, "email"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[@type='email']")
            ]
            
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"Found username field with selector: {selector_type}='{selector_value}'")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                # Log all input fields for debugging
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.error(f"No username field found. Available inputs: {[(inp.get_attribute('id'), inp.get_attribute('name'), inp.get_attribute('type')) for inp in inputs]}")
                return False
            
            # Try multiple selectors for password field
            password_field = None
            password_selectors = [
                (By.ID, "password"),
                (By.ID, "pass"),
                (By.NAME, "password"),
                (By.NAME, "pass"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    logger.info(f"Found password field with selector: {selector_type}='{selector_value}'")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                logger.error("No password field found")
                return False
            
            # Fill in credentials
            logger.info("Filling login credentials")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Take screenshot before submitting
            if not self.headless:
                self.driver.save_screenshot("momentus_before_submit.png")
                logger.info("Screenshot saved: momentus_before_submit.png")
            
            # Try multiple selectors for submit button
            login_button = None
            button_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.ID, "submit"),
                (By.ID, "login"),
                (By.CLASS_NAME, "btn-login")
            ]
            
            for selector_type, selector_value in button_selectors:
                try:
                    login_button = self.driver.find_element(selector_type, selector_value)
                    logger.info(f"Found login button with selector: {selector_type}='{selector_value}'")
                    break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                # Log all buttons for debugging
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.XPATH, "//input[@type='submit']")
                logger.error(f"No login button found. Available buttons: {[btn.text for btn in buttons]}")
                logger.error(f"Available submit inputs: {[inp.get_attribute('value') for inp in inputs]}")
                return False
            
            # Submit login form
            logger.info("Clicking login button")
            login_button.click()
            
            # Wait for page to change - check for various success indicators
            time.sleep(3)  # Give page time to load
            
            # Take screenshot after login attempt
            if not self.headless:
                self.driver.save_screenshot("momentus_after_login.png")
                logger.info("Screenshot saved: momentus_after_login.png")
            
            logger.info(f"After login - Page title: {self.driver.title}")
            logger.info(f"After login - Current URL: {self.driver.current_url}")
            
            # Check for successful login indicators
            success_indicators = [
                (By.CLASS_NAME, "dashboard"),
                (By.CLASS_NAME, "main-content"),
                (By.CLASS_NAME, "user-menu"),
                (By.XPATH, "//a[contains(@href, 'logout')]"),
                (By.XPATH, "//*[contains(text(), 'Dashboard')]"),
                (By.XPATH, "//*[contains(text(), 'Welcome')]")
            ]
            
            login_successful = False
            for selector_type, selector_value in success_indicators:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    logger.info(f"Login success indicator found: {selector_type}='{selector_value}'")
                    login_successful = True
                    break
                except TimeoutException:
                    continue
            
            # Also check if URL changed (indicating successful login)
            if not login_successful and self.driver.current_url != self.base_url:
                logger.info("URL changed after login, assuming success")
                login_successful = True
            
            # Check for error messages
            error_selectors = [
                (By.CLASS_NAME, "error"),
                (By.CLASS_NAME, "alert-danger"),
                (By.XPATH, "//*[contains(text(), 'Invalid')]"),
                (By.XPATH, "//*[contains(text(), 'incorrect')]"),
                (By.XPATH, "//*[contains(text(), 'failed')]")
            ]
            
            for selector_type, selector_value in error_selectors:
                try:
                    error_element = self.driver.find_element(selector_type, selector_value)
                    logger.error(f"Login error found: {error_element.text}")
                    return False
                except NoSuchElementException:
                    continue
            
            if login_successful:
                logger.info("Successfully logged into Momentus")
                return True
            else:
                logger.error("Login status unclear - no success indicators found")
                return False
            
        except TimeoutException:
            logger.error("Login timeout - check credentials or network")
            return False
        except Exception as e:
            logger.error(f"Login failed with exception: {str(e)}")
            return False
    
    def navigate_to_room_reservations(self) -> bool:
        """Navigate to the room reservations section after manual login"""
        try:
            if not self.driver:
                self.setup_driver()
            
            # Wait for page to be ready
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            logger.info(f"Current page title: {self.driver.title}")
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Enhanced search for room reservation links with more comprehensive selectors
            navigation_selectors = [
                # Direct text matches (case-insensitive)
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room reserv')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book room')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room booking')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'meeting room')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'conference room')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'momentus')]",
                
                # Button elements
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reserv')]",
                
                # Broader link searches
                "//a[contains(text(), 'Room')]",
                "//a[contains(text(), 'Reserv')]",
                "//a[contains(text(), 'Book')]",
                "//a[contains(text(), 'Momentus')]",
                
                # SharePoint specific selectors
                "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]//parent::a",
                "//div[contains(@class, 'ms-nav')]//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]",
                
                # Title and alt attributes
                "//a[contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]",
                "//a[contains(translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'room')]",
                
                # Href patterns
                "//a[contains(@href, 'room')]",
                "//a[contains(@href, 'reserv')]",
                "//a[contains(@href, 'book')]",
                "//a[contains(@href, 'momentus')]",
            ]
            
            logger.info("Searching for room reservation links...")
            room_link = None
            found_links = []
            
            for i, selector in enumerate(navigation_selectors):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            try:
                                text = element.text.strip()
                                href = element.get_attribute('href') or ''
                                title = element.get_attribute('title') or ''
                                
                                # Log all found links for debugging
                                found_links.append({
                                    'text': text,
                                    'href': href,
                                    'title': title,
                                    'selector_index': i
                                })
                                
                                # Check if this looks like a room reservation link
                                combined_text = f"{text} {href} {title}".lower()
                                room_keywords = ['room', 'reserv', 'book', 'meeting', 'conference', 'momentus']
                                
                                if any(keyword in combined_text for keyword in room_keywords):
                                    # Prioritize links with multiple keywords or specific phrases
                                    score = sum(1 for keyword in room_keywords if keyword in combined_text)
                                    if 'room' in combined_text and ('reserv' in combined_text or 'book' in combined_text):
                                        score += 2  # Bonus for room + reservation/booking
                                    if 'momentus' in combined_text:
                                        score += 3  # High priority for Momentus
                                    
                                    if not room_link or score > getattr(room_link, 'score', 0):
                                        room_link = element
                                        room_link.score = score
                                        logger.info(f"Found potential room link (score {score}): '{text}' -> {href}")
                                        
                            except Exception as e:
                                logger.debug(f"Error processing element: {e}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Selector {i} failed: {selector} - {e}")
                    continue
            
            # Log all found links for debugging
            logger.info(f"Found {len(found_links)} potential links:")
            for link in found_links[:10]:  # Show first 10
                logger.info(f"  - '{link['text']}' -> {link['href']}")
            
            if room_link:
                success = self._click_and_navigate_to_momentus(room_link)
                if success:
                    return True
            
            # If no direct link found, try to find the reservations page via URL patterns
            if not room_link:
                logger.warning("No room reservation link found, trying common URL patterns")
                
                common_patterns = [
                    "/reservations",
                    "/booking", 
                    "/rooms",
                    "/calendar",
                    "/meeting-rooms",
                    "/_layouts/15/Booking",
                    "/Sites/RoomReservations",
                    "/momentus"
                ]
                
                current_base = self.driver.current_url.split('?')[0].rstrip('/')
                
                for pattern in common_patterns:
                    try:
                        test_url = current_base + pattern
                        logger.info(f"Trying URL: {test_url}")
                        self.driver.get(test_url)
                        time.sleep(3)
                        
                        # Check if page loaded successfully (not 404)
                        title_lower = self.driver.title.lower()
                        if "404" not in title_lower and "error" not in title_lower and "not found" not in title_lower:
                            logger.info(f"Successfully accessed: {test_url}")
                            logger.info(f"Page title: {self.driver.title}")
                            return True
                    except Exception as e:
                        logger.debug(f"URL pattern failed: {pattern} - {e}")
                        continue
                
                logger.error("Could not find room reservation section")
                return False
            
            return False
                
        except Exception as e:
            logger.error(f"Navigation to room reservations failed: {str(e)}")
            return False

    def _click_and_navigate_to_momentus(self, room_link) -> bool:
        """Enhanced navigation that handles the transition from SharePoint to Momentus"""
        try:
            # Store original window handle
            original_window = self.driver.current_window_handle
            original_url = self.driver.current_url
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", room_link)
            time.sleep(2)
            
            # Highlight the element for debugging (if not headless)
            if not self.headless:
                self.driver.execute_script("arguments[0].style.border='3px solid red'", room_link)
                time.sleep(1)
            
            # Try clicking the element
            logger.info(f"Clicking room reservation link: '{room_link.text}'")
            room_link.click()
            
            # Wait for potential new tab/window or navigation
            time.sleep(3)
            
            # Check for new windows/tabs
            all_windows = self.driver.window_handles
            if len(all_windows) > 1:
                logger.info("New window/tab detected, switching to it")
                for window in all_windows:
                    if window != original_window:
                        self.driver.switch_to.window(window)
                        break
                        
                # Wait for new page to load
                time.sleep(5)
            
            new_url = self.driver.current_url
            new_title = self.driver.title
            
            logger.info(f"After click - Title: {new_title}")
            logger.info(f"After click - URL: {new_url}")
            
            # Check if we're now in the Momentus system
            if self._is_in_momentus_system(new_url, new_title):
                logger.info("Successfully navigated to Momentus system!")
                
                # Wait for Momentus interface to fully load
                self._wait_for_momentus_interface()
                return True
            elif new_url != original_url:
                logger.info("Navigated to new page, checking if it leads to Momentus...")
                
                # Look for additional links to enter Momentus system
                momentus_entry = self._find_momentus_entry_point()
                if momentus_entry:
                    logger.info("Found Momentus entry point, clicking...")
                    momentus_entry.click()
                    time.sleep(5)
                    
                    if self._is_in_momentus_system(self.driver.current_url, self.driver.title):
                        logger.info("Successfully entered Momentus system via secondary link!")
                        self._wait_for_momentus_interface()
                        return True
                
                return True  # At least we navigated somewhere relevant
            else:
                logger.warning("Click did not result in navigation")
                return False
                
        except Exception as e:
            logger.error(f"Failed to click and navigate to Momentus: {e}")
            return False

    def _is_in_momentus_system(self, url: str, title: str) -> bool:
        """Check if we're currently in the Momentus booking system"""
        momentus_indicators = [
            'momentus' in url.lower(),
            'momentus' in title.lower(),
            'utexas.momentus' in url.lower(),
            'room' in title.lower() and 'book' in title.lower(),
            'reservation' in title.lower() and 'system' in title.lower()
        ]
        return any(momentus_indicators)
    
    def _find_momentus_entry_point(self):
        """Look for additional links that might lead to the Momentus system"""
        try:
            # Look for buttons or links that might launch Momentus
            entry_selectors = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'launch')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'open')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'access')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'enter')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reserve')]",
                "//a[contains(@href, 'momentus')]",
                "//iframe[contains(@src, 'momentus')]",
            ]
            
            for selector in entry_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"Found Momentus entry point: '{element.text}' with selector: {selector}")
                        return element
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Momentus entry point: {e}")
            return None
    
    def _wait_for_momentus_interface(self):
        """Wait for the Momentus interface to fully load and become interactive"""
        try:
            logger.info("Waiting for Momentus interface to load...")
            wait = WebDriverWait(self.driver, 15)
            
            # Look for common Momentus interface elements
            momentus_indicators = [
                (By.XPATH, "//input[@type='date']"),
                (By.XPATH, "//select[contains(@name, 'room') or contains(@id, 'room')]"),
                (By.XPATH, "//form[contains(@class, 'booking') or contains(@class, 'reservation')]"),
                (By.XPATH, "//*[contains(text(), 'Select a room') or contains(text(), 'Choose room')]"),
                (By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'Find') or contains(text(), 'Book')]")
            ]
            
            for selector_type, selector_value in momentus_indicators:
                try:
                    element = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    logger.info(f"Momentus interface loaded - found: {selector_type}='{selector_value}'")
                    time.sleep(2)  # Additional time for JavaScript to initialize
                    return True
                except TimeoutException:
                    continue
            
            # Fallback - just wait for any form elements
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
                logger.info("Momentus interface loaded - found form elements")
                time.sleep(2)
                return True
            except TimeoutException:
                logger.warning("Momentus interface may not be fully loaded, but continuing...")
                return False
                
        except Exception as e:
            logger.error(f"Error waiting for Momentus interface: {e}")
            return False

    def search_rooms(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced room search with better Momentus integration"""
        try:
            # Check if we're already in Momentus, if not navigate there
            if not self._is_in_momentus_system(self.driver.current_url, self.driver.title):
                logger.info("Not in Momentus system, navigating...")
                if not self.navigate_to_room_reservations():
                    logger.error("Could not navigate to room reservations")
                    return []
            
            # Analyze the current page to understand available form elements
            logger.info("Analyzing Momentus booking interface...")
            page_analysis = self.analyze_momentus_page()
            
            # Try to fill the booking form with enhanced detection
            success = self._fill_momentus_booking_form(search_criteria, page_analysis)
            if not success:
                logger.warning("Could not fill booking form completely")
            
            # Try to submit the search/booking
            submitted = self._submit_momentus_form(page_analysis)
            if submitted:
                # Wait for results and parse them
                time.sleep(5)  # Allow results/booking to process
                
                # Check if booking was successful or if we got search results
                result = self._handle_momentus_response()
                
                if result.get('type') == 'booking_success':
                    logger.info("Room booking completed successfully!")
                    return [{'status': 'booked', 'details': result.get('details', {})}]
                elif result.get('type') == 'search_results':
                    rooms = result.get('rooms', [])
                    logger.info(f"Found {len(rooms)} available rooms")
                    return rooms
                else:
                    logger.warning("Unexpected response from Momentus")
                    return []
            else:
                logger.error("Could not submit Momentus form")
                return []
            
        except Exception as e:
            logger.error(f"Enhanced room search failed: {str(e)}")
            return []
    
    def book_room(self, room_id: str, booking_details: Dict[str, Any]) -> bool:
        """Book a specific room"""
        try:
            # Navigate to booking page for the room
            booking_url = f"{self.base_url}/booking/room/{room_id}"
            self.driver.get(booking_url)
            
            wait = WebDriverWait(self.driver, self.wait_timeout)
            
            # Fill booking form
            self._fill_booking_form(booking_details)
            
            # Submit booking
            book_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Book')]"))
            )
            book_button.click()
            
            # Wait for confirmation
            confirmation = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "booking-confirmation"))
            )
            
            logger.info(f"Successfully booked room {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"Room booking failed: {str(e)}")
            return False
    
    def _find_search_button(self):
        """Find the search/submit button on the current page"""
        search_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]",
            "//input[@type='submit'][contains(@value, 'Search')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'find')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book')]",
            "//input[@type='submit']",
            "//button[@type='submit']"
        ]
        
        for selector in search_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                logger.info(f"Found search button: '{element.text}' with selector: {selector}")
                return element
            except NoSuchElementException:
                continue
        
        return None

    def _fill_search_form(self, criteria: Dict[str, Any]):
        """Fill the room search form with provided criteria"""
        try:
            logger.info(f"Filling search form with criteria: {criteria}")
            
            # Extract criteria
            date = criteria.get('date')
            start_time = criteria.get('start_time')
            end_time = criteria.get('end_time')
            duration = criteria.get('duration')
            capacity = criteria.get('capacity')
            location = criteria.get('location')
            equipment = criteria.get('equipment', [])
            
            # Common date field selectors
            if date:
                date_selectors = [
                    "//input[@type='date']",
                    "//input[contains(@name, 'date')]",
                    "//input[contains(@id, 'date')]",
                    "//input[contains(@placeholder, 'date')]"
                ]
                self._fill_field_by_selectors(date_selectors, date, "date")
            
            # Time field selectors
            if start_time:
                start_time_selectors = [
                    "//input[@type='time'][contains(@name, 'start')]",
                    "//input[contains(@name, 'start')]",
                    "//input[contains(@id, 'start')]",
                    "//select[contains(@name, 'start')]"
                ]
                self._fill_field_by_selectors(start_time_selectors, start_time, "start time")
            
            if end_time:
                end_time_selectors = [
                    "//input[@type='time'][contains(@name, 'end')]",
                    "//input[contains(@name, 'end')]",
                    "//input[contains(@id, 'end')]",
                    "//select[contains(@name, 'end')]"
                ]
                self._fill_field_by_selectors(end_time_selectors, end_time, "end time")
            
            # Capacity field selectors
            if capacity:
                capacity_selectors = [
                    "//input[contains(@name, 'capacity')]",
                    "//input[contains(@id, 'capacity')]",
                    "//input[contains(@placeholder, 'people')]",
                    "//select[contains(@name, 'capacity')]"
                ]
                self._fill_field_by_selectors(capacity_selectors, str(capacity), "capacity")
            
            # Location field selectors
            if location:
                location_selectors = [
                    "//input[contains(@name, 'location')]",
                    "//input[contains(@id, 'location')]",
                    "//select[contains(@name, 'location')]",
                    "//input[contains(@name, 'building')]",
                    "//select[contains(@name, 'building')]"
                ]
                self._fill_field_by_selectors(location_selectors, location, "location")
            
            # Equipment checkboxes/selectors
            if equipment:
                for item in equipment:
                    equipment_selectors = [
                        f"//input[@type='checkbox'][contains(@value, '{item}')]",
                        f"//input[@type='checkbox'][following-sibling::label[contains(text(), '{item}')]]",
                        f"//label[contains(text(), '{item}')]//input[@type='checkbox']"
                    ]
                    
                    found = False
                    for selector in equipment_selectors:
                        try:
                            checkbox = self.driver.find_element(By.XPATH, selector)
                            if not checkbox.is_selected():
                                checkbox.click()
                                logger.info(f"Selected equipment: {item}")
                            found = True
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not found:
                        logger.warning(f"Could not find checkbox for equipment: {item}")
            
        except Exception as e:
            logger.error(f"Error filling search form: {str(e)}")

    def _fill_field_by_selectors(self, selectors: List[str], value: str, field_name: str):
        """Try multiple selectors to fill a field"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                
                # Handle different input types
                tag_name = element.tag_name.lower()
                input_type = element.get_attribute('type')
                
                if tag_name == 'select':
                    # Handle dropdown
                    from selenium.webdriver.support.ui import Select
                    select = Select(element)
                    
                    # Try to select by visible text first, then by value
                    try:
                        select.select_by_visible_text(value)
                    except:
                        try:
                            select.select_by_value(value)
                        except:
                            logger.warning(f"Could not select '{value}' in {field_name} dropdown")
                            continue
                            
                elif tag_name == 'input':
                    element.clear()
                    element.send_keys(value)
                
                logger.info(f"Filled {field_name} field with: {value}")
                return True
                
            except NoSuchElementException:
                continue
        
        logger.warning(f"Could not find {field_name} field")
        return False

    def _fill_momentus_booking_form(self, criteria: Dict[str, Any], page_analysis: Dict[str, Any]) -> bool:
        """Enhanced form filling specifically for Momentus booking interface"""
        try:
            logger.info("Filling Momentus booking form...")
            filled_fields = 0
            total_attempts = 0
            
            # Extract criteria
            date = criteria.get('date')
            start_time = criteria.get('start_time')
            end_time = criteria.get('end_time')
            duration = criteria.get('duration')
            capacity = criteria.get('capacity')
            location = criteria.get('location')
            equipment = criteria.get('equipment', [])
            
            # Use page analysis to fill fields more intelligently
            date_fields = page_analysis.get('date_fields', [])
            time_fields = page_analysis.get('time_fields', [])
            input_fields = page_analysis.get('input_fields', [])
            select_dropdowns = page_analysis.get('select_dropdowns', [])
            
            # Fill date fields
            if date and date_fields:
                for date_field in date_fields:
                    if self._fill_field_by_analysis(date_field, date, "date"):
                        filled_fields += 1
                    total_attempts += 1
            elif date:
                # Fallback to original method
                if self._fill_field_by_selectors([
                    "//input[@type='date']",
                    "//input[contains(@name, 'date')]",
                    "//input[contains(@id, 'date')]"
                ], date, "date"):
                    filled_fields += 1
                total_attempts += 1
            
            # Fill time fields
            if start_time and time_fields:
                for time_field in time_fields:
                    field_name = (time_field.get('name') or time_field.get('id') or '').lower()
                    if 'start' in field_name or 'begin' in field_name:
                        if self._fill_field_by_analysis(time_field, start_time, "start time"):
                            filled_fields += 1
                        total_attempts += 1
                        break
            elif start_time:
                if self._fill_field_by_selectors([
                    "//input[@type='time'][contains(@name, 'start')]",
                    "//select[contains(@name, 'start')]"
                ], start_time, "start time"):
                    filled_fields += 1
                total_attempts += 1
            
            if end_time and time_fields:
                for time_field in time_fields:
                    field_name = (time_field.get('name') or time_field.get('id') or '').lower()
                    if 'end' in field_name or 'finish' in field_name:
                        if self._fill_field_by_analysis(time_field, end_time, "end time"):
                            filled_fields += 1
                        total_attempts += 1
                        break
            elif end_time:
                if self._fill_field_by_selectors([
                    "//input[@type='time'][contains(@name, 'end')]",
                    "//select[contains(@name, 'end')]"
                ], end_time, "end time"):
                    filled_fields += 1
                total_attempts += 1
            
            # Fill capacity fields
            if capacity:
                capacity_filled = False
                for input_field in input_fields:
                    field_name = (input_field.get('name') or input_field.get('id') or input_field.get('placeholder') or '').lower()
                    if any(keyword in field_name for keyword in ['capacity', 'people', 'attendee', 'size']):
                        if self._fill_field_by_analysis(input_field, str(capacity), "capacity"):
                            filled_fields += 1
                            capacity_filled = True
                        total_attempts += 1
                        break
                
                if not capacity_filled:
                    if self._fill_field_by_selectors([
                        "//input[contains(@name, 'capacity')]",
                        "//select[contains(@name, 'capacity')]"
                    ], str(capacity), "capacity"):
                        filled_fields += 1
                    total_attempts += 1
            
            # Fill location/building fields
            if location:
                for dropdown in select_dropdowns:
                    field_name = (dropdown.get('name') or dropdown.get('id') or '').lower()
                    if any(keyword in field_name for keyword in ['location', 'building', 'floor', 'room']):
                        if self._fill_dropdown_by_analysis(dropdown, location, "location"):
                            filled_fields += 1
                        total_attempts += 1
                        break
            
            logger.info(f"Filled {filled_fields} out of {total_attempts} attempted fields")
            return filled_fields > 0
            
        except Exception as e:
            logger.error(f"Error filling Momentus booking form: {e}")
            return False
    
    def _fill_field_by_analysis(self, field_info: Dict[str, Any], value: str, field_name: str) -> bool:
        """Fill a field using information from page analysis"""
        try:
            # Construct selector based on field info
            field_id = field_info.get('id')
            field_name_attr = field_info.get('name')
            
            if field_id:
                selector = f"//input[@id='{field_id}']"
            elif field_name_attr:
                selector = f"//input[@name='{field_name_attr}']"
            else:
                return False
            
            element = self.driver.find_element(By.XPATH, selector)
            element.clear()
            element.send_keys(value)
            logger.info(f"Filled {field_name} field with: {value}")
            return True
            
        except Exception as e:
            logger.debug(f"Could not fill {field_name} field: {e}")
            return False
    
    def _fill_dropdown_by_analysis(self, dropdown_info: Dict[str, Any], value: str, field_name: str) -> bool:
        """Fill a dropdown using information from page analysis"""
        try:
            from selenium.webdriver.support.ui import Select
            
            dropdown_id = dropdown_info.get('id')
            dropdown_name = dropdown_info.get('name')
            
            if dropdown_id:
                selector = f"//select[@id='{dropdown_id}']"
            elif dropdown_name:
                selector = f"//select[@name='{dropdown_name}']"
            else:
                return False
            
            element = self.driver.find_element(By.XPATH, selector)
            select = Select(element)
            
            # Try to find matching option
            options = dropdown_info.get('options', [])
            for option in options:
                option_text = option.get('text', '').lower()
                option_value = option.get('value', '').lower()
                
                if value.lower() in option_text or value.lower() in option_value:
                    try:
                        select.select_by_visible_text(option.get('text'))
                        logger.info(f"Selected {field_name}: {option.get('text')}")
                        return True
                    except:
                        try:
                            select.select_by_value(option.get('value'))
                            logger.info(f"Selected {field_name}: {option.get('value')}")
                            return True
                        except:
                            continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Could not fill {field_name} dropdown: {e}")
            return False
    
    def _submit_momentus_form(self, page_analysis: Dict[str, Any]) -> bool:
        """Submit the Momentus booking form"""
        try:
            logger.info("Attempting to submit Momentus form...")
            
            # Look for submit buttons from page analysis
            buttons = page_analysis.get('buttons', [])
            
            # Prioritize buttons with booking-related text
            submit_button = None
            for button in buttons:
                button_text = button.get('text', '').lower()
                if any(keyword in button_text for keyword in ['book', 'reserve', 'submit', 'search', 'find']):
                    try:
                        if button.get('id'):
                            element = self.driver.find_element(By.ID, button['id'])
                        else:
                            element = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{button['text']}')]")
                        
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            logger.info(f"Found submit button: '{button['text']}'")
                            break
                    except:
                        continue
            
            # Fallback to generic selectors
            if not submit_button:
                submit_selectors = [
                    "//button[@type='submit']",
                    "//input[@type='submit']",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reserve')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]"
                ]
                
                for selector in submit_selectors:
                    try:
                        element = self.driver.find_element(By.XPATH, selector)
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            logger.info(f"Found submit button with selector: {selector}")
                            break
                    except:
                        continue
            
            if submit_button:
                # Scroll to button and click
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
                time.sleep(1)
                submit_button.click()
                logger.info("Successfully submitted Momentus form")
                return True
            else:
                logger.error("No submit button found")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting Momentus form: {e}")
            return False
    
    def _handle_momentus_response(self) -> Dict[str, Any]:
        """Handle the response from Momentus after form submission"""
        try:
            logger.info("Analyzing Momentus response...")
            
            # Wait for page to load/change
            time.sleep(3)
            
            current_url = self.driver.current_url
            current_title = self.driver.title
            page_source = self.driver.page_source.lower()
            
            logger.info(f"Response page title: {current_title}")
            logger.info(f"Response URL: {current_url}")
            
            # Check for booking success indicators
            success_indicators = [
                'booking confirmed',
                'reservation successful',
                'booking complete',
                'reserved successfully',
                'confirmation number',
                'booking reference'
            ]
            
            if any(indicator in page_source for indicator in success_indicators):
                logger.info("Detected booking success!")
                
                # Try to extract confirmation details
                confirmation_details = self._extract_booking_confirmation()
                
                return {
                    'type': 'booking_success',
                    'details': confirmation_details
                }
            
            # Check for search results
            elif 'available room' in page_source or 'search result' in page_source:
                logger.info("Detected search results page")
                
                rooms = self._parse_search_results()
                
                return {
                    'type': 'search_results',
                    'rooms': rooms
                }
            
            # Check for errors
            elif any(error in page_source for error in ['error', 'not available', 'conflict', 'invalid']):
                logger.warning("Detected error in Momentus response")
                
                return {
                    'type': 'error',
                    'message': 'Booking or search encountered an error'
                }
            
            else:
                logger.warning("Unknown Momentus response type")
                return {
                    'type': 'unknown',
                    'message': 'Could not determine response type'
                }
                
        except Exception as e:
            logger.error(f"Error handling Momentus response: {e}")
            return {
                'type': 'error',
                'message': f'Error processing response: {str(e)}'
            }
    
    def _extract_booking_confirmation(self) -> Dict[str, Any]:
        """Extract booking confirmation details from success page"""
        try:
            details = {}
            
            # Look for confirmation number
            conf_selectors = [
                "//span[contains(text(), 'Confirmation')]",
                "//div[contains(text(), 'Reference')]",
                "//*[contains(text(), 'Number')]"
            ]
            
            for selector in conf_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    details['confirmation_text'] = element.text
                    break
                except:
                    continue
            
            # Extract any visible booking details
            try:
                booking_info = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'booking') or contains(@class, 'confirmation')]")
                if booking_info:
                    details['booking_info'] = [elem.text for elem in booking_info[:5]]
            except:
                pass
            
            return details
            
        except Exception as e:
            logger.error(f"Error extracting booking confirmation: {e}")
            return {}
    
    def analyze_momentus_page(self) -> Dict[str, Any]:
        """Analyze the current Momentus page for available forms and fields"""
        try:
            if not self.driver:
                return {}
            
            logger.info("=== ANALYZING MOMENTUS PAGE ===")
            
            page_info = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'forms': [],
                'input_fields': [],
                'buttons': [],
                'links': [],
                'select_dropdowns': [],
                'date_fields': [],
                'time_fields': []
            }
            
            logger.info(f"Page Title: {page_info['title']}")
            logger.info(f"Page URL: {page_info['url']}")
            
            # Analyze forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            logger.info(f"Found {len(forms)} forms")
            
            for i, form in enumerate(forms):
                form_info = {
                    'index': i,
                    'id': form.get_attribute('id'),
                    'class': form.get_attribute('class'),
                    'action': form.get_attribute('action'),
                    'method': form.get_attribute('method')
                }
                page_info['forms'].append(form_info)
                logger.info(f"  Form {i}: ID='{form_info['id']}', Class='{form_info['class']}', Action='{form_info['action']}'")
            
            # Analyze input fields
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Found {len(inputs)} input fields")
            
            for i, inp in enumerate(inputs[:20]):  # Limit to first 20 for readability
                input_info = {
                    'index': i,
                    'type': inp.get_attribute('type'),
                    'name': inp.get_attribute('name'),
                    'id': inp.get_attribute('id'),
                    'class': inp.get_attribute('class'),
                    'placeholder': inp.get_attribute('placeholder'),
                    'value': inp.get_attribute('value')
                }
                page_info['input_fields'].append(input_info)
                
                # Categorize special field types
                if input_info['type'] == 'date':
                    page_info['date_fields'].append(input_info)
                elif input_info['type'] == 'time':
                    page_info['time_fields'].append(input_info)
                
                logger.info(f"  Input {i}: Type='{input_info['type']}', Name='{input_info['name']}', ID='{input_info['id']}', Placeholder='{input_info['placeholder']}'")
            
            # Analyze select dropdowns
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            logger.info(f"Found {len(selects)} select dropdowns")
            
            for i, select in enumerate(selects):
                select_info = {
                    'index': i,
                    'name': select.get_attribute('name'),
                    'id': select.get_attribute('id'),
                    'class': select.get_attribute('class'),
                    'options': []
                }
                
                # Get options
                options = select.find_elements(By.TAG_NAME, "option")
                for opt in options[:10]:  # Limit to first 10 options
                    select_info['options'].append({
                        'text': opt.text,
                        'value': opt.get_attribute('value')
                    })
                
                page_info['select_dropdowns'].append(select_info)
                logger.info(f"  Select {i}: Name='{select_info['name']}', ID='{select_info['id']}', Options={len(options)}")
                for opt in select_info['options'][:5]:  # Show first 5 options
                    logger.info(f"    Option: '{opt['text']}' = '{opt['value']}'")
            
            # Analyze buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"Found {len(buttons)} buttons")
            
            for i, btn in enumerate(buttons[:15]):  # Limit to first 15
                button_info = {
                    'index': i,
                    'text': btn.text.strip(),
                    'type': btn.get_attribute('type'),
                    'id': btn.get_attribute('id'),
                    'class': btn.get_attribute('class'),
                    'onclick': btn.get_attribute('onclick')
                }
                page_info['buttons'].append(button_info)
                logger.info(f"  Button {i}: Text='{button_info['text']}', Type='{button_info['type']}', ID='{button_info['id']}'")
            
            # Analyze relevant links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            relevant_links = []
            
            for link in links:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                # Filter for booking-related links
                if href and any(keyword in f"{href} {text}".lower() for keyword in ['book', 'reserv', 'room', 'calendar', 'schedule']):
                    link_info = {
                        'text': text,
                        'href': href,
                        'id': link.get_attribute('id'),
                        'class': link.get_attribute('class')
                    }
                    relevant_links.append(link_info)
            
            page_info['links'] = relevant_links[:10]  # Limit to first 10 relevant links
            logger.info(f"Found {len(relevant_links)} relevant links")
            for link in page_info['links']:
                logger.info(f"  Link: '{link['text']}' -> {link['href']}")
            
            # Look for specific Momentus patterns
            logger.info("=== LOOKING FOR MOMENTUS-SPECIFIC ELEMENTS ===")
            
            # Check for calendar/date picker elements
            calendar_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'calendar') or contains(@class, 'date') or contains(@class, 'picker')]")
            if calendar_elements:
                logger.info(f"Found {len(calendar_elements)} calendar/date elements")
            
            # Check for room/space selection elements
            room_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'room') or contains(@class, 'space') or contains(text(), 'Room') or contains(text(), 'Space')]")
            if room_elements:
                logger.info(f"Found {len(room_elements)} room/space elements")
            
            # Check for time selection elements
            time_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'time') or contains(@name, 'time') or contains(@id, 'time')]")
            if time_elements:
                logger.info(f"Found {len(time_elements)} time elements")
            
            logger.info("=== PAGE ANALYSIS COMPLETE ===")
            
            return page_info
            
        except Exception as e:
            logger.error(f"Error analyzing Momentus page: {str(e)}")
            return {}

    def _parse_search_results(self) -> List[Dict[str, Any]]:
        """Parse room search results from the page"""
        # This would contain logic to extract room information
        # from the search results page
        return []
    
    def _fill_booking_form(self, details: Dict[str, Any]):
        """Fill the room booking form with booking details"""
        # This would contain specific logic for filling Momentus booking form
        pass
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser driver closed")