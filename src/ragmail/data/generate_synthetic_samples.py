import numpy as np
import openai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
import os

# Set your OpenAI API key here
if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]
elif len(sys.argv) > 1:
    openai.api_key = sys.argv[1]
else:
    raise ValueError(
        "Please provide the OpenAI API key as an environment variable OPENAI_API_KEY or as a command line argument."
    )


def generate_email_body(topic, previous_emails=None):
    prompt = f"Write an email about {topic} in the financial domain."
    if previous_emails:
        prompt += " This email is a follow-up to previous discussions, with the most recent e-mails on the bottom:\n" + previous_emails

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response['choices'][0]['message']['content'].strip()


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


def generate_thread(topic, num_emails=3):
    sender = "sender@example.com"
    recipient = "recipient@example.com"
    subject = f"Discussion on {topic}"
    previous_body = ""
    thread = []
    base_msg_id = f"<{int(time.time())}@example.com>"

    for i in range(num_emails):
        body = generate_email_body(topic, previous_emails=previous_body)
        msg_id = base_msg_id if i == 0 else f"<{int(time.time())}-{i}@example.com>"
        in_reply_to = None if i == 0 else thread[-1]['Message-ID']
        email = create_email(sender, recipient, subject, body, msg_id=msg_id, in_reply_to=in_reply_to)
        thread.append(email)
        previous_body += f"\n\n---\n{body}"  # Append for context in next generation
        time.sleep(1)  # To vary the message IDs and mimic delay

    return thread


def save_mbox(thread, filename="emails.mbox"):
    with open(filename, "a") as mbox_file:
        for email in thread:
            mbox_file.write(email.as_string())
            mbox_file.write("\n\n")


# Example usage
if __name__ == "__main__":
    np.random.seed(0)

    # Settings
    max_thread_size = 10
    prob_per_email = 0.5
    email_threads_topics = ["investment strategies for NVIDIA"]

    for topic in email_threads_topics:
        num_emails = int(np.random.binomial(n=max_thread_size, p=prob_per_email, size=1)[0])
        thread = generate_thread(topic, num_emails=num_emails)
        save_mbox(thread, f"{topic.replace(' ', '_').lower()}.mbox")
