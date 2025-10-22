# Pi Parade

An infinite visualization of pi's digits streaming across the LED matrix in binary. Each digit (0-9) is converted to 4-bit binary and scrolls through all 64 LEDs in a mesmerizing snake pattern while pi is calculated in real-time in the background.

## Visual Legend

- **Green**: Binary 1 (active)
- **Off/Black**: Binary 0 (inactive)

## How It Works

1. **Real-time Pi Calculation**: Uses the `mpmath` library to compute pi to arbitrary precision
2. **Buffering System**: Maintains a buffer of ~1000 digits, automatically calculating more in the background when needed
3. **Binary Conversion**: Each digit (0-9) is converted to 4-bit binary (e.g., 5 → 0101)
4. **Snake Scrolling**: Bits travel from bottom-right to top-left in a zigzag pattern through all 64 pixels

## The Pattern

The snake path creates a continuous flow:
- Starts at bottom-right corner
- Zigzags up row by row (alternating left-to-right and right-to-left)
- Exits at top-left corner

This means each bit takes 64 frames to complete its journey across the matrix, creating a smooth, hypnotic flow of pi's binary representation.

## Technical Details

- **Grid size**: 8x8 (64 LEDs)
- **Calculation method**: `mpmath` library with dynamic precision
- **Update rate**: ~12.5 updates/second (0.08s per frame)
- **Buffer size**: Maintains 1000+ digits ahead of display
- **Background processing**: Separate thread calculates new digits when buffer drops below 1000 bits (250 digits)
- **Batch size**: Calculates 500 new digits (2000 bits) per batch

## Why This Is Cool

- **Truly Infinite**: Unlike pre-computed pi displays, this calculates new digits on-the-fly
- **Educational**: See the actual binary representation of pi's digits
- **Hypnotic**: The smooth scrolling and color contrast creates a mesmerizing effect
- **Mathematical Beauty**: Watching an irrational number unfold in real-time

## Performance

The background calculator is optimized to stay ahead of the display:
- Initial buffer: 1000 digits (4000 bits ≈ 5 minutes of display time at current speed)
- Calculation trigger: When buffer < 1000 bits
- Calculation time: ~1-2 seconds for 500 digits on Raspberry Pi Zero

The system is designed to never run out of pi digits, continuously computing new ones while displaying the current buffer.
