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
import ujson

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

SLEEP_PERIOD = 30*60*1000 # 30 minutes in milliseconds
#SLEEP_PERIOD = 1*60*1000

def isdebug():
    debug = Pin(cDEBUG, Pin.IN, Pin.PULL_UP)
    if debug.value()==0:
        print("DEBUG MODE!")
        return True
    return False

def write_file(fname, text):
    with open(fname, "a") as f:
        f.write(text)

def connect():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    #print(sta_if.scan())
    #print(sta_if.ifconfig())
    if not sta_if.active():
        print("WiFi is not active")
        return sta_if
    if not sta_if.isconnected():
        print('connect WiFi...')
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for t in range(15):
        if sta_if.isconnected():
            return sta_if
        time.sleep(1)
    print("WiFi is not connected using %s, %s" % (config.WIFI_SSID, config.WIFI_PASSWORD))
    return sta_if

data = list()

def indirect_send_data_(data):
    try:
        x = connect()
        if not x or not x.isconnected():
            print("cannot connect WiFi")
            with open("error.txt", "a") as f:
                f.write("cannot connect WiFi\n")
            return None
        while data:
            ts, temp, humidity, pressure = data.pop()
            url = f'http://192.168.1.67:5000/addtemp?temp={temp}&humidity={humidity}&pressure={pressure}&ts={ts}'
            #url = f'http://192.168.1.104:5000/addtemp?temp={temp}'
            #print('make url')
            #url = f'https://vespa-proxy.herokuapp.com/addtemp?temp={temp}&humidity={humidity}&pressure={pressure}&ts={ts}'
            #print('call GET', url)
            res = urequests.get(url)
        return res
    except Exception as e:
        print("error", str(e))
        if isdebug():
            print('ERROR')
        else:
            write_file("error.txt", f"send_data(): {str(e)}\n")
        return None

def send_data(data):
#Directly send to MongoDB API
    try:
        x = connect()
        if not x or not x.isconnected():
            print("cannot connect WiFi")
            write_file("error.txt", "cannot connect WiFi\n")
            return None

        cnt = 0
        while data:
            ts, temp, humidity, pressure = data[0]
            print(f"sending {ts}, {temp}, {humidity}, {pressure}")
            url =  'https://data.mongodb-api.com/app/data-blzil/endpoint/data/beta/action/insertOne'
            api_key = 'Z6p51gsY6CrdyGkhmLCy3uYHJJCmRWVvoVZHOZqPSfbxTX8u64tZg916BfdWLqXN'
            req = ujson.dumps({
                "collection": "temperature",
                "database": "weatherDb",
                "dataSource": "VespaCluster",
                "document": {
                    "ts": {"$date": ts},
                    #"ts": {"$date": {"$numberLong": "%s" % int(round(time.time())}}
                    "humidity": humidity,
                    "pressure": pressure,
                    "temp": temp
                }
            })
            headers = {
                    "content-type": "application/json",
                    "api-key": api_key,
                    "Access-Control-Request-Headers": "*",
                    }
            res = urequests.post(url, headers=headers, data=req)
            if res.status_code >= 200 and res.status_code <= 299:
                #with open("data.txt", "a") as f:
                #    f.write(f"{res.text}\n")
                print('OK', res.status_code, res.text)
                data.pop()
                cnt -= 1
            else:
                print('ERROR', res.status_code, res.text)
                write_file("error.txt", f"send_data(): unable to send data: {res.status_code} {res.text}\n")
                break
        return cnt
    except Exception as e:
        print('send_data() ERROR:', str(e))
        if not isdebug():
            write_file("error.txt", f"send_data(): {str(e)}\n")
        return None

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
    blink(1)
    print('try to connect')
    x = connect()
    if not x or not x.isconnected():
        print("cannot connect WiFi")
        write_file("error.txt", "cannot connect WiFi\n")
        return

    #ts = rtc.datetime()
    #if machine.reset_cause() == machine.DEEPSLEEP_RESET and ts[0] > 2020:
    #    print("from DEEPSLEEP_RESET")
    #else:
    #    print('try to get time')
    #    if machine.reset_cause() == machine.PWRON_RESET:
    #        print("reset from PWRON_RESET")
    #    else:
    #        print("reset from", machine.reset_cause())
    #
    #    for tt in range(0, 10):
    #        try:
    #            res = urequests.get("http://worldtimeapi.org/api/timezone/America/Chicago")
    #            if res.status_code==200:
    #                ts = ujson.loads(res.text)["datetime"]
    #                #day, time = ujson.loads(res.text)["datetime"].split('T',1)
    #                #day = day.split('-')
    #                #day = [int(day[0]), int(day[1]), int(day[2])]
    #                #time, zone = time.split('.')
    #                #time = time.split(':')
    #                #zone = int(zone.split('-')[1].split(':')[0])
    #                #time = [int(time[0]), int(time[1]), int(time[2])]
    #                #time[0] += zone
    #                #if time[0] >= 24:
    #                #        time[0] -= 24
    #                #        day[2] += 1
    #                #        if (day[1] in (1,3,5,7,8,10,12) and day[2] == 32) \
    #                #        or (day[1] in (4,6,9,11) and day[2] == 31) \
    #                #        or (day[1] == 2 and day[2] == 29):
    #                #            day[2] = 1
    #                #            day[1] += 1
    #                #rtc.datetime((day[0], day[1], day[2], 0, time[0], time[1], time[2], 0))
    #                #print("rtc is initialized", day, time, zone)
    #                break
    #            else:
    #                print("status_code=", res.status_code)
    #        except Exception as e:
    #            print("get time ERROR: ", tt, str(e))
    #            if tt == 9:
    #                write_file("error.txt", f"ERROR, cannot get current time error={str(e)}\n")
    #                return
    #            else:
    #                time.sleep(3)
    #ts = rtc.datetime()
    #if ts[0] < 2020:
    #    return

    ts = None
    for tt in range(0, 10):
        try:
            res = urequests.get("http://worldtimeapi.org/api/timezone/America/Chicago")
            if res.status_code==200:
                ts = ujson.loads(res.text)["datetime"]
                break
            else:
                print("status_code=", res.status_code)
        except Exception as e:
            print("get time ERROR: ", tt, str(e))
            if tt == 9:
                write_file("error.txt", f"ERROR, cannot get current time error={str(e)}\n")
                return
            else:
                time.sleep(3)
    print("time=", ts)
    if not ts:
        return
    blink(2)
        
    #ts = rtc.datetime(); ts = "%04d-%02d-%02dT%02d:%02d:%02dZ" % (ts[0:3] + ts[4:7]); ts = int(round(time.time()))
    temp, humidity = getTempHum()
    pressure = 0
    try:
        temp1, _, pressure = getPress()
        pressure = seeLevelPressure(179, pressure, temp1)
    except Exception as e:
        print("getPress() raised an error:", str(e))
    #pressure = seeLevelPressure(179, pressure, temp1)
    print(ts, temp, humidity, pressure)
    data.append((ts, temp, humidity, pressure))
    if len(data) > 0:
        indirect_send_data_(data)
    blink(3)
    write_file("data.txt", f"{ts} {temp} {humidity} {pressure}\n")

rtc = machine.RTC()
if not isdebug():
    run()
    blink(4)
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, SLEEP_PERIOD)
    machine.deepsleep()
# after one iteration machine does not do anything, just goes to deep sleep
# the alarm will wake up machine which will cause a next round of main module excecution
