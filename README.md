# Sound Level Meter - Python

Basic examples of a sound level meter (slm) coded python3 with [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/#docs) and [numpy](https://numpy.org/) (thanks people!). It allows to compute equivalent levels
in dB, dBA and dBC (with linear filter) which is fastest than using 1/3 octave values and ponderations.


Features :
* Equivalent Level (Leq) in dB.
* dbA and dBC ponderations (for 44100Hz and 48000Hz sampling frequency).
* Level Calibration (in dB).
* Soundcard listing with possible sampling frequency.
* Easy soundcard selection.


## Installation
Tested on a Raspberry Pi 4 / Raspbian Buster / Python 3.7. Microphone used NSRT MK3 by [Convergence Instruments](https://convergenceinstruments.com/).

* Make sure the raspberry pi is up to date

    `sudo apt-get update & sudo apt-get upgrade -y`
* Go to the HuBBuB-SLM folder (git clone it or download and unzip it)

    `cd HuBBuB-SLM`
* Install required packages : pip, portaudio lib (pyaudio is a python portaudio binding), atlas lib (for numpy)

    `sudo apt-get install python3-pip portaudio19-dev libatlas-base-dev`
* Install virtualenv and create a virtual environment

    `python3 -m pip install virtualenv`
    `python3 -m virtualenv hubbub`
* Install python required librairies

    `python -m pip install -r requirements.txt`

        cython
        numpy
        scipy
        pyaudio
        nsrt-mk3-dev


## Check that the usb microphone or soundcard is detected
**The rpi doesn't have an audio input by default.**
You can any usb soundcard, usb webcam with builtin microphone, a digital mems microphone, there also hats with audio input capability, etc... If you use a laptop you'll probably have a builtin microphone.
### With ALSA
List all recording soundcard detected.

    arecord -l
For me outputs :

    **** List of CAPTURE Hardware Devices ****
    card 1: NSRTmk3Dev [NSRT_mk3_Dev], device 0: USB Audio [USB Audio]
    Subdevices: 1/1
    Subdevice #0: subdevice #0

### With Python
    python hubbub/soundcards.py

Outputs :

                                 -- 0 --
        Name                : bcm2835 Headphones: - (hw:0,0)
        Default Fs          : 44100.0
        Max Input Channels  : 0
        Max Output Channels : 8
        __________________________________________________________
                                 -- 1 --
        Name                : NSRT_mk3_Dev: USB Audio (hw:1,0)
        Default Fs          : 48000.0
        Supported Fs        : [32000, 48000]
        Max Input Channels  : 1
        Max Output Channels : 0
        __________________________________________________________
                                 -- 2 --
        Name                : sysdefault
        Default Fs          : 44100.0
        Max Input Channels  : 0
        Max Output Channels : 128
        __________________________________________________________
                                 -- 3 --
        Name                : default
        Default Fs          : 44100.0
        Max Input Channels  : 0
        Max Output Channels : 128
        __________________________________________________________
                                 -- 4 --
        Name                : dmix
        Default Fs          : 48000.0
        Max Input Channels  : 0
        Max Output Channels : 2


## About the NSRT MK3

When used as a usb soundcard, the NSRT MK3 microphone outputs a weighted signal. This is a really nice feature !
The NSRT has a serial communication port to change theses settings and thanks to [Xander Hendriks there is a python package called
nsrt-mk3-dev](https://github.com/xanderhendriks/nsrt-mk3-dev) that allow us to communicate easily with it.


Two possibilities now :
* For multiple weighted measure (i.e dBA, dBC, and dBZ), we need to setup it as zero weighting (a.k.a Z weighting). *like the first 3 examples*
* For only one measure, we can change it to the wanted weighting. *see the soundlevels_nsrt example*


### Communication with the NSRT MK3
* Find the microphone serial port (from the nsrt-mk3-dev documentation)

    `dmesg | grep -i usb`

    and look for :

        [22339.508035] usb 1-1.2: Product: NSRT_mk3_Dev
        [22339.508044] usb 1-1.2: Manufacturer: Convergence Instruments
        [22339.520711] cdc_acm 1-1.2:1.1: ttyACM0: USB ACM device

* Open a python console (in the virtualenv)

    ```
    import nsrt_mk3_dev
    nsrt = nsrt_mk3_dev.NsrtMk3Dev('/dev/ttyACM0')
    weighting = nsrt.read_weighting()
    print(weighting)
    ```
        Outputs :Weighting.DB_C

    ```
    # FOR DBA
    nsrt.write_weighting(nsrt.Weighting.DB_A)
    # FOR DBC
    nsrt.write_weighting(nsrt.Weighting.DB_C)
    # FOR DBZ
    nsrt.write_weighting(nsrt.Weighting.DB_Z)
    ```

Don't overflood the microphone ! Here is a warning from the NSRT-MK3 documentation :

        The Flash memory that is used to contain these values can sustain approximately 10 000 write cycles
        over the lifetime of the instrument. Even though that is a large number, the instrument is not designed
        to  sustain  constantly  changing  the  values  in  rapid  succession.  For  instance,  switching  the  weighting
        function back and forth in an attempt to read both A and C levels all the time will quickly exhaust the
        number of cycles guarantied for that Flash memory.

        Whenever  Tau,  Fs  or  Weighting  are  modified,  the  instrument’s  correction  filters  are  reset  and  that
        creates a transient spike in the indicated levels. In order to read valid levels after changing one of these
        parameters,  a  delay  of  at  least  the  largest  of  1  second,  or  10  times  the  value  of  Tau  should  be
        observed.


## Folder contents

Even if it is not bundled as a python package, all useful function are located in the `hubbub/` folder :
* soundcards.py : Useful functions to list the detected soundcard and find the index of the wanted soundcard by name.
* slm.py : Sound level computation and weighting.


There is 4 examples :
* soundlevels_simple.py : Basic pyaudio example with blocking thread. It is not very optimised as you can easily overflow the input and miss frame.
* soundlevels_and_recording.py : Basic pyaudio example to compute sound levels and record the output as the same time.
* soundlevels_callback.py : The more advanced example which give the more accurate result.
* soundlevels_nsrt.py : This example, based on the soundlevels_callback, is only intended to be used with the nsrt microphone. It outputs only one weighted measure ('A', 'C' or 'Z') by changing the internal configuration of the NSRT MK3.


## Usage
In each example you change the config in the main() function.

        ### CONFIG ###
        # Microphone device name
        soundcard_name = 'NSRT_mk3'
        # Sampling Frequency (for dBA and dBC : can be either 44100 or 48000)
        sampling_rate = 48000
        # Equivalent level window time (in seconds)
        leq_time = 1
        # Calibration levels (in dB)
        calibration = 0
        calibration_A = 0
        calibration_C = 0

* List the soundcards detected :

    `python hubbub/soundcards.py`

                             -- 1 --
        Name                : NSRT_mk3_Dev: USB Audio (hw:1,0)
        Default Fs          : 48000.0
        Supported Fs        : [32000, 48000]
        Max Input Channels  : 1
        Max Output Channels : 0



* Change the `soundcard_name` depending on your configuration (you don't need to put the full name). In my config : `NSRT`
* Change the `leq_time` depending on your need. In my config :  1 second
* Change the `sampling_rate` depending on your card. Check `Default Fs` and `Supported Fs`. In my config : 48000 Hz
* Be sure to be in the same folder as the example script.
* Launch it !

    `python soundlevels_callback.py`


                   Stream Opened
         - Soundcard : 1 NSRT_mk3
         - FS : 48000Hz
         - Leq Time : 1sec
         - Leq Time (Real) : 1.0sec
         - Buffer Size : 48000
         - Calibration : 0dB(z) 0dB(a) 0dB(c)
        __________________________________________


        2021-09-29 17:04:10.90: dB=42.08 dBA=42.05 dBC=41.77
        2021-09-29 17:04:11.89: dB=46.49 dBA=46.15 dBC=45.94
        2021-09-29 17:04:12.89: dB=41.9 dBA=41.64 dBC=41.65

*PyAudio logs a lot of errors at the beginning, it is OK. Never succeeded to make it quiet, so if you have a hint please share in the issue comment!*


# References
The example that started all : http://stackoverflow.com/questions/4160175/detect-tap-with-pyaudio-from-live-mic

Theses examples are the result of several years of development of theses project :

* Was first used for the Musikiosk project (2015).
www.musikiosk.org / [Project Page](https://louisvoreux.wordpress.com/portfolio/musikiosk_eng/) / [Scientific papers](https://scholar.google.fr/scholar?as_vis=1&q=Musikiosk&hl=fr&as_sdt=0,5)

* Hubbub is a fully automated low-cost noise monitoring station based on Raspberry Pi.
Featuring an user interface (control/configuration), a telegram bot, visualization screen, scheduler, wifi hotspot and much more ;
It is a perfect tool for long term sound level measurement without expensive equipment. It was used in several research studies.
If you interested in this or if you want more informations please contact me.


