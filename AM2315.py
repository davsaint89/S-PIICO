import board
import busio
import adafruit_am2320
import math
import traceback

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_am2320.AM2320(i2c)

temperature = sensor.temperature

def tem_data():
    #while True:
    try:
        temperature = sensor.temperature
        return "{0}C".format(temperature)
    
    except(OSError):
        return "unplugged" # si el sensor esta desconectado

def hum_data():
    #while True:
    try:
        humidity = sensor.relative_humidity
        return '{0}%'.format(humidity)
    except(OSError):
        return "unplugged" # si el sensor esta desconectado


