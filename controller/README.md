# Hermie Control Setup

This directory contains the Hermie Control application, an Electron-based control interface for the Hermie robot.

## Overview

Hermie Control is an Electron 22.3.27 application that runs headlessly on a Raspberry Pi 5, automatically restarting every 10 minutes to ensure reliability.

## Prerequisites

- Raspberry Pi (tested on Pi 5 running Debian Trixie)
- Xvfb (X Virtual Framebuffer for headless operation)
- systemd (for service management)

## Installation Steps

### 1. Extract the Application

The `hermie-control-bin` directory should contain the extracted application files. If you have a `hermie-control.tar.gz` file inside this directory:

```bash
cd hermie-control-bin
tar -xzf hermie-control.tar.gz
```

### 2. Install Missing Dependencies

The Electron binary requires `libffmpeg.so` which is not included in the archive:

```bash
cd hermie-control-bin
wget https://github.com/electron/electron/releases/download/v22.3.27/ffmpeg-v22.3.27-linux-arm64.zip
unzip ffmpeg-v22.3.27-linux-arm64.zip
rm ffmpeg-v22.3.27-linux-arm64.zip
```

### 3. Install Xvfb

The application requires a display server to run. Install Xvfb for headless operation:

```bash
sudo apt-get update
sudo apt-get install -y xvfb
```

### 4. Update Start Script

The `start.sh` script has been updated to use Xvfb. It should contain:

```bash
#!/bin/bash
cd "$(dirname "$0")"
xvfb-run --auto-servernum ./hermie-control
```

### 5. Install Systemd Service

Copy the service file and enable it:

```bash
sudo cp hermie-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hermie-control.service
sudo systemctl start hermie-control.service
```

## Service Configuration

The systemd service is configured to:
- Run as user `odio`
- Automatically restart every 10 minutes (`RuntimeMaxSec=600`)
- Restart immediately if it crashes (`Restart=always`)
- Log output to systemd journal

## Managing the Service

### Check Status
```bash
sudo systemctl status hermie-control.service
```

### View Logs
```bash
# Follow logs in real-time
journalctl -u hermie-control.service -f

# View last 50 lines
journalctl -u hermie-control.service -n 50
```

### Stop Service
```bash
sudo systemctl stop hermie-control.service
```

### Restart Service
```bash
sudo systemctl restart hermie-control.service
```

### Disable Auto-Start
```bash
sudo systemctl disable hermie-control.service
```

## Troubleshooting

### Missing libffmpeg.so
If you see `error while loading shared libraries: libffmpeg.so`, ensure you've downloaded the correct version for your architecture (ARM64 for Raspberry Pi 5).

### Display Errors
If you see `Missing X server or $DISPLAY` errors, ensure Xvfb is installed and the start.sh script is using `xvfb-run`.

### Process Not Running
Check the journal logs for errors:
```bash
journalctl -u hermie-control.service --no-pager -n 100
```

## Files in This Directory

- `hermie-control-bin/` - Application directory containing the Electron binary and resources
- `hermie-control.js` - Additional control script
- `Hermie Control.sb3` - Scratch 3 project file
- `hermie-control.service` - systemd service configuration file
- `README.md` - This file

## Architecture

The application runs as multiple processes (typical for Electron apps):
- Main process
- GPU process
- Renderer process(es)
- Utility processes (network service, etc.)
- Zygote processes (for sandboxing)

This is normal and expected behavior for Chromium/Electron-based applications.
