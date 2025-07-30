// UT Austin Room Booking Agent JavaScript

class RoomBookingApp {
    constructor() {
        this.isLoggedIn = false;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Chat form
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleChatMessage(e));
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            this.showError('Please enter both username and password');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (response.ok) {
                this.isLoggedIn = true;
                this.showChatInterface();
                this.showSuccess('Logged in successfully! You can now book rooms.');
            } else {
                this.showError(result.error || 'Login failed');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Login error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async handleChatMessage(event) {
        event.preventDefault();
        
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessageToChat(message, 'user');
        messageInput.value = '';

        this.showLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            const result = await response.json();

            if (response.ok) {
                // Add bot response to chat
                this.addMessageToChat(result.response, 'bot');
                
                // If the response includes booking data, handle it
                if (result.data && result.data.booking_required) {
                    this.handleBookingFlow(result.data);
                }
            } else {
                this.addMessageToChat(`Error: ${result.error}`, 'bot');
            }
        } catch (error) {
            this.addMessageToChat('Sorry, I encountered an error processing your request.', 'bot');
            console.error('Chat error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('p');
        messageContent.textContent = message;
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async handleBookingFlow(bookingData) {
        // This would handle the room search and booking process
        try {
            // First, search for available rooms
            const searchResponse = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ criteria: bookingData.search_criteria })
            });

            const searchResult = await searchResponse.json();

            if (searchResponse.ok && searchResult.rooms.length > 0) {
                this.displayRoomOptions(searchResult.rooms);
            } else {
                this.addMessageToChat('Sorry, no rooms found matching your criteria.', 'bot');
            }
        } catch (error) {
            this.addMessageToChat('Error searching for rooms.', 'bot');
            console.error('Booking flow error:', error);
        }
    }

    displayRoomOptions(rooms) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        
        const intro = document.createElement('p');
        intro.textContent = `I found ${rooms.length} available room(s):`;
        messageDiv.appendChild(intro);

        rooms.forEach((room, index) => {
            const roomInfo = document.createElement('p');
            roomInfo.textContent = `${index + 1}. ${room.name} - Capacity: ${room.capacity}`;
            messageDiv.appendChild(roomInfo);

            const bookButton = document.createElement('button');
            bookButton.textContent = 'Book This Room';
            bookButton.className = 'book-room-btn';
            bookButton.onclick = () => this.bookRoom(room);
            messageDiv.appendChild(bookButton);
        });

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async bookRoom(room) {
        this.showLoading(true);

        try {
            const response = await fetch('/api/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_id: room.id,
                    booking_details: room.booking_details
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.addMessageToChat(`Great! I've successfully booked ${room.name} for you.`, 'bot');
                this.showSuccess('Room booked successfully!');
            } else {
                this.addMessageToChat(`Sorry, I couldn't book the room: ${result.error}`, 'bot');
            }
        } catch (error) {
            this.addMessageToChat('Error booking the room.', 'bot');
            console.error('Room booking error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    showChatInterface() {
        document.getElementById('authSection').style.display = 'none';
        document.getElementById('chatContainer').style.display = 'block';
    }

    showLoading(show) {
        const loadingElement = document.getElementById('loading');
        loadingElement.style.display = show ? 'block' : 'none';
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.error-message, .success-message');
        existingNotifications.forEach(notification => notification.remove());

        // Create new notification
        const notification = document.createElement('div');
        notification.className = `${type}-message`;
        notification.textContent = message;

        // Insert at the top of the container
        const container = document.querySelector('.container');
        container.insertBefore(notification, container.firstChild);

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize the app when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new RoomBookingApp();
});