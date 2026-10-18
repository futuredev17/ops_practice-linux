#!/bin/bash
echo "=== System Check ==="
echo "Disk Usage: $(df -h | grep '/$' | awk '{print $5}')"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2*100}')"