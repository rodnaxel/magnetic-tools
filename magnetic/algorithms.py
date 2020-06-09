import math
from math import cos, sin
from operator import itemgetter


def to_horizont(y, x, z, roll_grad, pitch_grad):
	""" This function used to convert field from non-horizontal to horizontal
		x,y : float : magnetic fields
		z : float : negetive from sensor
		roll_grad, pitch_grad: float : angle in grad
	"""
	r = math.radians(roll_grad)
	p = math.radians(-pitch_grad)

	# Rewrite formul with z is as negative
	xh = x * cos(p) - y * sin(p) * sin(r) + z * sin(p) * cos(r)
	yh = y * cos(r) + z * sin(r)
	zh = x * sin(p) + y * sin(r) * cos(p) - z * cos(p) * cos(r)

	return yh, xh, zh


class Algorithm:
	""" This class used to correct raw magnetic field B,C"""
	
	def __init__(self, fields):
		self.ds = fields.copy()
		self._compute()
	
	def __repr__(self):
		return "<class Algorithm> x_offset={0:.2f}, y_offset={1:.2f}, phi={2:.2f}, clockwise={3}, k={4:.2f}".format(
			self.x_offset,
			self.y_offset,
			self.phi_degree,
			self.clockwise,
			self.k)
	
	def _compute(self):
		""" Calculate calibration coefficients (Xoffset, Yoffset, А, B, C, D)"""
		self._compute_hard_iron()
		ds_hard_iron = [(x - self.x_offset, y - self.y_offset) for (x, y) in self.ds]
		self._compute_soft_iron(ds_hard_iron)
	
	def _compute_soft_iron(self, ds_hard_iron):
		# <4> Calculate full magnetic vector H for each pair X, Y and find max H <\>
		h_max = max(
			ds_hard_iron,
			key=lambda item: math.sqrt(item[0] * item[0] + item[1] * item[1])
		)
		# <5> Caclulate rotate side and angle phi <\>
		if (h_max[1] * h_max[0]) > 0:
			phi = math.atan(h_max[1] / h_max[0])
			self.clockwise = clockwise = True
		else:
			phi = -math.atan(h_max[1] / h_max[0])
			self.clockwise = clockwise = False
		self.phi_degree = phi * (180.0 / math.pi)
		
		# <6> Rotate each pair X, Y on theta angle <\>
		def rotate(x, y, angle, clockwise):
			if clockwise:
				x_rot = x * math.cos(angle) + y * math.sin(angle)
				y_rot = - x * math.sin(angle) + y * math.cos(angle)
			else:
				x_rot = x * math.cos(angle) - y * math.sin(angle)
				y_rot = x * math.sin(angle) + y * math.cos(angle)
			return x_rot, y_rot
		
		ds_rotate = [rotate(x, y, phi, clockwise) for (x, y) in ds_hard_iron]
		# <7> Caclulate a, b, k  magnetic ellipsoid <\>
		ds_rotate_module = [(abs(x), abs(y)) for (x, y) in ds_rotate]
		a = max(ds_rotate_module, key=itemgetter(0))[0]
		b = max(ds_rotate_module, key=itemgetter(1))[1]
		self.k = k = b / a
		# <8> Calculate correction coefficient A,B,C,D
		self.A = k * pow(math.cos(phi), 2) + pow(math.sin(phi), 2)
		self.B = (k * math.sin(2 * phi) - math.sin(2 * phi)) * 0.5
		self.C = (math.sin(2 * phi) - k * math.sin(2 * phi)) * 0.5
		self.D = k * pow(math.sin(phi), 2) + pow(math.cos(phi), 2)
	
	def _compute_hard_iron(self):
		x_max = max(self.ds)[0]
		x_min = min(self.ds)[0]
		y_max = max(self.ds, key=itemgetter(1))[1]
		y_min = min(self.ds, key=itemgetter(1))[1]
		# <2> Calculate hard iron offset <\>
		self.x_offset = (x_max + x_min) * 0.5
		self.y_offset = (y_max + y_min) * 0.5
	
	def correct(self, x, y):
		x0, y0 = self._compensate_hard_iron(x, y)
		return self._compensate_soft_iron(x0, y0)
	
	def _compensate_soft_iron(self, x0, y0):
		if self.clockwise:
			return (x0 * self.A + y0 * self.B), (-x0 * self.C + y0 * self.D)
		else:
			return (x0 * self.A - y0 * self.B), (x0 * self.C + y0 * self.D)
	
	def _compensate_hard_iron(self, x, y):
		x0 = x - self.x_offset
		y0 = y - self.y_offset
		return x0, y0
