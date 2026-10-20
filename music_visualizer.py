import socket
import time
import numpy as np
import soundcard as sc

HOST = "127.0.0.1"
PORT = 3636
LED_COUNT = 118
SAMPLE_RATE = 48000
FRAME_SIZE = 2048
SILENCE_THRESHOLD = 0.003
SILENCE_SECONDS = 8

BRIGHTNESS_MIN = 8
BRIGHTNESS_MAX = 255
FLASH_DECAY = 0.72

sock = None
locked = False
last_sound = time.monotonic()

bass_envelope = 0.0
previous_bass = 0.0
flash = 0.0
smoothed_volume = 0.0
last_color = (100, 0, 255)


def drain_replies():
    """Read available API replies without blocking."""
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                break
    except (BlockingIOError, socket.timeout):
        pass


def control_command(command):
    """Send a Prismatik API command and read its response."""
    sock.setblocking(True)
    sock.settimeout(0.5)

    try:
        sock.sendall((command + "\n").encode())
        result = b""

        while True:
            try:
                part = sock.recv(4096)
                if not part:
                    break
                result += part
            except socket.timeout:
                break

        return result.decode(errors="replace").strip()
    finally:
        sock.setblocking(False)


def acquire_control():
    """Lock Prismatik while music mode is active."""
    global locked

    if not locked:
        print("\nMusic detected: music mode ON")
        print("Lock:", control_command("lock"))
        print("Lighting:", control_command("setstatus:on"))
        print("Brightness:", control_command("setbrightness:100"))
        locked = True


def release_control():
    """Unlock Prismatik so screen ambient lighting can resume."""
    global locked

    if locked:
        print("\n8 seconds of silence: returning to Prismatik")
        print("Unlock:", control_command("unlock"))
        locked = False


def audio_to_colors(audio):
    """Convert one audio frame into a solid, music-reactive LED colour."""
    global bass_envelope, previous_bass, flash
    global smoothed_volume, last_color

    mono = np.mean(audio, axis=1)
    mono = mono - np.mean(mono)
    rms = float(np.sqrt(np.mean(mono ** 2)))

    windowed = mono * np.hanning(len(mono))
    spectrum = np.abs(np.fft.rfft(windowed))
    frequencies = np.fft.rfftfreq(len(mono), 1 / SAMPLE_RATE)

    def band_energy(low, high):
        mask = (frequencies >= low) & (frequencies < high)
        if not np.any(mask):
            return 0.0
        return float(np.sqrt(np.mean(spectrum[mask] ** 2)))

    bass = band_energy(35, 150)
    mids = band_energy(150, 2500)
    treble = band_energy(2500, 10000)

    # Detect sudden increases in bass energy.
    bass_envelope = 0.55 * bass_envelope + 0.45 * bass
    bass_rise = bass_envelope - previous_bass
    previous_bass = bass_envelope

    if bass_envelope > 0.12 and bass_rise > 0.025:
        flash = 1.0
    else:
        flash *= FLASH_DECAY

    # Pick one colour for the whole strip based on the sound balance.
    total = bass + mids + treble

    if total > 1e-8:
        bass_share = bass / total
        treble_share = treble / total

        if bass_share > 0.48:
            target_color = (25, 65, 255)       # Blue for bass-heavy audio
        elif treble_share > 0.42:
            target_color = (255, 30, 10)       # Red-orange for treble
        else:
            target_color = (145, 0, 255)       # Purple for balanced audio
    else:
        target_color = last_color

    last_color = target_color

    # Smooth volume changes while retaining a responsive feel.
    smoothed_volume = 0.65 * smoothed_volume + 0.35 * rms
    volume_level = np.clip(smoothed_volume * 18, 0.0, 1.0)

    brightness = int(
        BRIGHTNESS_MIN
        + (BRIGHTNESS_MAX - BRIGHTNESS_MIN) * volume_level ** 0.65
    )

    r, g, b = target_color

    # Blend toward white briefly when a bass hit is detected.
    white_mix = min(0.90, flash * 0.85)
    r = int((r * (1 - white_mix) + 255 * white_mix) * brightness / 255)
    g = int((g * (1 - white_mix) + 255 * white_mix) * brightness / 255)
    b = int((b * (1 - white_mix) + 255 * white_mix) * brightness / 255)

    # Send the same RGB value to all LEDs to avoid a gradient/rainbow wheel.
    led_data = ";".join(
        f"{i}-{r},{g},{b}"
        for i in range(1, LED_COUNT + 1)
    )
    return "setcolor:" + led_data + ";"


def main():
    global sock, last_sound

    speaker = sc.default_speaker()
    loopback = sc.get_microphone(
        id=str(speaker.name),
        include_loopback=True
    )

    print("Audio output:", speaker.name)
    sock = socket.create_connection((HOST, PORT), timeout=3)
    sock.settimeout(1)
    print(sock.recv(4096).decode(errors="replace").strip())
    sock.setblocking(False)

    print("Music visualizer ready.")
    print("Colour changes with music; bass hits flash white.")
    print(f"{SILENCE_SECONDS} seconds of silence returns control to Prismatik.")
    print("Press Ctrl+C to stop.")

    with loopback.recorder(
        samplerate=SAMPLE_RATE,
        channels=2
    ) as recorder:
        while True:
            audio = recorder.record(numframes=FRAME_SIZE)
            volume = float(np.sqrt(np.mean(audio ** 2)))
            now = time.monotonic()

            if volume >= SILENCE_THRESHOLD:
                last_sound = now
                acquire_control()

                if locked:
                    sock.sendall((audio_to_colors(audio) + "\n").encode())
                    drain_replies()

            elif locked and now - last_sound >= SILENCE_SECONDS:
                release_control()

            time.sleep(0.008)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping visualizer.")
    except Exception as exc:
        print("\nVisualizer error:", exc)
    finally:
        if sock:
            try:
                release_control()
            except Exception:
                pass
            sock.close()
        print("Visualizer closed.")
