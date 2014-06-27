MSGSTART			= 0x55

OPC_PARAM_REQUEST	= 0xFA
OPC_POT				= 0xFC
OPC_PARAM_DUMP		= 0xFD
OPC_PARAM_LOAD		= 0xFF

MSGCHK = [OPC_POT, OPC_PARAM_DUMP, OPC_PARAM_LOAD] #messages with csum
MSGMAP = {OPC_PARAM_REQUEST:2, OPC_POT:17, OPC_PARAM_DUMP:68,
	OPC_PARAM_LOAD:68} #length excl MSGSTART, incl checksum

def request_param_msg():
	return map(chr, [OPC_PARAM_REQUEST, 0])

def load_param_msg(payload):
	s = sum(payload)
	return map(chr, [OPC_PARAM_LOAD] + payload + [s>>8, s&0xFF])

def dump_param_msg(payload):
	s = sum(payload)
	return map(chr, [OPC_PARAM_DUMP] + payload + [s>>8, s&0xFF])

def pot_msg(c1,c2,c3,c4,c5,c6):
	payload = endbig(c1) + endbig(c2) + endbig(c3) + endbig(c4) +\
		endbig(c5) + endbig(c6) + endbig(0)
	s = sum(payload)
	return map(chr, [OPC_POT] + payload + [s>>8, s&0xFF])

def checksum(msg):
	if msg[0] not in MSGCHK:
		return True
	assert len(msg) > 3
	payload = msg[1:-2]
	checksum = (msg[-2]<<8)|msg[-1]
	return checksum == sum(payload)

def endbig(v):
	return [v>>8, v&0xFF]

UINT16 = 0 #enum
UINT8  = 1
UINT4H = 2
UINT4L = 3
SINT8  = 4
BIT1   = 5
BIT2   = 6
BIT3   = 7
BIT4   = 8
BIT5   = 9
BIT6   = 10
BIT7   = 11
BIT8   = 12

def uint16(descr, msg):
	return (msg[descr.offset]<<8)|msg[descr.offset+1]
def uint8(descr, msg):
	return msg[descr.offset]
def uint4h(descr, msg):
	return msg[descr.offset]>>4
def uint4l(descr, msg):
	return msg[descr.offset]&0xF
def sint8(descr, msg):
	if msg[descr.offset]>>7:
		return -(((~msg[descr.offset])+1)&0xFF)
	return msg[descr.offset]
def bit1(descr, msg):
	return (msg[descr.offset]>>0)&0x1
def bit2(descr, msg):
	return (msg[descr.offset]>>1)&0x1
def bit3(descr, msg):
	return (msg[descr.offset]>>2)&0x1
def bit4(descr, msg):
	return (msg[descr.offset]>>3)&0x1
def bit5(descr, msg):
	return (msg[descr.offset]>>4)&0x1
def bit6(descr, msg):
	return (msg[descr.offset]>>5)&0x1
def bit7(descr, msg):
	return (msg[descr.offset]>>6)&0x1
def bit8(descr, msg):
	return (msg[descr.offset]>>7)&0x1

def uint16_store(descr, msg, v):
	msg[descr.offset] = v>>8
	msg[descr.offset+1] = v&0xFF
def uint8_store(descr, msg, v):
	msg[descr.offset] = v
def uint4h_store(descr, msg, v):
	msg[descr.offset] = (v<<4)|(msg[descr.offset]&0xF)
def uint4l_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xF0)|(v&0xF)
def sint8_store(descr, msg, v):
	if v >= 0:
		msg[descr.offset] = v&0x7F
	else:
		msg[descr.offset] = (v&0xFF)|0x80
def bit1_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xFE)|(v&0x1)<<0
def bit2_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xFD)|(v&0x1)<<1
def bit3_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xFB)|(v&0x1)<<2
def bit4_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xF7)|(v&0x1)<<3
def bit5_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xEF)|(v&0x1)<<4
def bit6_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xDF)|(v&0x1)<<5
def bit7_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0xBF)|(v&0x1)<<6
def bit8_store(descr, msg, v):
	msg[descr.offset] = (msg[descr.offset]&0x7F)|(v&0x1)<<7

proc = {UINT16:(uint16, uint16_store), UINT8:(uint8, uint8_store),
	UINT4H:(uint4h, uint4h_store), UINT4L:(uint4l, uint4l_store),
	SINT8:(sint8, sint8_store), BIT1:(bit1, bit1_store),
	BIT2:(bit2, bit2_store), BIT3:(bit3, bit3_store),
	BIT4:(bit4, bit4_store), BIT5:(bit5, bit5_store),
	BIT6:(bit6, bit6_store), BIT7:(bit7, bit7_store),
	BIT8:(bit8, bit8_store)}


class Data:
	def __init__(self, opc, parser, offset, drange_raw, drange_show, label, pos=None):
		self.opc = opc
		self.parser = parser
		self.offset = offset
		self.drange_raw = drange_raw
		self.drange_show = drange_show
		if drange_show:
			assert len(drange_show) == len(drange_raw)
		self.label = label
		self.pos = pos
		self.changed = False

	def read(self, msg):
		assert self.opc == msg[0]
		return proc[self.parser][0](self, msg)
	def write(self, msg, v):
		assert self.opc == msg[0]
		return proc[self.parser][1](self, msg, v)

	def dec(self, msg):
		if not msg: return
		raw = self.read(msg)
		if not raw in self.drange_raw:
			self.write(msg, self.drange_raw[-1])
			return
		i = self.drange_raw.index(raw)
		if i == 0: return
		self.write(msg, self.drange_raw[i-1])

	def inc(self, msg):
		if not msg: return
		raw = self.read(msg)
		if not raw in self.drange_raw:
			self.write(msg, self.drange_raw[0])
			return
		i = self.drange_raw.index(raw)
		if i == len(self.drange_raw)-1: return
		self.write(msg, self.drange_raw[i+1])

	def get(self, msg):
		"""Return current value in presentation format"""
		raw = self.read(msg)
		if not raw in self.drange_raw:
			return "%3d?"%raw
		if not self.drange_show:
			return "%4d"%(raw)
		i = self.drange_raw.index(raw)
		return self.drange_show[i]

