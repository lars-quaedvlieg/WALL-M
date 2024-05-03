import openai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

# Set your OpenAI API key here
openai.api_key = 'your-api-key'


def generate_email_body(topic, previous_emails=None):
    prompt = f"Write an email about {topic} in the financial domain."
    if previous_emails:
        prompt += " This email is a follow-up to previous discussions:\n" + previous_emails
    # response = openai.Completion.create(
    #     engine="text-davinci-003",
    #     prompt=prompt,
    #     max_tokens=500,
    #     temperature=0.7,
    #     top_p=1,
    #     frequency_penalty=0,
    #     presence_penalty=0
    # )
    return f"hello world! {0 if previous_emails is None else len(previous_emails)}" # response.choices[0].text.strip()


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
    topic = "investment strategies"
    thread = generate_thread(topic, num_emails=5)
    save_mbox(thread, "financial_emails.mbox")
