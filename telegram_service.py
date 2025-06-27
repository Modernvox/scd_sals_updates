import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError

class TelegramService:
    def __init__(self, bot_token, chat_id=None, loop=None):
        """
        Initialize TelegramService with a bot token and optional asyncio loop.
        
        Args:
            bot_token (str): Telegram bot token from environment.
            loop (asyncio.AbstractEventLoop, optional): Asyncio event loop for sending messages.
        """
        self.bot = None
        self.chat_id = chat_id
        self.loop = loop or asyncio.get_event_loop()
        self.error_shown = False

        if not bot_token:
            logging.warning("Telegram bot token not found. Telegram features disabled.")
            return

        try:
            self.bot = Bot(token=bot_token)
            logging.info("Telegram bot initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Telegram bot: {e}", exc_info=True)
            self.error_shown = True

    async def send_bin_number(self, chat_id, username, bin_number):
        """
        Send a bin number notification to the specified Telegram chat.
        
        Args:
            chat_id (str): Telegram chat ID (e.g., '@ChannelName' or numeric ID).
            username (str): Username of the bidder.
            bin_number (int): Assigned bin number.
            
        Returns:
            bool: True if message sent successfully, False otherwise.
        """
        if not self.bot or not chat_id:
            logging.warning("Cannot send Telegram message: Bot or chat ID missing")
            return False

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"Username: {username} | Bin: {bin_number}"
            )
            logging.info(f"Sent Telegram message: Username: {username} | Bin: {bin_number}")
            return True
        except TelegramError as e:
            logging.error(f"Failed to send Telegram message: {e}", exc_info=True)
            if not self.error_shown:
                self.error_shown = True
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending Telegram message: {e}", exc_info=True)
            if not self.error_shown:
                self.error_shown = True
            return False

    def run_async(self, coro):
        """
        Run an async coroutine in the provided event loop.
        
        Args:
            coro: Coroutine to execute (e.g., send_bin_number).
            
        Returns:
            asyncio.Future: Future object for the coroutine.
        """
        if self.loop:
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        logging.warning("No asyncio loop available for Telegram message")
        return None
