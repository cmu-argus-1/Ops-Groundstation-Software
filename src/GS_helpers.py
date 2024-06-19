import datetime
import os
import sys
import time
from enum import Enum

import boto3
from gpiozero import LED

from src.keys import AWS_ACCESS_KEY, AWS_SECRET_KEY
from influx_db import DATABASE
from protocol_database import IMAGES, OTA, Definitions, gs_unpack_header

AWS_S3_BUCKET_NAME = 'spacecraft-files'
AWS_PUBLIC_BUCKET = 'public-argus-bucket'
AWS_REGION = 'us-east-2'

# Globals
received_success = False


class IMAGE_DEFS(Enum):
    IMAGE_1 = 1
    IMAGE_2 = 2
    IMAGE_3 = 3


class GROUNDSTATION:
    '''
        Name: __init__
        Description: Initialization of GROUNDSTATION class
    '''
    def __init__(self):
        print('Setting up AWS')
        self.s3_client = boto3.client(
            service_name='s3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )

        # New contact from the satellite
        # Changes to True when heartbeat is received, false when image transfer starts
        self.new_session = False
        self.reset_file_array = False
        # Track the number of commands sent before an image is requested
        self.num_commands_sent = 0
        # List of commands to send before image request
        self.cmd_queue = self.get_commands()
        self.cmd_queue_size = len(self.cmd_queue)
        # Commands issued by the groundstation
        self.gs_cmd = 0xFF
        # Sequence counter for images
        self.sequence_counter = 0
        # References to the image we are requesting
        self.target_image_UID = 0
        self.target_sequence_count = 0
        # Image Info class
        self.sat_images = IMAGES()
        self.image_array = []
        # RX message info
        self.rx_message_ID = 0x0
        self.rx_message_sequence_count = 0
        self.rx_message_size = 0
        self.rx_req_ack = 0
        # OTA Sequence Counter
        self.ota_sequence_counter = 0
        # Satellite request acknowledgement
        self.gs_req_ack = Definitions.REQ_ACK_NUM
        # OTA received success
        self.ota_sat_rec_success = 1
        # OTA satellite sequence counter
        self.ota_sat_sequence_counter = 0
        self.send_mod = 10
        # Missed message
        self.missed_message = False

        # Setup timestamp for timing packet arrival
        self.start_time = time.time()
        self.packet_time = 0
        self.time_diff = 0

        # Set up the GPIO pin as an output pin
        self.rx_ctrl = LED(22)
        self.tx_ctrl = LED(23)

        self.influx = DATABASE()

        # Logging Information
        # Get the current time
        current_time = datetime.datetime.now()

        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

        # Create image name
        self.log_name = f"GS_Logs_{formatted_time}.txt"

        self.log = open(self.log_name, 'wb')

        # Check command queue
        print("GS Command Queue: ", self.cmd_queue)
        print(f'{time.time() - self.start_time}: Listening for UHF LoRa packets')
        print()

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
        receive_multiple = 0
        while (receive_multiple == 0):
            received_success = False
            lora.set_mode_rx()

            while not received_success:
                time.sleep(0.1)

            # print(lora._last_payload.message)
            # print("From:", payload.header_from)
            # print("Received:", payload.message)
            # print("RSSI: {}; SNR: {}".format(payload.rssi, payload.snr))
            # print('')
            self.unpack_message(lora)
            receive_multiple = self.rx_req_ack

        if (self.reset_file_array or self.missed_message or lora.crc_error_count > 0):
            # If last command was an image, refetch last portion of image
            # to make sure it was received correctly
            if ((self.gs_cmd == Definitions.SAT_IMG_CMD) and self.missed_message):
                high_sequence_count = self.sequence_counter
                while ((self.sequence_counter > 0) and (self.sequence_counter > (high_sequence_count - self.send_mod))):
                    self.sequence_counter -= 1
                    self.image_array.pop(self.sequence_counter)
            # If last command was an OTA, resend the last portion of the file
            # to make sure it was received correctly.
            elif (self.gs_cmd == Definitions.GS_OTA_REQ):
                print(lora.crc_error_count)
                if (self.ota_sequence_counter >= self.send_mod):
                    self.ota_sequence_counter -= self.send_mod
                else:
                    self.ota_sequence_counter = 0
            # Reset variables
            self.reset_file_array = False
            self.missed_message = False

        # Turn GS RX pin LOW!
        self.rx_ctrl.off()

    '''
        Name: unpack_message
        Description: This function unpacks a message based on its ID
        Inputs:
            lora - Declaration of lora class
    '''
    def unpack_message(self, lora):
        # Get the current time
        current_time = datetime.datetime.now()
        # Format the current time
        formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S\n")
        formatted_time = formatted_time.encode('utf-8')

        header_info = (f"Header To: {lora._last_payload.header_to}," +
                       f"Header From: {lora._last_payload.header_from}," +
                       f"Header ID: {lora._last_payload.header_id}," +
                       f"Header Flags: {lora._last_payload.header_flags}," +
                       f"RSSI: {lora._last_payload.rssi}," +
                       f"SNR: {lora._last_payload.snr}\n")
        header_info = header_info.encode('utf-8')
        payload = f"Payload: {lora._last_payload.message}\n\n"
        payload = payload.encode('utf-8')
        self.log.write(formatted_time)
        self.log.write(header_info)
        self.log.write(payload)

        # Unpack header information - Received header, sequence count, and message size
        (self.rx_req_ack,
         self.rx_message_ID,
         self.rx_message_sequence_count,
         self.rx_message_size) = gs_unpack_header(lora, self.influx)
        self.influx.upload_last_received_packet(self.rx_req_ack,
                                                self.rx_message_ID,
                                                self.rx_message_sequence_count,
                                                self.rx_message_size)

        if (
            self.rx_message_ID == Definitions.SAT_HEARTBEAT_BATT or
            self.rx_message_ID == Definitions.SAT_HEARTBEAT_SUN or
            self.rx_message_ID == Definitions.SAT_HEARTBEAT_IMU or
            self.rx_message_ID == Definitions.SAT_HEARTBEAT_GPS
        ):
            if (self.rx_message_ID != self.gs_cmd):
                # print("Heartbeat received!")
                if (not self.new_session):
                    self.num_commands_sent = 0
                self.new_session = True
                self.reset_file_array = True

                self.cmd_queue.clear()
                self.cmd_queue = self.get_commands()

        elif self.rx_message_ID == Definitions.SAT_IMG_INFO:
            self.image_info_unpack(lora)
        elif (self.rx_message_ID == Definitions.SAT_IMG_CMD):
            # Get current timestamp
            time_this_packet = time.time() - self.time_diff
            self.time_diff = time.time()

            self.packet_time += time_this_packet

            # Add timestamp to output
            print(f'{time.time() - self.start_time}: Image Packet #{self.rx_message_sequence_count} received!')
            # Unpack image command
            self.image_unpack(lora)
        elif (self.rx_message_ID == Definitions.SAT_OTA_RES):
            self.ota_sat_rec_success = lora._last_payload.message[4:5]
            self.ota_sat_sequence_counter = lora._last_payload.message[5:7]
            print(f'OTA Response: {self.ota_sat_rec_success}')
        elif (self.rx_message_ID == Definitions.SAT_DEL_IMG):
            print(f'{time.time() - self.start_time}: Image fully downlinked, SAT deleted image')
        else:
            print("Telemetry received!")
            print("Lora header_to:", lora._last_payload.header_to)
            print("Lora header_from:", lora._last_payload.header_from)
            print("Lora header_id:", lora._last_payload.header_id)
            print("Lora header_flags:", lora._last_payload.header_flags)
            print("Message received header:", list(lora._last_payload.message[0:4]))

    '''
        Name: image_info_unpack
        Description: This function unpacks the image information from
        satellite such as command IDs, UIDs, size (KB), and message counts
        Inputs
            lora - lora - Declaration of lora class
    '''
    def image_info_unpack(self, lora):
        self.sat_images = Definitions.image_meta_info(lora)
        self.image_verification()

        # Diagnostic prints
        print("Image info received!")
        print("Message received header:", list(lora._last_payload.message[0:4]))

        if (self.sat_images.image_UID == 0x00):
            print("No images stored on satellite")

        else:
            print("Image UID:", self.sat_images.image_UID)
            print("Image size:", self.sat_images.image_size, "KB")
            print("Image message count:", self.sat_images.image_message_count)

    '''
        Name: image_verification
        Description: Ensures the satellite did not delete any images since the last pass.
                     Will reset the sequence counter if new image was loaded.
    '''
    def image_verification(self):
        if (self.target_image_UID != self.sat_images.image_UID):
            self.sequence_counter = 0
            self.image_array.clear()

    '''
        Name: image_unpack
        Description: This function unpacks the contents of the image and stores
        the image in a file when the complete image has been received.
        Inputs
            lora - Declaration of lora class
    '''
    def image_unpack(self, lora):
        self.image_array.append(lora._last_payload.message[4:self.rx_message_size + 4])

        if (self.sequence_counter != self.rx_message_sequence_count):
            self.missed_message = True

        # Increment sequence counter
        self.sequence_counter += 1
        if self.sequence_counter >= self.target_sequence_count:
            # Get the current time
            current_time = datetime.datetime.now()

            # Format the current time
            formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

            # Create image name
            filename = f"earth_image_{formatted_time}.jpg"
            refresh_file = "latest_earth_image.jpg"

            rec_bytes = open(filename, 'wb')
            more_bytes = open(refresh_file, 'wb')

            for i in range(self.target_sequence_count):
                rec_bytes.write(self.image_array[i])
                more_bytes.write(self.image_array[i])

            rec_bytes.close()
            more_bytes.close()

            response = self.s3_client.upload_file(filename, AWS_S3_BUCKET_NAME, filename)
            print(f'upload_log_to_aws response: {response}')

            response = self.s3_client.upload_file(refresh_file, AWS_PUBLIC_BUCKET, refresh_file)
            print(f'upload_log_to_aws response: {response}')

            self.image_array.clear()
            os.remove(filename)
            os.remove(refresh_file)
            self.influx.upload_image_info(self.sat_images.image_UID,
                                          self.sat_images.image_size,
                                          self.sat_images.image_message_count)

    '''
        Name: transmit_message
        Description: Ground station transmits a message via the LoRa module when the function is called.
        Inputs:
            lora - Declaration of lora class
    '''
    def transmit_message(self, lora):
        # Pull GS TX pin HIGH!
        self.tx_ctrl.on()
        send_multiple = True
        while (send_multiple):
            time.sleep(0.15)

            if self.num_commands_sent < self.cmd_queue_size:
                self.gs_cmd = self.cmd_queue[self.num_commands_sent]

                # OTA Update Sequence
                if (self.gs_cmd == Definitions.GS_OTA_REQ):
                    if (self.ota_sat_rec_success == 0):
                        self.ota_sequence_counter = self.ota_sat_sequence_counter

                    # If at the beginning of the OTA update sequence,
                    # fetch the file and store it in a buffer.
                    if (self.ota_sequence_counter <= 0):
                        self.OTA_get_info()
                    target_sequence_count = self.ota_files.file_message_count

                    # If 10 messages have not be sent and less than the target,
                    # request no ack and stay in loop.
                    if ((((self.ota_sequence_counter % self.send_mod) > 0) and
                         (self.ota_sequence_counter < (target_sequence_count - 1))) or (self.ota_sequence_counter == 0)):
                        send_multiple = True
                        self.gs_req_ack = 0x0
                    # Otherwise, exit loop and request ack
                    else:
                        send_multiple = False
                        self.gs_req_ack = Definitions.REQ_ACK_NUM

                    packets_remaining = (target_sequence_count - 1) - self.ota_sequence_counter
                    packet_size = len(self.file_array[self.ota_sequence_counter]) + 2
                    packet_size = packet_size.to_bytes(1, 'big')
                    # Transmit image in multiple packets
                    # Header
                    tx_header = ((self.gs_req_ack | Definitions.GS_OTA_REQ).to_bytes(1, 'big') +
                                 (self.ota_sequence_counter).to_bytes(2, 'big') + packet_size)
                    # Payload
                    tx_payload = packets_remaining.to_bytes(2, 'big') + self.file_array[self.ota_sequence_counter]
                    # Pack entire message
                    lora_tx_message = tx_header + tx_payload

                    self.ota_sequence_counter += 1
                    # If at the end of the file,
                    # Exit OTA sequence and reset sequence counter
                    if (self.ota_sequence_counter >= target_sequence_count):
                        self.num_commands_sent += 1
                        self.ota_sequence_counter = 0

                else:
                    lora_tx_message = self.pack_telemetry_command()
                    send_multiple = False
            else:
                lora_tx_message = self.pack_image_command()
                send_multiple = False

            # Send a message to the satellite device with address 2
            # Retry sending the message twice if we don't get an acknowledgment from the recipient

            status = lora.send(lora_tx_message, 255)

            # Check for groundstation acknowledgement
            if status is True:
                print(time.time() - self.start_time,
                      ": Ground station sent message: [",
                      *[hex(num) for num in lora_tx_message],
                      "]")
                print()
            else:
                print("No acknowledgment from recipient")
                print()

            while not lora.wait_packet_sent():
                pass

        lora.crc_error_count = 0

        # Set GS TX pin LOW!
        self.tx_ctrl.off()

    '''
        Name: pack_telemetry_command
        Description: Packs the next telemetry command to be transmitted
    '''
    def pack_telemetry_command(self):
        print("Sending command: ", self.cmd_queue[self.num_commands_sent])
        # Payload to transmit
        # Simulated for now!
        lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x01, 0x4])
        lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                           self.gs_cmd.to_bytes(1, 'big') +
                           (0x0).to_bytes(2, 'big'))
        lora_tx_message = lora_tx_header + lora_tx_payload
        self.num_commands_sent += 1

        return lora_tx_message

    '''
        Name: pack_image_command
        Description: Packs the next image command to be transmitted
    '''
    def pack_image_command(self):
        # Payload to transmit
        # Simulated for now!

        if self.new_session:
            self.time_diff = time.time()

            self.gs_cmd = Definitions.SAT_IMG_INFO
            lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x01, 0x4])
            lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                               self.gs_cmd.to_bytes(1, 'big') +
                               (0x0).to_bytes(2, 'big'))
            lora_tx_message = lora_tx_header + lora_tx_payload
            # Session is no longer "new" after telemetry has been retrieved
            self.new_session = False

        elif (self.gs_cmd == Definitions.SAT_DEL_IMG):
            # Downlinked an image, request to kill comms sequence
            self.gs_cmd = Definitions.GS_STOP
            lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x01, 0x4])
            lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                               self.gs_cmd.to_bytes(1, 'big') +
                               (0x0).to_bytes(2, 'big'))
            lora_tx_message = lora_tx_header + lora_tx_payload

        elif ((self.sequence_counter >= self.target_sequence_count) and (self.target_sequence_count != 0)):
            self.gs_cmd = Definitions.SAT_DEL_IMG
            lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x01, 0x4])
            lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                               self.gs_cmd.to_bytes(1, 'big') +
                               (0x0).to_bytes(2, 'big'))
            lora_tx_message = lora_tx_header + lora_tx_payload
            # Reset sequence counter and get new image
            self.sequence_counter = 0

        else:
            # Check image UID to see if SAT has a stored image or not
            if (self.sat_images.image_UID == 0x00):
                # No image on satellite, request to kill comms sequence
                self.gs_cmd = Definitions.GS_STOP
                lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x01, 0x4])
                lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                                   self.gs_cmd.to_bytes(1, 'big') +
                                   (0x0).to_bytes(2, 'big'))
                lora_tx_message = lora_tx_header + lora_tx_payload

            else:
                self.target_image_UID = self.sat_images.image_UID
                self.target_sequence_count = self.sat_images.image_message_count
                self.gs_cmd = Definitions.SAT_IMG_CMD

                # Output average packet time between last two acknowledgements
                sat_send_mod = 10
                print(f'Avg. transmission time: {self.packet_time / sat_send_mod}')
                self.packet_time = 0

                lora_tx_header = bytes([Definitions.REQ_ACK_NUM | Definitions.GS_ACK, 0x00, 0x00, 0x4])
                lora_tx_payload = (self.rx_message_ID.to_bytes(1, 'big') +
                                   self.gs_cmd.to_bytes(1, 'big') +
                                   self.sequence_counter.to_bytes(2, 'big'))
                lora_tx_message = lora_tx_header + lora_tx_payload

        return lora_tx_message

    '''
        Name: OTA_get_info
        Description: Read OTA file from memory and store in a buffer.
    '''
    def OTA_get_info(self):
        # Setup file class
        self.ota_files = OTA()

        # Setup initial file UIDs
        self.ota_files.file_UID = 0x1

        # ---------- File Size and Message Counts ---------- #
        # Get file size and message count
        file_stat = os.stat('tinyimage.jpg')
        self.ota_files.file_size = int(file_stat[6])
        self.ota_files.file_message_count = int(self.ota_files.file_size / 196)

        if ((self.ota_files.file_size % 196) > 0):
            self.ota_files.file_message_count += 1

        print("File size is", self.ota_files.file_size, "bytes")
        print("This file requires", self.ota_files.file_message_count, "messages")

        self.OTA_pack_files()

    '''
        Name: OTA_pack_info
        Description: Pack message UID, size, and message count for file in buffer.
    '''
    def OTA_pack_info(self):
        return (self.ota_files.file_UID.to_bytes(1, 'big') +
                self.ota_files.file_size.to_bytes(4, 'big') +
                self.ota_files.file_message_count.to_bytes(2, 'big'))

    '''
        Name: OTA_pack_files
        Description: Pack one file into an array
    '''
    def OTA_pack_files(self):
        # Initialize image arrays
        self.file_array = []

        # Image #Buffer Store
        bytes_remaining = self.ota_files.file_size
        send_bytes = open('tinyimage.jpg', 'rb')
        # Loop through image and store contents in an array
        while (bytes_remaining > 0):
            if (bytes_remaining >= 196):
                self.file_array.append(send_bytes.read(196))
            else:
                self.file_array.append(send_bytes.read(bytes_remaining))

            bytes_remaining -= 196
        # Close file when complete
        send_bytes.close()

    '''
        Name: get_commands
        Description: Gets Ground Station commands from a file.
    '''
    def get_commands(self):
        # Open the file in read mode
        with open('groundstation_commands.txt', 'r') as file:
            # Read all lines from the file
            lines = file.readlines()

        # Initialize an empty list to store the items
        items = []
        import protocol_database

        # Iterate over each line
        for line in lines:
            # Split the line based on the '.' character
            parts = line.split('.', 1)
            # If there are exactly 2 parts (number and item), add the item to the list
            if (len(parts) == 2) and (parts[1] != ''):
                command = parts[1].strip()
                items.append(getattr(protocol_database, command, None))

        return items

    def close_log(self):
        self.log.close()

        response = self.s3_client.upload_file(self.log_name, AWS_S3_BUCKET_NAME, self.log_name)
        print(f'upload_log_to_aws response: {response}')
        time.sleep(1)
        os.remove(self.log_name)


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
