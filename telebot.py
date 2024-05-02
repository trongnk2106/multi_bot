import argparse
from dataclasses import dataclass
import datetime
import time
from typing import Any
from telegram.ext import CallbackQueryHandler
from telegram import Bot, Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Application, MessageReactionHandler
    
import telegram.ext.filters as flters
import requests
from functools import partial
from io import BytesIO
import numpy as np
import shutil
from const import *
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


bearer_token  = 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImJhNjI1OTZmNTJmNTJlZDQ0MDQ5Mzk2YmU3ZGYzNGQyYzY0ZjQ1M2UiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiRmxleHN0YWNrIHN5c3RlbSIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLLWZYcFJ2WlU1YjlfdF9nUlUwNHM4ZzlyUTVqUi1mQktDTVZLaVkxTzA9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZG9jdHJhbnNsYXRlLWlvIiwiYXVkIjoiZG9jdHJhbnNsYXRlLWlvIiwiYXV0aF90aW1lIjoxNzEyMTMxMzkyLCJ1c2VyX2lkIjoiNmx5NHlmZTZWdFpqM1FHM0kySThFUkx4a3h6MiIsInN1YiI6IjZseTR5ZmU2VnRaajNRRzNJMkk4RVJMeGt4ejIiLCJpYXQiOjE3MTIxMzE4ODgsImV4cCI6MTcxMjEzNTQ4OCwiZW1haWwiOiJzeXN0ZW1AZmxleHN0YWNrLmFpIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDI2NzQ3MDg4MDk1NTYyODY1MjYiXSwiZW1haWwiOlsic3lzdGVtQGZsZXhzdGFjay5haSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.TRX-sKv6qAu_zGtYK4mNz2fufjukDGhvsVtpKyqsAbE4l1wUvE7GZVOGEHwyIQF0RstFpFK64hnhtE9vhYk3NwH50S6CeJTRx031ok1sXqQMBjCapcUTTfMWA5QmDVRUmtyGiTBturDgiKrt7pcSFLtgDxI1KtrWVmqERyw8o2mkmAOjrJQnrvdzc75crLT89_gbFyb-Bf4s9QANciTnYUsdXMAIezxNcMaAj4pDzSsA6q6EJwLJsQpvZBnFCSs6fNObF0d50wmQ61x-VhNHTkE4dCM_bAblxTvfeZmaXFQjQytnmXyJnEW1-oW420sXlj5sbvva6swzXp3kOZXraA'
headers = {
    "Authorization": f"Bearer {bearer_token}"
}


def detemine_dest_language(caption):
   
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = f'''You are an expert in language analysis. A user has asked you to translate a document. Based on the following statement, identify which language the user wants the document to be translated into:

    "{caption}"

    If they want it translated into Vietnamese, only respond with "vi." 
    If they want it translated into English, only respond with "en." 
    If it's another language, only respone the stand for name that language.'''

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ],
        model="gpt-3.5-turbo",
    )
    return str(chat_completion.choices[0].message.content)

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
        self.app.add_handler(MessageHandler(flters.ANIMATION, self._animation))
        self.app.add_handler(MessageReactionHandler(self._reaction))
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
   
            if f"@{self.bot_username}" in message:
                response = await self._get_response(message.replace(f"@{self.bot_username}", ""))
                await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode="Markdown")
    
    async def _photo(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for photo, get photo ID and download it to local
        '''
        print("handle photo")
        
        file = await context.bot.get_file(update.message.photo[-1].file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('image.jpg', 'wb') as f:
            f.write(file_bytes)
    
    
    async def _animation(self, update : Update ,context: CallbackContext):
            
            '''
            Handler for animation, get animation ID and download it to local
            '''
            print("handle animation")
            file = await context.bot.get_file(update.message.animation.file_id)
            file_bytes = await file.download_as_bytearray()
        
            with open('animation.gif', 'wb') as f:
                f.write(file_bytes)
    
    async def _document(self, update : Update ,context: CallbackContext):
        
        '''
        Handler for document, get document ID and download it to local
        '''
        dest = detemine_dest_language(update.message.caption)
        print(dest)
        
        file = await context.bot.get_file(update.message.document.file_id)
        file_name = update.message.document.file_name
        file_bytes = await file.download_as_bytearray()
        mime_type = update.message.document.mime_type # application/pdf
        url = 'https://doctranslate-api.doctranslate.io/v1/translate/document'
        # with open(f'{file_name}', 'wb') as f:
        #     f.write(file_bytes)
        # file = {
        #     "file": open(f"{file_name}", "rb")
        # }
        file = {
            "file" : file_bytes
        }
        
        data = {
            "file_type" : mime_type,
            "dest_lang" : dest
        }
        response = requests.post(url, headers=headers, files=file, data = data).json()

        task_id = response['data']['task_id']
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Translating document, please wait...", parse_mode="Markdown")
        count_time = 0
        status = False
        while True:
            res = requests.get(f"https://doctranslate-api.doctranslate.io/v1/result/{task_id}", headers=headers)
            time.sleep(2)
            count_time += 2
            if count_time > 60:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Timeout, please try again", parse_mode="Markdown")
                status = False 
                break
            res = res.json()
            if "url_download" in res['data'].keys():
                url_download = res['data']['url_download']
                name_file = res['data']['name_file']
                status = True
                break
        if status :
            res = requests.get(url_download)
            with open(name_file, "wb") as file:
                file.write(res.content)
            doc = open(f'{name_file}', 'rb')
    
            
            await context.bot.send_document(chat_id = update.effective_chat.id, document = doc)
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"done", parse_mode="Markdown")
      
    
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
       
        file = await context.bot.get_file(update.message.video.file_id)
        file_bytes = await file.download_as_bytearray()
    
        with open('video.mp4', 'wb') as f:
            f.write(file_bytes)
    
    async def _reaction(self, update : Update ,context: CallbackContext):
            
            '''
            Handler for reaction, get reaction ID and download it to local
            '''
            
            react = update.message_reaction
            print(react.user, react.reaction, react.message_id, react.chat_id, react.message)
            print(react)
        
    
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
            

      