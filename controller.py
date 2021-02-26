#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import requests
from multiprocessing import Process, Value
import json

fan = 13       # PWM pin
sensor = 4     # Temperature sensorSensor Pin

#GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(fan,GPIO.OUT)
GPIO.setup(sensor,GPIO.IN)

pwm = GPIO.PWM(fan, 100)
pwm.start(0)

#Define the upper and lower bounds of the temperature guage
tempMin = 25
tempMax = 45


def getTemperature():
    tempStore = open("/sys/bus/w1/devices/28-0060a70000af/w1_slave")
    data = tempStore.read()
    tempStore.close()

    tempData = data.split("\n")[1].split(" ")[9]
    temperature = float(tempData[2:])
    temperature = temperature/1000
    return int(temperature)


def setPWM(duty):
    pwm.ChangeDutyCycle(duty)


#Map the temperature range to the PWM range
def calcDuty(temp):
    #Set the PWM values
    pwmMin = 20
    pwmMax = 100
    
    #Sanity check for out of scope temperatures
    if temp < tempMin: return pwmMin
    if temp > tempMax: return pwmMax

    #Get the ranges
    tempRange = tempMax - tempMin
    pwmRange = pwmMax - pwmMin
    
    #Get the fraction of the value in the range
    valueScaled = float(temp-tempMin)/float(tempRange)
    
    #Return the fraction mutiplied by the pwm range from the pwmMin
    return int(pwmMin + (valueScaled*pwmRange))


def alert(temp):
    global alerted
    alerted.value = 1

    # Get the Webhook API key
    with open('key.json') as json_file:
        data = json.load(json_file)
        key = data['key']

    url = 'https://maker.ifttt.com/trigger/rack_temperature/with/key/' + key
    payload = {'value1' : "temp"}
    requests.post(url, data=payload)
    
    # Delay running this alert over and over
    time.sleep(1800)  
    temp = getTemperature()
    if temp <= tempMax: 
        alerted.value = 0
    else:
        alert(temp)       # Still hot, send another alert!


def main():
    global alerted
    try:
        while True:
            temperature = getTemperature()
            dutyCycle = calcDuty(temperature)
            setPWM(dutyCycle)
            
            if temperature > tempMax and alerted.value == 0:        # Start a seperate thread for alert
                p2 = Process(target=alert, args=[temperature])
                p2.start()

            time.sleep(5)
    except:
        pwm.stop()
        GPIO.cleanup()


if __name__ == '__main__':
    alerted = Value('i', 0)
    p1 = Process(target=main)
    p1.start()
