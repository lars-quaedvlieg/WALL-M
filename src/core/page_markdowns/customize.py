customize_page = """
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
|>

<|part|class_name=p2 align-item-top table scrollable|
<|navbar|on_action=on_menu|>
<|part|render={mail_data_path is not None}|
<|{dataset_samples}|table|>
|>
|>

|>
"""