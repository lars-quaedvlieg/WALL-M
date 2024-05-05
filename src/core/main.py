import os
import sys
from tkinter.filedialog import askdirectory

import openai
from dotenv import load_dotenv
from taipy.gui import Gui, State, notify, navigate

from src.core.page_markdowns.customize import customize_page
from src.core.page_markdowns.home import home_page
from src.ragmail.build_database import create_db, table_exists
from src.ragmail.query import get_senders, query, get_response, get_db_summary

TABLE_NAME = "ShazList10"

client = None

# App state
user_query = ""
start_date = ""
end_date = ""
data = {
    "user_query": "",
    "filter_names": [],
    "start_date": "",
    "end_date": "",
    "generated_response": "",
    "generated_emails_scores": "",
}
input_frozen = True
past_data = []
selected_conv = None
mail_data_path = None
show_dialog = False
dialog_success = False
selected_email = None
selected_email_id = None
logo_image = None
filter_names = None
people_names = None
table_name = None
dataset_samples = None
# TODO: Add table name

conversation = []
conversation_table = {"Conversation": []}
selected_row = [1]
current_user_message = ""

def on_init(state: State) -> None:
    """
    Initialize the app.

    Args:
        - state: The current state of the app.
    """
    state.logo_image = os.path.join(os.getcwd(), "res", "logo.png")
    state.show_dialog = False
    state.user_query = ""
    state.start_date = ""
    state.end_date = ""
    state.data["user_query"] = ""
    state.data["generated_response"] = ""
    state.data["generated_emails_scores"] = ""
    state.data["start_date"] = ""
    state.data["end_date"] = ""
    state.data["filter_names"] = []
    state.past_data = []
    state.input_frozen = True
    state.selected_conv = None
    state.mail_data_path = None
    state.dialog_success = False
    state.selected_email = None
    state.selected_email_id = None
    state.people_names = []
    state.table_name = None
    state.dataset_samples = {}

def request(state: State) -> tuple[str, list[tuple[str, float]]]:
    try:
        response, emails_scores = query(
            table_name=state.table_name,
            prompt=state.user_query,
            filters={
                "people_filter": state.filter_names,
                "dates_filter": [state.start_date, state.end_date],
            }
        )
        state.conversation.append(response)
        return response, emails_scores
    except FileNotFoundError:
        notify(state, "error", "No match was found with the provided question settings.")
        raise Exception()

def send_question(state: State) -> None:
    """
    Send the user's message to the API and update the context.

    Args:
        - state: The current state of the app.
    """
    notify(state, "info", "Sending message...")
    response, emails_scores = request(state) #.replace("\n", "")
    data = state.data._dict.copy()
    data["user_query"] = state.user_query
    data["start_date"] = state.end_date
    data["end_date"] = state.start_date
    data["filter_names"] = state.filter_names
    data["generated_response"] = response
    data["generated_emails_scores"] = [(i, email_score) for i, email_score in enumerate(emails_scores)]
    state.data = data
    notify(state, "success", "Response received!")

    state.past_data = state.past_data + [
        [len(state.past_data), state.data.copy()]
    ]
    reset_chat(state)


def reset_chat(state: State) -> None:
    """
    Reset the chat by clearing the conversation.

    Args:
        - state: The current state of the app.
    """
    state.user_query = ""
    state.data = {
        "user_query": "",
        "filter_names": [],
        "datetime_ranges": [],
        "generated_response": "",
        "generated_emails_scores": "",
    }
    state.input_frozen = False
    state.selected_conv = None

def tree_adapter(item: list) -> [str, str]:
    """
    Converts element of past_conversations to id and displayed string

    Args:
        item: element of past_conversations

    Returns:
        id and displayed string
    """
    chat_id = item[0]
    user_msg = item[1]["user_query"]
    if len(user_msg) > 0:
        return (chat_id, user_msg[:20] + "..." if len(user_msg) > 20 else user_msg)
    return (chat_id, "Empty conversation")


