import datetime
import os
from typing import List

import boto3
import pydantic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
app = FastAPI()
CLIENT = boto3.resource('s3',
                        aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY,
                        )
BUCKET = CLIENT.Bucket('prod-238783079787-temperature-data')
app.mount("/static", StaticFiles(directory="static"), name="static")


class TempData(pydantic.BaseModel):
    timestamp: datetime.datetime
    temperature: float
    humidity: float


DATA_SCRAG: List[TempData] = []


@app.get("/scrag")
async def scragging():
    global DATA_SCRAG
    DATA_SCRAG = scraggin()
    return {"status": DATA_SCRAG}


@app.get("/data")
async def data(start_time: datetime.datetime, end_time: int):
    return {"start": start_time, "end": end_time, "scrag": datetime.datetime.utcnow()}


@app.get("/static-data")
async def some_static_data():
    return [["2020-05-10T14:06:06.900Z", 34.5], ["2020-05-10T14:06:07.900Z", 24.7], ["2020-05-10T14:06:08.900Z", 27.5]]


@app.get("/current")
async def current_data(shizzle: TempData):
    pass


@app.get("/get-temp")
async def get_data():
    return [[datum.timestamp, datum.temperature] for datum in DATA_SCRAG]


@app.post("/update")
async def update(shizzle: List[TempData]):
    print(shizzle)
    DATA_SCRAG.extend(shizzle)
    return {"lol": 5}


def scraggin():
    output = []
    for obj in BUCKET.objects.all():
        key = obj.key
        body = obj.get()['Body'].read()
        output.append(body)
        print(body)

    return output


def get_data(start: datetime.datetime, end: datetime) -> list:
    # binary_search?
    print(start, end)
    return DATA_SCRAG
