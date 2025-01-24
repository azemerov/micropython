import machine, sdcard, os
def mount(mountDir='/fs'):
    sd = sdcard.SDCard(machine.SPI(1), machine.Pin(15))
    vfs = os.VfsFat(sd)
    os.mount(vfs, mountDir)

def umount(mountDir='/fs'):
    os.umount(mountDir)

def ls(dn='/fs'):
    return os.listdir(dn)

def write(fn='/fs/test.txt', lines=['abcd','1234']):
   with open(fn, 'a') as f:
       for line in lines:
           f.write(line + '\n')

def read(fn='/fs/test.txt'):
    with open(fn, 'r') as f:
       result = f.read()
       print("read ", len(result), "bytes, string=", result)
