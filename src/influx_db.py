from influxdb_client_3 import InfluxDBClient3, Point

class DATABASE:
    '''
        Name: __init__
        Description: Initialization of DATABASE class
    '''
    def __init__(self):
        self.host = "https://us-east-1-1.aws.cloud2.influxdata.com"

        self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org)

        self.database="Argus-1 Telemetry - Spring 2024"

    def upload_image_info(self, UID, image_size, message_count):
        data = {
        "point1": {
            "Subsystem": "Downlinked Image Info",
            "Image": {
            "Image UID": {
                "UID": UID,
            },
            "Image Size (Bytes)": {
                "Size": image_size,
            },
            "Image Message Count": {
                "Count": message_count,
            }
            }
        }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])
            
            # Add fields for each item under "Image"
            for item_key, item_value in data[key]["Image"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                point.field(item_key, item_value[field_name])

            self.client.write(database=self.database, record=point)

    def upload_last_received_packet(self, ack, message_ID, sequence_count, message_size):
        data = {
        "point1": {
            "Subsystem": "Downlinked Message Info",
            "Message": {
            "Request Acknowledgement": {
                "Request": ack,
            },
            "Message ID": {
                "ID": message_ID,
            },
            "Message Sequence Count": {
                "Count": sequence_count,
            },
            "Message Size (Bytes)": {
                "Size": message_size,
            }
            }
        }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])
            
            # Add fields for each item under "Image"
            for item_key, item_value in data[key]["Message"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                point.field(item_key, item_value[field_name])

            self.client.write(database=self.database, record=point)