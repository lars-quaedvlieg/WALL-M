import numpy as np
import openai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
import os
import getpass
import random

from openai import OpenAI
from tqdm import tqdm

from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = getpass.getpass("Enter your OpenAI API key: ")
else:
    print("API key found in environment variables.")
client = OpenAI(
    # This is the default and can be omitted
    api_key=api_key,
)

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

def generate_email_body(topic, author, previous_emails=None):
    prompt = f"""Pretend that you are {author} Investment Research. Generate text body about {topic} in the financial domain. End with a Trade Ideas section summarizing the trade suggestions.
    Follow the following example format:

    Dear Client,

    [Introduction: Greet the client , mention your firm {author} and provide a brief overview of the email content regarding {topic}]

    Investment Opportunities/Events:
    [Highlight specific investment opportunities within the input topic. Discuss why these opportunities are attractive and how investors can benefit from them. Provide relevant data and analysis to support your claims.]

    Trading Ideas:
    [List out 5 different trading ideas with time duration, expected return and brief explanation of the rationale behind each trade.]
    
    Disclaimer:
    Any views, strategies or products discussed in this material may not be appropriate for all individuals and are subject to risks. Investors may get back less than they invested, and past performance is not a reliable indicator of future results. Asset allocation/diversification does not guarantee a profit or protect against loss. Nothing in this material should be relied upon in isolation for the purpose of making an investment decision.
    Best regards,

    {author} Investment Research
        """
    # if previous_emails:
    #     prompt += " This email is a follow-up to previous discussions, with the most recent e-mails on the bottom:\n" + previous_emails

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
        max_tokens=700,
        model="gpt-3.5-turbo",
    )

    return response.choices[0].message.content


# def generate_work_emails(prompt):

#     text = generate_reply(prompt)

#     return text


def create_email(sender, recipient, subject, body, msg_id=None, in_reply_to=None):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    if msg_id:
        message['Message-ID'] = msg_id
    if in_reply_to:
        message['In-Reply-To'] = in_reply_to
    message.attach(MIMEText(body, 'plain'))
    return message


def generate_thread(topic, sender, name, num_emails=3):

    recipient = "hackupc-test@outlook.com"
    subject = f"Discussion on {topic}"
    previous_body = ""
    thread = []
    base_msg_id = f"<{int(time.time())}@example.com>"

    for i in tqdm(range(num_emails)):
        body = generate_email_body(topic, name, previous_emails=previous_body)
        msg_id = base_msg_id if i == 0 else f"<{int(time.time())}-{i}@example.com>"
        in_reply_to = None if i == 0 else thread[-1]['Message-ID']
        email = create_email(sender, recipient, subject, body, msg_id=msg_id, in_reply_to=in_reply_to)
        thread.append(email)
        previous_body += f"\n\n---\n{body}"  # Append for context in next generation
        time.sleep(1)  # To vary the message IDs and mimic delay

    return thread


def save_mbox(thread, filename="emails.txt"):
    with open(filename, "a") as mbox_file:
        for email in thread:
            mbox_file.write(email.as_string())
            mbox_file.write("\n\n")


# Example usage
if __name__ == "__main__":
    np.random.seed(0)

    # Settings
    email_threads_topics = ["Developing Markets", "eFx", "US Equity Markets", "Fixed Income"]
    authors = ["JP Morgan", "Goldman Sachs", "Morgan Stanley", "Bank of America"]
    emails = ["jpmorgan@upc.edu", "goldmansachs@upc.edu", "morganstanley@upc.edu", "boa@upc.edu"]

    
    for j in range(len(authors)):
        for topic in enumerate(email_threads_topics):
            num_emails = 2
            thread = generate_thread(topic, emails[j], authors[j], num_emails=num_emails)
            save_mbox(thread, f"./emails/{topic.replace(' ', '_').lower()}.txt")
