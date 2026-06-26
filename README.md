# Employee Management System

A desktop application built with **Python & Tkinter** for managing employees, tracking daily attendance, and calculating monthly salaries — with IST-aware date handling and secure hashed credentials.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## Features

- **Employee Management** — Add, edit, delete, search, and export employee records
- **Attendance Tracking** — Mark daily attendance (Present/Absent), log overtime hours, export per-day CSV
- **Salary Calculation** — Auto-calculate monthly net pay based on attendance and overtime; export to CSV
- **Secure Login** — Passwords stored as salted SHA-256 hashes (never plaintext)
- **Calendar Picker** — Built-in date picker widget with month/year navigation
- **IST Date Handling** — All default dates reflect Indian Standard Time (UTC+5:30)
- **Country Code Support** — Mobile numbers support international dialing codes

---

## Screenshots

> *(Add screenshots of the Login, Employees, Attendance, and Salary tabs here)*

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- No third-party packages required — uses Python standard library only (`tkinter`, `json`, `csv`, `hashlib`, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/employee-management-system.git
cd employee-management-system

# Run the application
python main.py
```

### Default Login

| Field    | Value      |
|----------|------------|
| Username | `Admin`    |
| Password | `admin123` |

> **Important:** Change the default password immediately after first login using the **Forgot Password** link.

---

## Project Structure

```
employee-management-system/
├── main.py          # Main application (UI + logic)
├── config.py        # Secure config & hashed credential management
├── requirements.txt # Dependencies (stdlib only)
├── .gitignore       # Excludes data/ and cache files
├── LICENSE          # MIT License
└── README.md        # This file
```

Data files are stored in a `data/` directory (auto-created on first run, excluded from version control):

```
data/
├── config.json       # Hashed credentials
├── employees.json    # Employee records
├── attendance/       # Per-day attendance JSON files
└── salary/           # Exported salary CSVs
```

---

## Salary Calculation

Net pay is calculated as:

```
Per Day Rate  = Base Salary / Working Days in Month
Prorated Pay  = Per Day Rate × Days Present
Overtime Pay  = (Base Salary / 176) × Overtime Hours
Net Pay       = Prorated Pay + Overtime Pay
```

*Working days are counted as Monday–Friday only.*

---

## Security

- Passwords are hashed with **SHA-256 + random salt** via Python's `hashlib` and `secrets` modules
- The `data/` directory is excluded from Git via `.gitignore`
- No plaintext passwords are stored anywhere on disk

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## License

[MIT](LICENSE)
