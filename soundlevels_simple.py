import pyaudio
from hubbub import get_leq, get_leq_a, get_leq_c, get_device_index
import numpy as np
from traceback import format_exc



def main():
    ### CONFIG ###
    # Microphone device name
    soundcard_name = 'NSRT_mk3'
    # Sampling Frequency (for dBA and dBC : can be either 44100 or 48000)
    sampling_rate = 48000
    # Buffer Size
    buffer_size = 4096
    # Calibration levels (in dB)
    calibration = 0
    calibration_A = 0
    calibration_C = 0


    ### CREATE STREAM ###
    audio_format = pyaudio.paInt16
    dev_index = get_device_index(soundcard_name)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=audio_format,
                     channels=1,
                     rate=sampling_rate,
                     input=True,
                     frames_per_buffer=buffer_size,
                     input_device_index=dev_index)


    ### LOOP ###
    stream.start_stream()
    try:
        while True:
            raw_data = stream.read(buffer_size, exception_on_overflow=False)
            data = np.frombuffer(raw_data, dtype=np.int16)
            # COMPUTE LEQ
            dB = get_leq(data, rate=sampling_rate, cal_value=calibration)
            dBA = get_leq_a(data, rate=sampling_rate, cal_value=calibration_A)
            dBC = get_leq_c(data, rate=sampling_rate, cal_value=calibration_C)
            print(f"dB={dB} dBA={dBA} dBC={dBC}")
    except Exception as e:
        print(f'Error while processing data : {format_exc()}')



if __name__ == '__main__':
    print('---------------------')
    print('  Sound Level Meter')
    print('---------------------')
    main()
