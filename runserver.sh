#!/bin/bash

echo "============================================"
echo "   Starting Celery Worker and Beat"
echo "============================================"
echo

# Activate virtual environment (if any)
# source venv/bin/activate

# Start Celery Worker
echo "Starting Celery Worker..."
nohup celery -A restserver worker \
    --pool=eventlet \
    -c 1000 \
    --loglevel=info \
    > celery_worker.log 2>&1 &

WORKER_PID=$!
echo "Celery Worker started with PID: $WORKER_PID"

# Start Celery Beat
echo "Starting Celery Beat..."
nohup celery -A restserver beat \
    --loglevel=info \
    > celery_beat.log 2>&1 &

BEAT_PID=$!
echo "Celery Beat started with PID: $BEAT_PID"

echo
echo "============================================"
echo " Celery Worker and Beat are now running"
echo "============================================"
