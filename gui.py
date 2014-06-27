from message import *
import Queue, curses, sys, signal, os

def remap(minfm, maxfm, minto, maxto, v):
	return (((v-minfm) * (maxto-minto)) / (maxfm-minfm)) + minto

def draw_pot(win, offy, offx, msg, channels):
	if not msg: return
	for channel in channels:
		win.addstr(channel.pos[0]+offy, offx, channel.label)
		win.addstr(channel.pos[0]+offy, offx+len(channel.label)+1, channel.get(msg))
		h,w = win.getmaxyx()
		t,l = win.getbegyx()
		l += 9 + offx
		markl = remap(900, 2100, l, w, 1000)
		markc = remap(900, 2100, l, w, 1500)
		markr = remap(900, 2100, l, w, 2000)
		markv = remap(900, 2100, l, w, channel.read(msg))
		#we expect value between 1000 and 2000
		c = " "
		for x in range(l, w):
			if x in [markl, markc, markr]: #markers
				if x == markv:
					style = curses.color_pair(3)|curses.A_BOLD
				else:
					style = curses.color_pair(1)|curses.A_BOLD
				win.addstr(channel.pos[0]+offy, x, c, style)
			else:
				if x == markv:
					style = curses.color_pair(3)|curses.A_BOLD
				else:
					style = curses.color_pair(2)|curses.A_BOLD
				win.addstr(channel.pos[0]+offy, x, c, style)

def autotrim(param_msg, pot_msg, trims, channels):
	"""Trims and channels need to be sorted the same"""
	for tr, ch in zip(trims, channels):
		d = 1500 - ch.read(pot_msg)
		t = tr.read(param_msg)
		v = t - d
		if v < -128: v = -128
		if v > 127: v = 127
		tr.write(param_msg, v)


def draw_param(win, offy, offx, msg, selected, datas):
	if not msg: return

	for i, data in enumerate(datas):
		v = data.get(msg)
		if i == selected:
			style = curses.color_pair(2)
			form = "%s: <%s>"
		else:
			if data.changed:
				style = curses.color_pair(1)
			else:
				style = curses.color_pair(3)
			form = "%s:  %s"
		y = offy + data.pos[0]
		x = offx + data.pos[1]
		win.addstr(y, x, form%(data.label, v), style)

def draw_legenda(win, offy, offx):
	win.addstr(offy+0, offx, "d: download configuration to PC",
		curses.color_pair(3)|curses.A_BOLD)
	win.addstr(offy+1, offx, "u: upload configuration to TX",
		curses.color_pair(3)|curses.A_BOLD)
	win.addstr(offy+2, offx, "a: Auto trim, keep sticks centered",
		curses.color_pair(3)|curses.A_BOLD)
	win.addstr(offy+3, offx, "q: quit",
		curses.color_pair(3)|curses.A_BOLD)

def gui(stdscr, inqueue, outqueue):
	#init
	curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

	index = 0

	last_pot_msg = None
	last_param_msg = None

	stdscr.nodelay(1)
	outqueue.put(request_param_msg())
	while True:
		stdscr.clear()
		draw_legenda(stdscr, 0, 0)
		draw_pot(stdscr, 4, 0, last_pot_msg, channels)
		draw_param(stdscr, 12, 0, last_param_msg, index, datas)
		stdscr.refresh()
		#user input
		c = stdscr.getch()
		if c != curses.ERR:
			if c == ord('q'):
				os.kill(os.getpid(), signal.SIGINT)
				break  # Exit the while()
			elif c == ord('d'):
				outqueue.put(request_param_msg())
				for d in datas:
					d.changed = False
			elif c == ord('u') and last_param_msg:
				outqueue.put(load_param_msg(last_param_msg[1:-2]))
				for d in datas:
					d.changed = False
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

		try:
			m = inqueue.get(timeout=1)
		except Queue.Empty:
			continue
		if not m:
			break
		if m[0] == OPC_POT:
			last_pot_msg = m
		elif m[0] == OPC_PARAM_DUMP:
			last_param_msg = m

def gui_loop(inqueue, outqueue):
	curses.wrapper(gui, inqueue, outqueue)
