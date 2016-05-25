#encoding=utf-8
import numpy
import math
from scipy.signal import lfilter



#Reference Pressure (20µPa)
trim = 93.97940008672037609572522210551
# Normalisation for format 16bits
SHORT_NORMALIZE = (1.0/32768.0)
#A-weigthing -  B and A coef for 44100 Hz
Ba = [ 0.25574113, -0.51148225, -0.25574113,  1.0229645,  -0.25574113, -0.51148225, 0.25574113]
Aa = [ 1.00000000, -4.01957618, 6.18940644, -4.45319890, 1.42084295, -0.141825474, 0.00435117723]
#C-wegthing
Ac = [ 1.0, -2.13467496, 1.27933353, -0.14955985, 0.0049087]
Bc = [ 0.21700856, 0.00, -0.43401712, 0.00, 0.21700856]


def Leq1s(block, CAL_VALUE_A, CAL_VALUE_C):

    sample = numpy.fromstring(block, dtype=numpy.int16)
    dBA = lfilter(Ba, Aa, sample)
    dBC = lfilter(Bc, Ac, sample)

#iterate over the block.
#sum_squares = 0.0
#for sample in filteredsample:
#sample is a signed short in +/- 32768.
#normalize it to 1.0

    dataA = numpy.array(dBA, dtype=float)*SHORT_NORMALIZE
    sumA = numpy.sum(dataA ** 2.0) / len(dataA)

    dataC = numpy.array(dBC, dtype=float)*SHORT_NORMALIZE
    sumC = numpy.sum(dataC ** 2.0) / len(dataC)

# n = sample * SHORT_NORMALIZE
# sum_squares += n*n
# ms = sum_squares/len(block)
# math.sqrt( sum_squares / count )

    LeqC=(10.0 * math.log(sumC, 10.0)) + trim + CAL_VALUE_C
    LeqA=(10.0 * math.log(sumA, 10.0)) + trim + CAL_VALUE_A

    return (LeqA,LeqC)
