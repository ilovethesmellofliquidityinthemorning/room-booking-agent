"""
Web interface module using Flask for the room booking agent
"""

from flask import Flask, render_template, request, jsonify, session
import os
from .agent import RoomBookingAgent
from .browser_automation import MomentusAutomation
from .utils import logger

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize the agent
    agent = RoomBookingAgent()
    
    @app.route('/')
    def index():
        """Main page with chat interface"""
        return render_template('index.html')
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Handle chat messages from the user"""
        try:
            data = request.get_json()
            user_message = data.get('message', '')
            
            if not user_message:
                return jsonify({'error': 'No message provided'}), 400
            
            # Process the user's request through the agent
            result = agent.process_request(user_message)
            
            if 'error' in result:
                return jsonify({'error': result['error']}), 500
            
            # For now, return a simple response
            response = agent.generate_response(result)
            
            return jsonify({
                'response': response,
                'data': result
            })
            
        except Exception as e:
            logger.error(f"Chat API error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/book', methods=['POST'])
    def book_room():
        """Handle room booking requests"""
        try:
            data = request.get_json()
            
            # Extract booking parameters
            room_id = data.get('room_id')
            booking_details = data.get('booking_details', {})
            
            if not room_id:
                return jsonify({'error': 'Room ID is required'}), 400
            
            # Initialize browser automation
            automation = MomentusAutomation(headless=True)
            
            # Login with credentials from session or environment
            username = session.get('username') or os.getenv('MOMENTUS_USERNAME')
            password = session.get('password') or os.getenv('MOMENTUS_PASSWORD')
            
            if not username or not password:
                return jsonify({'error': 'Authentication credentials required'}), 401
            
            login_success = automation.login(username, password)
            if not login_success:
                automation.close()
                return jsonify({'error': 'Failed to login to Momentus'}), 401
            
            # Attempt to book the room
            booking_success = automation.book_room(room_id, booking_details)
            automation.close()
            
            if booking_success:
                return jsonify({'success': True, 'message': 'Room booked successfully'})
            else:
                return jsonify({'error': 'Failed to book room'}), 500
                
        except Exception as e:
            logger.error(f"Booking API error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/search', methods=['POST'])
    def search_rooms():
        """Handle room search requests"""
        try:
            data = request.get_json()
            search_criteria = data.get('criteria', {})
            
            # Initialize browser automation
            automation = MomentusAutomation(headless=True)
            
            # Login
            username = session.get('username') or os.getenv('MOMENTUS_USERNAME')
            password = session.get('password') or os.getenv('MOMENTUS_PASSWORD')
            
            if not username or not password:
                return jsonify({'error': 'Authentication credentials required'}), 401
            
            login_success = automation.login(username, password)
            if not login_success:
                automation.close()
                return jsonify({'error': 'Failed to login to Momentus'}), 401
            
            # Search for rooms
            rooms = automation.search_rooms(search_criteria)
            automation.close()
            
            return jsonify({'rooms': rooms})
            
        except Exception as e:
            logger.error(f"Search API error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """Handle user login for Momentus credentials"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            # Store credentials in session (in production, use more secure storage)
            session['username'] = username
            session['password'] = password
            
            return jsonify({'success': True, 'message': 'Credentials stored'})
            
        except Exception as e:
            logger.error(f"Login API error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        """Clear stored credentials"""
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out'})
    
    return app