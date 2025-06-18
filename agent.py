import os
import openai
from dotenv import load_dotenv

# Load your OpenAI key from the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt user for booking input
user_input = input("Enter your room booking request:\n")

# Create the system + user messages
messages = [
    {"role": "system", "content": "You're a scheduling assistant. Extract structured information from natural language."},
    {"role": "user", "content": f"Extract date, time, event type, estimated attendance, and whether food will be served from this input: '{user_input}'"}
]

# Ask GPT
response = openai.ChatCompletion.create(
    model="gpt-4",  # use gpt-3.5-turbo if you're on that plan
    messages=messages,
    temperature=0.2
)

# Show results
print("\nParsed Details:")
print(response["choices"][0]["message"]["content"])
