from message import *
import Queue, curses, signal, os

# Cursus Color Pairs
CP_LABEL  = 0
CP_CHANGE = 1
CP_SELECT = 2
CP_FIELD  = 3

def remap(minfm, maxfm, minto, maxto, v):
	"""Map value v in 'from' range to 'to' range"""
	return (((v-minfm) * (maxto-minto)) / (maxfm-minfm)) + minto

def draw_pot(win, offy, offx, msg, channels):
	"""Draw positions of the potmeters"""
	for i, channel in enumerate(channels):
		addstr(win, offy+i, offx, channel.label)
		addstr(win, offy+i, offx+len(channel.label)+1,
			str(channel.read(msg)))
		h,w = win.getmaxyx()
		t,l = win.getbegyx()
		l += 9 + offx
		# MArker x-offsets
		markl = remap(970, 2030, l, w, 1000)
		markc = remap(970, 2030, l, w, 1500)
		markr = remap(970, 2030, l, w, 2000)
		markv = remap(970, 2030, l, w, channel.read(msg))
		#we expect value between 1000 and 2000
		for x in range(l, w):
			if x in [markl, markc, markr]: #markers
				if x == markv:
					style = CP_FIELD
				else:
					style = CP_CHANGE
				addstr(win, offy+i, x, " ", curses.color_pair(style))
			else:
				if x == markv:
					style = CP_FIELD
				else:
					style = CP_SELECT
				addstr(win, offy+i, x, " ", curses.color_pair(style))

def autotrim(param_msg, pot_msg, trims, channels, reverse):
	"""Trims and channels need to be sorted the same"""
	for tr, ch, rev in zip(trims, channels, reverse)[:4]:
		if not rev.read(param_msg):
			v = tr.read(param_msg) + (1500 - ch.read(pot_msg))
		else:
			v = tr.read(param_msg) - (1500 - ch.read(pot_msg))
		tr.write(param_msg, min(max(v, -128), 127))
		tr.changed = True

def addstr(win, y, x, text, style=None, wrapping_ok=False):
	"""Wrapper to make addstr safe"""
	h,w = win.getmaxyx()
	if x>=w or y>=h-1: return # -1 because of the trailing newline...
	if not wrapping_ok and x+len(text)>w:
		text = text[:w - x - 1]+">" #prevent wrapping
	if len(text)/w >= h-y-1: return
	if (style):
		win.addstr(y%h, x%w, text, style)
	else:
		win.addstr(y%h, x%w, text)

def draw_column(win, y, x, msg, selected, title, fields, form):
	"""Draw a column of similar data. Handle caption, selected
		fields and changed data"""
	addstr(win, y, x, title, curses.color_pair(CP_LABEL)|curses.A_BOLD)
	for i, d in enumerate(fields):
		if d == selected:
			style = curses.color_pair(CP_SELECT)|curses.A_BOLD
		elif d.changed:
			style = curses.color_pair(CP_CHANGE)|curses.A_BOLD
		else:
			style = curses.color_pair(CP_FIELD)|curses.A_BOLD
		addstr(win, y+i+1, x, form%d.get(msg), style)


def draw_param(win, offy, offx, msg, selected, datas):
	style = curses.color_pair(CP_LABEL)|curses.A_BOLD
	#channels
	for i in range(6):
		addstr(win, offy+i+1, offx+0, "CH%d:"%(i+1), style)
	draw_column(win, offy, offx+5,  msg, selected, "Left", endleft, "%4s")
	draw_column(win, offy, offx+10, msg, selected, "Trim", trims, "%4s")
	draw_column(win, offy, offx+15, msg, selected, "Rght", endright, "%4s")
	draw_column(win, offy, offx+20, msg, selected, "Rvrs", reverse, "%4s")

	#Curves
	addstr(win, offy, offx+30, "Throttle      Pitch", style)
	for i in range(5):
		addstr(win, offy+i+2, offx+26, "P%d:"%(i), style)
	draw_column(win, offy+1, offx+30, msg, selected, "Norm", thr_curve_norm, "%4s")
	draw_column(win, offy+1, offx+35, msg, selected, "Idle", thr_curve_idle, "%4s")
	draw_column(win, offy+1, offx+40, msg, selected, "Norm", ptch_curve_norm, "%4s")
	draw_column(win, offy+1, offx+45, msg, selected, "Idle", ptch_curve_idle, "%4s")

	#Mixing
	addstr(win, offy, offx+57, "Channel Mixing", style)
	for i,ii in enumerate(["Srce", "Dest", "Uprt", "Dwrt", "Swch"]):
		addstr(win, offy+i+2, offx+51, ii+":", style)
	draw_column(win, offy+1, offx+57, msg, selected, "Mix1", mix1, "%4s")
	draw_column(win, offy+1, offx+62, msg, selected, "Mix2", mix2, "%4s")
	draw_column(win, offy+1, offx+67, msg, selected, "Mix3", mix3, "%4s")

	#dual rate
	addstr(win, offy+8, offx+5, "Dual Rate", style)
	for i, ii in enumerate([1,2,4]):
		addstr(win, offy+i+10, offx+0, "CH%d:"%(ii), style)
	draw_column(win, offy+9, offx+5, msg, selected, "Off", dr_off, "%4s")
	draw_column(win, offy+9, offx+10, msg, selected, "On", dr_on, "%4s")

	#Swash AFR
	for i, ii in enumerate([1,2,6]):
		addstr(win, offy+i+10, offx+16, "CH%d:"%(ii), style)
	draw_column(win, offy+9, offx+21, msg, selected, "Swsh", swash, "%4s")

	#switch functions
	for i, ii in enumerate(["SWA", "SWB", "VRA", "VRB"]):
		addstr(win, offy+i+9, offx+27, "%s:"%ii, style)
	draw_column(win, offy+8, offx+32, msg, selected, "Functiom", [swa, swb, vra, vrb], "%9s")

	#mode,type
	for i, ii in enumerate(["TX", "Craft"]):
		addstr(win, offy+i+11, offx+43, "%5s:"%ii, style)
	draw_column(win, offy+10, offx+50, msg, selected, "Mode", [tx_mode, craft_type], "%7s")

