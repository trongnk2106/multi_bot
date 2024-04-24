from fastapi import FastAPI, Request, status

import router
import uvicorn
app =FastAPI()
app.include_router(router=router.router, prefix="")


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)