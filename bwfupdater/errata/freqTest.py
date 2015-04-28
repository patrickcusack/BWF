from numpy import *
from matplotlib import figure
from pylab import *


def convertToDecibels(value):
	return 20 * math.log10(1.0 * value)

# construct signal and plot in the time domain
def test():
	figure(figsize=(6,12))
	t = linspace(0, 1, 1001)
	y = sin(2*pi*t*6) + sin(2*pi*t*10) + sin(2*pi*t*13)
	subplot(311)
	plot(t, y, 'b-')
	xlabel("TIME (sec)")
	ylabel("SIGNAL MAGNITUDE")
	# compute FFT and plot the magnitude spectrum
	F = fft(y)
	N = len(t)             # number of samples
	dt = 0.001             # inter-sample time difference
	w = fftfreq(N, dt)     # gives us a list of frequencies for the FFT
	ipos = where(w>0)
	freqs = w[ipos]        # only look at positive frequencies
	mags = abs(F[ipos])    # magnitude spectrum
	subplot(312)
	plot(freqs, mags, 'b-')
	ylabel("POWER")
	subplot(313)
	plot(freqs, mags, 'b-')
	xlim([0, 50])          # replot but zoom in on freqs 0-50 Hz
	ylabel("POWER")
	xlabel("FREQUENCY (Hz)")
	savefig("signal_3freqs.jpg", dpi=150)

def testOriginal():
	# construct signal and plot in the time domain
	size = 2002
	t = linspace(0, 1, size)
	y = sin(2*pi*t*1000)
	# compute FFT and plot the magnitude spectrum
	F = fft(y)
	N = len(t)             # number of samples
	dt = 1.0/size             # inter-sample time difference
	w = fftfreq(N, dt)     # gives us a list of frequencies for the FFT
	ipos = where(w>0)
	freqs = w[ipos]        # only look at positive frequencies
	mags = abs(F[ipos])    # magnitude spectrum

	print 'freqs', len(freqs)
	print 'mags', len(mags)

	for i in range(0,len(freqs)):
		print freqs[i], convertToDecibels(mags[i]/(size/2))

def test2():
	figure(figsize=(6,12))
	t = linspace(0, 1, 1001)
	y = sin(2*pi*t*6) + sin(2*pi*t*10) + sin(2*pi*t*13)
	subplot(311)
	plot(t, y, 'b-')
	xlabel("TIME (sec)")
	ylabel("SIGNAL MAGNITUDE")
	# compute FFT and plot the magnitude spectrum
	F = fft(y)
	N = len(t)             # number of samples
	dt = 0.001             # inter-sample time difference
	w = fftfreq(N, dt)     # gives us a list of frequencies for the FFT
	ipos = where(w>0)
	freqs = w[ipos]        # only look at positive frequencies
	mags = abs(F[ipos])    # magnitude spectrum
	
	print 'freqs', len(freqs)
	print 'mags', len(mags)

	for i in range(0,len(freqs)):
		print freqs[i], mags[i]

	subplot(312)
	plot(freqs, mags, 'b-')
	ylabel("POWER")
	
	subplot(313)
	plot(freqs, mags, 'b-')
	xlim([0, 50])          # replot but zoom in on freqs 0-50 Hz
	ylabel("POWER")
	xlabel("FREQUENCY (Hz)")
	savefig("signal_3freqs.jpg", dpi=150)	

if __name__ == '__main__':
	# testOriginal()
	print 