import network
import config

def connect(blink=None):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if not sta_if.active():
        print("WiFi is not active")
        return sta_if
    if not sta_if.isconnected():
        print('connect WiFi...')
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for t in range(15):
        if sta_if.isconnected():
            return sta_if
        if blink:
            blink()
        time.sleep(1)
    print("WiFi is not connected using %s, %s" % (config.WIFI_SSID, config.WIFI_PASSWORD))
    return sta_if

