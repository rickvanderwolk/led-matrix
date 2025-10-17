# Quadrant Clock with Pomodoro Timer

A 4-quadrant LED matrix clock that displays hours, minutes, seconds, and an integrated Pomodoro productivity timer.

## Display Layout

The 8×8 LED matrix is divided into 4 quadrants (4×4 each):

```
┌─────────┬─────────┐
│  Hours  │ Minutes │  ← Top row
├─────────┼─────────┤
│ Seconds │Pomodoro │  ← Bottom row
└─────────┴─────────┘
```

- **Top-left**: Hours (1-12)
- **Top-right**: Minutes (0-59)
- **Bottom-left**: Seconds (0-59)
- **Bottom-right**: Pomodoro timer progress

## Column Display

Each quadrant uses a column-based layout with 12 LEDs arranged in a 4-4-2-2 pattern:
- Time values are mapped to 12 positions
- Columns fill from left to right (or right to left for mirrored quadrants)
- **Empty center**: The middle 4×4 LEDs remain unlit, creating a distinctive layout

**Pattern per quadrant:**
- Column 1: 4 LEDs
- Column 2: 4 LEDs
- Column 3: 2 LEDs
- Column 4: 2 LEDs

## Trailing Effect

All time indicators feature a smooth trailing animation:
- **Current position**: Fully bright LED
- **Trail**: Previous 5 positions gradually dim with exponential falloff (comet tail effect)
- **Past positions**: Very dim (10% brightness) to show the full progression
- **Smooth fading**: All quadrants use smooth transitions between positions

## Pomodoro Timer

The timer automatically runs on a fixed schedule:

**Schedule:**
- Starts at `:00` and `:30` of each hour
- `:00-:25` = Work session (25 minutes)
- `:25-:30` = Break (5 minutes)
- `:30-:55` = Work session (25 minutes)
- `:55-:00` = Break (5 minutes)

**Color Scheme:**
- **White** = Work session (all quadrants)
- **Purple** = Break time (all quadrants)

All quadrants use the same color simultaneously, creating a unified visual experience that indicates whether you're in a work or break period.

## Features

- **Column-based layout**: Unique 4-4-2-2 LED pattern per quadrant with empty center
- **Trailing animations**: Comet tail effect with exponential brightness falloff
- **Smooth fading**: All time indicators transition smoothly between positions
- **Synchronized colors**: All quadrants share the same color based on Pomodoro state
- **Auto-running timer**: No manual start/stop needed - follows the fixed schedule
- **12-hour format**: Hours displayed in 12-hour clock format
- **Visual depth**: Multiple brightness levels create depth and movement
