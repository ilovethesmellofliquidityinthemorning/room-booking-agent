# UT Austin Room Booking Agent

An intelligent room booking agent that automates the process of booking rooms through the Momentus system using natural language processing.

## Features

- **Natural Language Processing**: Describe your room booking needs in plain English
- **Automated Booking**: Automatically searches and books rooms through the Momentus system
- **Web Interface**: Clean, user-friendly web interface for interaction
- **Intelligent Parsing**: Extracts booking requirements from natural language input
- **Room Search**: Finds available rooms based on your criteria
- **Booking History**: Tracks your booking history

## Project Structure

```
room-booking-agent/
├── main.py                    # Application entry point
├── app/                       # Main application package
│   ├── __init__.py
│   ├── agent.py              # AI agent for processing requests
│   ├── browser_automation.py # Selenium automation for Momentus
│   ├── web_interface.py      # Flask web interface
│   └── utils.py              # Utility functions and helpers
├── templates/                 # HTML templates
│   └── index.html
├── static/                    # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser (for Selenium automation)
- OpenAI API key
- UT Austin Momentus account credentials

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd room-booking-agent
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv room-booking-env

# Activate virtual environment
# On Windows:
room-booking-env\Scripts\activate
# On macOS/Linux:
source room-booking-env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Chrome WebDriver

The application uses Selenium with Chrome. You can either:

**Option A: Use webdriver-manager (Recommended)**
The application will automatically download the appropriate ChromeDriver.

**Option B: Manual Installation**
1. Download ChromeDriver from https://chromedriver.chromium.org/
2. Add the ChromeDriver executable to your PATH or specify the path in your .env file

### 5. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual values
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `MOMENTUS_USERNAME`: Your UT Austin Momentus username
- `MOMENTUS_PASSWORD`: Your UT Austin Momentus password
- `SECRET_KEY`: A secure secret key for Flask sessions

## Configuration

Edit the `.env` file with your specific configuration:

```env
OPENAI_API_KEY=your_openai_api_key_here
MOMENTUS_BASE_URL=https://utexas.momentus.io/
MOMENTUS_USERNAME=your_momentus_username
MOMENTUS_PASSWORD=your_momentus_password
SECRET_KEY=your_secret_key_for_flask_sessions
DEBUG=False
PORT=5000
LOG_LEVEL=INFO
```

## Usage

### 1. Start the Application

```bash
python main.py
```

The application will start on `http://localhost:5000` (or the port specified in your .env file).

### 2. Access the Web Interface

1. Open your web browser and navigate to `http://localhost:5000`
2. Enter your Momentus credentials to log in
3. Start describing your room booking needs in natural language

### 3. Example Requests

You can make requests like:

- "I need a conference room for 10 people tomorrow at 2 PM for 2 hours"
- "Book a study room for 4 people next Monday from 10 AM to 12 PM"
- "Find a large meeting room with a projector for Friday afternoon"
- "I need a room for a presentation next week, around 50 people"

## API Endpoints

### POST `/api/login`
Login with Momentus credentials.

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

### POST `/api/chat`
Process natural language booking requests.

**Request:**
```json
{
  "message": "I need a conference room for 10 people tomorrow at 2 PM"
}
```

### POST `/api/search`
Search for available rooms.

**Request:**
```json
{
  "criteria": {
    "date": "2024-01-15",
    "start_time": "14:00",
    "end_time": "16:00",
    "capacity": 10
  }
}
```

### POST `/api/book`
Book a specific room.

**Request:**
```json
{
  "room_id": "room_123",
  "booking_details": {
    "date": "2024-01-15",
    "start_time": "14:00",
    "end_time": "16:00",
    "purpose": "Team meeting"
  }
}
```

## Development

### Running in Development Mode

Set `DEBUG=True` in your `.env` file and run:

```bash
python main.py
```

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting

```bash
# Format code
black .

# Lint code
flake8 .
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   - Ensure Chrome browser is installed
   - Check that ChromeDriver version matches your Chrome version
   - Try setting `CHROME_DRIVER_PATH` in your .env file

2. **OpenAI API Errors**
   - Verify your API key is correct and has sufficient credits
   - Check your OpenAI usage limits

3. **Momentus Login Issues**
   - Verify your credentials are correct
   - Check if Momentus requires 2FA (may need additional implementation)
   - Ensure the base URL is correct

4. **Port Already in Use**
   - Change the `PORT` value in your .env file
   - Or kill the process using the port: `lsof -ti:5000 | xargs kill -9`

### Logs

Application logs are written to `room_booking_agent.log`. Check this file for detailed error information.

## Security Considerations

- Never commit your `.env` file with real credentials
- Use strong, unique secret keys
- Consider using environment-specific configurations
- Regularly rotate API keys and passwords
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and internal use at UT Austin.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue in the repository