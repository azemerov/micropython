import ADXL345
from machine import Pin, I2C
import time
from math import sqrt, pow

D0 = 16
D1 = 5
D2 = 4
D3 = 0
D4 = 2
D5 = 14
D6 = 12
D7 = 13
D8 = 15

def Avg(coll):
    x = 0.0
    y = 0.0
    z = 0.0
    for c in coll:
        x += c[0]
        y += c[1]
        z += c[2]
    print(x,y,z)
    return x/len(coll), y/len(coll), z/len(coll)

def init(calibration_count=5):
    i2c = I2C(scl=Pin(D2), sda=Pin(D1), freq=10000)
    #i2c = I2C(scl=Pin(D4), sda=Pin(D5), freq=1000)
    adx = ADXL345.ADXL345(i2c)
    zero = Avg(read(adx, (0,0,0), calibration_count, 0))
    print(zero)
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

def read(adxl, zero, n=1, sleep_time=0):
    started = time.time_ns()
    result = []
    for _ in range(n):
        r = adxl.values
        #print(zero, r)
        r = (round(r[0]-zero[0],-1), round(r[1]-zero[1],-1), round(r[2]-zero[2],-1))
        result.append(r)
        if n>1 & sleep_time:
            time.sleep_ms(sleep_time)
    print('elapsed:', (time.time_ns() - started)/1000000, 'ms')
    return result

