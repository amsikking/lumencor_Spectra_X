# lumencor_Spectra_X
Python device adaptor: Lumencor Spectra X light engine, 6 solid state sources.
## Quick start:
- Use a USB to RS232 adaptor and associated driver to connect (see example cable in reference folder).
- ***Shutter output (or otherwise make safe for high power led emission).***
- Try installing the 'Spectra' GUI from Lumencor for basic testing (optional).
- Run either the main script or the 'analog' control example (configure as needed).
## Details:
The light engine comes in various models/configurations so be sure to update the main script (or analog control) to match the exact unit. Some things to look out for:
- Each LED has a changeable filter that can modify the spectrum and power output.
- Some of the LED's are configured differently from the factory (i.e. 'teal' -> NIR, or 'red' -> NIR).
- The TTL input can be ACTIVE = HIGH or ACTIVE = LOW (factory option). ACTIVE = HIGH is recommended so that the output defaults to 'OFF' if voltage to the TTL inputs is lost.
- TTL control may require a custom cable (see reference photo), or buying an extra part from Lumencor (part
number 29-10015 or 29-10080 from the manual).
- TTL switching time is quoted as "on the order of tens of microseconds".
