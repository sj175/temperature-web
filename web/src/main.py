import copy
import datetime
import json
import logging
import os
from typing import List

import boto3
import fastapi_utils.tasks
import pydantic
import starlette.responses
import starlette.status
import threading
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
S3 = boto3.resource('s3',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    )
app.mount("/static", StaticFiles(directory="static"), name="static")
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TemperatureData(pydantic.BaseModel):
    timestamp: datetime.datetime
    temperature: float
    humidity: float


GLOBAL_DATA: List[TemperatureData] = []
data_lock = threading.Lock()
api_key_header = APIKeyHeader(name=API_KEY_NAME)


async def get_api_key(header: str = Security(api_key_header)):
    if header == API_KEY:
        return header
    else:
        raise HTTPException(status_code=starlette.status.HTTP_403_FORBIDDEN, detail='Could not validate credentials')


@app.get("/get-temperature")
async def get_temperature():
    with data_lock:
        return [[datum.timestamp, datum.temperature] for datum in GLOBAL_DATA]


@app.get("/get-humidity")
async def get_humidity():
    with data_lock:
        return [[datum.timestamp, datum.humidity] for datum in GLOBAL_DATA]


@app.post("/update", status_code=status.HTTP_204_NO_CONTENT, response_class=starlette.responses.Response)
async def update(received: List[TemperatureData], token: str = Depends(get_api_key)):
    with data_lock:
        LOGGER.debug(received)
        GLOBAL_DATA.extend(received)


@app.on_event('startup')
@fastapi_utils.tasks.repeat_every(seconds=3600, logger=LOGGER)
def upload_to_s3() -> None:
    global GLOBAL_DATA
    with data_lock:
        if GLOBAL_DATA:
            key = str(datetime.datetime.utcnow().replace(microsecond=0)).split(" ")
            upload_data = S3.Object(BUCKETNAME, f"{key[0]}/{key[1].replace(':', '-')}")
            upload_data.put(Body=json
                            .dumps(copy.deepcopy(GLOBAL_DATA))
                            .encode('utf-8')
                            )

        GLOBAL_DATA = []
