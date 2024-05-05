home_page = """
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
<|navbar|on_action=on_menu|>
<|part|class_name=card mt1|
### Question ### {: .h5 .mt2 .mb-half}
<|part|render={mail_data_path is None}|
**Please choose a mail data directory before proceeding with asking questions!**
|>
<|{user_query}|input|active={not input_frozen}|label=Write your question here... (Press ENTER to submit)|on_action=send_question|class_name=fullwidth|change_delay=-1|>
<|part|render={mail_data_path is not None}|
<|{filter_dates}|date_range|>
<|{filter_names}|selector|multiple|label=Get e-mails from|lov={people_names}|dropdown|>
|>
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
<|layout|columns=1fr 3fr|
<|part|render={len(data["generated_emails_scores"]) > 0}|
<|{selected_email_id}|tree|class_name=past_prompts_list|lov={data["generated_emails_scores"]}|multiple|adapter=email_adapter|on_change=select_email|>
|>
<|{selected_email}|input|multiline|class_name=fullwidth scrollable-input|active=false|>
|>
|>

<|part|class_name=card mt1|
### Further questions? Start a conversation! ### {: .h5 .mt2 .mb-half}
<|part|class_name=p2 align-item-bottom table|
<|{conversation}|table|style=style_conv|show_all|selected={selected_row}|rebuild|>
<|part|class_name=card mt1|
<|{current_user_message}|input|label=Write your message here...|on_action=send_message|class_name=fullwidth|change_delay=-1|>
|>

|>

|>
|>

|>
"""
