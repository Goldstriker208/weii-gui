import sys
import time
import statistics
import subprocess
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from PyQt6.QtGui import QFont, QTextOption
from PyQt6.QtCore import Qt


import evdev
from evdev import ecodes


# ────────────────────────────── Core Weii Logic ──────────────────────────────

def get_board_device() -> Optional[evdev.InputDevice]:
    devices = [
        path
        for path in evdev.list_devices()
        if evdev.InputDevice(path).name == "Nintendo Wii Remote Balance Board"
    ]
    if not devices:
        return None
    return evdev.InputDevice(devices[0])


def get_raw_measurement(device: evdev.InputDevice) -> float:
    data = [None] * 4
    while True:
        event = device.read_one()
        if event is None:
            continue

        if event.code == ecodes.ABS_HAT1X:
            data[0] = event.value / 100
        elif event.code == ecodes.ABS_HAT0X:
            data[1] = event.value / 100
        elif event.code == ecodes.ABS_HAT0Y:
            data[2] = event.value / 100
        elif event.code == ecodes.ABS_HAT1Y:
            data[3] = event.value / 100
        elif event.code == ecodes.BTN_A:
            raise Exception("User pressed board button while measuring.")
        elif event.code == ecodes.SYN_REPORT and event.value == 0:
            if None in data:
                data = [None] * 4
                continue
            else:
                return sum(data)


def read_data(device: evdev.InputDevice, samples: int, threshold: float, signal_cb) -> List[float]:
    data: List[float] = []
    stuck_zero_count = 0

    while True:
        measurement = get_raw_measurement(device)

        if measurement == 0:
            stuck_zero_count += 1
        else:
            stuck_zero_count = 0

        if stuck_zero_count > 100:
            signal_cb("⚠️ Sensors not responding — check battery level!")
            time.sleep(2)
            continue

        if len(data) and measurement < threshold:
            signal_cb("User stepped off.")
            break
        if len(data) == 0 and measurement < threshold:
            continue
        data.append(measurement)
        if len(data) == 1:
            signal_cb("Measurement started, please wait...")
        if len(data) > samples:
            break
    device.close()
    return data


def measure_weight(
    adjust: float,
    disconnect_address: str,
    command: Optional[str],
    signal_cb,
    unit: str = "kg",
    fake: bool = False,
) -> float:
    signal_cb("Waiting for balance board...")
    while not fake:
        board = get_board_device()
        if board:
            break
        time.sleep(0.5)

    signal_cb("Balance board found, please step on.")

    if fake:
        weight_data = [85.2] * 200
    else:
        weight_data = read_data(board, 200, threshold=20, signal_cb=signal_cb)

    final_weight = statistics.median(weight_data) + adjust

    if unit == "lbs":
        final_weight *= 2.20462

    signal_cb(f"\aDone, weight: {final_weight:.1f} {unit}")

    if disconnect_address:
        signal_cb("Disconnecting...")
        subprocess.run(
            ["/usr/bin/env", "bluetoothctl", "disconnect", disconnect_address],
            capture_output=True,
        )

    if command:
        subprocess.run(command.replace("{weight}", f"{final_weight:.1f}"), shell=True)

    return final_weight


# ────────────────────────────── PyQt6 GUI Code ──────────────────────────────

class WeiiThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, adjust=0.0, disconnect="", command="", unit="kg"):
        super().__init__()
        self.adjust = adjust
        self.disconnect = disconnect
        self.command = command
        self.unit = unit

    def emit_text(self, text):
        self.update_signal.emit(text)

    def run(self):
        try:
            measure_weight(
                adjust=self.adjust,
                disconnect_address=self.disconnect,
                command=self.command,
                signal_cb=self.emit_text,
                unit=self.unit,
                fake=False
            )
        except Exception as e:
            self.emit_text(f"Error: {e}")


class WeiiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weii Balance Board GUI")
        self.setGeometry(300, 300, 400, 250)

        self.layout = QVBoxLayout()

        self.label = QLabel("Click to start measurement.")
        self.unit_selector = QComboBox()
        self.unit_selector.addItems(["kg", "lbs"])

        self.unit_selector.currentIndexChanged.connect(self.show_final_weight)

        self.adjust_spinbox = QDoubleSpinBox()
        self.adjust_spinbox.setDecimals(2)
        self.adjust_spinbox.setRange(-20.0, 20.0)
        self.adjust_spinbox.setValue(7.0)
        self.adjust_spinbox.setSuffix(" kg adjust")

        self.button = QPushButton("Start Weighing")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.unit_selector)
        self.layout.addWidget(self.adjust_spinbox)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.start_measurement)


        self.final_kg = None  # Holds the measured value in kg

    def start_measurement(self):
        self.button.setDisabled(True)
        unit = self.unit_selector.currentText()
        adjust = self.adjust_spinbox.value()
        self.label.setText("Initializing...")

        self.thread = WeiiThread(adjust=adjust, disconnect="", command="", unit=unit)
        self.thread.update_signal.connect(self.update_label)
        self.thread.finished.connect(lambda: self.button.setDisabled(False))
        self.thread.start()


    def update_label(self, text):
        clean_text = text.replace("\a", "")
        if clean_text.startswith("Done, weight:"):
            parts = clean_text.split(":")[1].strip()
            value, unit = parts.split()
            self.final_kg = float(value) if unit == "kg" else float(value) / 2.20462
            self.show_final_weight()
        else:
            self.label.setFont(QFont("Arial", 14))
            self.label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.label.setText(clean_text)

    def show_final_weight(self):
        if self.final_kg is None:
            return
        unit = self.unit_selector.currentText()
        if unit == "kg":
            converted = self.final_kg
        else:
            converted = self.final_kg * 2.20462

        self.label.setFont(QFont("Arial", 24))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setText(f"Your weight is:<br><b>{converted:.1f} {unit}</b>")





# ────────────────────────────── Run the GUI ──────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeiiApp()
    window.show()
    sys.exit(app.exec())
