from app.parser import date_parser
from fastapi import APIRouter
from fastapi.param_functions import Depends
from app.model import schemas
import sys
import os
from app.parser import datetime_range
sys.path.append(os.path.realpath(os.path.relpath("../..")))

import logging
logger = logging.getLogger(__name__)



router=APIRouter()

@router.post('/get-valid-date')
async def get_medicine_info(data:schemas.DateUtterance):
    result = date_parser.get_date(data.utterance)
    return result

@router.post('/get-datetime-range')
async def get_medicine_info(data:schemas.DateUtterance):
    result = datetime_range.translate_range(data.utterance)
    return result