def select_conv(state: State, var_name: str, value) -> None:
    """
    Selects conversation from past_conversations

    Args:
        state: The current state of the app.
        var_name: "selected_conv"
        value: [[id, conversation]]
    """
    state.input_frozen = True
    state.user_query = state.past_data[value[0][0]][1]["user_query"]
    state.data = state.past_data[value[0][0]][1]
    # Reset the information for the individual e-mails
    state.selected_email_id = None
    state.selected_email = None

def email_adapter(item: list) -> [str, str]:
    """
    Converts element of past_conversations to id and displayed string

    Args:
        item: element of past_conversations

    Returns:
        id and displayed string
    """
    email_id = item[0]
    score = f"{item[1][0][:30] + '...' if len(item[1][0]) > 30 else item[1][0]}"
    return email_id, score

def select_email(state: State, var_name: str, value) -> None:
    """
    Selects conversation from past_conversations

    Args:
        state: The current state of the app.
        var_name: "selected_conv"
        value: [[id, conversation]]
    """
    state.selected_email = state.data["generated_emails_scores"][value[0][0]][1][0]

    
def style_conv(state: State, idx: int, row: int) -> str:
    """
    Apply a style to the conversation table depending on the message's author.

    Args:
        - state: The current state of the app.
        - idx: The index of the message in the table.
        - row: The row of the message in the table.

    Returns:
        The style to apply to the message.
    """
    if idx is None:
        return None
    elif idx % 2 == 0:
        return "user_message"
    else:
        return "gpt_message"


def ask_the_gpt(state: State) -> str:
    def get_true_context(old_context: str) -> str:
        return "\n\n".join(old_context.split("\n\n")[1:])

    state.conversation.append(state.current_user_message)
    print("Contexts", state.data["generated_emails_scores"])
    contexts = [get_true_context(email)
                for _, (email, _) in state.data["generated_emails_scores"]]
    answer = get_response(state.data["user_query"], contexts,
                          new_messages=state.conversation)
    state.conversation.append(answer)
    state.selected_row = [len(state.conversation_table["Conversation"]) + 1]
    return answer


def send_message(state: State) -> None:
    """
    Send the user's message to the API and update the context.

    Args:
        - state: The current state of the app.
    """
    notify(state, "info", "Sending message...")
    answer = ask_the_gpt(state)
    state.conversation_table["Conversation"] += [state.current_user_message, answer]
    state.current_user_message = ""
    notify(state, "success", "Response received!")

def select_workspace(state):
    state.show_dialog = True

    # Blocking
    while state.show_dialog:
        pass

    if state.dialog_success:
        mail_path = askdirectory(title='Select Folder')
        if type(mail_path) is str:
            notify(state, "info", "Creating the database...")
            state.mail_data_path = mail_path

            # Create database
            state.table_name = TABLE_NAME
            if not table_exists(state.table_name):
                create_db(data_path=state.mail_data_path, table_name=state.table_name)

            # We can let the user ask a question now that a path is selected
            state.input_frozen = False

            # We can now get a list of people's names that we have e-mails from
            state.people_names = list(get_senders(table_name=state.table_name))

            # Create the sample dictionary for the example page
            state.dataset_samples = get_db_summary(state.table_name)

            notify(state, "success", "Created the database!")


# For debugging
# def on_exception(state, fct_name, e):
#     notify(state, "error", f"Error in function {fct_name}: {e}")
#     print(''.join(traceback.format_exc()))

past_prompts = []

def toggle_dialog(state, identifier, payload):
    state.show_dialog = False
    if payload["args"][0] in {-1, 1}:
        state.dialog_success = False
    else:
        state.dialog_success = True


def on_menu(state, action, info):
    page = info["args"][0]
    navigate(state, to=page)


pages = {
    "home": home_page,
    "dataviewer": customize_page,
}

if __name__ == "__main__":
    load_dotenv()
    if "OPENAI_API_KEY" in os.environ:
        api_key = os.environ["OPENAI_API_KEY"]
    elif len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        raise ValueError(
            "Please provide the OpenAI API key as an environment variable OPENAI_API_KEY or as a command line argument."
        )

    client = openai.Client(api_key=api_key)

    Gui(pages=pages).run(debug=True, dark_mode=True, use_reloader=True, title="E-maiLM")
