#!/bin/bash

# --- Configuration ---
RECEIVER_IP="127.0.0.1"
MESSAGE_FILE="./pg76895.txt"
TAU_VALUES=(5 10 20 30 40 50 100)
BASE_PORT=3330

echo "--- Starting Data Generation Experiments ---"

# Launch receivers
for i in ${!TAU_VALUES[@]}; do
    PORT=$((BASE_PORT + i + 1))
    OUTPUT_FILE="timings_$((i + 1)).csv"
    ./receiver -log ${PORT} ${OUTPUT_FILE} &
done

sleep 5

# Launch senders
for i in ${!TAU_VALUES[@]}; do
    TAU=${TAU_VALUES[$i]}
    TWO_TAU=$((TAU * 2))
    PORT=$((BASE_PORT + i + 1))
    ./sender ${RECEIVER_IP} ${PORT} -f ${MESSAGE_FILE} ${TAU} ${TWO_TAU} &
done

wait

echo "--- All sender processes finished ---"
echo "Receivers are still running; stop them with: killall receiver"

