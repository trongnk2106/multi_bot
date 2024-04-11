import argparse
from dataclasses import dataclass
from typing import Any
from telegram.ext import CallbackQueryHandler
from telegram import Bot, Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Application
import telegram.ext.filters as flters
import requests
import threading
from const import *
import asyncio

def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)


@dataclass
class TeleApp:
    TOKEN: str
    BOT_ID: str 

class TelegramDAppController:
    def __init__(self, token: str, bot_id: str):
        self.token = token
        self.bot_id = bot_id
        # Define App
        self.app = Application.builder().token(self.token).build()

        # Init conversation
        self.message_init_converstation = "Hello, I'm a FlexStack bot! How can I assist you today?"
        self.suggested_questions = self._get_suggested_questions()

        # HANDLE MAPPING
        sugesstion_mapping = {}
        for question in self.suggested_questions:
            if len(question) > 64:
                key = question[:61] + '...'
            else:
                key = question
            sugesstion_mapping[key] = question

        self.sugesstion_mapping = sugesstion_mapping
        # Handle
        self._handle()
    
    async def _get_response(self, question):
        data = {"message": question}
        response = requests.post(FLEXSTACK_BASE_URL + '/chat/conversation?app=' + self.bot_id, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, data=data)
        if response.status_code == 200:
            data = response.json()['messages']['content']
            return data
        else:
            print(response.status_code, response.text)
            return "I'm sorry, I don't know how to answer that."
        
    def _get_suggested_questions(self):
        response = requests.get(FLEXSTACK_BASE_URL + '/chat/prompt_discovery?app=' + self.bot_id, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"})
        if response.status_code == 200:
            data = response.json()['data']
            suggested_questions = [d['content'] for d in data]
            return suggested_questions
        else:
            print(response.status_code, response.text)
            return []
        
    def _handle(self):
        self.app.add_handler(CommandHandler("start", self._start_action))
        self.app.add_handler(CommandHandler("help", self._help_action))
        self.app.add_handler(MessageHandler(flters.TEXT & ~flters.COMMAND, self._message_action))
        self.app.add_handler(CallbackQueryHandler(self.callback_query_handler))

    async def _start_action(self, update: Update, context: CallbackContext):
        suggested_questions = list(self.sugesstion_mapping.keys())

        keyboard = [[InlineKeyboardButton(question, callback_data=question)] for question in suggested_questions]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Gửi tin nhắn với Inline Keyboard
        await update.message.reply_text(self.message_init_converstation, reply_markup=reply_markup)

    async def _help_action(self, update: Update, context: CallbackContext):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

    async def _message_action(self, update: Update, context: CallbackContext):
        # Get message
        message = update.message.text
        response = await self._get_response(message)
        # response = escape_markdown(response)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="Markdown")

    async def callback_query_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        data = query.data
        await query.answer()

        chat_id = query.message.chat_id
        message_id = query.message.message_id

        selected_question = self.sugesstion_mapping.get(data)
        response_message = await self._get_response(selected_question)

        response_message = f"> You: {selected_question}\n\n{response_message}"

        # response_message = escape_markdown(response_message)
        await context.bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # Run Bot
        self.app.run_polling()
        
import multiprocessing

def run_bot(token, bot_id):
    bot = TelegramDAppController(token, bot_id)
    bot()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Run TelegramDApp bot.')
    parser.add_argument('--tokens', nargs='+', help='List of bot tokens', required=True)
    parser.add_argument('--bot_ids', nargs='+', help='List of bot ids', required=True)
    args = parser.parse_args()
    list_tokens = args.tokens[0]
    list_bot_ids = args.bot_ids[0]
    print("List of tokens: ", list_tokens)
    print("List of bot ids: ", list_bot_ids)
    
    tokens = list_tokens.split(" ")
    bot_ids = list_bot_ids.split(" ")
    
    processes = []
    for token, bot_id in zip(tokens, bot_ids):
        process = multiprocessing.Process(target=run_bot, args=(token, bot_id))
        process.start()
        processes.append(process)


    for process in processes:
        process.join()
        
      