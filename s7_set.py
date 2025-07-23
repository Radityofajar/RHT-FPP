#!/usr/bin/env python3

import argparse
import snap7
import struct
import sys

# Define PLC IPs
PLC_IPS = {
    1: "192.168.102.211",  # PLC RHT
    2: "192.168.102.212",  # PLC NTC
}

# Define sensor offset mappings for each PLC
SENSOR_OFFSETS = {
    1: {  # RHT sensors (Min, Max)
        "RHT-T1": (6, 8),
        "RHT-T2": (54, 56),
        "RHT-T3": (102, 104),
        "RHT-H1": (30, 32),
        "RHT-H2": (78, 80),
        "RHT-H3": (126, 128),
    },
    2: {  # NTC sensors (Min, Max)
        "NTC-T1": (4, 6),
        "NTC-T2": (26, 28),
        "NTC-T3": (48, 50),
        "NTC-T4": (70, 72),
        "NTC-T5": (92, 94),
        "NTC-T6": (114, 116),
        "NTC-T7": (136, 138),
    }
}

def create_parser():
    helptext = """
    This script writes an INT value to a Siemens PLC using snap7 for min-max.
    Expected Zabbix key format:
    s7_set.py[PLC, DB, Sensor, Min/Max, Value]
    """
    parser = argparse.ArgumentParser(description=helptext)
    parser.add_argument("PLC", type=int, choices=[1, 2],
                        help="1 for PLC RHT or 2 for PLC NTC")
    parser.add_argument("DB", type=int)
    parser.add_argument("Sensor", type=str)
    parser.add_argument("MinMax", type=str.lower, choices=["min", "max"])
    parser.add_argument("Data", type=int)
    return parser.parse_args()

if __name__ == "__main__":
    args = create_parser()

    plc_ip = PLC_IPS.get(args.PLC)
    sensor_map = SENSOR_OFFSETS.get(args.PLC)

    if not sensor_map:
        print("ERROR: Invalid PLC ID.", file=sys.stderr)
        sys.exit(1)

    offsets = sensor_map.get(args.Sensor)
    if not offsets:
        valid_sensors = ', '.join(sensor_map.keys())
        print(f"ERROR: Invalid Sensor option. Valid options are: {valid_sensors}", file=sys.stderr)
        sys.exit(1)

    offset = offsets[0] if args.MinMax == "min" else offsets[1]

    plc = snap7.client.Client()
    try:
        plc.connect(plc_ip, rack=0, slot=1)

        if not plc.get_connected():
            print(f"ERROR: Failed to connect to PLC at {plc_ip}", file=sys.stderr)
            sys.exit(1)

        print(f"Connected to PLC at {plc_ip}")

        # Convert integer to 2-byte signed representation
        data_bytes = struct.pack('>h', args.Data)

        # Write the value to the PLC
        plc.db_write(args.DB, offset, data_bytes)
        print(f"Data written successfully to PLC at {plc_ip}: DB{args.DB}, offset {offset}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            plc.disconnect()
        except:
            pass
