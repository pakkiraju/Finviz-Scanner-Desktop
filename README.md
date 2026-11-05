# Finviz Scanner Desktop

Desktop day-trading scanners for **Finviz Elite**. Build Finviz-style screens (Signal + filters), save presets, and open each scan in its own movable window with live CSV refresh.

Requires a [Finviz Elite](https://finviz.com/elite) subscription and API key.

## Requirements

- Windows
- [Python 3.13+](https://www.python.org/downloads/) (check **Add python.exe to PATH** when installing)
- Finviz Elite API key

## Quick start

1. Download or clone this repo.
2. Double-click **`Start Finviz Scanner Desktop.bat`**.
   - First run creates a virtual environment and installs dependencies.
3. In the app, paste your Finviz Elite API key → **Save Key**.
4. Pick a **Signal** and/or filters, then **Open Scanner**.

Your API key, saved presets, and window session live in this folder (`settings.json`, `saved_scans.json`, `session.json`) and are **not** committed to git. Updating the code does not wipe them.

## How to use

### API key

Get your key from Finviz Elite (account / API settings). Paste it at the top of the main window and click **Save Key**. The status line should show **Key saved**.

### Build a scan

1. Choose a **Signal** (e.g. Top Gainers, Top Gainers 5M, Unusual Volume, chart patterns).
2. Set filters on the Descriptive / Fundamental / Technical / News tabs. **Any** = not applied; changed filters highlight.
3. Open **Custom…** at the bottom of any numeric filter (Price, Volume, P/E, RSI, Performance, 52-Week High/Low, Gap, and more) to enter your own From/To range — same as Finviz Elite. Performance / Performance 2 also let you pick the period (1m / 2m / 5m / …).
4. Optionally set **Sort** and a **Name** for the scanner window title.
5. Click **Open Scanner** to open a live window.

Green / red text in the table follows the day’s change %. Closing the main window exits the whole app and all scanner windows.

### Session restore

When you quit, the app remembers which scanner windows were open — including size, position, monitor, stacking order, poll interval, and always-on-top — and restores them on the next launch (requires a saved API key). Move or resize a window and it is saved automatically.

### Presets

Use the **Presets** row at the top:

| Button | What it does |
|--------|----------------|
| **Open Preset** | Open the selected saved scan in a new window |
| **Edit Preset** | Load that preset into the filter editor |
| **Delete Preset** | Remove the selected preset |
| **Save Preset** | Save the current Signal + filters under a name |
| **Open Scanner** | Open a scanner from the current (unsaved) filters |
| **Reset Filters** | Clear Signal and all filters back to Any |

## Manual install (optional)

If you prefer not to use the `.bat` file:

```bat
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Project layout

```
Finviz Scanner Desktop/
  Start Finviz Scanner Desktop.bat   ← double-click to run
  main.py
  requirements.txt
  finideas/                          ← app package
  settings.json                      ← local (gitignored)
  saved_scans.json                   ← local (gitignored)
  session.json                       ← local (gitignored)
  layout.json                        ← local (gitignored)
```

## Privacy

Do not commit or share `settings.json`, `.env`, `saved_scans.json`, or `session.json` — they can contain your API key and personal setup. Those paths are listed in `.gitignore`.

## Changelog

### 2026-11-04 — Custom… on all numeric filters

- Add Finviz Elite **Custom…** From/To ranges to Price, Volume, Float, Market Cap, fundamentals (P/E, margins, …), RSI, ATR, Beta, Gap, Change, and High/Low distance filters.
- Keep Performance / Performance 2 custom periods (1m–YTD).
- High/Low Custom supports Below High / Above Low modes.

### 2026-11-04 — Session restore

- Remember open scanner windows across launches (signal, filters, sort, title).
- Restore window size, position, monitor, and stacking order.
- Persist poll interval and always-on-top; auto-save when windows move or resize.
- Document session restore in this README; ignore `session.json` in git.

### 2026-11-04 — Initial public release

- Finviz Elite CSV scanners in movable windows.
- Full Signal list including Top Gainers/Losers timeframe presets (1M–4H, AH).
- Filter builder, custom Performance periods, saved presets.
- In-app API key storage; green/red day-change coloring.
- Windows launcher: `Start Finviz Scanner Desktop.bat`.

## License

Use at your own risk. Finviz is a trademark of its respective owner; this project is not affiliated with Finviz.
