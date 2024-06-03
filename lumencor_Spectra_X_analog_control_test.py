import numpy as np
import lumencor_Spectra_X
import ni_PCIe_6738

# initialize:
spx = lumencor_Spectra_X.Controller('COM12', verbose=False)
ao = ni_PCIe_6738.DAQ(num_channels=16, rate=1e5, verbose=False)

# set max voltages, pulse options and channels:
ttl_high_v = 5
pulse_s = 0.5
duty_cycle = 0.5    # Fraction of period to be high (range 0 to 1)
ao_channels = {'395/25':2,
               '440/20':3,
               '470/24':4,
               '510/25':5,
               '550/15':6,
               '640/30':7,
               }

# calculate voltages:
pulse_px = ao.s2p(pulse_s)
pulse_high_px = ao.s2p(pulse_s * duty_cycle)
names = tuple(ao_channels.keys())
voltage_series = []
for led in names:
    v = np.zeros((pulse_px, ao.num_channels), 'float64')
    v[pulse_high_px:, ao_channels[led]] = ttl_high_v
    voltage_series.append(v)
voltages = np.concatenate(voltage_series)

print('enabling leds!')
for led in spx.leds:
    spx.set_power(10, led)

print('playing led pulse train...')
ao.play_voltages(voltages, block=True)
print('done!')

ao.close()
spx.close()
