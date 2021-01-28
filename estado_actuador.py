import RPi.GPIO as GPIO

# To test the value of a pin use the .input method

def estado_valvula(channel):
    GPIO.setmode(GPIO.BCM)  
    GPIO.setup(channel, GPIO.OUT)
    channel_is_on = GPIO.input(channel)  # Returns 0 if OFF or 1 if ON

    if channel_is_on:
        valvula = 'on'
    else:
        valvula = 'off'
    return valvula

