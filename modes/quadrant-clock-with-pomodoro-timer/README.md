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

## Ring Display

Each quadrant shows a ring of 12 LEDs that fill clockwise (like a clock):
- Time values are mapped to 12 positions
- Hours: Discrete LEDs (jumps between positions)
- Minutes: Discrete LEDs (jumps between positions)
- Seconds: Smooth transitions (gradual fade)
- Pomodoro: Smooth transitions (gradual fade)

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

- **Synchronized colors**: All quadrants share the same color based on Pomodoro state
- **Smooth animations**: Seconds and Pomodoro timer use gradual LED transitions
- **Auto-running timer**: No manual start/stop needed - follows the fixed schedule
- **12-hour format**: Hours displayed in 12-hour clock format
- **Ring-based display**: Each time unit shown as a circular progress indicator
