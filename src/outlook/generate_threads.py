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
    max_tokens=300,
    model="gpt-3.5-turbo",
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # List of friends/acquaintances
    
    tasks = ["frontend", "business development", "scheduling meetings"]

    prompt = "Imagine that you work in a startup and there are many different projects at hand. Task related to {task}. Generate a sequence of mails enacting such a situation between the employees of the startup. Keep the mails brief and unstructured"

    text = generate_reply(prompt.format(task=random.choice(tasks)))

    print(text)

