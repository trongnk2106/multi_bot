import argparse
from dataclasses import dataclass
import datetime
from typing import Any
from telegram.ext import CallbackQueryHandler
from telegram import Bot, Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Application
import telegram.ext.filters as flters
import requests
from functools import partial
from io import BytesIO
import numpy as np
from const import *


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
        # self.chat_id = requests.get(f"https://api.telegram.org/bot{self.token}/getUpdates")
        # print("chat id : ", self.chat_id)
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
        self.app.add_handler(CommandHandler("morning_message", self.start_auto_messaging))
        self.app.add_handler(CommandHandler("stop_morning_message", self.stop_notify))
        self.app.add_handler(MessageHandler(flters.TEXT & ~flters.COMMAND, self._message_action))
        self.app.add_handler(MessageHandler(flters.PHOTO, self._photo))
        self.app.add_handler(MessageHandler(flters.Document.ALL, self._document))
        self.app.add_handler(MessageHandler(flters.AUDIO, self._audio))
        self.app.add_handler(MessageHandler(flters.VOICE, self._voice))
        self.app.add_handler(MessageHandler(flters.VIDEO, self._video))
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
        chat_type = update.message.chat.type
        message = update.message.text
        self.user_info = update.message.from_user
        # print(update.message)
    
        if chat_type == "private":
    
            response = await self._get_response(message)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="Markdown")
        elif chat_type in ["group", "supergroup"]:
      
            self.bot_username = await self.get_bot()
            print(self.bot_username)
            if f"@{self.bot_username}" in message:
                response = await self._get_response(message.replace(f"@{self.bot_username}", ""))
                await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="Markdown")
    
    async def _photo(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for photo, get photo ID and download it to local
        '''
        
        
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('image.jpg', 'wb') as f:
            f.write(file_bytes)
    
    async def _document(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for document, get document ID and download it to local
        '''
        
        file = await context.bot.get_file(update.message.document.file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('document.pdf', 'wb') as f:
            f.write(file_bytes)
    
    async def _audio(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for audio, get audio ID and download it to local
        '''
        
        file = await context.bot.get_file(update.message.audio.file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('audio.mp3', 'wb') as f:
            f.write(file_bytes)
            
    
    async def _voice(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for voice, get voice ID and download it to local
        '''
        
        file = await context.bot.get_file(update.message.voice.file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('voice.mp3', 'wb') as f:
            f.write(file_bytes)
            
    async def _video(self, update : Update ,context: CallbackContext):
        
        #TODO: Handle video
        
        print(update.message.video)
        file = await context.bot.get_file(update.message.video.file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('video.mp4', 'wb') as f:
            f.write(file_bytes)
    
    @staticmethod
    async def callback_auto_message(context: CallbackContext, update: Update):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Good morning!!', parse_mode="Markdown")

    async def start_auto_messaging(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        job = context.job_queue.run_daily(partial(self.callback_auto_message, update=update), time=datetime.time(hour=21, minute=53), days=(0, 1, 2, 3, 4, 5, 6), chat_id=chat_id, name=str(chat_id))
        # job = context.job_queue.run_repeating(partial(self.callback_auto_message, update=update), 10, chat_id=chat_id, name=str(chat_id))
        
        
    async def stop_notify(self, update : Update, context : CallbackContext):
        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id=chat_id, text='Stopping automatic messages!', parse_mode="Markdown")
        job = context.job_queue.get_jobs_by_name(str(chat_id))
        job[0].schedule_removal()

    async def callback_query_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        data = query.data
        await query.answer()

        chat_id = query.message.chat_id
        message_id = query.message.message_id

        selected_question = self.sugesstion_mapping.get(data)
        response_message = await self._get_response(selected_question)

        response_message = f"> You: {selected_question}\n\n{response_message}"

        await context.bot.send_message(chat_id=chat_id, text=response_message, parse_mode="Markdown")

    async def get_bot(self):
 
        bot = Bot(self.token)
        bot_info = await bot.get_me()
        bot_username = bot_info.username    

        return bot_username


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        # Run Bot
        self.app.run_polling()
            

      