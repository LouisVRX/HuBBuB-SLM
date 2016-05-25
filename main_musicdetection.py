import pyaudio
import struct
import math
import datetime
import numpy
import wave
from scipy.signal import lfilter
from subprocess import PIPE, Popen, call

def getIndex():
   p = Popen(["bash", "/home/pi/MSK_utils/finddevices.sh"], stdout=PIPE, bufsize =1)
   INDEXDEVICE = p.communicate()[0],
   if INDEXDEVICE == "2":
     return(2)
   if INDEXDEVICE == "1":
     return(1)

FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 1
RATE = 44100
INDEX = getIndex()
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
SLIDE=15
# One value (basic) Calibration 
CAL_VALUE_A= 29.25
CAL_VALUE_C= 25.0
#limit of level in dB
THRESHOLD =80
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

def BTstatus():
   p = Popen(["bash", "/home/pi/MSK_utils/BTcon.sh"], stdout=PIPE, bufsize =1)
   BTcon = p.communicate()[0],
   return (BTcon)

# Configation Audio stream
pa = pyaudio.PyAudio()                                 
stream = pa.open(format = FORMAT,                      
         channels =1,                          
         rate = RATE,                                  
         input = True,                                 
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK,
         input_device_index = INDEX)
  



def slm():
	errorcount = 0                                                  
	Array_dB = numpy.array([])
	j = 0
	t = 0
	recordON = 0
	record30On = 0
	musicON = 0
	musicONcmpt = 0
	musicOFF = 0
	musicOFFcmpt = 0
	timeThreshold = 0
	trig = 0
	trig2 = 0
	trig30 = 0
	record = []
	record30 = []
	BTopen=1
	LineInMusic=0
	SessionBegin = 0
	while True:
	    try:                                                    
	        block = stream.read(INPUT_FRAMES_PER_BLOCK)         
	    except IOError as e:                                      
	        errorcount += 1                                     
        	#print( "(%d) Error recording: %s"%(errorcount,e) )  
        	noisycount = 1                                      
 
	    dBA1s, dBC1s = get_Leq1s(block)
	    #print ("dBA_1sec=", str(dBA1s))

            # Sliding GLobal LEQ
            # fill the buffer
	    if j<SLIDE:
	    #if i<SLIDE:
                Array_dB=numpy.append(Array_dB,dBA1s)
	    #slide the buffer
	    else:
                Array_dB= numpy.roll(Array_dB,-1)
                Array_dB[SLIDE-1]= dBC1s
       

	    ms = numpy.sum(10 ** (Array_dB/10.0))/len(Array_dB)
	    dBG_S=(10.0 * math.log(ms, 10.0))
	    #print ("Sliding dBC", str(SLIDE), "sec =", str(dBG_S))
	    #print (t)
	    j += 1
	    t += 1
		
	    #writeCSV
	    mytime=datetime.datetime.now()
	    file=open(filename,"a")
	    file.write("dB,1s ")
	    file.write("{}, {} {}\n".format(mytime,dBC1s, dBA1s))
	    file.close()		

           #every 10 minutes recordings
           #if t == 1800-9
	    if t ==591:
	     record30On =1
	     #print("record every 10  minute ON") 
	    if record30On == 1:
	     record30.append(block)
	     trig30 += 1
	     if trig30 == 10:
	      filerecord = "/home/pi/LogMSK/recordings/"+datetime.datetime.now().strftime("%y%m%d_%H:%M:%S")+"_30min.wav"
	      trig30 = 0
	      record30On = 0
	      t= 0
	      #print("10 min record done")
	      #Write wav file
	      wavefile = wave.open(filerecord, 'wb')
	      wavefile.setnchannels(CHANNELS)
	      wavefile.setsampwidth(pyaudio.get_sample_size(FORMAT))
	      wavefile.setframerate(RATE)
	      wavefile.writeframes(b''.join(record30))
	      wavefile.close()
	      record30 = []

	    #print (musicONcmpt)
#threshold recordings
	    if dBG_S > THRESHOLD:
             musicOFFcmpt=0
             musicOFF=0
             recordON = 1
             timeThreshold  += 1
             musicONcmpt +=1
             if musicONcmpt > 11:
               musicON=1
               #print ("Music is ON")
              
	    if(recordON == 1 and timeThreshold < 11) or (trig > 1 and recordON==0):
              record.append(block)
              trig += 1
              #print ("record second ", trig, "seconds")
              if trig == 10:
               filerecord = "/home/pi/LogMSK/recordings/"+datetime.datetime.now().strftime("%y%m%d_%H:%M:%S")+"_peak.wav"
               trig = 0
               recordON = 0
	       #Write wav file
               wavefile = wave.open(filerecord, 'wb')
               wavefile.setnchannels(CHANNELS)
               wavefile.setsampwidth(pyaudio.get_sample_size(FORMAT))
               wavefile.setframerate(RATE)
               wavefile.writeframes(b''.join(record))
               wavefile.close()
               record = []
               
	    if(recordON == 1 and 110<timeThreshold<120) or (trig2 > 1 and recordON==0):
              record.append(block)
              trig2 += 1
              #print ("record second ", trig, "second")
              if trig2 == 10:
               filerecord = "/home/pi/LogMSK/recordings/"+datetime.datetime.now().strftime("%y%m%d_%H:%M:%S")+"_peak.wav"
               trig2 = 0
               recordON = 0
               timeThreshold =0
               #Write wav file
               wavefile = wave.open(filerecord, 'wb')
               wavefile.setnchannels(CHANNELS)
               wavefile.setsampwidth(pyaudio.get_sample_size(FORMAT))
               wavefile.setframerate(RATE)
               wavefile.writeframes(b''.join(record))
               wavefile.close()
               record = []                

	    if dBG_S < THRESHOLD:
             recordON=0
             timeThreshold=0
             musicONcmpt=0
             musicON=0
             SessionBegin=0
             #print("below",THRESHOLD)
             musicOFFcmpt +=1
             if musicOFFcmpt > 5:
              musicOFF=1
              #print("Music and sounds OFF")
              
	    if musicON == 1:

	      if BTstatus() == (b'0',) and LineInMusic==0:
	         p = Popen(["sudo", "hciconfig", "hci0", "noscan"])
	         BTopen = 0
	         LineInMusic = 1
	      #if LineInMusic == 1 :
	         #print ("Music From LineIn")
	      #else:
	         #print ("Music From Bluetooth")
	    if musicOFF == 1:
	      LineInMusic=0
	      if  BTstatus() == (b'0',):
	       if BTopen == 0 : 	         
	         p = Popen(["sudo", "hciconfig", "hci0", "piscan"])
	         BTopen = 1
	         #print ("Bluetooth reactivated")
	      else:
	       if musicOFFcmpt < 7:
	         p = Popen(["sudo", "bash", "/home/pi/MSK_utils/BTdecon.sh"])

	p.terminate()
slm()

