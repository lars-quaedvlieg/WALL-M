import numpy as np
import openai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
import os
import getpass

from openai import OpenAI
from tqdm import tqdm
import json
from dotenv import load_dotenv
import random

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    api_key = getpass.getpass("Enter your OpenAI API key: ")
else:
    print("API key found in environment variables.")

client = OpenAI(api_key=api_key)
input_dir = "Input/"

# Function to generate a reply based on the prompt
def generate_reply(prompt):

    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "/restart",
        },
        {
            "role": "user",
            "content": f"{prompt}",
        }
    ],
    max_tokens=150,
    model="gpt-3.5-turbo",
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # List of friends/acquaintances
    participants = ["Alice", "Bob", "Charlie"]


    # Initial prompt to start the conversation
    initial_prompt = "You are having a casual conversation with your friend, Friend 1. Start the conversation."

    # Generate the conversation
    conversation = []

    # First message from Friend 1
    friend1_message = initial_prompt
    friend2_message = generate_reply(friend1_message)
    conversation.append({"Friend 1": friend1_message, "Friend 2": friend2_message})

    # Generate replies in the conversation
    for _ in range(5):  # Number of messages in the conversation
        friend1_message = generate_reply(friend2_message)
        friend2_message = generate_reply(friend1_message)
        conversation.append({"Friend 1": friend1_message, "Friend 2": friend2_message})

    # Convert conversation to JSON format
    conversation_json = json.dumps(conversation, indent=4)
    
    with open("threads.json", "w") as outfile:
        outfile.write(conversation_json)


    # Print the JSON conversation
    print(conversation_json)

