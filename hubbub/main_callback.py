# source
import slm
from hubbubtools import Config
from hubbubtools import setup_logging

from soundcards import device_index

import pyaudio
import numpy
import time
from datetime import datetime
from traceback import format_exc
import wave
import os
import argparse

global datas
global recording
global thirdOct

import logging as log

import numpy as np
from scipy.signal import resample

from threading import Lock, Thread


record_data = []
recording = False
rec_lock = Lock()



def process_audio(in_data, frame_count, time_info, status):
    """ PERIODIC RECORDINGS """
    global record_data
    global recording
    global data
    global thirdOct
    try:
        data = numpy.frombuffer(in_data, dtype=np.int16)
        if frame_count == input_frames_per_block:
            data_norm = np.array(data, dtype=np.float64) * (1.0 / 32768.0)

            thirdOct = acoustics.signal.third_octaves(data_norm, config.rate) # FFT

            data_A = slm.weighting(data_norm, rate=config.rate, weighting_type='A')
            dBA = slm.leq(data_A, config.cal_a)

            data_C = slm.weighting(data_norm, rate=config.rate, weighting_type='C')
            dBC = slm.leq(data_C, config.cal_c)

            if debug:
                log.info("dBC={} dBA={}".format(round(dBC, 3), round(dBA, 3)))
            if recording:
                record_data.append(in_data)

        else:
            log.error('Missing frames !!')
    except Exception as exc_io:
        log.error(exc_io)
        log.error(format_exc())
        exit(0)
    return (None, pyaudio.paContinue)


def process_audio_simple(in_data, frame_count, time_info, status):
    """ NO RECORDINGS """
    global thirdOct
    try:
        data = numpy.frombuffer(in_data, dtype=np.int16)
        if frame_count == input_frames_per_block:
            # COMPUTE LEQ
            data_norm = np.array(data, dtype=np.float64) * (1.0 / 32768.0)
            thirdOct = acoustics.signal.third_octaves(data_norm, config.rate) # FFT
            data_A = slm.weighting(data_norm, rate=config.rate, weighting_type='A')
            dBA = slm.leq(data_A, config.cal_a)
            data_C = slm.weighting(data_norm, rate=config.rate, weighting_type='C')
            dBC = slm.leq(data_C, config.cal_c)

            if debug:
                log.info("dBC={} dBA={}".format(round(dBC, 3), round(dBA, 3)))

        else:
            log.error('Missing frames')
    except Exception as exc_io:
        log.error(exc_io)
        log.error(format_exc())
        exit(0)
    return (None, pyaudio.paContinue)



def main_loop(stream):
    log.info('-------------------------')
    log.info(' Starting monitoring!')
    log.info('-------------------------')

    global record_data
    global recording
    start_time = time.time() - config.rec_period
    try:
        stream.start_stream()
        while stream.is_active():
            if config.rec_enable:
                if not config.rec_trigger and time.time() - start_time >= config.rec_period and not recording:
                        acquired = rec_lock.acquire(0)
                        if acquired:
                            log.info('Recording launched')
                            recording = True
                            start_time = time.time()
                            rec_lock.release()
                        else:
                            log.info('Lock already acquired')

                if recording and len(record_data) >= config.rec_length:
                    log.info('Recording finished, acquiring lock')
                    rec_lock.acquire()
                    log.info('Lock acquired')
                    recording = False
                    now = datetime.now()
                    rec_filename = '{}.wav'.format(datetime.isoformat(now).replace('T', '_')[:19])
                    this_dir = os.getcwd()
                    path = os.path.join(this_dir, '../records/', rec_filename)
                    wf = wave.open(path, 'wb')
                    wf.setnchannels(config.channels)
                    wf.setsampwidth(pa.get_sample_size(audio_format))
                    wf.setframerate(config.rec_rate)
                    rec_data = b''.join(record_data)
                    if config.rate != config.rec_rate:
                        rec_data = np.frombuffer(rec_data, dtype=numpy.int16)
                        nb_resample = round(len(rec_data) * config.rec_rate / config.rate)
                        rec_data_resampled = resample(rec_data, nb_resample)
                        rec_data = rec_data_resampled.astype(np.int16)
                    wf.writeframes(rec_data)
                    wf.close()
                    record_data = []
                    rec_lock.release()
                    log.info('Recorded! {}'.format(rec_filename))
                    log_recording(rec_filename, client, config)

                    if alert_space():
                        log.error('Low Space on device (<1GB)')
                        exit(0)

            time.sleep(0.000001)
    except Exception as e:
        log.error(format_exc())
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

def main(config_filename):
    # setup
    setup_logging("slm.log")
    faulthandler.enable(all_threads=True)
    global config, input_frames_per_block, client, pa, audio_format
    # Start
    log.info('__________________________')
    log.info('         HUBBUB SLM')
    log.info('‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾')

    # Load config
    config = Config(config_filename)
    config.load()
    log.info(f'Input block time  = {config.input_block_time}')

    # Audio Flow Parameters
    audio_format = pyaudio.paInt16
    if config.device_name == '':
        log.info('Device name is not defined in config file {}'.format(config.filename))
        log.info('USING DEFAULT SOUNDCARD')
        config.device_name = 'default'
    index = device_index(config.device_name)
    if index is None:
        log.info('Device was not found')
        exit(0)

    # db init
    client = influxdb.InfluxDBClient(host=config.db_url, port=config.db_port, database=config.db_name)

    # trigger recording
    if not config.rec_enable:
        audio_callback = process_audio_simple
    elif config.rec_trigger and config.rec_enable:
        audio_callback = process_audio_trigger_rec
    elif not config.rec_trigger and config.rec_enable:
        audio_callback = process_audio
    else:
        log.error('Audio callback configuration error')
        exit(0)

    # Configation Audio stream
    input_frames_per_block = int(config.rate * config.input_block_time)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=audio_format,
                     channels=config.channels,
                     rate=config.rate,
                     input=True,
                     frames_per_buffer=input_frames_per_block,
                     input_device_index=index,
                     stream_callback=audio_callback)



    # Launch the main fonction.
    main_loop(stream)


if __name__ == '__main__':
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('config_file', help='Configuration file for differents parameters \Default=config.json',
                        default='config.json')
    parser.add_argument('-D', '--debug', help='Debug mode', action='store_true')
    args = parser.parse_args()
    debug = args.debug
    config_filename = args.config_file
    main(config_filename)


