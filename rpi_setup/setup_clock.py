#!/usr/bin/env python3
"""
setup_clock.py

Initializes the Si5351A clock generator to output a precise 12.288 MHz
master clock signal for the PCM1808 ADC on a Raspberry Pi.
"""

import sys
import board
import busio
import adafruit_si5351

def setup_master_clock():
    print("Initializing Si5351A Clock Generator...")
    
    try:
        # Initialize I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Initialize the Si5351
        si5351 = adafruit_si5351.SI5351(i2c)
        
        # Set CLK0 to exactly 12.288 MHz
        # (256 * 48kHz sampling rate)
        target_freq = 12288000
        si5351.clock_0.configure_integer(si5351.pll_a, target_freq)
        si5351.outputs_enabled = True
        
        print(f"Success! Si5351A CLK0 is now generating {target_freq / 1_000_000} MHz.")
        return True
        
    except Exception as e:
        print(f"Error initializing Si5351A: {e}", file=sys.stderr)
        print("Please check wiring and ensure I2C is enabled.", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = setup_master_clock()
    sys.exit(0 if success else 1)
