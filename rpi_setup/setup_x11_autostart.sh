#!/bin/bash
# Script to set up X11 and auto-start the visualizer on Raspberry Pi

echo "Installing minimal X11 components..."
sudo apt update
sudo apt install -y xserver-xorg xinit x11-xserver-utils openbox

echo "Creating .xinitrc for auto-start..."
cat > ~/.xinitrc << 'XINITRC_EOF'
#!/bin/bash
# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide mouse cursor after 1 second of inactivity
unclutter -idle 1 &

# Start openbox window manager in background
openbox &

# Wait a moment for X to fully initialize
sleep 1

# Start the visualizer
cd ~/audio_viz

echo "Running clock setup with venv python..."

# Start master clock generator first
venv/bin/python rpi_setup/setup_clock.py >> /home/james/visualizer_log.txt 2>&1 || true

echo "setup clock, about to start display"

venv/bin/python -m src.main --live --device plughw:0,0 >> /home/james/visualizer_log.txt 2>&1
XINITRC_EOF

chmod +x ~/.xinitrc

echo "Installing unclutter for hiding mouse cursor..."
sudo apt install -y unclutter

echo "Creating systemd service for X11 auto-start..."
sudo tee /etc/systemd/system/audio-viz-x11.service << 'SERVICE_EOF'
[Unit]
Description=Audio Visualizer with X11
After=multi-user.target

[Service]
Type=simple
User=james
WorkingDirectory=/home/james
Environment="DISPLAY=:0"
ExecStart=/usr/bin/startx
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
SERVICE_EOF

echo "Enabling and starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable audio-viz-x11.service

echo ""
echo "Setup complete!"
echo ""
echo "To start now: sudo systemctl start audio-viz-x11.service"
echo "To check status: sudo systemctl status audio-viz-x11.service"
echo "To view logs: sudo journalctl -u audio-viz-x11.service -f"
echo ""
echo "The visualizer will auto-start on boot."
