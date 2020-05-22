import datetime
import os
import time

import adafruit_dht
import board
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
URL = ''


def send_to_server(temperature: float, humidity: float):
    temperature_data = {'timestamp': datetime.datetime.utcnow(),
                        'temperature': temperature,
                        'humidity': humidity}
    requests.post(URL, headers={'access_token': API_KEY}, data=temperature_data)


def main():
    # Initial the dht device, with data pin connected to:
    dht_device = adafruit_dht.DHT22(board.D18)

    while True:
        try:
            # Print the values to the serial port
            temperature_c = dht_device.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = dht_device.humidity
            print(
                "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    temperature_f, temperature_c, humidity
                )
            )

        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])

        time.sleep(2.0)


if __name__ == '__main__':
    main()
