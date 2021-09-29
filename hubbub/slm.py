# encoding=utf-8
import numpy as np
from scipy.signal import lfilter

# Reference Pressure (20µPa)
trim = 93.97940008672037609572522210551

# Normalisation for format 16bits
short_normalize = (1.0 / 32768.0)

# dbA and dBC weighting coefficients
coefficients = {
    44100: {
        'A': {
            'a': [1.00000000, -4.01957618, 6.18940644, -4.45319890, 1.42084295, -0.141825474, 0.00435117723],
            'b': [0.25574113, -0.51148225, -0.25574113, 1.0229645, -0.25574113, -0.51148225, 0.25574113]
        },
        'C': {
            'a': [1.0, -2.13467496, 1.27933353, -0.14955985, 0.0049087],
            'b': [0.21700856, 0.00, -0.43401712, 0.00, 0.21700856]
        }
    },
    48000: {
        'A' : {
            'b': [0.234301792299513, -0.468603584599028, -0.234301792299510, 0.937207169198050, -0.234301792299512, -0.468603584599026, 0.234301792299513],
            'a': [1, -4.11304340877587, 6.55312175265504, -4.99084929416338, 1.78573730293757, -0.246190595319487, 0.0112242500332313]
        },
        'C':
            {
            'b': [0.19788712002639319, 1.1102230246251565E-15, -0.39577424005278772, 3.0531133177191805E-16, 0.19788712002639314],
            'a': [1, -2.2191729140528023, 1.4551358789471718, -0.24849607388778278, 0.012538823147272379],
            }
    }
}


def weighting(data, rate=44100, weighting_type=None):
    if rate not in coefficients.keys():
        print('Error : Sampling Frequency Must Be 44100 or 48000 (int)')
        exit(1)
    elif weighting_type is None or weighting_type not in ['A', 'C']:
        print('Error : Weighting should be A or C (str)')
        exit(1)
    return lfilter(coefficients[rate][weighting_type]['b'], coefficients[rate][weighting_type]['a'], data)


def leq(data, cal_value):
    sum_data = np.mean(data ** 2.0)
    leq_value = (10.0 * np.log10(sum_data)) + trim + cal_value
    return leq_value


#################
#   GET LEQs    #
#################
def get_leq_a(data, cal_value=0, rate=44100):
    data_norm = np.array(data, dtype=np.float64) * short_normalize
    data_weighted = weighting(data_norm, rate=rate, weighting_type='A')
    dBA = leq(data_weighted, cal_value)
    dBA = round(dBA, 2)
    return dBA


def get_leq_c(data, cal_value=0, rate=44100):
    data_norm = np.array(data, dtype=np.float64) * short_normalize
    data_weighted = weighting(data_norm, rate=rate, weighting_type='C')
    dBC = leq(data_weighted, cal_value)
    dBC = round(dBC, 2)
    return dBC


def get_leq(data, cal_value=0, rate=44100):
    data_norm = np.array(data, dtype=np.float64) * short_normalize
    dB = leq(data_norm, cal_value)
    dB = round(dB, 2)
    return dB
