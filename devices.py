#!/usr/bin/env python
import pyaudio
p = pyaudio.PyAudio()


def DeviceIndex(NAME):
    for i in range(p.get_device_count()):
        if p.get_device_info_by_index(i).get('name') == NAME:
            return (int(i))
    print ("Device " + str(NAME) + " not Found")
    return (None)


def __main__():
    for i in range(p.get_device_count()):
        print str(i)+ ": " + str(p.get_device_info_by_index(i).get('name'))

__main__()
