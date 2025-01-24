import ADXL345
from machine import Pin, I2C, ADC, RTC, DEEPSLEEP, deepsleep
import time
from math import sqrt, pow
import sdfs

D0 = 16
D1 = 5
D2 = 4
D3 = 0
D4 = 2
D5 = 14
D6 = 12
D7 = 13
D8 = 15
#
cSCL = D2
cSDA = D1
#
#led1 = Pin(D0, Pin.OUT)
led2 = Pin(D4, Pin.OUT)
# led blink patterns
START = ((1,1,300), (0,0,300))
ERROR = ((1,0,100), (0,1,100))
DEBUG = ((1,1,100), (0,0,100))
#
startTime = time.time()
lastTime = None
fileName = None
#
LONG_WAIT_PERIOD = 600     # 10 minute
SHORT_WAIT_PERIOD= 60      # 1 minute
NOEVENTS_SECONDS = 60      # if no events for more than NOEVENTS_SECONDS seconds, go sleep
SLEEP_SECONDS    = 600     # sleep 10 minutes

def set_wait_seconds(seconds):
    #print('set waiting period as ', seconds, 'seconds')
    global NOEVENTS_SECONDS
    NOEVENTS_SECONDS = seconds

def leds(status):
    if status==0:
        #led1.on()
        led2.on()
    #elif status==1:
    #    led1.off()
    #    led2.on()
    #elif status==2:
    #    led1.on()
    #    led2.off()
    else:
        #led1.off()
        led2.off()

def blinks(pattern, count):
    for _ in range(count):
        for p in pattern:
            #if p[0]:
            #    led1.off()
            #else:
            #    led1.on()
            if p[1]:
                led2.off()
            else:
                led2.on()
            time.sleep(p[2]/1000)

def Avg(coll):
    x = 0.0
    y = 0.0
    z = 0.0
    for c in coll:
        x += c[0]
        y += c[1]
        z += c[2]
    return x/len(coll), y/len(coll), z/len(coll)

def init(calibration_count=0):
    i2c = I2C(scl=Pin(cSCL), sda=Pin(cSDA), freq=10000)
    adx = ADXL345.ADXL345(i2c)
    if calibration_count:
        zero = Avg(read(adx, (0,0,0), calibration_count, 0))
    else:
        zero = (0,0,0)
    return adx, zero

def read0(adxl, n=1, sleep_time=10):
    for _ in range(n):
        print(adxl.xValue, adxl.yValue, adxl.zValue)
        if n>1 & sleep_time:
            time.sleep_ms(sleep_time)

def read1(adxl, n=1, sleep_time=10):
    for _ in range(n):
        print(sqrt(pow(adxl.xValue,2) +  pow(adxl.yValue,2) + pow(adxl.zValue,2)))
        if n>1 & sleep_time:
            time.sleep_ms(sleep_time)

def read(adxl, zero, cycles=1, sleep_time=0):

    result = []
    for _ in range(cycles):
        leds(1)
        r = adxl.values
        leds(0)

        r = (round(r[0]-zero[0],-1), round(r[1]-zero[1],-1), round(r[2]-zero[2],-1))

        #if any((abs(x)>300 for x in r)):
        #    leds(3)
        #elif any((abs(x)>100 for x in r)):
        #    leds(2)
        #el
        #if any((abs(x)>30 for x in r)):
        #    leds(1)
        #else:
        #    leds(0)
            
        if any((abs(x)>30 for x in r)):
            global lastTime
            lastTime = time.time()
            set_wait_seconds(LONG_WAIT_PERIOD)  # waiting for a next even for 10 minutes before going to sleep
            result.append(str((lastTime - startTime, r[0], r[1], r[2])))
            print(r)

        if cycles > 1 & sleep_time:
            time.sleep_ms(sleep_time)
    return result
    
def deep_sleep():
    print('Going into deepsleep for {seconds} seconds...'.format(seconds=SLEEP_SECONDS))
    rtc = RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, SLEEP_SECONDS * 1000)
    leds(0)
    deepsleep()
    

def isdebug():
    debug = ADC(0)
    if debug.read() > 100:
        #print("DEBUG MODE!")
        return True
    else:
        #print("RUNTIME MODE!")
        return False

def main():
    print("main()")
    sdfs.mount()
    try:
        files = sdfs.ls("/fs")
        c = 1
        global fileName
        while True:
            fileName = "results"+str(c)+".txt"
            if fileName not in files:
                break
            c += 1
        fileName = "/fs/"+fileName
        print("use file =", fileName)

        set_wait_seconds(SHORT_WAIT_PERIOD)
        global startTime, lastTime
        startTime = time.time()
        lastTime = startTime
        
        # recalibrate every 10 cycles and continue forewer
        while True:
            adx, zero = init()
            zero = (30, -70, 260)  # use hardcoded calibration
            result = read(adx, zero, 10, 500)
            print(len(result), "triggered events")
            if isdebug():
                break
            elif result:
                sdfs.write(fileName, result)

            if (time.time() - lastTime) > NOEVENTS_SECONDS:
                print("time is over, sleep!")
                #if not isdebug():
                deep_sleep()
            else:
                print('seconds left:', lastTime + NOEVENTS_SECONDS - time.time())

    except Exception as e:
        print("exception:", e)
        blinks(ERROR, 50)
        
    print("unmounting...")
    sdfs.umount()
    leds(0)

print('loaded')