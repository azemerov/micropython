#import config
import machine
import time
#import network
#import dht
##import onewire
##import ds18x20az as ds18x20
##import math
from machine import I2C, Pin
##import BME280
import urequests
import ujson
import connect

D0 = 16
D1 = 5
D2 = 4
D4 = 2
D5 = 14
D6 = 12
cDHT = D6 #was D2
cLED = D4
cDEBUG = D5
cSCL = D1
cSCA = D2

SLEEP_PERIOD = 20*60*1000 # 20 minutes in milliseconds
SLEEP_PERIOD = 5*1000 # 5 seconds

def isdebug():
    debug = Pin(cDEBUG, Pin.IN, Pin.PULL_UP)
    if debug.value()==0:
        print("DEBUG MODE!")
        return True
    return False

def blink(cnt=1, time1=0.3, time2=0.3):
    led = Pin(cLED, Pin.OUT)
    for _ in range(cnt):
        led.off()
        time.sleep(time1)
        led.on()
        time.sleep(time2)
    return led

def run():
    blink(1)
    connect.connect()
    blink(2)
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        print("from DEEPSLEEP_RESET")
    else:
        if machine.reset_cause() == machine.PWRON_RESET:
            print("reset from PWRON_RESET")
        else:
            print("reset from", machine.reset_cause())
        res = urequests.get("http://worldtimeapi.org/api/timezone/America/Chicago")
        if res.status_code==200:
            day, time = ujson.loads(res.text)["datetime"].split('T',1)
            day = day.split('-')
            time, zone = time.split('.')
            time = time.split(':')
            zone = -int(zone.split('-')[1].split(':')[0])
            rtc.datetime((int(day[0]), int(day[1]), int(day[2]), 0, int(time[0]), int(time[1]), int(time[2]), 0))
            print("rtc is initialized", (int(day[0]), int(day[1]), int(day[2]), int(time[0]), int(time[1]), int(time[2]), 0, zone))
        else:
            print("status_code=", res.status_code)
    print("...")
    print("time=")
    print(rtc.datetime())
    blink(3)
                   
    print("start the sleep for", SLEEP_PERIOD, "seconds")
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, SLEEP_PERIOD)
    machine.deepsleep()

#blink()
rtc = machine.RTC()

if not isdebug():
    run()
# after one iteration machine does not do anything, just goes to deep sleep
# the alarm will wake up machine which will cause a next round of main module excecution

