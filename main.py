# source http://stackoverflow.com/questions/4160175/detect-tap-with-pyaudio-from-live-mic

import pyaudio
import struct
import math
import datetime
import numpy
from soundlevelmeter import slm
from audio.devices import DeviceIndex


# Audio Flow Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100 #Constrained by the filters coefficients (see slm and Couvreur lib -octave- for more details)
INDEX = DeviceIndex("HDA Intel PCH: 92HD81B1X5 Analog (hw:0,0)")
INPUT_BLOCK_TIME = 1
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)

# Sound level meter Parameters
# Duration in seconds  of the sliding time weighted LEQ
SLIDE= 10
# One value (basic) Calibration
CAL_VALUE_A= 27.8
CAL_VALUE_C= 26.0
#limit of level in dB
THRESHOLD = 90

# Configation Audio stream
pa = pyaudio.PyAudio()
stream = pa.open(format = FORMAT,
         channels = CHANNELS,
         rate = RATE,
         input = True,
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK,
	     input_device_index = INDEX)

def SLM():
    errorcount = 0
    Array_dB = numpy.array([])
    dB_t = 0

    while True:
        try:
            block = stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError as e:
            errorcount += 1
            print( "(%d) Error recording: %s"%(errorcount,e) )
            noisycount = 1

        thismoment=datetime.datetime('%H:%M:%S.%f')

        dBA1s, dBC1s = slm.Leq1s(block, CAL_VALUE_A, CAL_VALUE_C)
        print str(thismoment), "dBC_1sec=", str(dBC1s), "dBA_1sec=", str(dBA1s)

        # Sliding GLobal LEQ
        if dB_t < SLIDE:
            # fill the buffer
            Array_dB = numpy.append(Array_dB,dBC1s)
        else:
            # slide the buffer
            Array_dB = numpy.roll(Array_dB,-1)
            Array_dB[SLIDE-1] = dBC1s

        ms = numpy.sum(10 ** (Array_dB/10.0))/len(Array_dB)
        dBG_S=(10.0 * math.log(ms, 10.0))

        thismoment=datetime.datetime.now()
        print str(thismoment), "Sliding dBC", str(SLIDE), "sec =", str(dBG_S)

        dB_t += 1

# Launch the main fonction.
SLM()
