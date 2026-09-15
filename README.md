# Check Writer

A modern, full-featured GNOME / Libadwaita application for writing, previewing, printing, and tracking bank checks.

![App Screenshot](/images/app.png?raw=true "Check Writer Screenshot")

---

## Features

- **WYSIWYG Live Check Preview**: Realistic, vector-rendered check preview updated in real-time as you type.
- **Legal Words Conversion Engine**: High-precision number-to-words converter supporting amounts up to trillions, cents formatting, anti-fraud security asterisks (`***`), and customizable casing.
- **Printing & PDF Export**: Native GTK Cairo vector printing (`Ctrl+P`) and direct PDF export. Supports:
  - Personal / Wallet single checks
  - Business voucher checks (Top check + 2 perforated transaction stubs)
  - 3-per-page check sheets
- **Checkbook Register & Ledger**: Local SQLite database automatically tracks all written checks with status filtering (*Issued*, *Cleared*, *Voided*), search, financial summaries, and one-click CSV export.
- **Payee Directory**: Save recurring payees with default memos, categories, and addresses for instant autofill.
- **Multi-Account & Calibration**: Configure bank account details, routing/account numbers, auto-incrementing check numbers, and printer X/Y margin calibration in Preferences.
- **Adaptive Libadwaita UI**: Built with GTK4 and Libadwaita, supporting light/dark themes, toast notifications, keyboard shortcuts, and responsive mobile/desktop layouts.

---

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl + N` | New Check / Reset Form |
| `Ctrl + S` | Save Check to Register |
| `Ctrl + P` | Print Check |
| `Ctrl + ,` | Preferences Dialog |
| `Ctrl + ?` | Keyboard Shortcuts |
| `Ctrl + Q` | Quit Application |

---

## Running and Building

### Quick Run (Development)
```bash
./run.py
```

### Running the Test Suite
```bash
python3 -m unittest discover tests
```

### Building with Meson & Ninja
```bash
meson setup _build
ninja -C _build
```

---

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later).
