import pyaudio


def get_device_index(dev_name):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        if dev_name in p.get_device_info_by_index(i)['name']:
            p.terminate()
            return i
    print("Device {} not found".format(str(dev_name)))
    p.terminate()
    return None


def get_devices_info():
    p = pyaudio.PyAudio()
    soundcards = {}
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        support_fs = []
        if dev['maxInputChannels'] > 0:
            for fs in [22050, 32000, 44100, 48000]:
                try:
                    if p.is_format_supported(fs, input_device=i, input_channels=1, input_format=pyaudio.paInt16):
                        support_fs.append(fs)
                except Exception as e:
                    pass
                except pyaudio.paInvalidSampleRate:
                    pass

        soundcards[i] = dev.copy()
        soundcards[i].update({
            'supportedSampleRate': support_fs,
            'index': i
        })
    p.terminate()
    return soundcards


def print_soundcards():
    sndcards = get_devices_info()
    for i, dev in sndcards.items():
        print("__________________________________________________________")
        print_soundcard(dev)


def print_soundcard(dev):
    print("                         -- {} --".format(dev['index']))
    print("Name                : {}".format(dev['name']))
    print("Default Fs          : {}".format(dev['defaultSampleRate']))
    if len(dev['supportedSampleRate']) != 0:
        print("Supported Fs        : {}".format(dev['supportedSampleRate']))
    print("Max Input Channels  : {}".format(dev['maxInputChannels']))
    print("Max Output Channels : {}".format(dev['maxOutputChannels']))


if __name__ == '__main__':
    print_soundcards()
