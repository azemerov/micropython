from machine import Pin, I2C
from time import sleep
import BME280

D1 = 5
D2 = 4
D4 = 2
D5 = 14

def test(scl, sda):
  # ESP32 - Pin assignment
  #i2c = I2C(scl=Pin(scl), sda=Pin(sda), freq=10000)
  # ESP8266 - Pin assignment
  i2c = I2C(scl=Pin(scl), sda=Pin(sda), freq=10000)

  while True:
    bme = BME280.BME280(i2c=i2c)
    #temp = bme.temperature
    #hum = bme.humidity
    #pres = bme.pressure
    temp, pres, hum = bme.readall()
    # uncomment for temperature in Fahrenheit
    #temp = (bme.read_temperature()/100) * (9/5) + 32
    #temp = str(round(temp, 2)) + 'F'
    print('Temperature: ', temp)
    print('Humidity: ', hum)
    print('Pressure: ', pres)

    sleep(5)

#test(D1, D2)


