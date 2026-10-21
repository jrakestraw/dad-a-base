# Dad-A-Base

An Android app with nothing but dad jokes.

- `docs/jokes.json` is the joke list. It is bundled into the APK and also served by GitHub Pages as the live feed at
  https://jrakestraw.github.io/dad-a-base/jokes.json, so the app picks up new jokes without a reinstall.
- `web/index.html` is the whole app (runs in a WebView). `android/` is the thin Java shell.
- `build.ps1` builds `DadABase.apk` with the Android SDK command-line tools.
- `tools/add_jokes.py new.txt` appends jokes (one `setup | punchline` per line), skipping duplicates.
