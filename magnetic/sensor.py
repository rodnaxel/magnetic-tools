import threading
from queue import Queue

import serial


def kang2dec(kang, signed=True):
	return round(int.from_bytes(kang, byteorder='little', signed=signed) * 359.9 / 65536.0, 3)


def gauss2tesla(gauss):
	return round(int.from_bytes(gauss, byteorder='little', signed=True) * 750.0 / 65536.0, 3)


def fetch_dorient(message):
	fields = [message[2 * i: 2 * (i + 1)] for i in range(9)]
	
	roll = kang2dec(fields[0])
	pitch = kang2dec(fields[1])
	course = kang2dec(fields[2], signed=False)
	magb = gauss2tesla(fields[6])
	magc = gauss2tesla(fields[7])
	magz = gauss2tesla(fields[8])
	
	return roll, pitch, course, magb, magc, magz


sensor_buffer = Queue(maxsize=1)


class Sensor:
	SOP1 = bytes.fromhex("0d")
	SOP2 = bytes.fromhex("0a")
	SOP3 = bytes.fromhex("7e")
	
	def __init__(self, bus):
		self.bus = bus
	
	# self.messages = deque(maxlen=1)
	
	def revert(self):
		self.bus.write(bytes.fromhex("0d0a7e7201040c"))
	
	def data(self):
		d = sensor_buffer.get()
		return d
	
	def readany(self):
		""" This function used to read any message from sensor"""
		print('Start readany')
		message = b''
		start = 0
		pid = 0
		size = 0
		
		while True:
			buf = self.bus.read(1)
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
						data = fetch_dorient(message)
						sensor_buffer.put(data)
					start = 0
					message = b''
			else:
				print("Error: sensor.readany(): ")


class Calibration:
	def __init__(self, bus):
		self.sensor = Sensor(bus)
		self.dataset = []
		self.finish = False
	
	def start(self):
		self.data_collection()
	
	def stop(self):
		self.finish = True
	
	def data_collection(self):
		self.sensor.revert()
		
		# TODO: <1> Make algoritm finish data collection
		# TODO: <2> Run sensor.readany() in separate thread and then get data by Timer
		thread = threading.Thread(target=self.sensor.readany, daemon=True)
		thread.start()
		
		while not self.finish:
			data = self.sensor.data()
			if not data:
				continue
			roll, pitch, heading, hx, hy, hz = data
			print(hx, hy)
	
	def compute(self):
		"""TODO: This function used to compute deviation coefficients"""


def debug():
	serobj = serial.Serial("/dev/ttyUSB0", timeout=0.1)
	cal = Calibration(serobj)
	
	try:
		cal.data_collection()
	except KeyboardInterrupt as e:
		cal.stop()
		serobj.close()


# plot(cal.dataset)


if __name__ == "__main__":
	debug()
