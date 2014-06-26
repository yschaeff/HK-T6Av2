from message import *
import Queue, curses, sys, signal, os

def remap(minfm, maxfm, minto, maxto, v):
	return (((v-minfm) * (maxto-minto)) / (maxfm-minfm)) + minto

def draw_pot(win, offy, offx, p):
	if not p: ##dummy data so we can paint the screen when no data
		p = {}
		for x in map(lambda x: "CH%d"%x, range(1,7)):
			p[x]=1500 
	for y in range(6):
		ch = "CH%d"%(y+1)
		win.addstr(y+offy, offx, ch)
		win.addstr(y+offy, offx+len(ch)+1, "%4d"%p[ch])
		h,w = win.getmaxyx()
		t,l = win.getbegyx()
		l += 9 + offx
		markl = remap(900, 2100, l, w, 1000)
		markc = remap(900, 2100, l, w, 1500)
		markr = remap(900, 2100, l, w, 2000)
		markv = remap(900, 2100, l, w, p[ch])
		#we expect value between 1000 and 2000
		for x in range(l, w):
			if x in [markl, markc, markr]:
				if x == markv:
					c = "I"
				else:
					c = " "
				win.addstr(y+offy, x, c, curses.color_pair(1)|curses.A_BOLD)
			else:
				if x == markv:
					c = "I"
				else:
					c = " "
				win.addstr(y+offy, x, c, curses.color_pair(2)|curses.A_BOLD)

def draw_param(win, offy, offx, p):
	if not p: return
	for i in range(6):
		ch = "CH%d subtrim"%(i+1)
		win.addstr(offy+i, offx, "%s: %d"%(ch, p[ch]),
			curses.color_pair(0))

def draw_legenda(win, offy, offx):
	win.addstr(offy+0, offx, "d: download configuration to PC",
		curses.color_pair(3)|curses.A_BOLD)
	win.addstr(offy+1, offx, "u: upload configuration to TX",
		curses.color_pair(3)|curses.A_BOLD)
	win.addstr(offy+2, offx, "q: quit",
		curses.color_pair(3)|curses.A_BOLD)

def gui(stdscr, inqueue, outqueue):
	#init
	curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
	curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)

	last_pot = None
	last_param = None
	last_param_msg = None
	
	stdscr.nodelay(1)
	while True:
		draw_legenda(stdscr, 0, 0)
		draw_pot(stdscr, 4, 0, last_pot)
		draw_param(stdscr, 11, 0, last_param)
		stdscr.refresh()
		#user input
		c = stdscr.getch()
		if c != curses.ERR:
			if c == ord('q'):
				os.kill(os.getpid(), signal.SIGINT)
				break  # Exit the while()
			elif c == ord('d'):
				outqueue.put(request_param_msg())
			elif c == ord('u') and last_param_msg:
				outqueue.put(load_param_msg(last_param_msg[1:-2]))

		try:
			m = inqueue.get(timeout=1)
		except Queue.Empty:
			continue
		if not m:
			break
		p = parse(m)
		if p["opcode"] == OPC_POT:
			last_pot = p
		elif p["opcode"] == OPC_PARAM_DUMP:
			last_param = p
			last_param_msg = m
		

def gui_loop(inqueue, outqueue):
	curses.wrapper(gui, inqueue, outqueue)
	
