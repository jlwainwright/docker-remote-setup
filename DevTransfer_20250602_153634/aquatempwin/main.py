import sys
import os
import logging
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QSpinBox, QComboBox, QGroupBox, QMessageBox, QDialog, QCheckBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from dotenv import load_dotenv
from aquatempConnect import aquatempConnect

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AquaTemp Login")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Save credentials checkbox
        self.save_credentials = QCheckBox("Save credentials")
        layout.addWidget(self.save_credentials)
        
        # Buttons
        button_layout = QHBoxLayout()
        login_button = QPushButton("Login")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(login_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Connect signals
        login_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
    def get_credentials(self):
        return {
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'save': self.save_credentials.isChecked()
        }

class AquaTempWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AquaTemp Controller")
        self.setMinimumSize(800, 600)
        
        # Initialize variables
        self.api = None
        self.timer = QTimer()  # Initialize timer here
        self.timer.timeout.connect(self.update_status)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Load credentials from .env file
        load_dotenv()
        self.username = os.getenv('AQUATEMP_USERNAME')
        self.password = os.getenv('AQUATEMP_PASSWORD')
        
        self.init_ui()
        
        # If no credentials, show login dialog
        if not self.username or not self.password:
            self.show_login_dialog()
        else:
            self.connect_api()

    def connect_api(self):
        try:
            if self.username and self.password:
                self.api = aquatempConnect(self.username, self.password)
                if not self.api.devices:
                    raise Exception("No devices found")
                    
                # Show device information
                device = self.api.devices[0]  # Get first device
                device_info = (f"Connected to {device.get('device_name', 'Unknown Device')} "
                             f"(ID: {device.get('device_code', 'Unknown')})")
                self.status_label.setText(device_info)
                self.status_label.setStyleSheet("color: green")
                
                self.update_status()
                self.timer.start(5000)  # Start timer only after successful connection
            else:
                self.status_label.setText("Please log in")
                self.status_label.setStyleSheet("color: orange")
                self.show_login_dialog()
        except Exception as e:
            self.api = None
            error_msg = str(e)
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: red")
            QMessageBox.critical(self, "Connection Error", 
                               f"{error_msg}\n\nPlease check your credentials and try again.")
            self.show_login_dialog()

    def init_ui(self):
        # Create menu bar
        menubar = self.menuBar()
        account_menu = menubar.addMenu('Account')
        
        # Add login action
        login_action = account_menu.addAction('Login')
        login_action.triggered.connect(self.show_login_dialog)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red")
        status_layout.addWidget(self.status_label)
        
        # Temperature readings
        temp_layout = QHBoxLayout()
        self.inlet_temp = QLabel("Inlet: --°C")
        self.outlet_temp = QLabel("Outlet: --°C")
        self.ambient_temp = QLabel("Ambient: --°C")
        for label in [self.inlet_temp, self.outlet_temp, self.ambient_temp]:
            label.setFont(QFont("Arial", 12))
            temp_layout.addWidget(label)
        
        status_layout.addLayout(temp_layout)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Controls section
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        # Power control
        power_layout = QHBoxLayout()
        self.power_btn = QPushButton("Turn ON")
        self.power_btn.clicked.connect(self.toggle_power)
        power_layout.addWidget(QLabel("Power:"))
        power_layout.addWidget(self.power_btn)
        controls_layout.addLayout(power_layout)
        
        # Temperature control
        temp_layout = QHBoxLayout()
        self.temp_spinbox = QSpinBox()
        self.temp_spinbox.setRange(16, 40)
        self.temp_spinbox.setValue(22)
        self.temp_spinbox.valueChanged.connect(self.set_temperature)
        temp_layout.addWidget(QLabel("Set Temperature:"))
        temp_layout.addWidget(self.temp_spinbox)
        controls_layout.addLayout(temp_layout)
        
        # Mode control
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Cooling", "Heating", "Auto"])
        self.mode_combo.currentIndexChanged.connect(self.set_mode)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        controls_layout.addLayout(mode_layout)
        
        # Silent mode
        silent_layout = QHBoxLayout()
        self.silent_btn = QPushButton("Silent Mode OFF")
        self.silent_btn.clicked.connect(self.toggle_silent)
        silent_layout.addWidget(self.silent_btn)
        controls_layout.addLayout(silent_layout)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            creds = dialog.get_credentials()
            
            # Validate input
            if not creds['username'] or not creds['password']:
                QMessageBox.warning(self, "Invalid Input", 
                                  "Username and password cannot be empty.")
                self.show_login_dialog()
                return
                
            self.username = creds['username']
            self.password = creds['password']
            
            if creds['save']:
                # Save credentials to .env file
                with open('.env', 'w') as f:
                    f.write(f"AQUATEMP_USERNAME={self.username}\n")
                    f.write(f"AQUATEMP_PASSWORD={self.password}\n")
            
            self.connect_api()
        else:
            if not self.api:  # If no active connection
                self.status_label.setText("Please log in to continue")
                self.status_label.setStyleSheet("color: orange")
    
    def update_status(self):
        if not self.api:
            return
            
        try:
            status = self.api.getStatus()
            
            # Update temperature displays with proper formatting
            self.inlet_temp.setText(f"Inlet: {float(status.get('T02', 0)):.1f}°C")
            self.outlet_temp.setText(f"Outlet: {float(status.get('T03', 0)):.1f}°C")
            self.ambient_temp.setText(f"Ambient: {float(status.get('T05', 0)):.1f}°C")
            
            # Update power button
            power_state = status.get('Power', '0')
            self.power_btn.setText("Turn OFF" if power_state == "1" else "Turn ON")
            
            # Update silent mode button
            silent_state = status.get('Manual-mute', '0')
            self.silent_btn.setText("Silent Mode ON" if silent_state == "1" else "Silent Mode OFF")
            
            # Update mode combobox
            current_mode = status.get('Mode', '1')
            mode_map = {'1': 'Cooling', '2': 'Heating', '3': 'Auto'}
            if current_mode in mode_map:
                index = self.mode_combo.findText(mode_map[current_mode])
                if index >= 0:
                    self.mode_combo.setCurrentIndex(index)
            
            # Update temperature setpoint
            set_temp = status.get('Set_Temp', '22')
            try:
                self.temp_spinbox.setValue(int(float(set_temp)))
            except (ValueError, TypeError):
                pass
                
            # Update status label with device name and timestamp
            device = self.api.devices[0]
            device_name = device.get('device_name', 'Unknown Device')
            self.status_label.setText(f"{device_name} - Last update: {time.strftime('%H:%M:%S')}")
            self.status_label.setStyleSheet("color: green")
            
            # Adjust refresh rate based on success
            if self.timer.interval() != 30000:  # If not at normal refresh rate
                self.timer.setInterval(30000)  # Set to normal 30-second refresh
                
        except Exception as e:
            logging.error(f"Status update failed: {str(e)}")
            self.status_label.setText(f"Update failed: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            
            # Increase refresh rate when there are errors
            if self.timer.interval() != 5000:  # If not at error refresh rate
                self.timer.setInterval(5000)  # Set to 5-second refresh
    
    def toggle_power(self):
        if not self.api:
            return
        
        try:
            current_state = "1" if self.power_btn.text() == "Turn OFF" else "0"
            self.api.setPower("0" if current_state == "1" else "1")
            self.update_status()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to toggle power: {str(e)}")
    
    def set_temperature(self):
        if not self.api:
            return
            
        try:
            self.api.setTemperature(self.temp_spinbox.value())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set temperature: {str(e)}")
    
    def set_mode(self):
        if not self.api:
            return
            
        try:
            mode_map = {"Cooling": 1, "Heating": 2, "Auto": 3}
            mode = mode_map[self.mode_combo.currentText()]
            self.api.setTemperature(self.temp_spinbox.value(), mode=mode)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set mode: {str(e)}")
    
    def toggle_silent(self):
        if not self.api:
            return
            
        try:
            current_state = "1" if self.silent_btn.text() == "Silent Mode ON" else "0"
            self.api.setSilent("0" if current_state == "1" else "1")
            self.update_status()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to toggle silent mode: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Set the application style
    app.setStyle('Fusion')
    
    # Create dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(palette)
    
    window = AquaTempWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
