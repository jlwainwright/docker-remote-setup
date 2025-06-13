#!/bin/bash
# Script to install and configure Zigbee2MQTT on Alpine Linux CT 101

echo "Installing Zigbee2MQTT on Alpine Linux..."

# Update packages
apk update
apk upgrade

# Install required packages
echo "Installing Node.js, npm, and build tools..."
apk add nodejs npm git python3 make g++ linux-headers

# Create zigbee2mqtt user if it doesn't exist
if ! id "zigbee2mqtt" &>/dev/null; then
    echo "Creating zigbee2mqtt user..."
    adduser -D -s /bin/sh zigbee2mqtt
    addgroup zigbee2mqtt dialout
fi

# Switch to zigbee2mqtt user and install
echo "Installing Zigbee2MQTT..."
su - zigbee2mqtt -c "
    if [ ! -d '/home/zigbee2mqtt/zigbee2mqtt' ]; then
        git clone https://github.com/Koenkk/zigbee2mqtt.git
        cd zigbee2mqtt
        npm ci --production
    else
        echo 'Zigbee2MQTT already installed, updating...'
        cd zigbee2mqtt
        git pull
        npm ci --production
    fi
"

# Create data directory and copy configuration
echo "Setting up configuration..."
mkdir -p /home/zigbee2mqtt/zigbee2mqtt/data
chown -R zigbee2mqtt:zigbee2mqtt /home/zigbee2mqtt/zigbee2mqtt/data

# Note: You'll need to copy the zigbee2mqtt-configuration.yaml to the data directory

echo "Installation complete!"
echo "Next steps:"
echo "1. Copy configuration.yaml to /home/zigbee2mqtt/zigbee2mqtt/data/"
echo "2. Install the OpenRC service"
echo "3. Start the service"
