# Toubleshooting

We try to make the code as robust as possible, but some errors cannot be avoided completely.

## Telegram

|Title|Solution|
|---|---|
|Nothing happens in Telegram when starting the bot | A chat id is added upon receiving the "/start" command. So try the command /start in Telegram, it should be displayed in the shell of the bot|
|Telegram does not find the bot| Check that you inserted the token in a file trading_bot/etc/TELEGRAM_TOKEN ? |
|Several chats are found and no message goes out | Go in reporting/telegram_sub.py and modify the function send_to_all. Replace the for loop by a chat_id=self.chat_ids[index_of_your_choice]. |
|You don't understand why an order was not performed | Have a look in the trade log, it is there for this purpose |

