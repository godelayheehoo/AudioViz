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
        # To get 12.288 MHz from the 25 MHz internal crystal:
        # We need PLL to be between 15x and 90x of 25MHz (375 MHz to 2250 MHz)
        # And the output divider must be an even integer (if possible) for best jitter, or just a valid integer.
        
        # Let's use an output divider of 64
        # Target PLL = 12.288 MHz * 64 = 786.432 MHz
        # PLL Multiplier = 786.432 MHz / 25 MHz = 31.45728
        # 31.45728 = 31 + (45728 / 100000) = 31 + (1429 / 3125)
        
        # Configure PLL A to 786.432 MHz
        si5351.pll_a.configure_fractional(31, 1429, 3125)
        
        # Configure CLK0 to divide PLL A by exactly 64
        si5351.clock_0.configure_integer(si5351.pll_a, 64)
        
        si5351.outputs_enabled = True
        
        target_freq = 12288000
        print(f"Success! Si5351A CLK0 is now generating {target_freq / 1_000_000} MHz.")
        return True
        
    except Exception as e:
        print(f"Error initializing Si5351A: {e}", file=sys.stderr)
        print("Please check wiring and ensure I2C is enabled.", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = setup_master_clock()
    sys.exit(0 if success else 1)
