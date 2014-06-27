#!/usr/bin/python

from message import *

g_spurious = 0
g_cksm_err = 0

def send_msg(msg, serialdev):
	for c in msg:
		serialdev.write(c)

def read_test_msg():
	import time, math
	v = int(math.sin(time.time())*500 + 1500)
	w = int(math.sin(time.time()+1)*500 + 1500)
	time.sleep(0.01)
	return map(ord, pot_msg(1500, v, w, 1500, 1500, 1500))

def handle_commandline():
	import argparse
	parser = argparse.ArgumentParser(
		description="HK-T6A V2 configuration tool",
		epilog="Yuri Schaeffer - MIT License")
	parser.add_argument('-t', '--tty', default='/dev/ttyUSB0',
		help="Serial port. Default /dev/ttyUSB0")
	parser.add_argument('-b', '--baud', metavar='BAUDRATE',
		default='115200', type=int,
		help="Transmitter baudrate. Default 115200")
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-u', '--upload', metavar='FILE',
		help="Load config in to transmitter and exit. Make sure"
		" transmitter is switched on prior to running program.")
	group.add_argument('-d', '--download', metavar='FILE',
		help="Dump config from transmitter and exit. Make sure"
		" transmitter is switched on prior to running program.")
	return parser.parse_args()

import serial, sys, pickle, threading, Queue, signal
from gui import gui_loop

if __name__ == '__main__':
	error = 0
	payload = None
	dump_file = None
	args = handle_commandline()

	try:
		#~ serialdev = serial.Serial(
			#~ port=args.tty, baudrate=args.baud, parity=serial.PARITY_NONE,
			#~ stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

		if args.download:
			dump_file = open(args.download, "w")
			#~ send_msg(request_param_msg(), serialdev)
		elif args.upload:
			load_file = open(args.upload, "r")
			payload = pickle.load(load_file)
			load_file.close()
			#~ send_msg(load_param_msg(payload), serialdev)
	except serial.serialutil.SerialException as e:
		print "Error opening serial port:\n\t%s"%str(e)
		sys.exit(1)
	except (IOError, KeyError, EOFError) as e:
		print "Error opening file:\n\t%s"%str(e)
		#~ serialdev.close()
		sys.exit(1)

	interactive = not args.download and not args.upload
	if interactive:
		outqueue = Queue.Queue()
		inqueue  = Queue.Queue()
		gui_thread = threading.Thread(target=gui_loop,
			args=[outqueue, inqueue])
		gui_thread.start()

	try:
		while True:
			#~ msg = read_msg(serialdev)
			msg = read_test_msg()
			if msg[0] == OPC_PARAM_DUMP and args.download:
				pickle.dump(msg[1:-2], dump_file)
				break
			elif msg[0] == OPC_PARAM_DUMP and args.upload:
				if msg[1:-2] != payload:
					print "Uploading failed. Written settings differ"\
						" from what is read back."
					error = 1
				break
			if interactive:
				outqueue.put(msg)
				if not gui_thread.is_alive():
					break
			if interactive and not inqueue.empty():
				item = inqueue.get(block=False, timeout=0) #todo try/except
				item = map(ord, item)
				#~ send_msg(item, serialdev)
				if item[0] == OPC_PARAM_LOAD:
					item[0] = OPC_PARAM_DUMP
					outqueue.put(item)
				elif item[0] == OPC_PARAM_REQUEST:
					outqueue.put(map(ord, dump_param_msg([0]*(MSGMAP[OPC_PARAM_DUMP]-3))))

	except KeyboardInterrupt:
		pass
	except serial.serialutil.SerialException:
		print "error reading from serial port"
	if interactive:
		outqueue.put(None)
		gui_thread.join()
	#~ serialdev.close()
	if dump_file:
		dump_file.close()

	sys.exit(error)
