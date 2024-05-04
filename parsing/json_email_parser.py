from pathlib import Path
import os
import json
from typing import Optional
from .email_parser import EmailParser
from pandas import DataFrame

class JsonEmailParser(EmailParser):

    def parse(self) -> Optional[DataFrame]:

        email_files = [os.path.join(self.folder_path, f) for f in os.listdir(self.folder_path) if f.endswith('.json')]

        if len(email_files) <= 0:
            print("No json emails found in directory")
            return None

        emails = []

        for thread_id, file in enumerate(email_files):

            try:
                with open(file) as f:
                    email_thread = json.load(f)

                for email_id, email in enumerate(email_thread):
                    email['thread_id'] = thread_id
                    email['email_id'] = email_id
                    emails.append(email)

            except Exception as e:
                print(f"An error occurred: {e}")

        return DataFrame(emails)
