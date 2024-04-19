"""
'protocol_database.py'
======================
Python package containing protocol constants (IDs etc.). 
Also contains functions for constructing/deconstructing 
protocol messages. 

Each message has the following header: 
MESSAGE_ID : 1 byte 
SEQ_COUNT  : 2 bytes
LENGTH     : 1 byte  

Authors: Akshat Sahay, DJ Morvay
"""

# Message ID definitions 
SAT_HEARTBEAT_BATT  = 0x00
SAT_HEARTBEAT_SUN   = 0x01
SAT_HEARTBEAT_IMU   = 0x02
SAT_HEARTBEAT_GPS   = 0x03

GS_ACK  = 0x08
SAT_ACK = 0x09

GS_OTA_REQ = 0x14
SAT_OTA_RES = 0x15

SAT_IMG_INFO   = 0x21
SAT_DEL_IMG = 0x22

SAT_IMG_CMD = 0x50

REQ_ACK_NUM = 0x80

class IMAGES:
    def __init__(self):
        # Image #1 declarations
        self.image_UID = 0x0
        self.image_size = 0
        self.image_message_count = 0

class OTA:
    def __init__(self):
        # Image #1 declarations
        self.file_UID = 0x0
        self.file_size = 0
        self.file_message_count = 0

# Function definitions 
def gs_unpack_header(lora):
    """
        Name: gs_unpack_header
        Description: Unpacks the header information (message ID, message sequence count, and message size)
                     from the received lora message. 

        Return
            acknowledgement_request
            message_ID
            message_sequence_count
            message_sizes
    """
    ack_req = (int.from_bytes((lora._last_payload.message[0:1]),byteorder='big') & 0b10000000) >> 7
    message_ID = int.from_bytes((lora._last_payload.message[0:1]),byteorder='big') & 0b01111111
    message_sequence_count = int.from_bytes(lora._last_payload.message[1:3],byteorder='big')
    message_size = int.from_bytes(lora._last_payload.message[3:4],byteorder='big')

    lora_rx_message = list(lora._last_payload.message)
    lora_rx_message[0] = lora_rx_message[0] & 0b01111111
    deconstruct_message(lora_rx_message)

    return ack_req, message_ID, message_sequence_count, message_size

def image_meta_info(lora):
    """
        Name: image_meta_info
        Description: Parses a lora packet and returns the stored images meta information, 
                     such as the CMD ID, UID, size, and message count.

        Return 
            stored_images (class)
    """
    stored_image = IMAGES()

    # Get image information
    stored_image.image_UID = int.from_bytes(lora._last_payload.message[4:5],byteorder='big')
    stored_image.image_size = int.from_bytes(lora._last_payload.message[5:9],byteorder='big')
    stored_image.image_message_count = int.from_bytes(lora._last_payload.message[9:11],byteorder='big')

    return stored_image

def deconstruct_message(lora_rx_message):
    """
    :param lora_rx_message: Received LoRa message
    :return: None

    Deconstructs RX message based on message ID
    """
    # Check RX message ID 
    if(lora_rx_message[0] == SAT_HEARTBEAT_BATT):
        # Received satellite heartbeat, deconstruct header 
        print("Received SAT heartbeat!")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("Sequence Count:", sq)
        print("Message Length:", lora_rx_message[3])

        # Deconstruct message 
        print("Satellite system status: " + str(lora_rx_message[4]) + str(lora_rx_message[5]))

        print("Battery SOC 1:", lora_rx_message[6])
        print("Battery SOC 2:", lora_rx_message[7])
        print("Battery SOC 3:", lora_rx_message[8])
        print("Battery SOC 4:", lora_rx_message[9])
        print("Battery SOC 5:", lora_rx_message[10])
        print("Battery SOC 6:", lora_rx_message[11])

        sat_current = (lora_rx_message[12] << 8) + lora_rx_message[13]
        print("Total current draw:", sat_current)

        print("Reboot count:", lora_rx_message[14])
        print("Payload statys:", hex(lora_rx_message[15]))

        sat_time = (lora_rx_message[16] << 24) + (lora_rx_message[17] << 16) + (lora_rx_message[18] << 8) + lora_rx_message[19]
        print("Satellite time:", sat_time)

        print()
    
    elif(lora_rx_message[0] == SAT_HEARTBEAT_SUN):
        # Received satellite heartbeat, deconstruct header 
        print("Received SAT heartbeat!")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("Sequence Count:", sq)
        print("Message Length:", lora_rx_message[3])

        # Deconstruct message 
        print("Satellite system status: " + str(lora_rx_message[4]) + str(lora_rx_message[5]))

        print("Sun vector X:", convert_floating_point_hp(lora_rx_message[6:10]))
        print("Sun vector Y:", convert_floating_point_hp(lora_rx_message[10:14]))
        print("Sun vector Z:", convert_floating_point_hp(lora_rx_message[14:18]))

        sat_time = (lora_rx_message[18] << 24) + (lora_rx_message[19] << 16) + (lora_rx_message[20] << 8) + lora_rx_message[21]
        print("Satellite time:", sat_time)

        print()
    
    elif(lora_rx_message[0] == SAT_IMG_INFO):
        # Image packet, do nothing 
        return 

    elif(lora_rx_message[0] == SAT_IMG_CMD):
        # Image packet, do nothing 
        return 

    elif(lora_rx_message[0] == SAT_DEL_IMG):
        # Image packet, do nothing 
        return 
    
    else:
        # Received satellite heartbeat, deconstruct header 
        print("Received unknown SAT message")
        sq = (lora_rx_message[1] << 8) + lora_rx_message[2]
        print("Sequence Count:", sq)
        print("Message Length:", lora_rx_message[3])

        print("Message has unknown definition")
        print()

