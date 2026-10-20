# Music-Reactive LED Strip with Prismatik

A Python music visualizer for a WS2812B LED strip driven by an Arduino Nano and controlled through the Prismatik API. It captures PC audio output, changes the whole strip's colour based on the audio balance, flashes toward white on detected bass hits, and returns control to Prismatik after eight seconds of silence.

## Features

- Solid-strip colours: blue for bass-heavy audio, purple for balanced audio, red-orange for treble-heavy audio.
- Bass-hit flash that briefly blends the strip toward white.
- Brightness follows the audio volume.
- No position-based rainbow gradient.
- Automatically locks Prismatik during music and unlocks it after silence.
- Does not require changing Arduino firmware.

## Hardware and software

- Arduino Nano compatible board
- WS2812B LED strip (configured here for 118 LEDs)
- External, suitable 5 V LED power supply and common ground
- Windows PC
- Prismatik with its local API enabled
- Python 3
- Python packages: `numpy`, `soundcard`

The script uses Prismatik at `127.0.0.1:3636`. Ensure the API port and LED count match your installation.

## Setup

1. Connect and test the LED strip using your existing Arduino firmware.
2. Configure Prismatik for your Adalight-compatible controller and the correct COM port.
3. Enable Prismatik's local API and confirm it listens on port `3636`.
4. Install Python dependencies:

   ```bash
   python -m pip install numpy soundcard
   ```

5. Save `music_visualizer.py` and run:

   ```bash
   python music_visualizer.py
   ```

6. Play audio through the Windows output device selected as the default speaker.

Stop the program with `Ctrl+C`.

## Behaviour

- Audio above `SILENCE_THRESHOLD` activates music mode.
- Prismatik is locked while the script sends colours.
- Bass-heavy audio selects blue; balanced audio selects purple; treble-heavy audio selects red-orange.
- A detected bass transient briefly blends the colour toward white.
- After `SILENCE_SECONDS` of audio below the threshold, the script unlocks Prismatik so screen ambient lighting can resume.

## Configuration

Edit the constants near the top of `music_visualizer.py`:

| Constant | Purpose |
|---|---|
| `PORT` | Prismatik API port |
| `LED_COUNT` | Number of LEDs |
| `SAMPLE_RATE` | Audio capture sample rate |
| `FRAME_SIZE` | Number of audio samples per frame |
| `SILENCE_THRESHOLD` | Audio level required to enter/keep music mode |
| `SILENCE_SECONDS` | Quiet duration before returning to Prismatik |
| `BRIGHTNESS_MIN`, `BRIGHTNESS_MAX` | Music-mode brightness range |
| `FLASH_DECAY` | How quickly the bass flash fades |

If music mode activates when nothing is playing, increase `SILENCE_THRESHOLD`. If it does not activate during quiet music, lower it slightly.

## Troubleshooting

- **Cannot connect to Prismatik:** make sure Prismatik is running, its API is enabled, and the port is correct.
- **No music response:** check the default Windows output device and make sure sound is playing through it.
- **Wrong LED count:** change `LED_COUNT` to match the configured strip.
- **Colours remain too dim/bright:** adjust `BRIGHTNESS_MIN`, `BRIGHTNESS_MAX`, or the `smoothed_volume * 18` sensitivity factor.
- **Screen lighting does not resume:** stop the script cleanly with `Ctrl+C` and check Prismatik API lock/unlock support.

## Safety

Use an appropriately rated 5 V supply for the LED strip. Do not power a long LED strip directly from the Arduino's 5 V pin. Ensure the controller and LED supply share a common ground, and verify the wiring and power limits of your hardware.

## License

Choose a license before publishing if you want others to reuse or modify the project. For example, MIT is a common permissive option; only add it if you are comfortable granting those permissions.


## Automatic startup on Windows

To launch the visualizer automatically after you sign in to Windows:

1. Confirm Python's executable path. In Command Prompt, run:

   ```bat
   py -0p
   ```

2. Create `start_music_visualizer.bat` on your Desktop with the following contents (adjust paths if your installation differs):

   ```bat
   @echo off
   timeout /t 30 /nobreak >nul
   cd /d "%USERPROFILE%\OneDrive\Desktop"
   start "" "C:\Users\SPMU_\AppData\Local\Python\pythoncore-3.15-64\python.exe" "%USERPROFILE%\OneDrive\Desktop\music_visualizer.py"
   ```

3. Press `Win + R`, enter `shell:startup`, and press Enter.
4. Copy `start_music_visualizer.bat` into the Startup folder.
5. Ensure Prismatik also starts with Windows, and that its local API is enabled.
6. Restart and sign in to test. Wait around 30 seconds, then play music.

This runs after Windows sign-in, not before login. The batch file uses a machine-specific Python path; use the path reported by `py -0p` on your own PC. Keep the script and batch file in the locations referenced above, or update the paths.

To stop the visualizer, press `Ctrl+C` in its Python console window. Minimise the window if you want it to continue running.
