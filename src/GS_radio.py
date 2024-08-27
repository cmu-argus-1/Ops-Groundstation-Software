import datetime
import os
import sys
import time
from enum import Enum

import boto3
from gpiozero import LED

from keys import AWS_ACCESS_KEY, AWS_SECRET_KEY
from influx_db import DATABASE
from protocol_database import IMAGES, OTA, Definitions, gs_unpack_header

AWS_S3_BUCKET_NAME = 'spacecraft-files'
AWS_PUBLIC_BUCKET = 'public-argus-bucket'
AWS_REGION = 'us-east-2'

# Globals
received_success = False


class GROUNDSTATION:
    '''
        Name: __init__
        Description: Initialization of GROUNDSTATION class
    '''
    def __init__(self):
        print('Setting up AWS')
        # self.s3_client = boto3.client(
        #     service_name='s3',
        #     region_name=AWS_REGION,
        #     aws_access_key_id=AWS_ACCESS_KEY,
        #     aws_secret_access_key=AWS_SECRET_KEY
        # )

        # New contact from the satellite
        # Changes to True when heartbeat is received, false when image transfer starts
        self.new_session = False
        self.reset_file_array = False

        # Commands issued by the groundstation
        self.gs_cmd = 0xFF

        # RX message info
        self.rx_message_ID = 0x0
        self.rx_message_sequence_count = 0
        self.rx_message_size = 0
        self.rx_req_ack = 0

        # Missed message
        self.missed_message = False

        # Setup timestamp for timing packet arrival
        self.start_time = time.time()
        self.packet_time = 0
        self.time_diff = 0

        # Set up the GPIO pin as an output pin
        self.rx_ctrl = LED(22)
        self.tx_ctrl = LED(23)

        # self.influx = DATABASE()

        # # Logging Information
        # # Get the current time
        # current_time = datetime.datetime.now()

        # # Format the current time
        # formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

        # if "logs" not in os.listdir():
        #     os.mkdir("logs")

        # # Create image name
        # self.log_name = f"logs/GS_Logs_{formatted_time}.txt"

        # self.log = open(self.log_name, 'wb')

        # # Check command queue
        # print("GS Command Queue: ", self.cmd_queue)
        print(f'{time.time() - self.start_time}: Listening for UHF LoRa packets')
        # print()

    '''
        Name: received_message
        Description: This function waits for a message to be received from the LoRa module
        Inputs:
            lora - Declaration of lora class
    '''
    def receive_message(self, lora):
        # Pull GS RX pin HIGH!
        self.rx_ctrl.on()
        global received_success

        received_success = False
        lora.set_mode_rx()

        while not received_success:
            time.sleep(0.1)

        print(lora._last_payload.message)
        print("From:", payload.header_from)
        print("Received:", payload.message)
        print("RSSI: {}; SNR: {}".format(payload.rssi, payload.snr))
        print('')

        # self.unpack_message(lora)


def on_recv(payload):
    '''
        Name: on_recv
        Description: Callback function that runs when a message is received.
        Inputs:
            payload - message that was received
    '''
    global received_success
    received_success = True


def hard_exit(lora, GS, signum, frame):
    '''
        Name: hard_exit
        Description: Shutdown when ctrl-c is pressed
        Inputs:
            lora - Declaration of lora class
    '''
    GS.close_log()
    lora.close()
    sys.exit(0)