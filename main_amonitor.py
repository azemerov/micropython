import amonitor

if amonitor.isdebug():
    print("Debug!")
    amonitor.blinks(amonitor.DEBUG, 6)
else:
    print("Runtime!!!")
    amonitor.blinks(amonitor.START, 10)
    amonitor.main()