def draw_legenda(win, offy, offx):
	addstr(win, offy, offx,
		"d: download, u: upload, a: auto-trim, q: quit, arrow keys (hjkl), tab, +, -, space",
		curses.color_pair(0)|curses.A_BOLD)

def draw_help(win, offy, offx, index, datas):
	h,w = win.getmaxyx()
	if offy+1 >= h: return
	win.move(offy,   offx); win.clrtoeol()
	win.move(offy+1, offx); win.clrtoeol()
	addstr(win, offy+0, offx,
		datas[index].label + ": " + datas[index].helpstr,
		curses.color_pair(0), wrapping_ok=True)

def prev_column(settings, index, tabstops):
	## find out position
	idxs = [settings.index(t) for t in tabstops]
	right = index % len(settings)
	while right not in idxs:
		right -= 1
	offset = index - right
	left = (right - 1) % len(settings)
	while left not in idxs:
		left = (left - 1) % len(settings)
	target = (left + offset) % len(settings)
	if target >= right:
	    target = right - 1
	return target

def next_column(settings, index, tabstops):
	## find out position
	idxs = [settings.index(t) for t in tabstops]
	left = index % len(settings)
	while left not in idxs:
		left -= 1
	offset = index - left
	right = (index + 1) % len(settings)
	while right not in idxs:
		right = (right + 1) % len(settings)
	target = (right + offset) % len(settings)
	return target

def gui(stdscr, inqueue, outqueue):
	#define colors
	curses.init_pair(CP_CHANGE, curses.COLOR_BLACK, curses.COLOR_RED)
	curses.init_pair(CP_SELECT, curses.COLOR_BLACK, curses.COLOR_WHITE)
	curses.init_pair(CP_FIELD,  curses.COLOR_WHITE, curses.COLOR_BLUE)

	#order in which to select fields
	settings = endleft + trims + endright + reverse + thr_curve_norm + \
		thr_curve_idle + ptch_curve_norm + ptch_curve_idle + mix1 + \
		mix2 + mix3 + dr_off + dr_on + swash + switches + mode
	tabstops = [ch1_end_left, ch1_subtrim, ch1_end_right, ch1_reverse,
		thrcrv_norm_0, thrcrv_idle_0, ptchcrv_norm_0, ptchcrv_idle_0,
		mix1_src, mix2_src, mix3_src, ch1_dr_on, ch1_dr_off, ch1_swash,
		swa, tx_mode]

	index = 0 #index of selected field
	last_pot_msg = None
	last_param_msg = None

	stdscr.nodelay(1)
	#TODO on resize, refresh
	outqueue.put(request_param_msg())
	while True:
		draw_legenda(stdscr, 0, 0)
		if last_param_msg:
			draw_param(stdscr, 10, 0, last_param_msg, settings[index],
				settings)
		else:
			stdscr.addstr(5,10,"Connected but no data received. Is your"\
				" radio turned on?")
		draw_help(stdscr, 1, 0, index, settings)
		if last_pot_msg:
			draw_pot(stdscr, 3, 0, last_pot_msg, channels)
		stdscr.refresh()
		
		#Handle user input, non-blocking
		c = stdscr.getch()
		if c != curses.ERR:
			if c == ord('q'):
				#signal the main thread to quit
				os.kill(os.getpid(), signal.SIGINT)
				break  # Exit the while()
			elif c == ord('d'):
				outqueue.put(request_param_msg())
			elif c == ord('u') and last_param_msg:
				outqueue.put(load_param_msg(last_param_msg[1:-2]))
			elif c == ord('a') and last_param_msg and last_pot_msg:
				autotrim(last_param_msg, last_pot_msg, trims, channels,
					reverse)

			## vi style navigation
			elif c == ord('j') or c == curses.KEY_DOWN:
				index = (index+1)%len(settings)
			elif c == ord('k') or c == curses.KEY_UP:
				index = (index-1)%len(settings)
			elif c == ord('l') or c == curses.KEY_RIGHT:
				index = next_column(settings, index, tabstops)
			elif c == ord('h') or c == curses.KEY_LEFT:
				index = prev_column(settings, index, tabstops)

			elif c == ord(' '):
				settings[index].inc_wrap(last_param_msg)
				settings[index].changed = True
			elif c == ord('+') or c == ord(' ') or c == ord('='):
				settings[index].inc(last_param_msg)
				settings[index].changed = True
			elif c == ord('-'):
				settings[index].dec(last_param_msg)
				settings[index].changed = True

			elif c == ord('\t'):
				index = (index+1)%len(settings)
				cur = settings[index]
				while cur not in tabstops:
					index = (index+1)%len(settings)
					cur = settings[index]
			elif c == curses.KEY_BTAB:
				index = (index-1)%len(settings)
				cur = settings[index]
				while cur not in tabstops:
					index = (index-1)%len(settings)
					cur = settings[index]

		# Handle incoming message, short timeout to keep gui responsive.
		# Especially with radio switched off.
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
			for d in settings:
				d.changed = False

def gui_loop(inqueue, outqueue):
	"""Wrap the actual gui loop. It will take care or resetting
		the terminal when shit hits the fan. """
	curses.wrapper(gui, inqueue, outqueue)
