# micropython
set of programs for execution on ESP8266
1) weather - monitor temperature, humidity and pressure
2) ...
'
# first of all upload micropyrthon firmware to ESP board
esptool.py --baud 460800 write_flash --flash_size=detect -fm dout 0 /mnt/chromeos/MyFiles/Downloads/esp8266-20220603-unstable-v1.18-567-g2111ca0b8.bin
# start remote shell over COM port
rshell --port /dev/ttyUSB0
# then run micropython
repl
# you may execute main.py
import main

# current version uses main_save2.py as main module:
cp main_save2.py /pyboard/main.py
