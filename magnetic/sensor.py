import threading
import time
from queue import Queue

import serial
import serial.tools.list_ports as tools


def scan_ports():
	ports = [port.device for port in tools.comports()]
	return ports


def kang2dec(kang, signed=True):
	return round(int.from_bytes(kang, byteorder='little', signed=signed) * 359.9 / 65536.0, 3)


def dec2kang(dec, signed=True):
	return (int(dec * 65536.0 / 359.9)).to_bytes(2, byteorder='little', signed=signed)


def gauss2tesla(gauss):
	return round(int.from_bytes(gauss, byteorder='little', signed=True) * 750.0 / 65536.0, 3)


def tesla2gauss(tesla):
	return (int(tesla * 65536.0 / 750.0)).to_bytes(2, byteorder='little', signed=True)


def parse_dorient(message):
	fields = [message[2 * i: 2 * (i + 1)] for i in range(9)]
	roll = kang2dec(fields[0])
	pitch = kang2dec(fields[1])
	heading = kang2dec(fields[2], signed=False)
	magc_raw = gauss2tesla(fields[3])
	magb_raw = gauss2tesla(fields[4])
	magz_raw = gauss2tesla(fields[5])
	magc = gauss2tesla(fields[6])
	magb = gauss2tesla(fields[7])
	magz = gauss2tesla(fields[8])
	return roll, pitch, heading, magc_raw, magb_raw, magz_raw, magc, magb, magz


SENSOR_QUEUE = Queue(maxsize=1)


class SensorDriver(object):
	SOP1 = bytes.fromhex("0d")
	SOP2 = bytes.fromhex("0a")
	SOP3 = bytes.fromhex("7e")

	def __init__(self, bus):
		self.bus = bus

	def recieve(self):
		pass

	def send(self):
		pass


class Sensor(object):
	SOP1 = bytes.fromhex("0d")
	SOP2 = bytes.fromhex("0a")
	SOP3 = bytes.fromhex("7e")

	def __init__(self, bus):
		self.bus = bus
		self._running = True

	def recieve(self):
		return SENSOR_QUEUE.get()
	
	def terminate(self):
		self._running = False
	
	def run(self):
		""" This function used to read any message from sensor"""
		print('Start readany')
		message = b''
		start = 0
		pid = 0
		size = 0
		
		while self._running:
			try:
				buf = self.bus.read(1)
			except serial.SerialException:
				SENSOR_QUEUE.put(object())

			if start == 0:
				if buf == self.SOP1:
					start += 1
				else:
					start = 0
			elif start == 1:
				if buf == self.SOP2:
					start += 1
				else:
					start = 0
			elif start == 2:
				if buf == self.SOP3:
					start += 1
				else:
					start = 0
			elif start == 3:
				pid = int.from_bytes(buf, byteorder='little')
				start = 4
			elif start == 4:
				size = int.from_bytes(buf, byteorder='little')
				start = 5
			elif start == 5:
				if len(message) < size:
					message += buf
				else:
					if pid == 112:
						data = [pid]
						data.extend(parse_dorient(message))
						SENSOR_QUEUE.put(data)
					start = 0
					message = b''
			else:
				print("Error: sensor.readany(): ")


def debug():
	ports = scan_ports()
	print(f"Available ports: {ports}")
	port = input("Select port:")
	serobj = serial.Serial(port, timeout=0.1)
	sensor = Sensor(serobj)

	t = threading.Thread(target=sensor.run)
	t.start()
	
	try:
		while True:
			data = sensor.recieve()
			print(data)
			time.sleep(0.1)
	except KeyboardInterrupt as e:
		sensor.terminate()
		serobj.close()


if __name__ == "__main__":
	debug()