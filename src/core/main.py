import os
import sys
import traceback

import openai
from taipy.gui import Gui, State, notify

client = None
user_query = ""
data = {
    "user_query": "",
    "generated_response": "",
}
input_frozen = False
past_data = []
selected_conv = None

def on_init(state: State) -> None:
    """
    Initialize the app.

    Args:
        - state: The current state of the app.
    """
    state.user_query = ""
    state.data["user_query"] = ""
    state.data["generated_response"] = ""
    state.past_data = []
    state.input_frozen = False
    state.selected_conv = None

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
    data["user_query"] += state.user_query
    data["generated_response"] += answer
    state.data = data
    notify(state, "success", "Response received!")

    state.past_data = state.past_data + [
        [len(state.past_data), state.data.copy()]
    ]
    reset_chat(state)


def on_exception(state, function_name: str, ex: Exception) -> None:
    """
    Catches exceptions and notifies user in Taipy GUI

    Args:
        state (State): Taipy GUI state
        function_name (str): Name of function where exception occured
        ex (Exception): Exception
    """
    notify(state, "error", f"An error occured in {function_name}: {ex}")


def reset_chat(state: State) -> None:
    """
    Reset the chat by clearing the conversation.

    Args:
        - state: The current state of the app.
    """
    print(f'Called with {state.data._dict}')
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
    print(var_name)
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

# For debugging
# def on_exception(state, fct_name, e):
#     notify(state, "error", f"Error in function {fct_name}: {e}")
#     print(''.join(traceback.format_exc()))

past_prompts = []

page = """
<|layout|columns=300px 1|

<|part|class_name=sidebar|
# E-mai**LM**{: .color-primary} # {: .logo-text}
<|Select Mail Directory|button|class_name=fullwidth plain|id=select_workspace_button|on_action=reset_chat|>
### Questions ### {: .h5 .mt2 .mb-half}
<|{selected_conv}|tree|lov={past_data}|class_name=past_prompts_list|multiple|adapter=tree_adapter|on_change=select_conv|>
|>

<|part|class_name=p2 align-item-top table scrollable|
<|part|class_name=card mt1|
### Question ### {: .h5 .mt2 .mb-half}
<|{user_query}|input|active={not input_frozen}|label=Write your question here...|on_action=send_question|class_name=fullwidth|change_delay=-1|>
<|part|render={input_frozen}|
<|Ask new question|button|class_name=fullwidth plain|id=reset_app_button|on_action=reset_chat|>
|>
|>

<|part|class_name=card mt1|
### Response ### {: .h5 .mt2 .mb-half}
<|{data["generated_response"]}|>
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
