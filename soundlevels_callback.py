import pyaudio
from hubbub import get_leq, get_leq_a, get_leq_c, get_device_index
import time
from datetime import datetime, timedelta
import numpy as np
from traceback import format_exc


def slm_callback(in_data, frame_count, time_info, status):
    now = datetime.now()
    adc_timedelta = time_info['current_time'] - time_info['input_buffer_adc_time'] - leq_time
    adc_timestamp = now - timedelta(seconds=adc_timedelta)

    try:
        data = np.frombuffer(in_data, dtype=np.int16)
        # COMPUTE LEQ
        dB = get_leq(data, rate=sampling_rate, cal_value=calibration)
        dBA = get_leq_a(data, rate=sampling_rate, cal_value=calibration_A)
        dBC = get_leq_c(data, rate=sampling_rate, cal_value=calibration_C)
        print(f"{adc_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:22]}: dB={dB} dBA={dBA} dBC={dBC}")
    except Exception as e:
        print(f'Error while processing sound levels : {format_exc()}')
        exit(0)
    return None, pyaudio.paContinue


def main():
    global sampling_rate, calibration, calibration_A, calibration_C, leq_time
    ### CONFIG ###
    # Microphone device name
    soundcard_name = 'NSRT_mk3'
    # Sampling Frequency (for dBA and dBC : can be either 44100 or 48000)
    sampling_rate = 48000
    # Equivalent level window time (in seconds)
    leq_time = 1
    # Calibration levels (in dB)
    calibration = -13
    calibration_A = -3
    calibration_C = -9


    ### CREATE STREAM ###
    audio_format = pyaudio.paInt16
    dev_index = get_device_index(soundcard_name)
    input_frames_per_block = int(sampling_rate * leq_time)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=audio_format,
                     channels=1,
                     rate=sampling_rate,
                     input=True,
                     frames_per_buffer=input_frames_per_block,
                     input_device_index=dev_index,
                     stream_callback=slm_callback)
    print('__________________________________________')
    print('               Stream Opened')
    print(f' - Soundcard : {dev_index} {soundcard_name}')
    print(f' - FS : {sampling_rate}Hz')
    print(f' - Leq Time : {leq_time}sec')
    print(f' - Leq Time (Real) : {input_frames_per_block/sampling_rate}sec')
    print(f' - Buffer Size : {input_frames_per_block}')
    print(f' - Calibration : {calibration}dB(z) {calibration_A}dB(a) {calibration_C}dB(c)')
    print('__________________________________________\n\n')

    ### LOOP ###
    try:
        stream.start_stream()
        while stream.is_active():
            time.sleep(.0000001)
    except Exception as e:
        print(f'Error while opening stream: {format_exc()}')
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == '__main__':
    print('---------------------')
    print('  Sound Level Meter')
    print('---------------------')
    main()
