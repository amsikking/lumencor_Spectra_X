import serial

class Controller:
    '''
    ***WARNING: THIS SCRIPT CAN FIRE LED EMISSION! SHUTTER LEDS FIRST***
    Basic device adaptor for a Lumencor Spectra X led box.
    
    To use TTL control:
    1. Set enable = False on all LED's (default on __init__). If enable = True
    the TTL signal is ignored by the controller.
    2. Set power using .set_power() command.
    3. Apply TTL signals (5v high)
    
    NOTE: "TTL polarity may be set ACTIVE = HIGH or ACTIVE = LOW. This setting
    is part of the order specification provided by the customer."
    
    (DB15HD connector pins: 'R'=1, 'GY'=2, 'C'=3, 'TN'=11, 'B'=12, 'V'=13,
    Ground = 6, 7, 8, 10, Not connected = 4, 9, 14)
    '''
    def __init__(self,
                 which_port,            # COM port for laser box
                 name='Spectra_X',      # optional name
                 led_names=None,        # optional nicknames -> len(tuple) = 6
                 yellow_filter=False,   # False = Green filter (user swapable)
                 teal_to_NIR=False,     # optional color change (factory)
                 red_to_NIR=False,      # optional color change (factory)
                 verbose=True,          # False for max speed
                 very_verbose=False):   # True for debug
        self.name = name
        self.verbose = verbose
        self.very_verbose = very_verbose
        if self.verbose: print('%s: opening...'%name, end='')
        try:
            self.port = serial.Serial(port=which_port, timeout=0.25)
        except serial.serialutil.SerialException:
            raise IOError('%s: No connection on port %s'%(name, which_port))
        self._send(b'\x57\x02\xff\x50') # Mandatory initialize commmand
        self._send(b'\x57\x03\xAB\x50') # Mandatory initialize commmand
        self._force_response()
        if self.verbose: print(" done.")
        self.get_temperature()
        # Configure default LED and filter options -> check actual hardware
        self.slot2led = {       # slot in box to actual led/filter setup
            'V': (395, 25, 295),# wavelength (nm), bandpass (nm), power (mW)
            'B': (440, 20, 256),
            'C': (470, 24, 196),
            'TN':(510, 25,  62),
            'GY':(550, 15, 260),
            'R': (640, 30, 231)}
        if yellow_filter:   self.slot2led['GY'] = (575, 25, 310)
        if teal_to_NIR:     self.slot2led['TN'] = (730, 40, 123)
        if red_to_NIR:      self.slot2led['R']  = (740, 20,  65)
        if led_names is not None:
            assert type(led_names) is tuple and len(led_names) == 6
            for n in led_names: assert type(n) is str
            self.leds = led_names
        else:
            self.leds = []
            for k, v in self.slot2led.items():
                self.leds.append(str(v[0]))
            self.leds = tuple(self.leds)
        if self.verbose: print('%s: led names = %s'%(name, self.leds))
        self.leds2slot = dict(zip(self.leds, self.slot2led.keys()))
        # Set state:
        self.power = {}
        self.enable = dict(zip(self.leds, 6 * (False,)))
        for led in self.leds:
            self.set_power(0, led)      # safety -> power to 0%
            self.set_enable(False, led) # safety -> enable to False

    def _send(self, cmd, response_bytes=0):
        assert type(cmd) is bytes
        assert type(response_bytes) is int and response_bytes >= 0
        if self.very_verbose: print("%s: sending cmd = %s"%(self.name, cmd))
        self.port.write(cmd)
        response = None
        if response_bytes > 0:
            response = self.port.read(response_bytes)
            assert response != b'', ("%s: no response! (expected %i bytes)"%(
                self.name, response_bytes))
        assert self.port.in_waiting == 0
        if self.very_verbose: print("%s: -> response ="%self.name, response)     
        return response

    def _force_response(self):
        """
        The serial port protocol does not provide a response (or handshake) 
        upon receipt of a command. This function uses the 'check temperature'
        command to block until a response is received (with the hope that if
        the unit responds to this it has executed all previous commands).
        """
        if self.very_verbose: print("%s: force response..."%self.name)
        self._send(b'\x53\x91\x02\x50', response_bytes=2)
        if self.very_verbose: print("%s: response recieved."%self.name)
        return None

    def get_temperature(self):
        if self.verbose: print("%s: getting temperature"%self.name)
        response = self._send(b'\x53\x91\x02\x50', response_bytes=2)
        temperature_c = 0.125 * (int.from_bytes(response, byteorder='big') >> 5)
        if self.verbose:
            print("%s: -> temperature (degC) = %s"%(self.name, temperature_c))
        return temperature_c   

    def set_power(self, power_pct, name):
        if self.verbose:
            print("%s(%s): setting power (%%) = %s"%(
                self.name, name, power_pct))
        assert type(power_pct) is int or type(power_pct) is float
        assert 0 <= power_pct <= 100
        power = int(255 * (power_pct / 100))# controller takes 0 -> 255
        power_pct = 100 * (power / 255)     # re-calculate pct for attribute
        assert name in self.leds
        slot = self.leds2slot[name]
        color_cmd = {'B' :b'\x53\x1a\x03\x01',
                     'TN':b'\x53\x1a\x03\x02',
                     'V' :b'\x53\x18\x03\x01',
                     'C' :b'\x53\x18\x03\x02',
                     'GY':b'\x53\x18\x03\x04',
                     'R' :b'\x53\x18\x03\x08'}[slot]
        power_cmd = (((4095 - power) << 12) + 80).to_bytes(3, byteorder='big')
        self._send(color_cmd + power_cmd)
        self._force_response()
        self.power[name] = power_pct
        if self.verbose:
            print("%s(%s): -> done setting power."%(self.name, name))
        return None

    def set_enable(self, mode, name):
        if self.verbose:
            print("%s(%s): setting enable = %s"%(self.name, name, mode))
        assert mode in (True, False)
        assert name in self.leds
        self.enable[name] = mode
        enables = tuple(self.enable.values())
        enable_code = (127                  # max value (everything off)
                       - enables[5] * 1     # 'R'
                       - enables[4] * 2     # 'GY' Spectra X -> G and Y share
                       - enables[2] * 4     # 'C'
                       - enables[0] * 8     # 'V'
                      #- enables[6] * 16    # 'Y' for Spectra -> not used for X
                       - enables[1] * 32    # 'B'
                       - enables[3] * 64)   # 'TN'
        cmd = b'\x4f' + enable_code.to_bytes(1, byteorder='big') + b'\x50'
        self._send(cmd)
        self._force_response()
        if self.verbose:
            print("%s(%s): -> done setting enable."%(self.name, name))
        return None

    def close(self):
        if self.verbose: print("%s: closing..."%self.name)
        verbose = self.verbose
        self.verbose = False
        for led in self.leds:
            self.set_power(0, led)      # safety -> power to 0%
            self.set_enable(False, led) # safety -> enable to False
        self.port.close()
        self.verbose = verbose
        if self.verbose: print("%s: closed."%self.name)
        return None

if __name__ == '__main__':
    leds = ('395/25', '440/20', '470/24', '510/25', '550/15', '640/30')
    spx = Controller(
        which_port='COM5', led_names=leds, verbose=True, very_verbose=False)

    for led in spx.leds:
        spx.set_enable(True, led)
        for p in range(0, 20):
            spx.set_power(p, led)
        spx.set_enable(False, led)   

    spx.close()
