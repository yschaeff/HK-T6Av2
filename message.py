MSGSTART			= 0x55

OPC_PARAM_REQUEST	= 0xFA
OPC_POT				= 0xFC
OPC_PARAM_DUMP		= 0xFD
OPC_PARAM_LOAD		= 0xFF

MSGCHK = [OPC_POT, OPC_PARAM_DUMP, OPC_PARAM_LOAD] #messages with csum
MSGMAP = {OPC_PARAM_REQUEST:2, OPC_POT:17, OPC_PARAM_DUMP:68,
	OPC_PARAM_LOAD:68} #length excl MSGSTART, incl checksum

def request_param_msg():
	return map(chr, [MSGSTART, OPC_PARAM_DUMP, 0])

def load_param_msg(payload):
	s = sum(payload)
	return map(chr, [MSGSTART, OPC_PARAM_LOAD] + payload + [s>>8, s&0xFF])

def checksum(msg):
	if msg[0] not in MSGCHK:
		return True
	assert len(msg) > 3
	payload = msg[1:-2]
	checksum = (msg[-2]<<8)|msg[-1]
	return checksum == sum(payload)

def bigend(v):
	assert len(v) == 2
	return (v[0]<<8)|v[1]

def twos(v):
	if v>>7:
		return ((~v)+1)&0xF
	return v

def parse_pot(msg):
	m = {}
	m["opcode"] = msg[0]
	m["CH1"] = bigend(msg[1:3])
	m["CH2"] = bigend(msg[3:5])
	m["CH3"] = bigend(msg[5:7])
	m["CH4"] = bigend(msg[7:9])
	m["CH5"] = bigend(msg[9:11])
	m["CH6"] = bigend(msg[11:13])
	m["?"] = bigend(msg[13:15])
	m["checksum"] = bigend(msg[15:17])
	return m

def parse_request(msg):
	m = {}
	m["opcode"] = msg[0]
	m["?"] = msg[1]
	return m

def parse_param(msg):
	m = {}
	m["opcode"] = msg[0]
	m["tx model"] = (msg[1]>>4)&0xF
	m["craft type"] = msg[1]&0xF

	m["CH1 reverse"] = (msg[2]>>0)&0x1
	m["CH2 reverse"] = (msg[2]>>1)&0x1
	m["CH3 reverse"] = (msg[2]>>2)&0x1
	m["CH4 reverse"] = (msg[2]>>3)&0x1
	m["CH5 reverse"] = (msg[2]>>4)&0x1
	m["CH6 reverse"] = (msg[2]>>5)&0x1
	m["CH7 reverse"] = (msg[2]>>6)&0x1
	m["CH8 reverse"] = (msg[2]>>7)&0x1

	m["CH1 DR on"]  = msg[3]
	m["CH1 DR off"] = msg[4]
	m["CH2 DR on"]  = msg[5]
	m["CH2 DR off"] = msg[6]
	m["CH4 DR on"]  = msg[7]
	m["CH4 DR off"] = msg[8]

	m["CH1 swash AFR"] = msg[9]
	m["CH2 swash AFR"] = msg[10]
	m["CH6 swash AFR"] = msg[11]

	m["CH1 endpoint left"]  = msg[12]
	m["CH1 endpoint right"] = msg[13]
	m["CH2 endpoint left"]  = msg[14]
	m["CH2 endpoint right"] = msg[15]
	m["CH3 endpoint left"]  = msg[16]
	m["CH3 endpoint right"] = msg[17]
	m["CH4 endpoint left"]  = msg[18]
	m["CH4 endpoint right"] = msg[19]
	m["CH5 endpoint left"]  = msg[20]
	m["CH5 endpoint right"] = msg[21]
	m["CH6 endpoint left"]  = msg[22]
	m["CH6 endpoint right"] = msg[23]

	m["throttlecurve normal EP0"] = msg[24]
	m["throttlecurve normal EP1"] = msg[26]
	m["throttlecurve normal EP2"] = msg[28]
	m["throttlecurve normal EP3"] = msg[30]
	m["throttlecurve normal EP4"] = msg[32]
	m["throttlecurve ID EP0"] = msg[25]
	m["throttlecurve ID EP1"] = msg[27]
	m["throttlecurve ID EP2"] = msg[29]
	m["throttlecurve ID EP3"] = msg[31]
	m["throttlecurve ID EP4"] = msg[33]

	m["pitchcurve normal EP0"] = msg[34]
	m["pitchcurve normal EP1"] = msg[36]
	m["pitchcurve normal EP2"] = msg[38]
	m["pitchcurve normal EP3"] = msg[40]
	m["pitchcurve normal EP4"] = msg[42]
	m["pitchcurve ID EP0"] = msg[35]
	m["pitchcurve ID EP1"] = msg[37]
	m["pitchcurve ID EP2"] = msg[39]
	m["pitchcurve ID EP3"] = msg[41]
	m["pitchcurve ID EP4"] = msg[43]

	m["CH1 subtrim"] = twos(msg[44])
	m["CH2 subtrim"] = twos(msg[45])
	m["CH3 subtrim"] = twos(msg[46])
	m["CH4 subtrim"] = twos(msg[47])
	m["CH5 subtrim"] = twos(msg[48])
	m["CH6 subtrim"] = twos(msg[49])

	m["mix1 source"]      = msg[50]>>4
	m["mix1 destination"] = msg[50]&0xF
	m["mix1 uprate"]      = msg[51]
	m["mix1 downrate"]    = msg[52]
	m["mix1 switch"]      = msg[53]
	m["mix2 source"]      = msg[54]>>4
	m["mix2 destination"] = msg[54]&0xF
	m["mix2 uprate"]      = msg[55]
	m["mix2 downrate"]    = msg[56]
	m["mix2 switch"]      = msg[57]
	m["mix3 source"]      = msg[58]>>4
	m["mix3 destination"] = msg[58]&0xF
	m["mix3 uprate"]      = msg[59]
	m["mix3 downrate"]    = msg[60]
	m["mix3 switch"]      = msg[61]

	m["SWA"] = msg[62]
	m["SWB"] = msg[63]
	m["VRA"] = msg[64]
	m["VRB"] = msg[65]
	
	return m

def parse(msg):
	assert msg
	assert len(msg) > 0 and msg[0] in MSGMAP
	assert len(msg) == MSGMAP[msg[0]]

	parser = {
		OPC_PARAM_REQUEST:parse_request,
		OPC_POT:parse_pot,
		OPC_PARAM_DUMP:parse_param,
		OPC_PARAM_LOAD:parse_param
	}
	return parser[msg[0]](msg)
