import os
import sys
import traceback
from tkinter.filedialog import askdirectory

import openai
from taipy.gui import Gui, State, notify

client = None

# App state
user_query = ""
data = {
    "user_query": "",
    "generated_response": "",
}
input_frozen = True
past_data = []
selected_conv = None
mail_data_path = None
show_dialog = False
dialog_success = False

def on_init(state: State) -> None:
    """
    Initialize the app.

    Args:
        - state: The current state of the app.
    """
    state.show_dialog = False
    state.user_query = ""
    state.data["user_query"] = ""
    state.data["generated_response"] = ""
    state.past_data = []
    state.input_frozen = True
    state.selected_conv = None
    state.mail_data_path = None
    state.dialog_success = False

def request(state: State) -> str:
    """
    Send a prompt to the GPT-4 API and return the response.

    Args:
        - state: The current state of the app.
        - prompt: The prompt to send to the API.

    Returns:
        The response from the API.
    """
    # response = state.client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": f"{prompt}",
    #         }
    #     ],
    #     model="gpt-4-turbo-preview",
    # )
    return state.user_query  # response.choices[0].message.content


def send_question(state: State) -> None:
    """
    Send the user's message to the API and update the context.

    Args:
        - state: The current state of the app.
    """
    notify(state, "info", "Sending message...")
    answer = request(state) #.replace("\n", "")
    data = state.data._dict.copy()
    data["user_query"] = state.user_query
    data["generated_response"] = answer
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
        "generated_response": ""
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

def select_workspace(state):
    state.show_dialog = True

    # Blocking
    while state.show_dialog:
        pass

    if state.dialog_success:
        mail_path = askdirectory(title='Select Folder')
        if type(mail_path) is str:
            state.mail_data_path = mail_path
            # We can let the user ask a question now that a path is selected
            state.input_frozen = False

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

page = """
<|{show_dialog}|title=WARNING|labels=Validate;Cancel|dialog|on_action=toggle_dialog
Are you sure you want to load the data? Even if you have data loaded, this will rebuild the database, and might take a second!
|>

<|layout|columns=300px 1|

<|part|class_name=sidebar|
# E-mai**LM**{: .color-primary} # {: .logo-text}
<|Select Mail Directory|button|class_name=fullwidth plain|id=select_workspace_button|on_action=select_workspace|>
<|part|render={mail_data_path is not None}|
*Current e-mail data directory*: <|{mail_data_path}|>
|>
### Questions ### {: .h5 .mt2 .mb-half}
<|part|render={len(past_data) > 0}|
<|{selected_conv}|tree|lov={past_data}|class_name=past_prompts_list|multiple|adapter=tree_adapter|on_change=select_conv|>
|>
|>

<|part|class_name=p2 align-item-top table scrollable|
<|navbar|lov={[("home", "Home"), ("customize", "Customize")]}|>
<|part|class_name=card mt1|
### Question ### {: .h5 .mt2 .mb-half}
<|part|render={mail_data_path is None}|
**Please choose a mail data directory before proceeding with asking questions!**
|>
<|{user_query}|input|active={not input_frozen}|label=Write your question here...|on_action=send_question|class_name=fullwidth|change_delay=-1|>
<|part|render={input_frozen and mail_data_path is not None}|
<|Ask new question|button|class_name=fullwidth plain|id=reset_app_button|on_action=reset_chat|>
|>
|>

<|part|render={data["generated_response"] != ""}|
<|part|class_name=card mt1|
### Response ### {: .h5 .mt2 .mb-half}
<|{data["generated_response"]}|>
|>

<|part|class_name=card mt1|
### Corresponding e-mails ### {: .h5 .mt2 .mb-half}
<|{data["generated_response"]}|>
|>
|>
|>

|>
"""

if __name__ == "__main__":
    if "OPENAI_API_KEY" in os.environ:
        api_key = os.environ["OPENAI_API_KEY"]
    elif len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        raise ValueError(
            "Please provide the OpenAI API key as an environment variable OPENAI_API_KEY or as a command line argument."
        )

    client = openai.Client(api_key=api_key)

    Gui(page).run(debug=True, dark_mode=True, use_reloader=True, title="📧 E-maiLM")
