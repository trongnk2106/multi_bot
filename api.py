import signal
from fastapi import FastAPI, Request, Response
from fastapi import APIRouter
from pydantic import BaseModel
import subprocess
import os
router = APIRouter()


class BotDetails(BaseModel):
    token: str
    bot_id: str
    # api_url: str

def runbot(tokens, bot_ids):
    # check process id, neu process dang chay file telebot.py thi kill nham reload lai cac process
     # Stop the bot.py process if it's already running
    try :
        proc = subprocess.Popen(['wmic', 'process', 'where', 'CommandLine like "%telebot.py%"', 'get', 'ProcessId'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()

        # Duyệt qua tất cả các tiến trình tìm thấy
        for pid in stdout.decode().split("\n")[1:]:
            if pid.strip():
                # Dừng tiến trình bằng cách sử dụng lệnh 'taskkill'
                subprocess.run(['taskkill', '/PID', pid.strip(), '/F'])
    except Exception as e:
        print(e)
    finally:
        # get absolute path to python enviroment
        '''import sys
        print(sys.executable)'''
        subprocess.Popen(["python", "telebot.py", 
                        "--tokens", tokens, "--bot_ids", bot_ids])
        
def register_bot(bot_details: BotDetails):
    # write to temp backend file
    with open('./account.txt', 'a+', encoding='utf-8') as f:
        f.write(f"{bot_details.token},{bot_details.bot_id}\n")
    
    with open('./account.txt', 'r', encoding='utf-8') as f:
        content = f.readlines()
        tokens = []
        bot_ids = []
        for line in content:
            token, bot_id = line.strip().split(',')
            tokens.append(token)
            bot_ids.append(bot_id)
        tokens = " ".join(tokens)
        bot_ids = " ".join(bot_ids)
    return tokens, bot_ids
    
@router.get("/")
async def read_root():
    return {"Hello": "World"}

@router.post("/create_bot/")
async def create_bot(bot_details: BotDetails):
    tokens, bot_ids = register_bot(bot_details)
    runbot(tokens, bot_ids)
    
   

    return {"message": "Bot instance created successfully!"}