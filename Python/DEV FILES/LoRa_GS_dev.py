from raspi_lora import LoRa, ModemConfig
from message_database_dev import *
from GS_helpers import *
import time
import signal
import sys

GS = GROUNDSTATION()

## ---------- MAIN CODE STARTS HERE! ---------- ##
# LoRa module setup
# Use chip select 0. GPIO pin 19 will be used for interrupts
# The address of this device will be set to 10
lora = LoRa(0, 19, 10, modem_config=ModemConfig.Bw125Cr45Sf128, acks=False, freq=433)
lora.on_recv = on_recv

# Setup interrupt
signal.signal(signal.SIGINT, lambda signum, frame: hard_exit(lora, signum, frame))

while True:
    GS.receive_message(lora)
    GS.transmit_message(lora)

lora.close()