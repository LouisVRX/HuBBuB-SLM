import pyaudio
from hubbub import get_leq, get_leq_a, get_leq_c, get_device_index
import numpy as np
from traceback import format_exc
import wave
import time

def main():
    ### CONFIG ###
    # Microphone device name
    soundcard_name = 'NSRT_mk3'
    # Sampling Frequency (for dBA and dBC : can be either 44100 or 48000)
    sampling_rate = 48000
    # Buffer Size
    buffer_size = 128
    # Calibration levels (in dB)
    calibration = 0
    calibration_A = 0
    calibration_C = 0
    # Recording time (in seconds)
    record_time = 5
    record_filepath = f'recording_{time.time()}.wav'

    ### CREATE STREAM ###
    audio_format = pyaudio.paInt16
    dev_index = get_device_index(soundcard_name)
    channels=1
    pa = pyaudio.PyAudio()
    stream = pa.open(format=audio_format,
                     channels=channels,
                     rate=sampling_rate,
                     input=True,
                     frames_per_buffer=buffer_size,
                     input_device_index=dev_index)

    ### LOOP ###
    print('START RECORDING')
    stream.start_stream()
    try:
        frames = []
        for frame_idx in range(0, int(sampling_rate * record_time / buffer_size)):
            raw_data = stream.read(buffer_size, exception_on_overflow=False)
            frames.append(raw_data)

            data = np.frombuffer(raw_data, dtype=np.int16)
            # COMPUTE LEQ
            dB = get_leq(data, rate=sampling_rate, cal_value=calibration)
            dBA = get_leq_a(data, rate=sampling_rate, cal_value=calibration_A)
            dBC = get_leq_c(data, rate=sampling_rate, cal_value=calibration_C)
            print(f"dB={dB} dBA={dBA} dBC={dBC}")
    except Exception as e:
        print(f'Error while processing data : {format_exc()}')

    print('RECORDING FINISHED')
    stream.stop_stream()
    stream.close()
    pa.terminate()

    with wave.open(record_filepath, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(pa.get_sample_size(audio_format))
        wf.setframerate(sampling_rate)
        wf.writeframes(b''.join(frames))

    print(f'FILE SAVED : {record_filepath}')

if __name__ == '__main__':
    print('---------------------')
    print('  Sound Level Meter')
    print('---------------------')
    main()
