# Copyright (c) 2021-2023 Oleg Polakow. All rights reserved.

"""Messaging using Python Telegram Bot."""

from vectorbtpro.utils.module_ import assert_can_import

assert_can_import("telegram")

import logging
from functools import wraps

from vectorbtpro import _typing as tp
from vectorbtpro.utils.config import merge_dicts, Configured
from vectorbtpro.utils.parsing import get_func_kwargs
from vectorbtpro.utils.requests_ import text_to_giphy_url

__all__ = [
    "TelegramBot",
]

logger = logging.getLogger(__name__)


def send_action(action: str) -> tp.Callable:
    """Sends `action` while processing func command.

    Suitable only for bound callbacks taking arguments `self`, `update`, `context` and optionally other."""

    def decorator(func: tp.Callable) -> tp.Callable:
        @wraps(func)
        def command_func(self, update: Update, context: CallbackContext, *args, **kwargs) -> tp.Callable:
            if update.effective_chat:
                context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)
            return func(self, update, context, *args, **kwargs)

        return command_func

    return decorator


def self_decorator(self, func: tp.Callable) -> tp.Callable:
    """Pass bot object to func command."""

    def command_func(update, context, *args, **kwargs):
        return func(self, update, context, *args, **kwargs)

    return command_func


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    from telegram import Update
    from telegram.error import Unauthorized, ChatMigrated
    from telegram.ext import (
        Handler,
        CallbackContext,
        Updater,
        Dispatcher,
        CommandHandler,
        MessageHandler,
        Filters,
        PicklePersistence,
        Defaults,
    )
    from telegram.utils.helpers import effective_message_type

    class LogHandler(Handler):
        """Handler to log user updates."""

        def check_update(self, update: object) -> tp.Optional[tp.Union[bool, object]]:
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message
                message_type = effective_message_type(message)
                if message_type is not None:
                    if message_type == "text":
                        logger.info(f'{message.chat_id} - User: "%s"', message.text)
                    else:
                        logger.info(f"{message.chat_id} - User: %s", message_type)
                return False
            return None

    class TelegramBot(Configured):
        """Telegram bot.

        See [Extensions – Your first Bot](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot).

        `**kwargs` are passed to `telegram.ext.updater.Updater` and override
        settings under `telegram` in `vectorbtpro._settings.messaging`.

        Usage:
            Let's extend `TelegramBot` to track cryptocurrency prices:

            ```python
            import ccxt
            import logging
            import vectorbtpro as vbt

            from telegram.ext import CommandHandler
            from telegram import __version__ as TG_VER

            try:
                from telegram import __version_info__
            except ImportError:
                __version_info__ = (0, 0, 0, 0, 0)

            if __version_info__ >= (20, 0, 0, "alpha", 1):
                raise RuntimeError(f"This example is not compatible with your current PTB version {TG_VER}")

            # Enable logging
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
            )
            logger = logging.getLogger(__name__)


            class MyTelegramBot(vbt.TelegramBot):
                @property
                def custom_handlers(self):
                    return (CommandHandler('get', self.get),)

                @property
                def help_message(self):
                    return "Type /get [symbol] [exchange id (optional)] to get the latest price."

                def get(self, update, context):
                    chat_id = update.effective_chat.id

                    if len(context.args) == 1:
                        symbol = context.args[0]
                        exchange = 'binance'
                    elif len(context.args) == 2:
                        symbol = context.args[0]
                        exchange = context.args[1]
                    else:
                        self.send_message(chat_id, "This command requires symbol and optionally exchange id.")
                        return
                    try:
                        ticker = getattr(ccxt, exchange)().fetchTicker(symbol)
                    except Exception as e:
                        self.send_message(chat_id, str(e))
                        return
                    self.send_message(chat_id, str(ticker['last']))


            if __name__ == "__main__":
                bot = MyTelegramBot(token='1628351231:AAEgvZyRRfOV4_6ZArMS_lXzZd6XkG932zg')
                bot.start()
            ```
        """

        def __init__(self, giphy_kwargs: tp.KwargsLike = None, **kwargs) -> None:
            from vectorbtpro._settings import settings

            telegram_cfg = settings["messaging"]["telegram"]
            giphy_cfg = settings["messaging"]["giphy"]

            Configured.__init__(self, giphy_kwargs=giphy_kwargs, **kwargs)

            # Resolve kwargs
            giphy_kwargs = merge_dicts(giphy_cfg, giphy_kwargs)
            self.giphy_kwargs = giphy_kwargs
            default_kwargs = dict()
            passed_kwargs = dict()
            for k in get_func_kwargs(Updater.__init__):
                if k in telegram_cfg:
                    default_kwargs[k] = telegram_cfg[k]
                if k in kwargs:
                    passed_kwargs[k] = kwargs.pop(k)
            updater_kwargs = merge_dicts(default_kwargs, passed_kwargs)
            persistence = updater_kwargs.pop("persistence", None)
            if persistence is not None:
                if isinstance(persistence, bool):
                    if persistence:
                        persistence = "telegram_bot.pickle"
                    else:
                        persistence = None
                if persistence is not None:
                    if isinstance(persistence, str):
                        persistence = PicklePersistence(persistence)
            defaults = updater_kwargs.pop("defaults", None)
            if defaults is not None:
                if isinstance(defaults, dict):
                    defaults = Defaults(**defaults)

            # Create the (persistent) Updater and pass it your bot's token.
            logger.info("Initializing bot")
            self._updater = Updater(persistence=persistence, defaults=defaults, **updater_kwargs)

            # Get the dispatcher to register handlers
            self._dispatcher = self.updater.dispatcher

            # Register handlers
            self.dispatcher.add_handler(self.log_handler)
            self.dispatcher.add_handler(CommandHandler("start", self.start_callback))
            self.dispatcher.add_handler(CommandHandler("help", self.help_callback))
            for handler in self.custom_handlers:
                self.dispatcher.add_handler(handler)
            self.dispatcher.add_handler(MessageHandler(Filters.status_update.migrate, self.chat_migration_callback))
            self.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown_callback))
            self.dispatcher.add_error_handler(self_decorator(self, type(self).error_callback))

            # Set up data
            if "chat_ids" not in self.dispatcher.bot_data:
                self.dispatcher.bot_data["chat_ids"] = []
            else:
                logger.info("Loaded chat ids %s", str(self.dispatcher.bot_data["chat_ids"]))

        @property
        def updater(self) -> Updater:
            """Updater."""
            return self._updater

        @property
        def dispatcher(self) -> Dispatcher:
            """Dispatcher."""
            return self._dispatcher

        @property
        def log_handler(self) -> LogHandler:
            """Log handler."""
            return LogHandler(lambda update, context: None)

        @property
        def custom_handlers(self) -> tp.Iterable[Handler]:
            """Custom handlers to add.
            Override to add custom handlers. Order counts."""
            return ()

        @property
        def chat_ids(self) -> tp.List[int]:
            """Chat ids that ever interacted with this bot.
            A chat id is added upon receiving the "/start" command."""
            return self.dispatcher.bot_data["chat_ids"]

        def start(self, in_background: bool = False, **kwargs) -> None:
            """Start the bot.
            `**kwargs` are passed to `telegram.ext.updater.Updater.start_polling`
            and override settings under `telegram` in `vectorbtpro._settings.messaging`."""
            from vectorbtpro._settings import settings

            telegram_cfg = settings["messaging"]["telegram"]

            # Resolve kwargs
            default_kwargs = dict()
            passed_kwargs = dict()
            for k in get_func_kwargs(self.updater.start_polling):
                if k in telegram_cfg:
                    default_kwargs[k] = telegram_cfg[k]
                if k in kwargs:
                    passed_kwargs[k] = kwargs.pop(k)
            polling_kwargs = merge_dicts(default_kwargs, passed_kwargs)

            # Start the Bot
            logger.info("Running bot %s", str(self.updater.bot.get_me().username))
            self.updater.start_polling(**polling_kwargs)
            self.started_callback()

            if not in_background:
                # Run the bot until you press Ctrl-C or the process receives SIGINT,
                # SIGTERM or SIGABRT. This should be used most of the time, since
                # start_polling() is non-blocking and will stop the bot gracefully.
                self.updater.idle()

        def started_callback(self) -> None:
            """Callback once the bot has been started.
            Override to execute custom commands upon starting the bot."""
            self.send_message_to_all("I'm back online!")

        def send(self, kind: str, chat_id: int, *args, log_msg: tp.Optional[str] = None, **kwargs) -> None:
            """Send message of any kind to `chat_id`."""
            try:
                getattr(self.updater.bot, "send_" + kind)(chat_id, *args, **kwargs)
                if log_msg is None:
                    log_msg = kind
                logger.info(f"{chat_id} - Bot: %s", log_msg)
            except ChatMigrated as e:
                # transfer data, if old data is still present
                new_id = e.new_chat_id
                if chat_id in self.chat_ids:
                    self.chat_ids.remove(chat_id)
                self.chat_ids.append(new_id)
                # Resend to new chat id
                self.send(kind, new_id, *args, log_msg=log_msg, **kwargs)
            except Unauthorized as e:
                logger.info(f"{chat_id} - Unauthorized to send the %s", kind)

        def send_to_all(self, kind: str, *args, **kwargs) -> None:
            """Send message of any kind to all in `TelegramBot.chat_ids`."""
            for chat_id in self.chat_ids:
                self.send(kind, chat_id, *args, **kwargs)

        def send_message(self, chat_id: int, text: str, *args, **kwargs) -> None:
            """Send text message to `chat_id`."""
            log_msg = '"%s"' % text
            self.send("message", chat_id, text, *args, log_msg=log_msg, **kwargs)

        def send_message_to_all(self, text: str, *args, **kwargs) -> None:
            """Send text message to all in `TelegramBot.chat_ids`."""
            log_msg = '"%s"' % text
            self.send_to_all("message", text, *args, log_msg=log_msg, **kwargs)

        def send_giphy(self, chat_id: int, text: str, *args, giphy_kwargs: tp.KwargsLike = None, **kwargs) -> None:
            """Send GIPHY from text to `chat_id`."""
            if giphy_kwargs is None:
                giphy_kwargs = self.giphy_kwargs
            gif_url = text_to_giphy_url(text, **giphy_kwargs)
            log_msg = '"%s" as GIPHY %s' % (text, gif_url)
            self.send("animation", chat_id, gif_url, *args, log_msg=log_msg, **kwargs)

        def send_giphy_to_all(self, text: str, *args, giphy_kwargs: tp.KwargsLike = None, **kwargs) -> None:
            """Send GIPHY from text to all in `TelegramBot.chat_ids`."""
            if giphy_kwargs is None:
                giphy_kwargs = self.giphy_kwargs
            gif_url = text_to_giphy_url(text, **giphy_kwargs)
            log_msg = '"%s" as GIPHY %s' % (text, gif_url)
            self.send_to_all("animation", gif_url, *args, log_msg=log_msg, **kwargs)

        @property
        def start_message(self) -> str:
            """Message to be sent upon "/start" command.
            Override to define your own message."""
            return "Hello!"

        def start_callback(self, update: object, context: CallbackContext) -> None:
            """Start command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                if chat_id not in self.chat_ids:
                    self.chat_ids.append(chat_id)
                self.send_message(chat_id, self.start_message)

        @property
        def help_message(self) -> str:
            """Message to be sent upon "/help" command.
            Override to define your own message."""
            return "Can't help you here, buddy."

        def help_callback(self, update: object, context: CallbackContext) -> None:
            """Help command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                self.send_message(chat_id, self.help_message)

        def chat_migration_callback(self, update: object, context: CallbackContext) -> None:
            """Chat migration callback."""
            if isinstance(update, Update) and update.message:
                old_id = update.message.migrate_from_chat_id or update.message.chat_id
                new_id = update.message.migrate_to_chat_id or update.message.chat_id
                if old_id in self.chat_ids:
                    self.chat_ids.remove(old_id)
                self.chat_ids.append(new_id)
                logger.info(f"{old_id} - Chat migrated to {new_id}")

        def unknown_callback(self, update: object, context: CallbackContext) -> None:
            """Unknown command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                logger.info(f'{chat_id} - Unknown command "{update.message}"')
                self.send_message(chat_id, "Sorry, I didn't understand that command.")

        def error_callback(self, update: object, context: CallbackContext, *args) -> None:
            """Error callback."""
            logger.error('Exception while handling an update "%s": ', update, exc_info=context.error)
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                self.send_message(chat_id, "Sorry, an error happened.")

        def stop(self) -> None:
            """Stop the bot."""
            logger.info("Stopping bot")
            self.updater.stop()

        @property
        def running(self) -> bool:
            """Whether the bot is running."""
            return self.updater.running

else:
    import asyncio
    import platform
    import signal
    import warnings
    import threading

    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        Application,
        Defaults,
        PicklePersistence,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        BaseHandler,
        filters,
    )
    from telegram.error import TelegramError, ChatMigrated, Forbidden
    from telegram.helpers import effective_message_type
    from telegram.request import BaseRequest

    class LogHandler(BaseHandler):
        """Handler to log user updates."""

        def check_update(self, update: object) -> tp.Optional[tp.Union[bool, object]]:
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message
                message_type = effective_message_type(message)
                if message_type is not None:
                    if message_type == "text":
                        logger.info(f'{message.chat_id} - User: "%s"', message.text)
                    else:
                        logger.info(f"{message.chat_id} - User: %s", message_type)
                return False
            return None

    class TelegramBot(Configured):
        """Telegram bot.

        See [Extensions – Your first Bot](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-Your-first-Bot).

        Keyword arguments are passed to `TelegramBot.build_application`.

        !!! note
            If you get "RuntimeError: Cannot close a running event loop" when running in Jupyter,
            you might need to patch `asyncio` using https://github.com/erdewit/nest_asyncio, like this
            (right before `bot.start()` in each new runtime)

            ```pycon
            >>> !pip install nest_asyncio
            >>> import nest_asyncio
            >>> nest_asyncio.apply()
            ```

        Usage:
            Let's extend `TelegramBot` to track cryptocurrency prices, as a Python script:

            ```python
            import ccxt
            import logging
            import vectorbtpro as vbt

            from telegram.ext import CommandHandler
            from telegram import __version__ as TG_VER

            try:
                from telegram import __version_info__
            except ImportError:
                __version_info__ = (0, 0, 0, 0, 0)

            if __version_info__ < (20, 0, 0, "alpha", 1):
                raise RuntimeError(f"This example is not compatible with your current PTB version {TG_VER}")

            # Enable logging
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
            )
            logger = logging.getLogger(__name__)


            class MyTelegramBot(vbt.TelegramBot):
                @property
                def custom_handlers(self):
                    return (CommandHandler('get', self.get),)

                @property
                def help_message(self):
                    return "Type /get [symbol] [exchange id (optional)] to get the latest price."

                async def get(self, update, context):
                    chat_id = update.effective_chat.id

                    if len(context.args) == 1:
                        symbol = context.args[0]
                        exchange = 'binance'
                    elif len(context.args) == 2:
                        symbol = context.args[0]
                        exchange = context.args[1]
                    else:
                        await self.send_message(chat_id, "This command requires symbol and optionally exchange id.")
                        return
                    try:
                        ticker = getattr(ccxt, exchange)().fetchTicker(symbol)
                    except Exception as e:
                        await self.send_message(chat_id, str(e))
                        return
                    await self.send_message(chat_id, str(ticker['last']))


            if __name__ == "__main__":
                bot = MyTelegramBot(token='YOUR_TOKEN')
                bot.start()
            ```
        """

        def __init__(self, giphy_kwargs: tp.KwargsLike = None, **kwargs) -> None:
            from vectorbtpro._settings import settings

            giphy_cfg = settings["messaging"]["giphy"]

            Configured.__init__(self, giphy_kwargs=giphy_kwargs, **kwargs)

            giphy_kwargs = merge_dicts(giphy_cfg, giphy_kwargs)
            self._giphy_kwargs = giphy_kwargs
            self._application = self.build_application(**kwargs)
            self.register_handlers()
            self._loop = None

        def build_application(self, **kwargs) -> Application:
            """Build application.

            `**kwargs` override settings under `telegram` in `vectorbtpro._settings.messaging`
            and those keys that can be found as attributes of `telegram.ext._applicationbuilder.ApplicationBuilder`
            will be called on the builder. If any value is a dict, it will be unpacked to be able to
            provide multiple keyword arguments to any method (apart from `defaults`, which is just one argument)."""
            from vectorbtpro._settings import settings

            telegram_cfg = dict(settings["messaging"]["telegram"])
            telegram_cfg = merge_dicts(telegram_cfg, kwargs)

            builder = ApplicationBuilder()

            persistence = telegram_cfg.pop("persistence", None)
            if persistence is not None:
                if isinstance(persistence, bool):
                    if persistence:
                        persistence = "telegram_bot.pickle"
                    else:
                        persistence = None
                if persistence is not None:
                    if isinstance(persistence, str):
                        persistence = PicklePersistence(persistence)
                    builder.persistence(persistence)
            defaults = telegram_cfg.pop("defaults", None)
            if defaults is not None:
                if isinstance(defaults, dict):
                    defaults = Defaults(**defaults)
                builder.defaults(defaults)
            for k, v in telegram_cfg.items():
                if hasattr(builder, k):
                    if isinstance(v, dict):
                        getattr(builder, k)(**v)
                    else:
                        getattr(builder, k)(v)

            return builder.build()

        @property
        def custom_handlers(self) -> tp.Iterable[BaseHandler]:
            """Custom handlers to add.

            Override to add custom handlers. Order counts."""
            return ()

        def register_handlers(self) -> None:
            """Register handlers."""
            self.application.add_handler(self.log_handler)
            self.application.add_handler(CommandHandler("start", self.start_callback))
            self.application.add_handler(CommandHandler("help", self.help_callback))
            for handler in self.custom_handlers:
                self.application.add_handler(handler)
            self.application.add_handler(MessageHandler(filters.StatusUpdate.MIGRATE, self.chat_migration_callback))
            self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown_callback))
            self.application.add_error_handler(self_decorator(self, type(self).error_callback))

        @property
        def giphy_kwargs(self) -> tp.Kwargs:
            """Keyword arguments for GIPHY."""
            return self._giphy_kwargs

        @property
        def application(self) -> Application:
            """Application."""
            return self._application

        @property
        def chat_ids(self) -> tp.Set[int]:
            """Chat ids that ever interacted with this bot.

            A chat id is added upon receiving the "/start" command."""
            return self.application.bot_data.setdefault("chat_ids", set())

        async def log_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Callback for logging."""
            pass

        @property
        def log_handler(self) -> LogHandler:
            """Log handler."""
            return LogHandler(self.log_callback)

        async def send(self, kind: str, chat_id: int, *args, log_msg: tp.Optional[str] = None, **kwargs) -> None:
            """Send message of any kind to `chat_id`."""
            try:
                await getattr(self.application.bot, "send_" + kind)(chat_id, *args, **kwargs)
                if log_msg is None:
                    log_msg = kind
                logger.info(f"{chat_id} - Bot: %s", log_msg)
            except ChatMigrated as e:
                # transfer data, if old data is still present
                new_id = e.new_chat_id
                if chat_id in self.chat_ids:
                    self.chat_ids.remove(chat_id)
                self.chat_ids.add(new_id)
                # Resend to new chat id
                await self.send(kind, new_id, *args, log_msg=log_msg, **kwargs)
            except Forbidden as e:
                logger.info(f"{chat_id} - Forbidden to send the %s", kind)

        async def send_to_all(self, kind: str, *args, **kwargs) -> None:
            """Send message of any kind to all in `TelegramBot.chat_ids`."""
            for chat_id in self.chat_ids:
                await self.send(kind, chat_id, *args, **kwargs)

        async def send_message(self, chat_id: int, text: str, *args, **kwargs) -> None:
            """Send text message to `chat_id`."""
            log_msg = '"%s"' % text
            await self.send("message", chat_id, text, *args, log_msg=log_msg, **kwargs)

        async def send_message_to_all(self, text: str, *args, **kwargs) -> None:
            """Send text message to all in `TelegramBot.chat_ids`."""
            log_msg = '"%s"' % text
            await self.send_to_all("message", text, *args, log_msg=log_msg, **kwargs)

        async def send_giphy(
            self, chat_id: int, text: str, *args, giphy_kwargs: tp.KwargsLike = None, **kwargs
        ) -> None:
            """Send GIPHY from text to `chat_id`."""
            if giphy_kwargs is None:
                giphy_kwargs = self.giphy_kwargs
            gif_url = text_to_giphy_url(text, **giphy_kwargs)
            log_msg = '"%s" as GIPHY %s' % (text, gif_url)
            await self.send("animation", chat_id, gif_url, *args, log_msg=log_msg, **kwargs)

        async def send_giphy_to_all(self, text: str, *args, giphy_kwargs: tp.KwargsLike = None, **kwargs) -> None:
            """Send GIPHY from text to all in `TelegramBot.chat_ids`."""
            if giphy_kwargs is None:
                giphy_kwargs = self.giphy_kwargs
            gif_url = text_to_giphy_url(text, **giphy_kwargs)
            log_msg = '"%s" as GIPHY %s' % (text, gif_url)
            await self.send_to_all("animation", gif_url, *args, log_msg=log_msg, **kwargs)

        async def post_start_callback(self) -> None:
            """Callback after the application is started."""
            await self.send_message_to_all("I'm back to life!")

        async def pre_stop_callback(self) -> None:
            """Callback before the application is shutdown."""
            await self.send_message_to_all("Bye!")

        @property
        def start_message(self) -> str:
            """Message to be sent upon "/start" command.

            Override to define your own message."""
            return "Hello!"

        async def start_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Start command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                if chat_id not in self.chat_ids:
                    self.chat_ids.add(chat_id)
                await self.send_message(chat_id, self.start_message)

        @property
        def help_message(self) -> str:
            """Message to be sent upon "/help" command.

            Override to define your own message."""
            return "Can't help you here, buddy."

        async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Help command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                await self.send_message(chat_id, self.help_message)

        async def chat_migration_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Chat migration callback."""
            if isinstance(update, Update) and update.message:
                old_id = update.message.migrate_from_chat_id or update.message.chat_id
                new_id = update.message.migrate_to_chat_id or update.message.chat_id
                if old_id in self.chat_ids:
                    self.chat_ids.remove(old_id)
                self.chat_ids.add(new_id)
                logger.info(f"{old_id} - Chat migrated to {new_id}")

        async def unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Unknown command callback."""
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                logger.info(f'{chat_id} - Unknown command "{update.message}"')
                await self.send_message(chat_id, "Sorry, I didn't understand that command.")

        async def error_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> None:
            """Error callback."""
            logger.error('Exception while handling an update "%s": ', update, exc_info=context.error)
            if isinstance(update, Update) and update.effective_chat:
                chat_id = update.effective_chat.id
                await self.send_message(chat_id, "Sorry, an error happened.")

        @property
        def loop(self) -> tp.Optional[asyncio.BaseEventLoop]:
            """Event loop."""
            return self._loop

        def start(
            self,
            close_loop: bool = True,
            stop_signals: tp.Sequence[int] = BaseRequest.DEFAULT_NONE,
            **kwargs,
        ) -> None:
            """Start the bot.

            `**kwargs` override settings under `telegram` in `vectorbtpro._settings.messaging` and only those
            keys that can be found in `telegram.ext._updater.Updater.start_polling` are passed."""
            from vectorbtpro._settings import settings

            telegram_cfg = settings["messaging"]["telegram"]

            if not self.application.updater:
                raise RuntimeError("Application.run_polling is only available if the application has an Updater.")

            def error_callback(exc: TelegramError) -> None:
                self.application.create_task(self.application.process_error(error=exc, update=None))

            # Prepare arguments
            default_kwargs = dict()
            passed_kwargs = dict()
            for k in get_func_kwargs(self.application.updater.start_polling):
                if k in telegram_cfg:
                    default_kwargs[k] = telegram_cfg[k]
                if k in kwargs:
                    passed_kwargs[k] = kwargs.pop(k)
            polling_kwargs = merge_dicts(default_kwargs, passed_kwargs)

            # Run the Bot
            updater_coroutine = self.application.updater.start_polling(**polling_kwargs)
            # Calling get_event_loop() should still be okay even in py3.10+ as long as there is a
            # running event loop or we are in the main thread, which are the intended use cases.
            # See the docs of get_event_loop() and get_running_loop() for more info
            self._loop = asyncio.get_event_loop()

            if stop_signals is BaseRequest.DEFAULT_NONE and platform.system() != "Windows":
                stop_signals = (signal.SIGINT, signal.SIGTERM, signal.SIGABRT)

            def _raise_system_exit() -> None:
                raise SystemExit

            try:
                if stop_signals is not BaseRequest.DEFAULT_NONE:
                    for sig in stop_signals or []:
                        self.loop.add_signal_handler(sig, _raise_system_exit)
            except NotImplementedError as exc:
                warnings.warn(
                    f"Could not add signal handlers for the stop signals {stop_signals} due to "
                    f"exception `{exc!r}`. If your event loop does not implement `add_signal_handler`,"
                    " please pass `stop_signals=None`.",
                    stacklevel=3,
                )

            try:
                self.loop.run_until_complete(self.application.initialize())
                if self.application.post_init is not None:
                    self.loop.run_until_complete(self.application.post_init(self.application))
                self.loop.run_until_complete(updater_coroutine)  # one of updater.start_webhook/polling
                self.loop.run_until_complete(self.application.start())
                self.loop.run_until_complete(self.post_start_callback())
                self.loop.run_forever()
            except (KeyboardInterrupt, SystemExit):
                pass
            except Exception as exc:
                # In case the coroutine wasn't awaited, we don't need to bother the user with a warning
                updater_coroutine.close()
                raise exc
            finally:
                # We arrive here either by catching the exceptions above or if the loop gets stopped
                self.stop(close_loop=close_loop)

        def stop(self, close_loop: bool = True) -> None:
            """Stop the bot."""
            if self.loop is None:
                raise RuntimeError("There is no event loop running this Application")
            try:
                self.loop.run_until_complete(self.pre_stop_callback())
                if self.application.updater.running:
                    self.loop.run_until_complete(self.application.updater.stop())
                if self.application.running:
                    self.loop.run_until_complete(self.application.stop())
                self.loop.run_until_complete(self.application.shutdown())
                if self.application.post_shutdown is not None:
                    self.loop.run_until_complete(self.application.post_shutdown(self.application))
            finally:
                if close_loop and not self.loop.is_running():
                    self.loop.close()

        @property
        def running(self) -> bool:
            """Whether the bot is running."""
            return self.application.running
