import signal
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi import APIRouter
from pydantic import BaseModel
import subprocess
import os
from multiprocessing import Process
from telebot import TelegramDAppController
from typing import Dict

router = APIRouter()


from telegram import Bot

class BotConfig(BaseModel):
    token: str
    bot_id : str


running_bots: Dict[str, Process] = {}

def run_bot(token, bot_id):
    bot = TelegramDAppController(token, bot_id)
    bot()
    
@router.get("/")
async def read_root():
    return {"Hello": "World"}

@router.post("/start_bot/")
async def start_bot(config: BotConfig):
    if config.bot_id in running_bots:
        raise HTTPException(status_code=400, detail="Bot already running.")
    
    process = Process(target=run_bot, args=(config.token, config.bot_id))
    process.start()
    running_bots[config.bot_id] = process


    return {"message": "Bot instance created successfully!"}

@router.post("/stop_bot/")
async def stop_bot(bot_id: str):
    if bot_id not in running_bots:
        raise HTTPException(status_code=404, detail="Bot not found.")
    
    # Stop the process
    process = running_bots[bot_id]
    process.terminate()
    process.join()
    del running_bots[bot_id]
    return {"message": "Bot stopped successfully."}








