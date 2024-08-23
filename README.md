# Ops-Groundstation-Software
Software for RPi-based ground station using RFM98/95W radio modules.

This code is primarily written in Python with development files in C and CircuitPython. 

To setup dependancies on a Raspberry Pi...
 1. `sudo bash requirements.sh`

To run the code...
  1. `cd src/`
  2. `python3 LoRa_GS.py`

'src' contains the active files used for operating the GS. Other directories in the repo are: 
'PY4_gs' - All source code from the original PY4 ground station. Code has been slightly modified to accommodate the Argus-1 ground station hardware. Original repo is here -> https://github.com/maholli/PY4_gs
'Pi-C' - Experimental ground station code written in C. We recommend using this as a starting point if the Flight Software code switches from CircuitPython to C.
'Python' - Various Python and CircuitPython test files. Definitely not perfect.
'REFERENCE' - Various documentation we used as the basis for our implementation, messaging protocol, and data handling.
'SQL' - Original SQL database we tried to use, but did not implement in our final code. Maybe worth trying it again in the future.

Have fun!
