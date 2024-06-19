from influxdb_client_3 import InfluxDBClient3, Point


class DATABASE:
    '''
        Name: __init__
        Description: Initialization of DATABASE class
    '''
    def __init__(self):
        self.host = "https://us-east-1-1.aws.cloud2.influxdata.com"

        self.client = InfluxDBClient3(host=self.host, token=self.token, org=self.org)

        self.database = "Argus-1 Telemetry - Spring 2024"

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

    def upload_battery_info(self, soc, current):
        data = {
            "point1": {
                "Subsystem": "Battery",
                "Battery Info": {
                    "State of Charge (%)": {
                        "SOC": soc,
                    },
                    "Battery Current (mA)": {
                        "Current": current,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "Battery Info"
            for item_key, item_value in data[key]["Battery Info"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                field_value = item_value[field_name]
                point.field(item_key, field_value)

            self.client.write(database=self.database, record=point)

    def upload_sun_vector(self, x, y, z):
        data = {
            "point1": {
                "Subsystem": "Sun Vector Info",
                "Sun Vector": {
                    "Sun Vector X (Lux)": {
                        "X": x,
                    },
                    "Sun Vector Y (Lux)": {
                        "Y": y,
                    },
                    "Sun Vector Z (Lux)": {
                        "Z": z,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "Image"
            for item_key, item_value in data[key]["Sun Vector"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                point.field(item_key, item_value[field_name])

            self.client.write(database=self.database, record=point)

    def upload_IMU_Info(self, x_mag, y_mag, z_mag, x_gyro, y_gyro, z_gyro):
        data = {
            "point1": {
                "Subsystem": "IMU Info",
                "IMU": {
                    "X-Axis Magnetometer (µT)": {
                        "X Magnetometer": x_mag,
                    },
                    "Y-Axis Magnetometer (µT)": {
                        "Y Magnetometer": y_mag,
                    },
                    "Z-Axis Magnetometer (µT)": {
                        "Z Magnetometer": z_mag,
                    },
                    "X-Axis Gyroscope (deg/sec)": {
                        "X Gyroscope": x_gyro,
                    },
                    "Y-Axis Gyroscope (deg/sec)": {
                        "Y Gyroscope": y_gyro,
                    },
                    "Z-Axis Gyroscope (deg/sec)": {
                        "Z Gyroscope": z_gyro,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "Image"
            for item_key, item_value in data[key]["IMU"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                point.field(item_key, item_value[field_name])

            self.client.write(database=self.database, record=point)

    def upload_system_info(self, status, time):
        data = {
            "point1": {
                "Subsystem": "System",
                "System Info": {
                    "Satellite Status": {
                        "Status": status,
                    },
                    "Time Reference": {
                        "Time": time,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "System Info"
            for item_key, item_value in data[key]["System Info"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                field_value = item_value[field_name]
                point.field(item_key, field_value)

            self.client.write(database=self.database, record=point)

    def upload_jetson_info(self, ram_usage, disk_usage, cpu_temp, gpu_temp):
        data = {
            "point1": {
                "Subsystem": "Jetson",
                "Jetson Info": {
                    "RAM Usage": {
                        "RAM": ram_usage,
                    },
                    "Disk Usage": {
                        "Disk": disk_usage,
                    },
                    "CPU Temperature": {
                        "C_Temp": cpu_temp,
                    },
                    "GPU Temperature": {
                        "G_Temp": gpu_temp,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "Jetson Info"
            for item_key, item_value in data[key]["Jetson Info"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                field_value = item_value[field_name]
                point.field(item_key, field_value)

            self.client.write(database=self.database, record=point)

    def upload_reboot(self, reboot):
        data = {
            "point1": {
                "Subsystem": "Satellite Reboot Counter",
                "SAT Reboot Counter": {
                    "Reboot Counter": {
                        "Counter": reboot,
                    }
                }
            }
        }

        for key in data:
            point = Point("argus-1").tag("Subsystem", data[key]["Subsystem"])

            # Add fields for each item under "System Info"
            for item_key, item_value in data[key]["SAT Reboot Counter"].items():
                field_name = list(item_value.keys())[0]  # Extracting the key of the inner dictionary
                field_value = item_value[field_name]
                point.field(item_key, field_value)

            self.client.write(database=self.database, record=point)
