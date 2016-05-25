import pyaudio
import struct
import math
import datetime
import numpy
import wave
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

filename = '/home/pi/LogMSK/monitoring/' + datetime.datetime.now().strftime('%y%m%d') + '_monitoring.CSV'

trim = 93.97940008672037609572522210551

#A-weigthing -  B and A coef for 44100 Hz
Ba = [ 0.25574113, -0.51148225, -0.25574113,  1.0229645,  -0.25574113, -0.51148225, 0.25574113]
Aa = [ 1.00000000, -4.01957618, 6.18940644, -4.45319890, 1.42084295, -0.141825474, 0.00435117723]
#C-wegthing
Ac = [ 1.0, -2.13467496, 1.27933353, -0.14955985, 0.0049087]
Bc = [ 0.21700856, 0.00, -0.43401712, 0.00, 0.21700856]


#duration in seconds  of the sliding time weighted LEQ
SLIDE= 10
# One value (basic) Calibration 
CAL_VALUE_A= 27.8
CAL_VALUE_C= 26.0
#limit of level in dB
THRESHOLD = 88
#trigger recording
SECONDS = 5

def get_Leq1s(block):

    shorts = numpy.fromstring(block, dtype=numpy.int16)
    dBA = lfilter(Ba, Aa, shorts) 
    dBC = lfilter(Bc, Ac, shorts) 
    
    # iterate over the block.
    #sum_squares = 0.0
    #for sample in filteredshorts:
    ## sample is a signed short in +/- 32768. 
    ## normalize it to 1.0
    dataA = numpy.array(dBA, dtype=float)*SHORT_NORMALIZE
    sumA = numpy.sum(dataA ** 2.0) / len(dataA)
	
    dataC = numpy.array(dBC, dtype=float)*SHORT_NORMALIZE
    sumC = numpy.sum(dataC ** 2.0) / len(dataC)
    LeqC=(10.0 * math.log(sumC, 10.0)) + trim + CAL_VALUE_C
    LeqA=(10.0 * math.log(sumA, 10.0)) + trim + CAL_VALUE_A
    return LeqA,LeqC


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
	recordOn = 0
	trig = 0
        record = []
	while True:
	#for i in range(1000):
	    try:                                                    
	        block = stream.read(INPUT_FRAMES_PER_BLOCK)         
	    except IOError as e:                                      
	        errorcount += 1                                     
        	print( "(%d) Error recording: %s"%(errorcount,e) )  
        	noisycount = 1                                      
 
	    dBA1s, dBC1s = get_Leq1s(block)
	    print ("dBC_1sec=", str(dBC1s), "dBA_1sec=", str(dBA1s))

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
	     delta = dBG_S - THRESHOLD 
	     p=call(['/home/pi/MSK_utils/Playback_Master.sh - ' +str(round(delta))], shell=True,)
	     
	     #Trigger Recording
	     recordOn = 1

	    if recordOn == 1:
	     record.append(block)
	     trig += 1
	     if trig == 20:
	      filerecord = "/home/pi/LogMSK/recordings/" + datetime.datetime.now().strftime("%y%m%d_%H:%M:%S") + "_peak.wav"
	      trig = 0
	      recordOn = 0
	    
	      #Write wav file
	      wavefile = wave.open(filerecord, 'wb')
	      wavefile.setnchannels(CHANNELS)
	      wavefile.setsampwidth(pyaudio.get_sample_size(FORMAT))
	      wavefile.setframerate(RATE)
	      wavefile.writeframes(b''.join(record))
	      wavefile.close()
	      record = []
	    #writeCSV
	    mytime=datetime.datetime.now()
	    file=open(filename,"a")
	    file.write("dB,1s ")
	    file.write("{}, {} {}\n".format(mytime,dBC1s, dBA1s))
	    file.close()


	p.terminate()
slm()
