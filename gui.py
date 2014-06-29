from message import *
import Queue, curses, sys, signal, os

CP_LABEL  = 0
CP_CHANGE = 1
CP_SELECT = 2
CP_FIELD  = 3

def remap(minfm, maxfm, minto, maxto, v):
	return (((v-minfm) * (maxto-minto)) / (maxfm-minfm)) + minto

def draw_pot(win, offy, offx, msg, channels):
	if not msg: return
	for i, channel in enumerate(channels):
		win.addstr(offy+i, offx, channel.label)
		win.addstr(offy+i, offx+len(channel.label)+1, str(channel.read(msg)))
		h,w = win.getmaxyx()
		t,l = win.getbegyx()
		l += 9 + offx
		markl = remap(970, 2030, l, w, 1000)
		markc = remap(970, 2030, l, w, 1500)
		markr = remap(970, 2030, l, w, 2000)
		markv = remap(970, 2030, l, w, channel.read(msg))
		#we expect value between 1000 and 2000
		c = " "
		for x in range(l, w):
			if x in [markl, markc, markr]: #markers
				if x == markv:
					style = CP_FIELD
				else:
					style = CP_CHANGE
				win.addstr(offy+i, x, c, curses.color_pair(style))
			else:
				if x == markv:
					style = CP_FIELD
				else:
					style = CP_SELECT
				win.addstr(offy+i, x, c, curses.color_pair(style))

def autotrim(param_msg, pot_msg, trims, channels):
	"""Trims and channels need to be sorted the same"""
	for tr, ch in zip(trims, channels):
		d = 1500 - ch.read(pot_msg)
		t = tr.read(param_msg)
		v = t + d
		if v < -128: v = -128
		if v > 127: v = 127
		tr.write(param_msg, v)

def draw_column(win, y, x, msg, selected, title, fields, form):
	
	win.addstr(y, x, title, curses.color_pair(CP_LABEL)|curses.A_BOLD)
	for i, d in enumerate(fields):
		if d == selected:
			style = curses.color_pair(CP_SELECT)|curses.A_BOLD
		elif d.changed:
			style = curses.color_pair(CP_CHANGE)|curses.A_BOLD
		else:
			style = curses.color_pair(CP_FIELD)|curses.A_BOLD
		v = d.get(msg)
		win.addstr(y+i+1, x, form%v, style)


def draw_param(win, offy, offx, msg, selected, datas):
	if not msg: return

	#channels
	for i in range(6):
		win.addstr(offy+i+1, offx+0, "CH%d:"%(i+1), curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy, offx+5,  msg, selected, "Left", endleft, "%4s")
	draw_column(win, offy, offx+10, msg, selected, "Trim", trims, "%4s")
	draw_column(win, offy, offx+15, msg, selected, "Rght", endright, "%4s")
	draw_column(win, offy, offx+20, msg, selected, "Rvrs", reverse, "%4s")

	#Curves
	win.addstr(offy, offx+30, "Throttle      Pitch", curses.color_pair(0)|curses.A_BOLD)
	for i in range(5):
		win.addstr(offy+i+2, offx+26, "P%d:"%(i), curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+1, offx+30, msg, selected, "Norm", thr_curve_norm, "%4s")
	draw_column(win, offy+1, offx+35, msg, selected, "Idle", thr_curve_idle, "%4s")
	draw_column(win, offy+1, offx+40, msg, selected, "Norm", ptch_curve_norm, "%4s")
	draw_column(win, offy+1, offx+45, msg, selected, "Idle", ptch_curve_idle, "%4s")

	#Mixing
	win.addstr(offy, offx+57, "Channel Mixing", curses.color_pair(0)|curses.A_BOLD)
	for i,ii in enumerate(["Srce", "Dest", "Uprt", "Dwrt", "Swch"]):
		win.addstr(offy+i+2, offx+51, ii+":", curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+1, offx+57, msg, selected, "Mix1", mix1, "%4s")
	draw_column(win, offy+1, offx+62, msg, selected, "Mix2", mix2, "%4s")
	draw_column(win, offy+1, offx+67, msg, selected, "Mix3", mix3, "%4s")

	#dual rate
	win.addstr(offy+8, offx+5, "Dual Rate", curses.color_pair(0)|curses.A_BOLD)
	for i, ii in enumerate([1,2,4]):
		win.addstr(offy+i+10, offx+0, "CH%d:"%(ii), curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+9, offx+5, msg, selected, "Off", dr_off, "%4s")
	draw_column(win, offy+9, offx+10, msg, selected, "On", dr_on, "%4s")

	#Swash AFR
	for i, ii in enumerate([1,2,6]):
		win.addstr(offy+i+10, offx+16, "CH%d:"%(ii), curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+9, offx+21, msg, selected, "Swsh", swash, "%4s")

	#switch functions
	for i, ii in enumerate(["SWA", "SWB", "VRA", "VRB"]):
		win.addstr(offy+i+9, offx+27, "%s:"%ii, curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+8, offx+32, msg, selected, "Functiom", [swa, swb, vra, vrb], "%9s")

	#mode,type
	for i, ii in enumerate(["TX", "Craft"]):
		win.addstr(offy+i+11, offx+43, "%5s:"%ii, curses.color_pair(0)|curses.A_BOLD)
	draw_column(win, offy+10, offx+50, msg, selected, "Mode", [tx_mode, craft_type], "%7s")

def draw_legenda(win, offy, offx):
	win.addstr(offy+0, offx, "d: download, u: upload, a: auto-trim, q: quit",
		curses.color_pair(0)|curses.A_BOLD)

def draw_help(win, offy, offx, index, datas):
	win.addstr(offy+0, offx, datas[index].label + ": " + datas[index].helpstr,
		curses.color_pair(0))
	win.clrtoeol()
	

def gui(stdscr, inqueue, outqueue):
	#init
	curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

	index = 0
	last_pot_msg = None
	last_param_msg = None
	repaint = True

	stdscr.nodelay(1)
	#TODO on resize, refresh
	outqueue.put(request_param_msg())
	while True:
		draw_legenda(stdscr, 0, 0)
		draw_param(stdscr, 10, 0, last_param_msg, datas[index], datas)
		draw_help(stdscr, 1, 0, index, datas)
		draw_pot(stdscr, 3, 0, last_pot_msg, channels)
		repaint = False
		stdscr.refresh()
		
		c = stdscr.getch()
		if c != curses.ERR:
			if c == ord('q'):
				os.kill(os.getpid(), signal.SIGINT)
				break  # Exit the while()
			elif c == ord('d'):
				outqueue.put(request_param_msg())
			elif c == ord('u') and last_param_msg:
				outqueue.put(load_param_msg(last_param_msg[1:-2]))
			elif c == ord('a') and last_param_msg:
				autotrim(last_param_msg, last_pot_msg, trims, channels)
			elif c == curses.KEY_DOWN:
				index = (index+1)%len(datas)
			elif c == curses.KEY_UP:
				index = (index-1)%len(datas)
			elif c == curses.KEY_LEFT:
				datas[index].dec(last_param_msg)
				datas[index].changed = True
			elif c == curses.KEY_RIGHT:
				datas[index].inc(last_param_msg)
				datas[index].changed = True

		#user input
		try:
			m = inqueue.get(timeout=0.05)
		except Queue.Empty:
			continue
		if not m:
			break
		if m[0] == OPC_POT:
			last_pot_msg = m
		elif m[0] == OPC_PARAM_DUMP:
			last_param_msg = m
			for d in datas:
				d.changed = False

def gui_loop(inqueue, outqueue):
	curses.wrapper(gui, inqueue, outqueue)