## TODO storing position in gui here is layer violation

# Accessors
ch1 = Data(OPC_POT, UINT16,  1, range(1000, 2001), None, "CH1", (1,0))
ch2 = Data(OPC_POT, UINT16,  3, range(1000, 2001), None, "CH2", (2,0))
ch3 = Data(OPC_POT, UINT16,  5, range(1000, 2001), None, "CH3", (3,0))
ch4 = Data(OPC_POT, UINT16,  7, range(1000, 2001), None, "CH4", (4,0))
ch5 = Data(OPC_POT, UINT16,  9, range(1000, 2001), None, "CH5", (5,0))
ch6 = Data(OPC_POT, UINT16, 11, range(1000, 2001), None, "CH6", (6,0))

ch1_subtrim = Data(OPC_PARAM_DUMP, SINT8, 44, range(-128, 128), None, "CH1 subtrim", (0,0))
ch2_subtrim = Data(OPC_PARAM_DUMP, SINT8, 45, range(-128, 128), None, "CH2 subtrim", (1,0))
ch3_subtrim = Data(OPC_PARAM_DUMP, SINT8, 46, range(-128, 128), None, "CH3 subtrim", (2,0))
ch4_subtrim = Data(OPC_PARAM_DUMP, SINT8, 47, range(-128, 128), None, "CH4 subtrim", (3,0))
ch5_subtrim = Data(OPC_PARAM_DUMP, SINT8, 48, range(-128, 128), None, "CH5 subtrim", (4,0))
ch6_subtrim = Data(OPC_PARAM_DUMP, SINT8, 49, range(-128, 128), None, "CH6 subtrim", (5,0))

ch1_end_left = Data(OPC_PARAM_DUMP, UINT8, 11, range(128), None, "CH1 End Left", (0,20))
ch2_end_left = Data(OPC_PARAM_DUMP, UINT8, 13, range(128), None, "CH2 End Left", (1,20))
ch3_end_left = Data(OPC_PARAM_DUMP, UINT8, 15, range(128), None, "CH3 End Left", (2,20))
ch4_end_left = Data(OPC_PARAM_DUMP, UINT8, 17, range(128), None, "CH4 End Left", (3,20))
ch5_end_left = Data(OPC_PARAM_DUMP, UINT8, 19, range(128), None, "CH5 End Left", (4,20))
ch6_end_left = Data(OPC_PARAM_DUMP, UINT8, 21, range(128), None, "CH6 End Left", (5,20))

ch1_end_right = Data(OPC_PARAM_DUMP, UINT8, 12, range(128), None, "CH1 End Right", (0,41))
ch2_end_right = Data(OPC_PARAM_DUMP, UINT8, 14, range(128), None, "CH2 End Right", (1,41))
ch3_end_right = Data(OPC_PARAM_DUMP, UINT8, 16, range(128), None, "CH3 End Right", (2,41))
ch4_end_right = Data(OPC_PARAM_DUMP, UINT8, 18, range(128), None, "CH4 End Right", (3,41))
ch5_end_right = Data(OPC_PARAM_DUMP, UINT8, 20, range(128), None, "CH5 End Right", (4,41))
ch6_end_right = Data(OPC_PARAM_DUMP, UINT8, 22, range(128), None, "CH6 End Right", (5,41))

tx_mode = Data(OPC_PARAM_DUMP, UINT4H, 1, range(4), ["model1", "model2", "model3", "model4"], "TX mode", (7,0))
craft_type = Data(OPC_PARAM_DUMP, UINT4L, 1, range(4), ["acro", "heli120", "heli90", "heli140"], "Craft Type", (8,0))

ch1_reverse = Data(OPC_PARAM_DUMP, BIT1, 2, range(2), ["off", "on"], "CH1 Reverse", (0,64))
ch2_reverse = Data(OPC_PARAM_DUMP, BIT2, 2, range(2), ["off", "on"], "CH2 Reverse", (1,64))
ch3_reverse = Data(OPC_PARAM_DUMP, BIT3, 2, range(2), ["off", "on"], "CH3 Reverse", (2,64))
ch4_reverse = Data(OPC_PARAM_DUMP, BIT4, 2, range(2), ["off", "on"], "CH4 Reverse", (3,64))
ch5_reverse = Data(OPC_PARAM_DUMP, BIT5, 2, range(2), ["off", "on"], "CH5 Reverse", (4,64))
ch6_reverse = Data(OPC_PARAM_DUMP, BIT6, 2, range(2), ["off", "on"], "CH6 Reverse", (5,64))

# Accessor collections
channels = [ch1, ch2, ch3, ch4, ch5, ch6]
trims = [ch1_subtrim, ch2_subtrim, ch3_subtrim, ch4_subtrim, ch5_subtrim, ch6_subtrim]
endpoints = [ch1_end_left, ch2_end_left, ch3_end_left, ch4_end_left,
	ch5_end_left, ch6_end_left, ch1_end_right, ch2_end_right,
	ch3_end_right, ch4_end_right, ch5_end_right, ch6_end_right]
reverse = [ch1_reverse, ch2_reverse, ch3_reverse, ch4_reverse, ch5_reverse, ch6_reverse]
datas = trims+endpoints+[tx_mode, craft_type]+reverse
