# شاشة Raspberry Pi Touch Display 2 — تركيب واختبار

- الشاشة 7 بوصة، native 720×1280 Portrait. Raspberry Pi 5 needs the supplied
  22-way ↔15-way FFC and GPIO power cable; follow official Raspberry Pi hardware docs.
- Raspberry Pi OS desktop: Preferences → Control Centre → Screens → rotate.
- The Python app uses desktop fullscreen (`F11` toggles; `Esc` exits fullscreen).
- Verify touch alignment after rotation, audio output, camera permissions and Pi temperature.
- If landscape at 1280×720 is crowded, use portrait orientation; dynamic responsive
  enhancements and physical testing should be completed on the real display.
- Use a suitable 5V/5A-rated Raspberry Pi 5 PSU as recommended by Raspberry Pi;
  display draws from Pi GPIO and has no separate supply.

Official docs: https://www.raspberrypi.com/documentation/accessories/touch-display-2.html
