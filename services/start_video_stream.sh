#!/bin/bash

set -u

CAMERA_DEV="/dev/video0"
COMPUTER_IP="" # Enter your computer's static IP
PORT=5000
POLL_INTERVAL=2

echo "Watching for camera at ${CAMERA_DEV}"
already_logged_waiting=false

while true; do
    if [ -e "${CAMERA_DEV}" ]; then
        already_logged_waiting=false
        echo "Camera detected at ${CAMERA_DEV}. Starting stream to ${COMPUTER_IP}:${PORT}..."

        ffmpeg -f v4l2 \
            -framerate 30 \
            -video_size 640x480 \
            -i "${CAMERA_DEV}" \
            -c:v libx264 \
            -flags +global_header \
            -bsf:v dump_extra \
            -g 30 \
            -preset ultrafast \
            -tune zerolatency \
            -pix_fmt yuv420p \
            -f mpegts "udp://${COMPUTER_IP}:${PORT}?pkt_size=1316"
        
        exit_code=$?
        echo "Streaming stopped. exit code=${exit_code}."
        echo "Resume watch for ${CAMERA_DEV}..."
    else
        if [ "${already_logged_waiting}" = false ]; then
            echo "No camera at ${CAMERA_DEV}. Please make sure your camera is connected."
            already_logged_waiting=true
        fi
        sleep "${POLL_INTERVAL}"
    fi
done
