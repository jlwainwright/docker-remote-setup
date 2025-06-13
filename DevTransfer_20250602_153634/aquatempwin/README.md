# AquaTemp Controller

A Windows application to monitor and control your AquaTemp heat pump.

## Features

- Real-time monitoring of heat pump temperatures (inlet, outlet, ambient)
- Power control
- Temperature setting
- Mode selection (Cooling, Heating, Auto)
- Silent mode toggle
- Dark mode UI
- Auto-refresh every 30 seconds

## Installation

1. Install Python 3.8 or higher
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `example.env` to `.env` and fill in your credentials:
   ```bash
   cp example.env .env
   ```
4. Edit `.env` with your AquaTemp username and password

## Running the Application

```bash
python main.py
```

## Usage

- The status section shows current temperature readings
- Use the controls section to:
  - Toggle power on/off
  - Set desired temperature
  - Change operating mode
  - Toggle silent mode
- The application automatically refreshes every 30 seconds
- Status indicators will show connection state and any errors
