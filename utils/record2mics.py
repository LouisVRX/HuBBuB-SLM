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
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 1
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)


# Configation Audio stream USB card 
pa = pyaudio.PyAudio()                                 
stream = pa.open(format = FORMAT,                      
         channels = 1,                         
         rate = 48000,                                  
         input = True,                                 
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK,input_device_index=0)
  
 # Configation Audio stream UMIK
pa2 = pyaudio.PyAudio()                                 
stream2 = pa2.open(format = FORMAT,                      
         channels =1,                          
         rate = 48000,                                  
         input = True,                                 
         frames_per_buffer = INPUT_FRAMES_PER_BLOCK,
		 input_device_index = 1)
		 
	
def slm():
	errorcount = 0                                                  
	j = 0
	t=0
	record = []
	record2 = []

	# records 10 seconds 
	for i in range(10):
	 try:
	  block = stream.read(INPUT_FRAMES_PER_BLOCK)
	  block2 = stream2.read(INPUT_FRAMES_PER_BLOCK)
	 except IOError as e:                                      
	  errorcount += 1
	  print( "(%d) Error recording: %s"%(errorcount,e) )  	
 	
	 record.append(block)
	 record2.append(block2)
	 print (i)
		
	filerecordUmik = "/home/pi/python_code/umik.wav"
	filerecordUSB = "/home/pi/python_code/usb.wav"
	
	#Write wav file
	wavefileUmik = wave.open(filerecordUmik, 'wb')
	wavefileUmik.setnchannels(1)
	wavefileUmik.setsampwidth(pyaudio.get_sample_size(FORMAT))
	wavefileUmik.setframerate(48000)
	wavefileUmik.writeframes(b''.join(record2))
	wavefileUmik.close()

	wavefileUSB = wave.open(filerecordUSB, 'wb')
	wavefileUSB.setnchannels(1)
	wavefileUSB.setsampwidth(pyaudio.get_sample_size(FORMAT))
	wavefileUSB.setframerate(48000)
	wavefileUSB.writeframes(b''.join(record))
	wavefileUSB.close()
	

	pa.terminate()
	pa2.terminate()
slm()
	 
