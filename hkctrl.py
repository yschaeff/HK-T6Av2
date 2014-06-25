#!/bin/python

from message import *

g_spurious = 0
g_cksm_err = 0

def send_msg(msg, serialdev):
	for c in msg:
		serialdev.write(c)

def read_msg(serialdev):
	import select
	global g_spurious
	global g_cksm_err
	
	msglen = 0
	msg = None
	s = 0
	while True:
		try:
			c = ord(serialdev.read(1))
		except select.error: #normal syscal interrupt
			continue
		if s == 0:
			s = (c == MSGSTART)
		elif s == 1:
			if c in MSGMAP:
				s = 2
				msg = [c] + [0]*(MSGMAP[c]-1)
				msglen = 1
			else:
				s = 0
				g_spurious += 1
		else:
			msg[msglen] = c
			msglen += 1
			if msglen >= MSGMAP[msg[0]]:
				if checksum(msg):
					return msg
				g_cksm_err += 1
				print "checksum error"
				s = 0

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
		serialdev = serial.Serial(
			port=args.tty, baudrate=args.baud, parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
		
		if args.download:
			dump_file = open(args.download, "w")
			send_msg(request_param_msg(), serialdev)
		elif args.upload:
			load_file = open(args.upload, "r")
			payload = pickle.load(load_file)
			load_file.close()
			send_msg(load_param_msg(payload), serialdev)
	except serial.serialutil.SerialException as e:
		print "Error opening serial port:\n\t%s"%str(e)
		sys.exit(1)
	except IOError as e:
		print "Error opening file:\n\t%s"%str(e)
		serialdev.close()
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
			msg = read_msg(serialdev)
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
				#~ print "gui: %s"%str(map(ord, item))
				send_msg(item, serialdev)

	except KeyboardInterrupt:
		pass
	except serial.serialutil.SerialException:
		print "error reading from serial port"
	if interactive:
		outqueue.put(None)
		gui_thread.join()
	serialdev.close()
	if dump_file:
		dump_file.close()

	sys.exit(error)
