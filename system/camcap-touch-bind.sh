#!/bin/sh
# The Goodix touch controller on the 5" DSI panel is probed at boot before
# the panel has powered up, so the probe fails ("I2C communication failure:
# -5") and touch is dead until the driver is re-bound. Re-bind it here,
# retrying while the panel finishes powering up. Hardware-verified
# 2026-09-25: a manual bind after boot works every time.

DEVICE=10-005d
DRIVER=/sys/bus/i2c/drivers/Goodix-TS

for attempt in 1 2 3 4 5 6 7 8 9 10; do

    if [ -e "$DRIVER/$DEVICE" ]; then
        echo "Touchscreen bound (attempt $attempt)"
        exit 0
    fi

    # Driver module may still be loading on early attempts.
    if [ -e "$DRIVER/bind" ] && [ -e "/sys/bus/i2c/devices/$DEVICE" ]; then
        echo "$DEVICE" > "$DRIVER/bind" 2>/dev/null
    fi

    sleep 1
done

echo "Touchscreen still not bound after 10 attempts - touch will not work"
exit 1
