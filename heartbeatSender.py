import can
import time

# CAN constants
UNIVERSAL_HEARTBEAT_CAN_ID = 0x01011840

# Settings
CAN_CHANNEL = 0
CAN_DEVICE = 0
CAN_BITRATE = 1000000

# Initialize counter, mimic RoboRIO counter increments (~32,000 each frame)
fake_fpga_counter = 0x2882b8fd  # Start from your captured value
COUNTER_INCREMENT = 32152  # Based on your capture

def build_packet(enabled, auto, test, alliance_red, countdown):
    global fake_fpga_counter

    # Bytes 0–3: FPGA counter (incrementing)
    counter_bytes = fake_fpga_counter.to_bytes(4, byteorder='big')

    # Byte 4: mode bits
    byte4 = 0
    if enabled:
        byte4 |= (1 << 4)
    if test:
        byte4 |= (1 << 3)
    if auto:
        byte4 |= (1 << 2)
    if alliance_red:
        byte4 |= (1 << 0)

    # Bytes 5–6: Reserved (set to zero)
    byte5 = 0x00
    byte6 = 0x00

    # Byte 7: Countdown (seconds)
    byte7 = countdown if countdown is not None else 0xFF

    data = list(counter_bytes) + [byte4, byte5, byte6, byte7]

    return data

def main():
    global fake_fpga_counter

    print("Initializing CANalyst-II interface for sending heartbeat...")

    try:
        bus = can.Bus(
            interface='canalystii',
            channel=CAN_CHANNEL,
            device=CAN_DEVICE,
            bitrate=CAN_BITRATE
        )
    except Exception as e:
        print(f"CAN bus initialization failed: {e}")
        return

    print("CAN bus ready! Sending heartbeat packets...")
    print("Press Ctrl+C to stop.\n")

    # Configurable:
    enabled = True
    auto = False
    test = False
    alliance_red = False  # Blue alliance for your test
    countdown = None  # Not active for Teleop Disabled

    try:
        while True:
            # Build CAN frame
            data = build_packet(enabled, auto, test, alliance_red, countdown)

            # Send CAN message
            msg = can.Message(arbitration_id=UNIVERSAL_HEARTBEAT_CAN_ID,
                              data=data,
                              is_extended_id=True)

            bus.send(msg)

            # Print sent message for debug
            print(f"Sent: {msg}")

            # Update counter to simulate FPGA timer tick
            fake_fpga_counter = (fake_fpga_counter + COUNTER_INCREMENT) % (2 ** 32)

            time.sleep(0.02)  # ~50Hz heartbeat
    except KeyboardInterrupt:
        print("Stopping heartbeat sender...")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()
