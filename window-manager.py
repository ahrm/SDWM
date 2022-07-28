import os
import datetime
import time
import ctypes
user32 = ctypes.windll.user32
from PIL.ImageQt import ImageQt
import PIL.ImageGrab
import PyQt5
import PyQt5.QtWidgets
import PyQt5.QtGui
import win32con
import win32gui

NAME = 'SDWM'
# if set, we create an image for alt-tab preview, at the cost of some annoyances
PREVIEW = True

def restore_state(state, foreground_window):
	prev = None
	for i, (hwnd, placement) in enumerate(reversed(state)):
		name = win32gui.GetWindowText(hwnd)
		try:
			rect = placement[-1]
			win32gui.SetWindowPlacement(hwnd, placement)
			if i < len(state) - 1:
				win32gui.SetWindowPos(hwnd, state[-(i+2)][0], rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], win32con.SWP_SHOWWINDOW)
			else:
				win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], win32con.SWP_SHOWWINDOW)

			win32gui.SetForegroundWindow(hwnd)
			# this should not be necessary but for some reason if we remove this, windows sometimes
			# confuses the order of windows, I am not sure if this value works for all systems, you
			# might need to increase it if you see inconsistent behavior
			time.sleep(0.04)
		except:
			pass
	try:
		win32gui.SetForegroundWindow(foreground_window)
	except:
		pass

def get_window_order_helper(hwnd):
	if not hwnd:
		return []
	next_window = user32.GetWindow(hwnd, win32con.GW_HWNDNEXT)
	if win32gui.IsWindowVisible(hwnd) and len(win32gui.GetWindowText(hwnd)) > 0:
		return [hwnd] + get_window_order_helper(next_window)
	else:
		return get_window_order_helper(next_window)
	
def get_visible_window_order():
	top = user32.GetTopWindow(None)
	return get_window_order_helper(top)

def get_window_placement(hwnd):
	placement = win32gui.GetWindowPlacement(hwnd)
	rect = win32gui.GetWindowRect(hwnd)
	processed_placement = (placement[0], placement[1], placement[2], placement[3], rect)
	return processed_placement

if __name__ == '__main__':
	icon_path = os.path.dirname(os.path.abspath(__file__)) + r'\SDWM-icon.png'

	active = False
	windows = get_visible_window_order()
	window_placements = list(map(get_window_placement, windows))
	foreground_window = win32gui.GetForegroundWindow()
	state = list(zip(windows, window_placements))
	screenshot = PIL.ImageGrab.grab()
	last_focus_time = datetime.datetime.now()

	app = PyQt5.QtWidgets.QApplication([])
	window = PyQt5.QtWidgets.QWidget()

	def on_focus(first, second):
		if active:
			if first == None:
				restore_state(state, foreground_window)
				last_focus_time = datetime.datetime.now()
				if not PREVIEW:
					window.showMinimized()

	layout = PyQt5.QtWidgets.QVBoxLayout()
	if PREVIEW:
		pic = PyQt5.QtWidgets.QLabel()
		pic.setPixmap(PyQt5.QtGui.QPixmap.fromImage(ImageQt(screenshot).copy()))
	name = PyQt5.QtWidgets.QLineEdit()

	# set window icon
	icon = PyQt5.QtGui.QIcon(icon_path)
	app.setWindowIcon(icon)

	def on_return_pressed():
		global active
		active = True
		if len(name.text()) > 0:
			window.setWindowTitle(NAME +  ' > ' + name.text())
		else:
			window.setWindowTitle(NAME)
		window.showMinimized()

	if PREVIEW:
		def on_timout():
			global active
			if active:
				if (datetime.datetime.now() - last_focus_time).seconds > 1:
					# win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1], win32con.SWP_SHOWWINDOW)
					window.showMinimized()
					for i in range(10):
						window.lower()

		# if we minimize it in focusEvent, then the window is not properly rendered
		# so we try to minimize it periodically here
		# (if we don't minimize the window at all, then the user might accidentally activate
		# the window by minimizing other windows)
		timer = PyQt5.QtCore.QTimer()
		timer.timeout.connect(on_timout)
		timer.start(1000)

	name.returnPressed.connect(on_return_pressed)
	layout.addWidget(name)
	if PREVIEW:
		layout.addWidget(pic)
	window.setLayout(layout)
	window.setFocusPolicy(PyQt5.QtCore.Qt.StrongFocus)
	if PREVIEW:
		window.showMaximized()
	else:
		window.show()
	app.focusChanged.connect(on_focus)
	app.exec()