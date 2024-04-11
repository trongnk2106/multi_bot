from fastapi import FastAPI, Request, Response
from fastapi import APIRouter

import api

router = APIRouter()

router.include_router(router=api.router, prefix="/flexstack/tele", tags=["telegrambot"])
