from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as router
import datetime

import logging
import sys
import os

logging.config.fileConfig("./app/logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
TRACE_LEVEL_NUM = 9 
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
def trace(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    self._log(TRACE_LEVEL_NUM, message, args, **kws) 
logging.Logger.trace = trace
PROFILE_LEVEL_NUM = 51
logging.addLevelName(PROFILE_LEVEL_NUM, "PROFILE")
def profile(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    self._log(PROFILE_LEVEL_NUM, message, args, **kws) 
logging.Logger.profile = profile

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError

load_dotenv(Path(os.path.realpath(os.path.relpath("..")))/"dev.env")

app = FastAPI(
	title="backend-services",
	description="REST API"
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origin_regex='.*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count","Content-Range"]
    )

app.router.include_router(router, prefix="/datetime-parser")

@app.on_event("startup")
def handle_startup():
    logger.info("*"*30)
    logger.info("Initializing Backend.")

    # Add code above this line
    logger.info("Application startup event.")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(str(exc),str(request),datetime.datetime.now())
