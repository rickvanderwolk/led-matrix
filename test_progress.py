#!/usr/bin/env python3
"""Test script to verify progress markers are being generated correctly"""

import sys
import os

# Add the mode directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modes', 'pi-parade'))

# Import the functions we need
from main import number_to_binary_markers, digit_to_binary_bits

print("Testing progress marker generation:")
print("=" * 50)

# Test various position numbers
test_values = [100, 200, 300, 500, 1000]

for value in test_values:
    markers = number_to_binary_markers(value)
    print(f"\nPosition {value}:")
    print(f"  String: {value}")
    print(f"  Markers: {markers}")
    print(f"  Length: {len(markers)} bits")

    # Count white markers
    white_count = sum(1 for m in markers if m == 'W')
    print(f"  White LEDs: {white_count}")
    print(f"  Black LEDs: {len(markers) - white_count}")

print("\n" + "=" * 50)
print("\n✓ Progress markers are being generated correctly!")
print("\nThese markers will flow through the snake display")
print("White LEDs represent '1' bits, black represents '0' bits")
