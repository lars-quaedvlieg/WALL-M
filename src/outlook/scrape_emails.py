from pathlib import Path
import win32com.client  #pip install pywin32
from generate_emails import *
import json
import argparse

# Create output folder
output_dir = Path.cwd() / "Output"
output_dir.mkdir(parents=True, exist_ok=True)

# Connect to outlook
outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Scrape emails from Outlook')
parser.add_argument('--email', type=str, help='Email address to connect to Outlook', default='hackupc-test@outlook.com')
args = parser.parse_args()

# Connect to folder
inbox = outlook.Folders(args.email).Folders('Inbox')
# inbox = outlook.Folders('hackupc-test@outlook.com').Folders('Inbox')
# inbox = outlook.GetDefaultFolder(6)

# https://docs.microsoft.com/en-us/office/vba/api/outlook.oldefaultfolders
# DeletedItems=3, Outbox=4, SentMail=5, Inbox=6, Drafts=16, FolderJunk=23

# Get messages
messages = inbox.Items

list_of_messages = []

print("Scraping emails from Outlook...")

for message in messages:
    subject = message.Subject
    body = message.body
    # attachments = message.Attachments
    recipients = message.Recipients
    sender = message.Sender
    date = message.SentOn
    entry_id = message.EntryID
    # Create separate folder for each message, exclude special characters and timestampe

    msg = dict()
    msg["subject"] = getattr(message, "Subject", "<UNKNOWN>")
    msg["recipient"] = [r.Name for r in message.Recipients]
    
    msg["email_date"] = getattr(message, "SentOn", "<UNKNOWN>")
    msg["email_id"] = getattr(message, "EntryID", "<UNKNOWN>")
    msg["sender"] = getattr(message, "Sender", "<UNKNOWN>")
    #msg["Size"] = getattr(message, "Size", "<UNKNOWN>")
    msg["text"] = getattr(message, "Body", "<UNKNOWN>")

    list_of_messages.append(msg)

print("Emails scraped from Outlook")

with open(f"./data/emails/emails_{args.email}.json", "w") as f:
    json.dump(list_of_messages, f, indent=4, default=str)

print("Emails saved to emails.json")