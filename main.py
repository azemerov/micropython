import config
import machine
import time
import network
import dht
#import onewire
#import ds18x20az as ds18x20
#import math
from machine import I2C, Pin
#import BME280
import urequests
#import ujson

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

def isdebug():
    debug = Pin(cDEBUG, Pin.IN, Pin.PULL_UP)
    if debug.value()==0:
        print("DEBUG MODE!")
        return True
    return False

def connect():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    #print(sta_if.scan())
    #print(sta_if.ifconfig())
    if not sta_if.active():
        print("WiFi is not active")
        return sta_if
    if not sta_if.isconnected():
        print('conenct WiFi...')
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        time.sleep(3)
    if not sta_if.isconnected():
        print("WiFi is not connected using %s, %s" % (config.WIFI_SSID, config.WIFI_PASSWORD))
        return sta_if
    return sta_if

data = list()

def send_data():
    #print('send_data')
    try:
        x = connect()
        if not x:
            blink(5, 0.1, 0.1)
            print("cannot connect WiFi")
            with open("error.txt", "a") as f:
                f.write("cannot connect WiFi\n")
            return None
        blink()
        while data:
            temp, humidity, pressure, ts = data.pop()

            #url =  'https://data.mongodb-api.com/app/data-blzil/endpoint/data/beta/action/insertOne'
            #url = f'http://192.168.1.86:5000/addtemp?temp={temp}'
            #url = f'http://192.168.1.104:5000/addtemp?temp={temp}'
            #print('make url')
            url = f'https://vespa-proxy.herokuapp.com/addtemp?temp={temp}&humidity={humidity}&pressure={pressure}&ts={ts}'
            #print('call GET', url)
            res = urequests.get(url)
            #print( temp, humidity, res.status_code )
            #print('return', res)
        return res
    except Exception as e:
        if isdebug():
            print('ERROR')
        else:
            with open("error.txt", "a") as f:
                f.write(f"send_data(): {str(e)}\n")
        return None

    ##Directly send to MongoDB API
    #api_key = 'Z6p51gsY6CrdyGkhmLCy3uYHJJCmRWVvoVZHOZqPSfbxTX8u64tZg916BfdWLqXN'
    #data = ujson.dumps({"collection": "temperature", "database": "weatherDb", "dataSource": "VespaCluster", "document": {
    #    "ts": "2022-05-01", "temp": temp}})
    #headers = {
    #        "content-type": "application/json",
    #        "api-key": api_key,
    #        "Access-Control-Request-Headers": "*",
    #        }
    #res = urequests.post(url, headers=headers, data=None) #.json()
    #return res

def blink(cnt=1, time1=0.3, time2=0.3):
    led = Pin(cLED, Pin.OUT)
    for _ in range(cnt):
        led.off()
        time.sleep(time1)
        led.on()
        time.sleep(time2)
    return led

def _readDS18x20(pull=Pin.PULL_UP):
    p = Pin(D2, Pin.IN, pull) #Pin.PULL_UP)
    s = ds18x20.DS18X20(onewire.OneWire(p))
    roms = s.scan()
    #print(roms)
    s.convert_temp()
    time.sleep_ms(750)
    return s.read_temp(roms[0]), 0

def readDHT22():
    d = dht.DHT22(Pin(cDHT))
    d.measure()
    blink()
    return d.temperature(), d.humidity()

def _readNTC(R=14290.00, R25=9660.00, B=3380):
    C25 = 298.15
    C0 = 273.15
    V = 3.3

    p = machine.ADC(0)
    n = p.read()
    r = n*R/(1023-n)
    print(n, 'N', r, 'Ohm')
    t = 1 / ((1/C25) + (1/B) * math.log(r/R25))
    print(t, 'K')
    t = t - C0
    return t, 0

getTempHum = readDHT22

def readBME():
    # also look at https://github.com/rm-hull/bme280
    #
  i2c = I2C(scl=Pin(cSCL), sda=Pin(cSCA), freq=10000)
  #from BME280 import BME280
  from BME280_int import BME280
  bme = BME280(i2c=i2c)
  #temp = bme.temperature
  #hum = bme.humidity
  #pres = bme.pressure
  #temp, pres, hum = bme.readall()
  temp, pres, hum = bme.values
  return temp, hum, pres

getPress = readBME

def seeLevelPressure(height, pressure, temperature):
    import math
    v = 1 - (0.0065 * height) / (temperature + 0.0065*height + 273.15)
    v = pressure * pow(v, -5.257)
    return v

def run():
    blink()
    
    #ts = rtc.datetime()
    #ts = "%04d-%02d-%02d %02d:%02d:%02d" % (ts[0:3] + ts[4:7])
    ts = int(round(time.time()))
    temp, humidity = getTempHum()
    temp1, _, pressure = getPress()
    pressure = seeLevelPressure(179, pressure, temp1)
    data.append((temp, humidity, pressure, ts))
    if len(data) > 0:
        send_data()
    blink()

    rtc = machine.RTC()
    with open("data.txt", "a") as f:
        f.write(f"{ts} {temp} {humidity} {pressure}\n")

    led = blink()

    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, SLEEP_PERIOD)
    if not isdebug():
        machine.deepsleep()


blink()
run()
# after one iteration machine does not do anything, just goes to deep sleep
# the alarm will wake up machine which will cause a next round of main module excecution

