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

def generate_email_body(topic, author, previous_emails=None):
    prompt = f"""Pretend that you are {author} Investment Research. Generate text body about {topic} in the financial domain. End with a Trade Ideas section summarizing the trade suggestions.
    Follow the following example format:

    Dear Client,

    [Introduction: Greet the client , mention your firm {author} and provide a brief overview of the email content regarding {topic}]

    Market Overview:
    [Provide a brief overview of the current market conditions related to the input topic. Discuss key trends, recent developments, and any pertinent news that could impact investment decisions.]

    Investment Opportunities/Events:
    [Highlight specific investment opportunities within the input topic. Discuss why these opportunities are attractive and how investors can benefit from them. Provide relevant data and analysis to support your claims.]

    Trading Ideas:
    [List out the trading ideas with a brief explanation of the rationale behind each trade..]
    
    Disclaimer:
    [Discuss any potential risks associated with the trading ideas mentioned above. Highlight factors that investors should be aware of and consider before implementing any trades.]

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
        max_tokens=500,
        model="gpt-3.5-turbo",
    )

    return response.choices[0].message.content


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
