from typing import Union

import serial
from serial import Serial


def kang2dec(kang, signed=True):
    return round(int.from_bytes(kang, byteorder='little', signed=signed) * 359.9 / 65536.0, 3)


def gauss2tesla(gauss):
    return round(int.from_bytes(gauss, byteorder='little', signed=True) * 750.0 / 65536.0, 3)


def fetch_dorient(message):
    if not message:
        return None
    else:
        message = message[3:-1]

    fields = [message[2 * i: 2 * (i + 1)] for i in range(9)]

    roll = kang2dec(fields[0])
    pitch = kang2dec(fields[1])
    course = kang2dec(fields[2], signed=False)
    magb = gauss2tesla(fields[6])
    magc = gauss2tesla(fields[7])
    magz = gauss2tesla(fields[8])

    return roll, pitch, course, magb, magc, magz


class Sensor:
    def __init__(self, bus):
        self.bus = bus

    def read(self):
        buf = b''
        while self.bus.in_waiting:
            buf = self.bus.read(1)
            if buf != b'~':
                continue
            buf += self.bus.read(21)
        return fetch_dorient(buf)


def debug():
    import threading
    import time

    serobj = serial.Serial(port="/dev/ttyUSB0")
    sensor = Sensor(bus=serobj)

    counter_empty_message = 0
    try:
        while True:
            message = sensor.read()
            time.sleep(0.1)
            if message:
                print(message)
            else:
                counter_empty_message += 1
                print("warning: empty message: {}".format(counter_empty_message))
    except KeyboardInterrupt as e:
        print(type(e).__name__, ": finish")
        serobj.close()


if __name__ == "__main__":
    debug()

