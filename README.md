# Platform Jumper Game

A simple platformer game where you control a yellow square and need to avoid rising fire particles while jumping between platforms.

## Setup and Installation

1. Make sure you have Python installed (Python 3.7 or higher recommended)

2. Create a virtual environment:
   ```
   # On Windows
   python -m venv venv

   # On macOS/Linux
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```
   # On Windows
   .\venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

4. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Game

With the virtual environment activated:
```
python main.py
```

## Controls
- Left Arrow: Move left
- Right Arrow: Move right
- Space: Jump (when on a platform)
- Space (in mid-air): Double jump (only once between platforms)

## Game Rules
- You have a health bar that decreases when hit by particles or spikes
- Red triangular particles rise from the bottom
- Orange platforms are extra bouncy
- The frequency of particles increases over time
- Jump on blue/orange platforms to stay safe
- Platforms become more challenging (rotated/irregular) as you fall deeper
- Touching the side spikes causes damage
- Score increases based on how far you've fallen

## Tips
- Use bouncy platforms (orange) for higher jumps
- Save your double jump for emergencies
- Watch out for rotating platforms at deeper levels
- Keep track of your health bar above the player
- Don't get pushed into the side spikes by particles