# source http://stackoverflow.com/questions/4160175/detect-tap-with-pyaudio-from-live-mic

import pyaudio
import struct
import math
import datetime
import numpy
from scipy.signal import lfilter
from subprocess import Popen
from subprocess import call



FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 1
RATE = 44100
INDEX = 2  
INPUT_BLOCK_TIME = 1
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
filename = '/home/pi/LogMSK/monitoring/log_monitoring.CSV'
trim = 93.97940008672037609572522210551
#A-weigthing -  B and A coef for 44100 Hz
B = [ 0.25574113, -0.51148225, -0.25574113,  1.0229645,  -0.25574113, -0.51148225, 0.25574113]
A = [ 1.00000000, -4.01957618, 6.18940644, -4.45319890, 1.42084295, -0.141825474, 0.00435117723]
#C-wegthing
Ac = [ 1.0, -2.13467496, 1.27933353, -0.14955985, 0.0049087]
Bc = [ 0.21700856, 0.00, -0.43401712, 0.00, 0.21700856]


#duration in seconds  of the sliding time weighted LEQ
SLIDE= 10
# One value (basic) Calibration 
CAL_VALUE= 0
#limit of level in dB
THRESHOLD = 75

def get_Leq1s(block):

#    count = len(block)/2
#    format = "%dh"%(count)
#    shorts = struct.unpack( format, block )

    shorts = numpy.fromstring(block, dtype=numpy.int16)
    filtshorts = lfilter(Bc, Ac, shorts) 
    
    # iterate over the block.
    #sum_squares = 0.0
    #for sample in filteredshorts:
    ## sample is a signed short in +/- 32768. 
    ## normalize it to 1.0
    data = numpy.array(filtshorts, dtype=float)*SHORT_NORMALIZE
    ms = numpy.sum(data ** 2.0) / len(data)
       # n = sample * SHORT_NORMALIZE
	#sum_squares += n*n
       # ms = sum_squares/len(block)
#    math.sqrt( sum_squares / count )
    dBC=(10.0 * math.log(ms, 10.0)) + trim +CAL_VALUE
    return dBC


# Configation Audio stream
pa = pyaudio.PyAudio()                                 
stream = pa.open(format = FORMAT,                      
         channels = CHANNELS,                          
         rate = RATE,                                  
         input = True,                                 
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK,
	 input_device_index = INDEX)   



def slm():
	errorcount = 0                                                  
	Array_dB = numpy.array([])
	j = 0

	while True:
	#for i in range(1000):
	    try:                                                    
	        block = stream.read(INPUT_FRAMES_PER_BLOCK)         
	    except IOError as e:                                      
	        errorcount += 1                                     
        	print( "(%d) Error recording: %s"%(errorcount,e) )  
        	noisycount = 1                                      
 
	    dBC1s = get_Leq1s(block)
	    print ("dBC_1sec=", str(dBC1s))

            # Sliding GLobal LEQ
            # fill the buffer
	    if j<SLIDE:
	    #if i<SLIDE:
                Array_dB=numpy.append(Array_dB,dBC1s)
	    #slide the buffer
	    else:
                Array_dB= numpy.roll(Array_dB,-1)
                Array_dB[SLIDE-1]= dBC1s
       

	    ms = numpy.sum(10 ** (Array_dB/10.0))/len(Array_dB)
	    dBG_S=(10.0 * math.log(ms, 10.0))
	    print ("Sliding dBC", str(SLIDE), "sec =", str(dBG_S))

	    j += 1            
	
	    #basic limiter 
	    if dBG_S > THRESHOLD:
	     #p=Popen(['aplay', 'Brixton.wav'])
	     #delta = THRESHOLD - dBG_S
	     delta = dBG_S - THRESHOLD
	     deltaP = delta / 2 
	     p=call(['/home/pi/Playback_Master.sh - ' +str(round(delta))], shell=True,)
	    
	    #writeCSV
	    mytime=datetime.datetime.now()
	    file=open(filename,"a")
	    file.write("dB(C)1s ")
	    file.write("{}, {}\n".format(mytime,dBC1s))
	    file.close()


	p.terminate()

#call(["amixer", "-c", "2", "set", "Mic", "capture", str(mic_gain) + "dB"])
slm()
