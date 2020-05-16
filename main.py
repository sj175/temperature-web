import datetime
import logging
import os
from typing import List

import boto3
import pydantic
import starlette.responses
import starlette.status
from dotenv import load_dotenv
from fastapi import FastAPI, Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles

load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BUCKETNAME = os.getenv('BUCKET')
API_KEY = os.getenv('API_KEY')
API_KEY_NAME = 'access_token'
app = FastAPI()
CLIENT = boto3.resource('s3',
                        aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY,
                        )
BUCKET = CLIENT.Bucket(BUCKETNAME)
app.mount("/static", StaticFiles(directory="static"), name="static")
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TemperatureData(pydantic.BaseModel):
    timestamp: datetime.datetime
    temperature: float
    humidity: float


GLOBAL_DATA: List[TemperatureData] = []
api_key_header = APIKeyHeader(name=API_KEY_NAME)


async def get_api_key(header: str = Security(api_key_header)):
    if header == API_KEY:
        return header
    else:
        raise HTTPException(status_code=starlette.status.HTTP_403_FORBIDDEN, detail='Could not validate credentials')


@app.get("/get-temperature")
async def get_temperature():
    return [[datum.timestamp, datum.temperature] for datum in GLOBAL_DATA]


@app.get("/get-humidity")
async def get_humidity():
    return [[datum.timestamp, datum.humidity] for datum in GLOBAL_DATA]


@app.post("/update", status_code=status.HTTP_204_NO_CONTENT, response_class=starlette.responses.Response)
async def update(received: List[TemperatureData], token: str = Depends(get_api_key)):
    LOGGER.debug(received)
    GLOBAL_DATA.extend(received)
