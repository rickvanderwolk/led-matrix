# LED Matrix Visualizer

Een visualisatie tool om LED matrix applicaties te testen zonder fysieke hardware.

## Functionaliteit

Deze visualizer maakt het mogelijk om alle LED matrix modi te zien en te testen op je computer, zonder een echte LED matrix nodig te hebben. De originele scripts worden gebruikt zonder aanpassingen.

## Installatie

### Optie 1: Automatisch (aanbevolen)

Gebruik het install script dat automatisch een virtual environment aanmaakt:

```bash
./visualizer/install.sh
```

Dit maakt een virtual environment aan in `visualizer/venv/` en installeert alle dependencies.

### Optie 2: Handmatig

1. Maak een virtual environment aan:

```bash
python3 -m venv visualizer/venv
source visualizer/venv/bin/activate
```

2. Installeer de dependencies:

```bash
pip install -r visualizer/requirements.txt
```

## Gebruik

### Quick Start (aanbevolen)

Gebruik het start script dat automatisch de virtual environment activeert:

```bash
./visualizer/start.sh
```

Dit toont een interactief menu waar je een mode kunt selecteren.

Of start direct een specifieke mode:

```bash
./visualizer/start.sh evolving-square
```

### Handmatig starten

Als je liever handmatig de virtual environment activeert:

```bash
source visualizer/venv/bin/activate
python visualizer/run_mode.py
```

### Interactief menu

Start de visualizer zonder argumenten voor een interactief menu:

```bash
./visualizer/start.sh
```

Je krijgt een lijst van beschikbare modi en kunt er een selecteren.

### Directe mode selectie

Start een specifieke mode direct:

```bash
python visualizer/run_mode.py quadrant-clock-with-pomodoro-timer
```

Of gebruik het volledige pad:

```bash
python visualizer/run_mode.py modes/pixels-fighting/main.py
```

### Lijst van modi

Bekijk alle beschikbare modi:

```bash
python visualizer/run_mode.py --list
```

### Custom config

Gebruik een aangepast config bestand:

```bash
python visualizer/run_mode.py quadrant-clock-with-pomodoro-timer --config my-config.json
```

## Controls

Tijdens het draaien van de visualizer:

- **Q** - Afsluiten
- **SPACE** - Pauzeren/hervatten
- **+** of **=** - Helderheid verhogen
- **-** - Helderheid verlagen

## Hoe het werkt

1. **Mock Hardware** (`mock_hardware.py`): Vervangt de `board` en `neopixel` modules met dummy versies die LED updates onderscheppen
2. **GUI** (`gui.py`): PyGame-based visualisatie van de 8x8 LED matrix
3. **Runner** (`run_mode.py`): Laadt de originele mode scripts en verbindt ze met de visualizer

De originele scripts worden ongewijzigd uitgevoerd - ze denken dat ze met echte hardware praten, maar in plaats daarvan worden de LED updates naar de visualizer gestuurd.

## Ondersteunde Modi

Alle bestaande modi worden ondersteund:

- quadrant-clock-with-pomodoro-timer
- pixels-fighting
- led-sort
- evolving-square
- ntfy-sh
- En alle andere modes in de `modes/` directory

## Technische Details

- **8x8 LED Matrix**: Standaard weergave
- **60 FPS**: Soepele animaties
- **Brightness Control**: Simulatie van helderheid aanpassingen
- **Threading**: Mode scripts draaien in een aparte thread voor responsiviteit
