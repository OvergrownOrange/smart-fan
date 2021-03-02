#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import requests
from multiprocessing import Process, Value
import json
import os, sys

fan = 13       # PWM pin
sensor = 4     # Temperature sensorSensor Pin

#GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(fan,GPIO.OUT)
GPIO.setup(sensor,GPIO.IN)

#Define the upper and lower bounds of the temperature gauge
tempMin = 25
tempMax = 45

# Get the Webhook API key
with open(os.path.join(sys.path[0], 'key.json'), 'r') as json_file:
    data = json.load(json_file)
    key = data['key']

url = 'https://maker.ifttt.com/trigger/smart_fan/with/key/' + key

def getTemperature():
    tempStore = open("/sys/bus/w1/devices/28-0060a70000af/w1_slave")
    data = tempStore.read()
    tempStore.close()

    tempData = data.split("\n")[1].split(" ")[9]
    temperature = float(tempData[2:])
    temperature = temperature/1000
    return int(temperature)


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

    #Send the high temperature notification
    message = 'High temperature detected in Rack! ' + str(temp) + '°C'
    payload = {'value1' : message}
    requests.post(url, data=payload)
    
    time.sleep(1800)        # Sleep this process to stop several notifications
    temp = getTemperature()
    if temp <= tempMax: 
        alerted.value = 0
    else:
        alert(temp)         # Still hot, send another alert!


def main():
    global alerted
    pwm = GPIO.PWM(fan, 100)
    pwm.start(0)
    try:
        while True:
            temperature = getTemperature()
            dutyCycle = calcDuty(temperature)
            pwm.ChangeDutyCycle(dutyCycle)
            
            if temperature > tempMax and alerted.value == 0:        # Start a seperate process for alerts
                p2 = Process(target=alert, args=[temperature])      # to avoid the main loop sleep
                p2.start()

            time.sleep(60)                                          # Run every minute
    except:
        #Notify that the application has failed
        payload = {'value1' : "Smartfan application has failed!"}
        requests.post(url, data=payload)
        
        pwm.stop()
        GPIO.cleanup()


if __name__ == '__main__':
    alerted = Value('i', 0)
    p1 = Process(target=main)
    p1.start()
