import sys
import pyaudio

## index the devices in the system

p = pyaudio.PyAudio()
count = p.get_device_count()
devices = []

for i, dev in enumerate(devices):
    print( "%d - %s" % (i, dev['name']))

info = p.get_device_info_by_index(0)
print (info)
info1 = p.get_device_info_by_index(1)
print (info1)
info2 = p.get_device_info_by_index(2)
print (info2)
