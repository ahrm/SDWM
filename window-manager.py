import os
import datetime
import time
import ctypes
user32 = ctypes.windll.user32
from PIL.ImageQt import ImageQt
import PIL.ImageGrab
import PyQt5
import PyQt5.QtWidgets
from PyQt5.QtWidgets import QWidget
import PyQt5.QtGui
import win32con
import win32gui
import wmi
import json
import win32process
import copy
import subprocess
import argparse

WMI = wmi.WMI()

NAME = 'SDWM'
# if set, we create an image for alt-tab preview, at the cost of some annoyances
PREVIEW = True
CONFIG_FILE_LOCATION = os.path.dirname(os.path.abspath(__file__)) + r"\config.json"
ICON_PATH = os.path.dirname(os.path.abspath(__file__)) + r'\SDWM-icon.png'
CONFIG_FILE_VERSION = 1

def get_app_path(hwnd):
    """Get applicatin path given hwnd."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        for p in WMI.query('SELECT ExecutablePath FROM Win32_Process WHERE ProcessId = %s' % str(pid)):
            exe = p.ExecutablePath
            break
    except Exception as e:
        return print(str(e))
    else:
        return exe

def create_saved_config(selected_hwnds_with_commands, state, foreground_window):
    selected_file_locations = {hwnd: get_app_path(hwnd) for hwnd, _ in selected_hwnds_with_commands}
    state_dict = {hwnd: place for hwnd, place in state}
    result = dict()
    result['state'] = dict()

    for hwnd, command in selected_hwnds_with_commands:
        result['state'][selected_file_locations[hwnd]] = (state_dict[hwnd], command)

    result['foreground_window'] = selected_file_locations[foreground_window]
    result['version'] = CONFIG_FILE_VERSION
    return result

def load_config():
    try:
        with open(CONFIG_FILE_LOCATION, 'r') as f:
            config = json.load(f)
        return config
    except:
        return dict()

def save_config(config_to_save):
    with open(CONFIG_FILE_LOCATION, 'w') as f:
        json.dump(config_to_save, f)

def add_new_config(new_config, config_name):
    prev_config = load_config()
    prev_config[config_name] = new_config
    save_config(prev_config)
    

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

def run_independent_program(path):
    subprocess.Popen(path, creationflags=subprocess.DETACHED_PROCESS, close_fds=True)


def does_process_with_path_exist(path):
    windows = get_visible_window_order()
    for win in windows:
        winpath = get_app_path(win)
        if winpath == path:
            return True
    return False

def ensure_process_exists(path, command, timeout=10):
    start_time = datetime.datetime.now()

    if (not does_process_with_path_exist(path)) or (len(command) > 0):
        if len(command) == 0:
            run_independent_program(path)
        else:
            run_independent_program(command)
        while (datetime.datetime.now() - start_time).total_seconds() < timeout:
            time.sleep(0.3)
            if does_process_with_path_exist(path):
                return True
        return False
    return True


def select_windows():
    windows = get_visible_window_order()

    dialog = PyQt5.QtWidgets.QDialog()
    dialog.setWindowTitle('Select Windows')
    layout = PyQt5.QtWidgets.QVBoxLayout()
    dialog.setLayout(layout)
    checkboxes = []
    command_lines = []
    for i, hwnd in enumerate(windows):
        row_widget = PyQt5.QtWidgets.QWidget()
        row_layout = PyQt5.QtWidgets.QHBoxLayout()

        name = win32gui.GetWindowText(hwnd)
        checkbox = PyQt5.QtWidgets.QCheckBox(name)
        checkbox.setChecked(False)
        command_line = PyQt5.QtWidgets.QLineEdit()

        checkboxes.append(checkbox)
        command_lines.append(command_line)

        row_layout.addWidget(checkbox)
        row_layout.addWidget(command_line)
        row_widget.setLayout(row_layout)

        layout.addWidget(row_widget)
    button_box = PyQt5.QtWidgets.QDialogButtonBox(PyQt5.QtWidgets.QDialogButtonBox.Ok | PyQt5.QtWidgets.QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    dialog.exec()
    swindows = [(windows[i], command_lines[i].text()) for i, checkbox in enumerate(checkboxes) if checkbox.isChecked()]
    return swindows

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

def get_file_to_hwnd_map(priority_hwnds=[]):
    windows = get_visible_window_order()
    res = {get_app_path(w): w for w in windows}
    for hwnd in priority_hwnds:
        res[get_app_path(hwnd)] = hwnd
    return res

def minimize(window):
    # visible_windows = get_visible_window_order()
    # hwnd = int(window.winId())
    # win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    # # window.setWindowState(PyQt5.QtCore.Qt.WindowMinimized)
    window.showMinimized()
class WindowState(QWidget):

    def __init__(self):
        super().__init__()

        self.is_active = False
        self.update_screenshot()

        layout = PyQt5.QtWidgets.QVBoxLayout()
        if PREVIEW:
            self.pic_widget = PyQt5.QtWidgets.QLabel()
            self.pic_widget.setPixmap(PyQt5.QtGui.QPixmap.fromImage(ImageQt(self.screenshot).copy()))
        self.name_widget = PyQt5.QtWidgets.QLineEdit()
        self.name_widget.returnPressed.connect(self.on_return_pressed)
        config_names = list(load_config().keys())
        completer = PyQt5.QtWidgets.QCompleter(['*' + name for name in config_names] + ['+' + name for name in config_names])
        self.name_widget.setCompleter(completer)
        layout.addWidget(self.name_widget)
        if PREVIEW:
            layout.addWidget(self.pic_widget)

        self.setLayout(layout)
        self.setFocusPolicy(PyQt5.QtCore.Qt.StrongFocus)

    def update_screenshot(self):
        self.screenshot = PIL.ImageGrab.grab()
    
    def set_state(self, new_state, new_foreground_window):
        if new_state != None:
            self.state = new_state
        if new_foreground_window != None:
            self.foreground_window = new_foreground_window
    
    def get_snapshot(self):
        windows = get_visible_window_order()
        window_placements = list(map(get_window_placement, windows))
        foreground_window = win32gui.GetForegroundWindow()
        state = list(zip(windows, window_placements))
        self.set_state(state, foreground_window)
    
    def hwnd(self):
        return int(self.winId())
    
    def restore_config(self, config_, should_launch_programs=False, priority_hwnds=[]):
        config = copy.copy(config_)

        file_to_hwnd = get_file_to_hwnd_map(priority_hwnds)
        foreground_process = file_to_hwnd.get(config['foreground_window'], None)
        new_state = []
        missing_programs = set()

        for process_path, (process_state, command) in config['state'].items():
            if (process_path in file_to_hwnd.keys()) and ((not should_launch_programs) or (len(command) == 0)):
                new_state.append((file_to_hwnd[process_path], process_state))
            else:
                missing_programs.add((process_path, command))
        
        if len(missing_programs) == 0 or should_launch_programs == False:
            self.set_state(new_state, foreground_process)
        else:
            if should_launch_programs:
                prev_hwnds = set(get_visible_window_order())
                for program, command in missing_programs:
                    ensure_process_exists(program, command)
                new_hwnds = set(get_visible_window_order())
                return self.restore_config(config_, should_launch_programs=False, priority_hwnds=list(new_hwnds - prev_hwnds))
            else:
                return False

        return True
    
    def restore(self):
        restore_state(self.state, self.foreground_window)

    def focus_handler(self, old, new):
        if self.is_active:
            if old == None:
                self.restore()
                if not PREVIEW:
                    minimize(self)

    def handle_new_config(self, new_config_name):
        selected_windows = select_windows()
        conf = create_saved_config(selected_windows, self.state, self.foreground_window)
        add_new_config(conf, new_config_name)
    
    def handle_restore_config(self, restore_config_name, type_symbol):
        config = load_config()
        if config and restore_config_name in config.keys():
            self.restore_config(config[restore_config_name], type_symbol=='*')
            self.is_active = True
            self.focus_handler(None, True)

    def on_return_pressed(self):
        new_config_name = self.name_widget.text()
        if new_config_name.startswith('++'):
            new_config_name = new_config_name[2:]
            self.handle_new_config(new_config_name)

        if new_config_name.startswith('+') or new_config_name.startswith('*'):
            symb = new_config_name[0]
            new_config_name = new_config_name[1:]
            self.handle_restore_config(new_config_name, symb)

        self.is_active = True
        if len(new_config_name) > 0:
            self.setWindowTitle(NAME +  ' > ' + new_config_name)
        else:
            self.setWindowTitle(NAME)
        # window.showMinimized()
        minimize(self)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SDWM - Simple Dynamic Window Manager for Windows")
    parser.add_argument('--no-preview', action='store_true', help='do not show an alt-tab preview')
    parser.add_argument('--load-config', help='load CONFIG instead of snapshotting the current layout', metavar='CONFIG')
    parser.add_argument('--launch', action='store_true', help='if used with --load-config then launch any windows from the config which are not present')
    
    args = parser.parse_args()
    
    if args.no_preview:
        PREVIEW = False
    
    app = PyQt5.QtWidgets.QApplication([])
    icon = PyQt5.QtGui.QIcon(ICON_PATH)
    app.setWindowIcon(icon)

    manager_window = WindowState()
    
    if args.load_config is None:
        manager_window.get_snapshot()
    else:
        if args.launch:
            manager_window.name_widget.setText('*' + args.load_config)
        else:
            manager_window.name_widget.setText('+' + args.load_config)
        
        manager_window.on_return_pressed()

    if PREVIEW:
        def on_timout():
            if manager_window.is_active:
                minimize(manager_window)

        # if we minimize it in focusEvent, then the window is not properly rendered
        # so we try to minimize it periodically here
        # (if we don't minimize the window at all, then the user might accidentally activate
        # the window by minimizing other windows)
        timer = PyQt5.QtCore.QTimer()
        timer.timeout.connect(on_timout)
        timer.start(1000)

    if PREVIEW:
        manager_window.showMaximized()
    else:
        manager_window.show()

    app.focusChanged.connect(manager_window.focus_handler)
    app.exec()

