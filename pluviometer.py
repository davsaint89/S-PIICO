from gpiozero import Button
import math
import time
import statistics

####### variable cantidad de agua
BUCKET_SIZE 	= 0.2794
rain_count      = 0
water_amount	= 0

rain_sensor = Button(6)

store_rain = []

def bucket_tipped():
	global rain_count
	global water_amount
	rain_count   = rain_count + 1
	water_amount = rain_count * BUCKET_SIZE
    

def reset_rainfall():
	global rain_count
	rain_count   = 0

def rain_data():
    rain_sensor.when_pressed = bucket_tipped
    lluvia = water_amount
    return "{0:.2f}".format(lluvia)