### Helper functions for converting to FP format and back ###
def convert_fixed_point(val):
    """
    :param val: Value to convert to fixed point 
    :return: value in FP as byte list 

    Convert value to FP with 2 int bytes, 2 dec bytes
    Range: [-32767.9999], 32767.9999]
    """
    message_list = []
    neg_bit_flag = 0

    # If val -ve, convert to natural, set first bit of MSB 
    if(val < 0):
        val = -1 * val
        neg_bit_flag = 1

    # Isolate int and write to 2 bytes 
    val_int = int(val)
    val_int_LSB = val_int & 0xFF
    val_int_MSB = (val_int >> 8) & 0xFF

    # Set MSB first bit as neg_bit_flag
    val_int_MSB |= (neg_bit_flag << 7)

    # Add the values to the test list 
    message_list.append(val_int_MSB)
    message_list.append(val_int_LSB)

    # Isolate decimal and write to 2 bytes
    val_dec = val - val_int
    val_dec = int(val_dec * 65536)
    val_dec_LSB = val_dec & 0xFF
    val_dec_MSB = (val_dec >> 8) & 0xFF

    # Add the values to the test list 
    message_list.append(val_dec_MSB)
    message_list.append(val_dec_LSB)

    return message_list

def convert_floating_point(message_list):
    """
    :param message_list: Byte list to convert to floating 
    :return: value as floating point  

    Convert FP value back to floating point 
    Range: [-32767.9999], 32767.9999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine 
    if((message_list[0] >> 7) == 1): 
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine 
    val += (message_list[0] << 8) + message_list[1]
    val += ((message_list[2] << 8) + message_list[3]) / 65536
    if(neg_bit_flag == 1): val = -1 * val

    return val

def convert_fixed_point_hp(val):
    """
    :param val: Value to convert to fixed point 
    :return: value in FP as byte list 

    Convert value to HP FP with 1 int byte, 3 dec bytes
    Range: [-128.9999999, 128.9999999]
    """
    message_list = []
    neg_bit_flag = 0

    # If val -ve, convert to natural, set first bit of MSB 
    if(val < 0):
        val = -1 * val
        neg_bit_flag = 1

    # Isolate int and write to 1 byte 
    val_int = int(val)
    val_int_LSB = val_int & 0xFF

    # Set LSB first bit as neg_bit_flag
    val_int_LSB |= (neg_bit_flag << 7)

    # Add the values to the test list 
    message_list.append(val_int_LSB)

    # Isolate decimal and write to 3 bytes
    val_dec = val - val_int
    val_dec = int(val_dec * 16777216)
    val_dec_LSB  = val_dec & 0xFF
    val_dec_MiSB = (val_dec >> 8) & 0xFF
    val_dec_MSB  = (val_dec >> 16) & 0xFF

    # Add the values to the test list 
    message_list.append(val_dec_MSB)
    message_list.append(val_dec_MiSB)
    message_list.append(val_dec_LSB)

    return message_list

def convert_floating_point_hp(message_list):
    """
    :param message_list: Byte list to convert to floating 
    :return: value as floating point  

    Convert HP FP value back to floating point 
    Range: [-128.9999999, 128.9999999]
    """
    val = 0
    neg_bit_flag = 0

    # Check -ve, extract LSB bytes for val, combine 
    if((message_list[0] >> 7) == 1): 
        message_list[0] &= 0x7F
        neg_bit_flag = 1

    # Extract bytes for val, combine 
    val += message_list[0]
    val += ((message_list[1] << 16) + (message_list[2] << 8) + message_list[3] + 1) / 16777216
    if(neg_bit_flag == 1): val = -1 * val

    return val