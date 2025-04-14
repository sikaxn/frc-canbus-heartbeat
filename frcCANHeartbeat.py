import can
import time

# Constants
UNIVERSAL_HEARTBEAT_CAN_ID = 0x01011840

# State tracking
last_mode = None
last_countdown = None
last_raw_data = None
last_alliance = None

def parse_frame(data):
    if len(data) != 8:
        raise ValueError(f"Expected 8 bytes, got {len(data)}")

    byte4 = data[4]
    byte7 = data[7]

    # Extract relevant bits
    enabled = (byte4 >> 4) & 0x01
    test_mode = (byte4 >> 3) & 0x01
    auto = (byte4 >> 2) & 0x01
    alliance_bit = byte4 & 0x01

    # Determine mode
    if test_mode:
        mode = "TEST ENABLED" if enabled else "TEST DISABLED"
    elif auto:
        mode = "AUTO ENABLED" if enabled else "AUTO DISABLED"
    else:
        mode = "TELEOP ENABLED" if enabled else "TELEOP DISABLED"

    # Determine alliance
    alliance = "RED" if alliance_bit else "BLUE"

    # Parse countdown timer
    countdown = byte7 if byte7 != 0xFF else None

    return mode, alliance, countdown

class HeartbeatListener(can.Listener):
    def on_message_received(self, msg):
        global last_mode, last_countdown, last_raw_data, last_alliance

        if not msg.is_extended_id:
            return

        if msg.arbitration_id != UNIVERSAL_HEARTBEAT_CAN_ID:
            return

        raw_data = msg.data.hex()

        try:
            mode, alliance, countdown = parse_frame(msg.data)
        except Exception as e:
            print(f"Error parsing frame: {e}")
            return

        changes = []

        # Mode changes
        if mode != last_mode:
            changes.append(f"Mode: {mode}")
            last_mode = mode

        # Alliance changes
        if alliance != last_alliance:
            changes.append(f"Alliance: {alliance}")
            last_alliance = alliance

        # Countdown changes
        if countdown != last_countdown:
            if countdown is not None:
                changes.append(f"Countdown: {countdown}")
            last_countdown = countdown

        # Print if anything changed or raw data changed
        if raw_data != last_raw_data or changes:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] Raw Data: {raw_data}", end='')
            if changes:
                print(f" | {' | '.join(changes)}")
            else:
                print()
            last_raw_data = raw_data

def main():
    print("Initializing CANalyst-II interface...")

    try:
        bus = can.Bus(
            interface='canalystii',
            channel=0,
            device=0,
            bitrate=1000000
        )
    except Exception as e:
        print(f"CAN bus initialization failed: {e}")
        return

    print("CAN interface initialized successfully!")
    print("Listening for Universal Heartbeat (fully accurate mode parsing)...")
    print("Press Ctrl+C to stop.\n")

    listener = HeartbeatListener()
    notifier = can.Notifier(bus, [listener])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping CAN monitor...")
    finally:
        notifier.stop()
        bus.shutdown()

if __name__ == "__main__":
    main()
