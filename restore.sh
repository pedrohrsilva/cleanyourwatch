#!/usr/bin/env bash
# Quick restore script for CleanYourWatch
set -e

DEVICE="${1:-192.168.31.47:44713}"

echo "==========================================================="
echo " CleanYourWatch - One-Click Revert & Restore"
echo "==========================================================="
echo "Target Watch Device: $DEVICE"
echo ""

# Ensure adb is connected
if ! adb devices | grep -q "$DEVICE"; then
    echo "Connecting to $DEVICE..."
    adb connect "$DEVICE" || true
fi

python3 main.py -d "$DEVICE" restore
