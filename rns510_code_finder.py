import serial
import time
import argparse
import logging


class RNS510CodeFinder:
    """
    A class to interface with the RNS510 device and attempt to decode the PIN by brute force.

    Attributes:
        portname (str): The name of the serial port to which the RNS510 device is connected.
        baudrate (int): The baud rate for the serial connection.
        timeout (float): The read timeout for the serial connection.
        serial_port (serial.Serial): The serial port object for communication.
        stop_count (bool): A flag to stop the PIN search process.
        pin (str): The current PIN being tested.
        rx (str): A buffer to store received data from the device.
    """

    def __init__(self, portname, baudrate=115200, timeout=1):
        """
        Initializes the RNS510Decode object with the specified serial port settings.

        Args:
            portname (str): The name of the serial port to use.
            baudrate (int): The baud rate for the serial connection.
            timeout (float): The timeout for the serial connection read operations.
        """
        self.serial_port = serial.Serial(
            port=portname, baudrate=baudrate, timeout=timeout
        )
        self.stop_count = False
        self.pin = "0000"
        self.rx = ""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def open_port(self):
        """
        Opens the serial port if it is not already open.
        """
        if not self.serial_port.is_open:
            self.serial_port.open()
            logging.info(f"Opened serial port {self.serial_port.port}")

    def close_port(self):
        """
        Closes the serial port if it is open.
        """
        if self.serial_port.is_open:
            self.serial_port.close()
            logging.info(f"Closed serial port {self.serial_port.port}")

    def send_command(self, command):
        """
        Sends a command to the RNS510 device over the serial connection.

        Args:
            command (str): The command string to send.
        """
        self.serial_port.write(f"{command}\n".encode("utf-8"))
        logging.debug(f"Sent command: {command}")

    def read_response(self):
        """
        Reads the response from the RNS510 device.

        Returns:
            str: The accumulated response from the device.
        """
        self.rx += self.serial_port.read(self.serial_port.in_waiting).decode("utf-8")
        logging.debug(f"Received response: {self.rx}")
        return self.rx

    def verify_pin(self, pin):
        """
        Verifies if the given PIN is correct by sending a command to the device.

        Args:
            pin (str): The PIN to verify.

        Returns:
            bool: True if the PIN is valid, False if invalid, or None if no response.
        """
        self.send_command(f"TpPvVerifyPin({pin})")
        time.sleep(0.1)
        response = self.read_response()
        if "Hash valid" in response:
            return True
        elif "Hash invalid" in response:
            return False
        return None

    def find_code(self, start, stop):
        """
        Attempts to find the correct PIN by brute force within a specified range.

        Args:
            start (int): The starting value of the PIN range.
            stop (int): The stopping value of the PIN range.
        """
        try:
            self.open_port()
            for i in range(start, stop + 1):
                if self.stop_count:
                    logging.info("Process stopped by user.")
                    break
                pin = str(i).zfill(4)
                logging.info(f"Trying code: {pin}")
                valid = self.verify_pin(pin)
                if valid is True:
                    logging.info(f"Code found: {pin}")
                    self.pin = pin
                    break
                elif valid is False:
                    logging.info(f"Code {pin} is invalid.")
                else:
                    logging.warning(f"No response for code {pin}, retrying...")
        except serial.SerialException as e:
            logging.error(f"Serial communication error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            self.close_port()


def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="RNS510 PIN Code Decoder")
    parser.add_argument(
        "--portname",
        type=str,
        required=True,
        help="The name of the COM port (e.g., COM3)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="The baud rate for the serial connection (default: 115200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1,
        help="Timeout for the serial connection in seconds (default: 1)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="The starting value of the PIN range (default: 0)",
    )
    parser.add_argument(
        "--stop",
        type=int,
        default=1999,
        help="The stopping value of the PIN range (default: 1999)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    decoder = RNS510CodeFinder(
        portname=args.portname, baudrate=args.baudrate, timeout=args.timeout
    )

    try:
        decoder.find_code(args.start, args.stop)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        decoder.close_port()
