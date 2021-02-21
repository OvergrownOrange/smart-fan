#!/usr/bin/python3


import RPi.GPIO as GPIO
import time

fan = 13        # PWM pin
sensor = 4     # Temperature sensor

#GPIO Setup
#GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(fan,GPIO.OUT)
GPIO.setup(sensor,GPIO.IN)

pwm = GPIO.PWM(fan, 100)
pwm.start(0)


def getTemperature():
    tempStore = open("/sys/bus/w1/devices/28-0060a70000af/w1_slave")
    data = tempStore.read()
    tempStore.close()

    tempData = data.split("\n")[1].split(" ")[9]
    temperature = float(tempData[2:])
    temperature = temperature/1000
    return temperature


def setPWM(duty):
    pwm.ChangeDutyCycle(duty)


#Map the temperature range to the PWM range
def translate(temp, tempMin, tempMax):
    #Set the PWM values
    pwmMin = 20
    pwmMax = 100
    
    #Get the ranges
    tempRange = tempMax - tempMin
    pwmRange = pwmMax - pwmMin
    
    #Get the fraction of the value in the range
    valueScaled = float(temp-tempMin)/float(tempRange)
    
    #Return the fraction mutiplied by the pwm range from the pwmMin
    return int(pwmMin + (valueScaled*pwmRange))


def runFan():
    
    # TODO: Adjust these to more accurate readings within the rack
    tempMin = 25
    tempMax = 40

    try:
        while True:
            temperature = getTemperature()
            dutyCycle = translate(temperature, tempMin, tempMax)
            setPWM(dutyCycle)
            time.sleep(60)
    except KeyboardInterrupt:
        pass

runFan()

pwm.stop()
GPIO.cleanup()