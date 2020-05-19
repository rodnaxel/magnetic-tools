import math
from operator import itemgetter


class HeelingError:
	""" The algorithm used to correction heeling error magnetic compass"""
	
	def __init__(self):
		pass
	
	def correct(self):
		pass


class HardIron:
	""" This algorithm used to compute and compensate hard iron """
	
	def __init__(self, fields: list):
		self._fields = fields
		self._compute()
	
	def __call__(self, x, y):
		return self.correct(x, y)
	
	def _compute(self):
		""" Compute hard iron compensate ratio Xoffset, Yoffset"""
		# <1> Find Xmax, Xmin, Ymax, Ymin <\>
		x_max = max(self._fields)[0]
		x_min = min(self._fields)[0]
		y_max = max(self._fields, key=itemgetter(1))[1]
		y_min = min(self._fields, key=itemgetter(1))[1]
		
		# <2> Compute hard iron offset <\>
		self.x_offset = (x_max + x_min) * 0.5
		self.y_offset = (y_max + y_min) * 0.5
	
	def correct(self, x, y):
		return x - self.x_offset, y - self.y_offset


class SoftIron:
	""" This algorithm used to compute adn compensate soft iron"""
	
	def __init__(self, fields: list):
		self._fields = fields
		self.A = 0
		self.B = 0
		self.C = 0
		self.D = 0
		self.clockwise = None
		
		self._compute()
	
	def _compute(self):
		# <1> Calculate full magnetic vector H for each pair X, Y and find max H <\>
		h_max = max(
			self._fields,
			key=lambda item: math.sqrt(item[0] * item[0] + item[1] * item[1])
		)
		
		# <2> Caclulate rotate side and angle phi <\>
		if (h_max[1] * h_max[0]) > 0:
			self.phi = phi = math.atan(h_max[1] / h_max[0])
			self.clockwise = clockwise = True
		else:
			self.phi = phi = -math.atan(h_max[1] / h_max[0])
			self.clockwise = clockwise = False
		self.phi_degree = phi * (180.0 / math.pi)
		
		# <3> Rotate each pair X, Y on theta angle <\>
		def rotate(x, y, angle, clockwise):
			if clockwise:
				x_rot = x * math.cos(angle) + y * math.sin(angle)
				y_rot = - x * math.sin(angle) + y * math.cos(angle)
			else:
				x_rot = x * math.cos(angle) - y * math.sin(angle)
				y_rot = x * math.sin(angle) + y * math.cos(angle)
			return x_rot, y_rot
		
		ds_rotate = [rotate(x, y, phi, clockwise) for (x, y) in self._fields]
		
		# <4> Caclulate a, b, k  magnetic ellipsoid <\>
		ds_rotate_module = [(abs(x), abs(y)) for (x, y) in ds_rotate]
		a = max(ds_rotate_module, key=itemgetter(0))[0]
		b = max(ds_rotate_module, key=itemgetter(1))[1]
		self.k = k = b / a
		
		# <5> Calculate A,B,C,D
		self.A = k * pow(math.cos(phi), 2) + pow(math.sin(phi), 2)
		self.B = (k * math.sin(2 * phi) - math.sin(2 * phi)) * 0.5
		self.C = (math.sin(2 * phi) - k * math.sin(2 * phi)) * 0.5
		self.D = k * pow(math.sin(phi), 2) + pow(math.cos(phi), 2)
	
	def correct(self, x, y):
		if self.clockwise:
			xc, yc = (x * self.A + y * self.B, -x * self.C + y * self.D)
		else:
			xc, yc = (x * self.A - y * self.B, x * self.C + y * self.D)
		return xc, yc


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
