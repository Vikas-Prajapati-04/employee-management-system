import json
import os
import re
import csv
import calendar
import hashlib
import secrets
from datetime import datetime, date, timedelta, timezone
import socket
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config import load_config, save_config

# ---------------------- Storage Helpers ----------------------

DATA_DIR = "data"
EMP_FILE = os.path.join(DATA_DIR, "employees.json")
ATT_DIR = os.path.join(DATA_DIR, "attendance")
SAL_DIR = os.path.join(DATA_DIR, "salary")


def get_current_date_in_india():
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = utc_now + ist_offset
    return ist_now.strftime("%Y-%m-%d")


DEFAULT_DATE_STR = get_current_date_in_india()


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ATT_DIR, exist_ok=True)
    os.makedirs(SAL_DIR, exist_ok=True)
    if not os.path.exists(EMP_FILE):
        with open(EMP_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def load_employees():
    ensure_dirs()
    try:
        with open(EMP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_employees(records):
    ensure_dirs()
    with open(EMP_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def attendance_path(day_str):
    return os.path.join(ATT_DIR, f"{day_str}.json")


def load_attendance(day_str):
    ensure_dirs()
    path = attendance_path(day_str)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_attendance(day_str, rows):
    ensure_dirs()
    with open(attendance_path(day_str), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def export_csv(path, headers, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
    return path

# ---------------------- Password Helpers ----------------------

def hash_password(password: str, salt: str = None):
    """Return (salt, hashed) using SHA-256 + salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, hashed


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    _, computed = hash_password(password, salt)
    return computed == stored_hash

# ---------------------- Validators & Utils ----------------------

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_date(s):
    if not DATE_RE.match(s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_month(s):
    if not MONTH_RE.match(s):
        return False
    y, m = map(int, s.split("-"))
    return 1 <= m <= 12 and 1900 <= y <= 3000


def get_host_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


def month_days_iter(year, month):
    d1 = date(year, month, 1)
    _, last = calendar.monthrange(year, month)
    for i in range(last):
        yield (d1 + timedelta(days=i)).strftime("%Y-%m-%d")


def business_days_in_month(year, month):
    cnt = 0
    for d in month_days_iter(year, month):
        dt = datetime.strptime(d, "%Y-%m-%d").date()
        if dt.weekday() < 5:
            cnt += 1
    return cnt

# ---------------------- Calendar Picker ----------------------

class CalendarPicker(tk.Toplevel):
    def __init__(self, master, variable, year=None, month=None):
        super().__init__(master)
        self.transient(master)
        self.title("Select Date")
        self.resizable(False, False)
        self.variable = variable
        current_date = datetime.strptime(get_current_date_in_india(), "%Y-%m-%d")
        self.year = year or current_date.year
        self.month = month or current_date.month
        self._build()
        self.grab_set()

    def _build(self):
        hdr = ttk.Frame(self)
        hdr.pack(padx=8, pady=6)
        self.prev = ttk.Button(hdr, text="<", width=3, command=self._prev_month)
        self.prev.grid(row=0, column=1)
        self.title_lbl = ttk.Label(hdr, text="", width=18, anchor="center")
        self.title_lbl.grid(row=0, column=2, columnspan=2)
        self.next = ttk.Button(hdr, text=">", width=3, command=self._next_month)
        self.next.grid(row=0, column=4)

        year_frame = ttk.Frame(self)
        year_frame.pack(pady=6)
        ttk.Label(year_frame, text="Year:").pack(side="left", padx=2)
        current_date = datetime.strptime(get_current_date_in_india(), "%Y-%m-%d")
        current_year = current_date.year
        years = list(range(current_year - 20, current_year + 11))
        self.year_var = tk.IntVar(value=self.year)
        self.year_combo = ttk.Combobox(year_frame, textvariable=self.year_var, values=years, width=8, state="readonly")
        self.year_combo.pack(side="left", padx=2)
        self.year_combo.bind("<<ComboboxSelected>>", self._year_selected)

        self.cal_frame = ttk.Frame(self, padding=6)
        self.cal_frame.pack()
        self._draw()

    def _draw(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()
        self.title_lbl.config(text=f"{calendar.month_name[self.month]} {self.year}")
        wkdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for c, wd in enumerate(wkdays):
            ttk.Label(self.cal_frame, text=wd, width=4).grid(row=0, column=c)
        mc = calendar.monthcalendar(self.year, self.month)
        for r, week in enumerate(mc, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.cal_frame, text="", width=4).grid(row=r, column=c)
                else:
                    ttk.Button(self.cal_frame, text=str(day), width=4,
                               command=lambda d=day: self._select(d)).grid(row=r, column=c, padx=1, pady=1)

    def _select(self, day):
        self.variable.set(f"{self.year:04d}-{self.month:02d}-{day:02d}")
        self.destroy()

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.year_var.set(self.year)
        self._draw()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.year_var.set(self.year)
        self._draw()

    def _year_selected(self, event):
        self.year = self.year_var.get()
        self._draw()

# ---------------------- Login Window ----------------------

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Login")
        self.geometry("360x260")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.on_success = on_success
        self.forgot_window = None
        self.cfg = load_config()

        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Employee Management System",
                  font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))

        form = ttk.Frame(container)
        form.pack(fill="x", pady=4)
        ttk.Label(form, text="Username", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.username = ttk.Entry(form, width=25)
        self.username.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Label(form, text="Password", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.password = ttk.Entry(form, show="*", width=25)
        self.password.grid(row=1, column=1, sticky="ew", pady=6)
        form.columnconfigure(1, weight=1)

        self.forgot_btn = tk.Label(container, text="Forgot Password?", fg="blue",
                                   cursor="hand2", font=("Segoe UI", 9))
        self.forgot_btn.pack(pady=(2, 10))
        self.forgot_btn.bind("<Button-1>", self.show_forgot_password)

        ttk.Button(container, text="Login", command=self.try_login, width=15).pack(pady=8)

        current_date_india = get_current_date_in_india()
        ttk.Label(container, text=f"Date in India: {current_date_india}",
                  font=("Segoe UI", 9)).pack(pady=(5, 0))

        self.username.focus_set()
        self.bind("<Return>", lambda e: self.try_login())

    def try_login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        stored_salt = self.cfg.get("password_salt", "")
        stored_hash = self.cfg.get("password_hash", "")

        if u == "Admin" and verify_password(p, stored_salt, stored_hash):
            self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def show_forgot_password(self, event=None):
        if self.forgot_window is not None and self.forgot_window.winfo_exists():
            self.forgot_window.lift()
            return

        self.forgot_window = tk.Toplevel(self)
        self.forgot_window.title("Reset Password")
        self.forgot_window.geometry("350x280")
        self.forgot_window.resizable(False, False)
        self.forgot_window.update_idletasks()
        w, h = self.forgot_window.winfo_width(), self.forgot_window.winfo_height()
        x = (self.forgot_window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.forgot_window.winfo_screenheight() // 2) - (h // 2)
        self.forgot_window.geometry(f"{w}x{h}+{x}+{y}")

        container = ttk.Frame(self.forgot_window, padding=20)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Reset Password", font=("Segoe UI", 12, "bold")).pack(pady=(0, 15))
        ttk.Label(container, text="Enter your username:").pack(anchor="w", pady=2)
        self.fp_username = ttk.Entry(container, width=25)
        self.fp_username.pack(fill="x", pady=5)
        ttk.Label(container, text="Enter new password (min 6 chars):").pack(anchor="w", pady=2)
        self.fp_new_password = ttk.Entry(container, show="*", width=25)
        self.fp_new_password.pack(fill="x", pady=5)
        ttk.Label(container, text="Confirm new password:").pack(anchor="w", pady=2)
        self.fp_confirm_password = ttk.Entry(container, show="*", width=25)
        self.fp_confirm_password.pack(fill="x", pady=5)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Reset Password", command=self.reset_password).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.forgot_window.destroy).pack(side="left", padx=5)

    def reset_password(self):
        username = self.fp_username.get().strip()
        new_password = self.fp_new_password.get().strip()
        confirm_password = self.fp_confirm_password.get().strip()

        if not username or not new_password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        if username != "Admin":
            messagebox.showerror("Error", "Only the Admin user can reset the password.")
            return
        if len(new_password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long.")
            return
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        salt, hashed = hash_password(new_password)
        self.cfg["password_salt"] = salt
        self.cfg["password_hash"] = hashed
        save_config(self.cfg)

        if self.forgot_window and self.forgot_window.winfo_exists():
            self.forgot_window.destroy()
            self.forgot_window = None
        messagebox.showinfo("Success", "Password has been reset successfully!")

    def _on_close(self):
        self.master.destroy()

# ---------------------- Employees Tab ----------------------

class EmployeesTab(ttk.Frame):
    COLS = ("Emp Id", "Name", "Department", "Role", "Base Salary", "Join Date", "Phone", "Email")

    COUNTRY_CODES = [
        "+1", "+7", "+20", "+27", "+33", "+34", "+39", "+41", "+44", "+46",
        "+47", "+48", "+49", "+52", "+54", "+55", "+57", "+60", "+61", "+62",
        "+63", "+64", "+65", "+66", "+81", "+82", "+84", "+86", "+90", "+91",
        "+92", "+93", "+94", "+95", "+98", "+212", "+213", "+216", "+218",
        "+234", "+249", "+254", "+255", "+256", "+880", "+966", "+971", "+972",
        "+977", "+992", "+994", "+995", "+996", "+998",
    ]

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.records = load_employees()
        self._build_ui()
        self._refresh_tree(self.records)

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Employee Management", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(header, text=f"Date (IST): {get_current_date_in_india()}",
                  font=("Segoe UI", 9)).pack(side="right")

        search_box = ttk.Frame(self)
        search_box.pack(fill="x", pady=(0, 8))
        ttk.Label(search_box, text="Search").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        ttk.Entry(search_box, textvariable=self.search_var, width=25).pack(side="left")
        ttk.Button(search_box, text="Go", command=self.on_search).pack(side="left", padx=6)
        ttk.Button(search_box, text="Export CSV", command=self.on_export).pack(side="left", padx=6)
        ttk.Button(search_box, text="Delete Selected", command=self.on_delete_selected).pack(side="left", padx=6)

        form = ttk.LabelFrame(self, text="Add / Edit Employee")
        form.pack(fill="x", pady=8)

        self.emp_id = tk.StringVar()
        self.name = tk.StringVar()
        self.dept = tk.StringVar()
        self.role = tk.StringVar()
        self.base = tk.StringVar()
        self.join_date = tk.StringVar(value=get_current_date_in_india())
        self.phone = tk.StringVar()
        self.email = tk.StringVar()
        self.country_code_var = tk.StringVar(value="+91")

        vcmd_digits = (self.register(lambda P: P.isdigit() or P == ""), "%P")
        vcmd_decimal = (self.register(lambda P: P == "" or (P.count(".") <= 1 and all(c.isdigit() or c == "." for c in P))), "%P")
        vcmd_phone = (self.register(lambda P: P.isdigit() or P == ""), "%P")

        r1 = ttk.Frame(form); r1.pack(fill="x", pady=4)
        ttk.Label(r1, text="Employee ID*").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(r1, textvariable=self.emp_id, width=18, validate="key", validatecommand=vcmd_digits).grid(row=0, column=1, sticky="w")
        ttk.Label(r1, text="Name*").grid(row=0, column=2, sticky="w", padx=(12, 6))
        ttk.Entry(r1, textvariable=self.name, width=20).grid(row=0, column=3, sticky="ew")

        r2 = ttk.Frame(form); r2.pack(fill="x", pady=4)
        ttk.Label(r2, text="Department").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(r2, textvariable=self.dept, width=20).grid(row=0, column=1, sticky="ew")
        ttk.Label(r2, text="Role").grid(row=0, column=2, sticky="w", padx=(12, 6))
        ttk.Entry(r2, textvariable=self.role, width=20).grid(row=0, column=3, sticky="ew")

        r3 = ttk.Frame(form); r3.pack(fill="x", pady=4)
        ttk.Label(r3, text="Base Salary*").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(r3, textvariable=self.base, validate="key", validatecommand=vcmd_decimal).grid(row=0, column=1, sticky="ew")
        ttk.Label(r3, text="Join Date").grid(row=0, column=2, sticky="w", padx=(12, 6))
        jd = ttk.Frame(r3); jd.grid(row=0, column=3, sticky="ew")
        ttk.Entry(jd, textvariable=self.join_date, width=12).pack(side="left", fill="x", expand=True)
        ttk.Button(jd, text="📅", command=lambda: CalendarPicker(self, self.join_date)).pack(side="left", padx=(3, 0))

        r4 = ttk.Frame(form); r4.pack(fill="x", pady=4)
        ttk.Label(r4, text="Mobile No*").grid(row=0, column=0, sticky="w", padx=(0, 6))
        pf = ttk.Frame(r4); pf.grid(row=0, column=1, sticky="ew")
        ttk.Combobox(pf, textvariable=self.country_code_var, values=self.COUNTRY_CODES,
                     width=6, state="readonly").pack(side="left", padx=(0, 5))
        ttk.Entry(pf, textvariable=self.phone, validate="key",
                  validatecommand=vcmd_phone, width=14).pack(side="left", fill="x", expand=True)
        ttk.Label(r4, text="Email").grid(row=0, column=2, sticky="w", padx=(12, 6))
        ttk.Entry(r4, textvariable=self.email, width=20).grid(row=0, column=3, sticky="ew")

        for frm in (r1, r2, r3, r4):
            frm.columnconfigure(3, weight=1)

        btns = ttk.Frame(form); btns.pack(fill="x", pady=(6, 2))
        ttk.Button(btns, text="Save New", command=self.on_save_new).pack(side="left")
        ttk.Button(btns, text="Update", command=self.on_update).pack(side="left", padx=6)
        ttk.Button(btns, text="Clear", command=self.clear_form).pack(side="left")

        table = ttk.Frame(self); table.pack(fill="both", expand=True, pady=(8, 0))
        self.tree = ttk.Treeview(table, columns=self.COLS, show="headings", height=10)
        for c in self.COLS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=110, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

    def _refresh_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=(
                r.get("emp_id", ""), r.get("name", ""), r.get("department", ""),
                r.get("role", ""), r.get("base_salary", ""), r.get("join_date", ""),
                r.get("phone", ""), r.get("email", ""),
            ))

    def on_search(self):
        q = self.search_var.get().strip().lower()
        if not q:
            self._refresh_tree(self.records)
            return
        self._refresh_tree([r for r in self.records if any(
            q in str(r.get(k, "")).lower() for k in ("emp_id", "name", "department", "role")
        )])

    def on_export(self):
        if not self.records:
            messagebox.showinfo("Export", "No employees to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="employees.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path: return
        headers = ["Emp Id", "Name", "Department", "Role", "Base Salary", "Join Date", "Phone", "Email"]
        rows = [{"Emp Id": r.get("emp_id", ""), "Name": r.get("name", ""), "Department": r.get("department", ""),
                 "Role": r.get("role", ""), "Base Salary": r.get("base_salary", ""),
                 "Join Date": r.get("join_date", ""), "Phone": r.get("phone", ""), "Email": r.get("email", "")}
                for r in self.records]
        export_csv(path, headers, rows)
        messagebox.showinfo("Export", f"Exported to:\n{path}")

    def _read_form(self):
        phone_number = self.phone.get().strip()
        country_code = self.country_code_var.get().strip()
        full_phone = f"{country_code}{phone_number}" if phone_number else ""
        rec = {
            "emp_id": self.emp_id.get().strip(),
            "name": self.name.get().strip(),
            "department": self.dept.get().strip(),
            "role": self.role.get().strip(),
            "base_salary": self.base.get().strip(),
            "join_date": self.join_date.get().strip(),
            "phone": full_phone,
            "email": self.email.get().strip(),
        }
        if not rec["emp_id"] or not rec["emp_id"].isdigit():
            raise ValueError("Employee ID is required and must be numeric.")
        if not rec["name"]:
            raise ValueError("Name is required.")
        try:
            bs = float(rec["base_salary"])
            if bs < 0: raise ValueError
        except:
            raise ValueError("Base Salary must be a positive number.")
        if rec["join_date"] and not valid_date(rec["join_date"]):
            raise ValueError("Join Date must be in YYYY-MM-DD format.")
        if rec["email"] and not EMAIL_RE.match(rec["email"]):
            raise ValueError("Email format is invalid.")
        if phone_number and not phone_number.isdigit():
            raise ValueError("Phone number must contain digits only.")
        return rec

    def clear_form(self):
        for var in (self.emp_id, self.name, self.dept, self.role, self.base, self.phone, self.email):
            var.set("")
        self.join_date.set(get_current_date_in_india())
        self.country_code_var.set("+91")
        self.tree.selection_remove(self.tree.selection())

    def on_save_new(self):
        try:
            rec = self._read_form()
        except ValueError as e:
            messagebox.showerror("Validation", str(e))
            return
        if any(r["emp_id"] == rec["emp_id"] for r in self.records):
            messagebox.showerror("Duplicate", "Employee ID already exists.")
            return
        rec["base_salary"] = float(rec["base_salary"])
        self.records.append(rec)
        save_employees(self.records)
        self._refresh_tree(self.records)
        messagebox.showinfo("Saved", "Employee saved successfully.")
        self.clear_form()

    def on_update(self):
        try:
            rec = self._read_form()
        except ValueError as e:
            messagebox.showerror("Validation", str(e))
            return
        idx = next((i for i, r in enumerate(self.records) if r["emp_id"] == rec["emp_id"]), None)
        if idx is None:
            messagebox.showerror("Not Found", "Employee ID not found. Use 'Save New' to add.")
            return
        rec["base_salary"] = float(rec["base_salary"])
        self.records[idx] = rec
        save_employees(self.records)
        self._refresh_tree(self.records)
        messagebox.showinfo("Updated", "Employee updated successfully.")
        self.clear_form()

    def on_delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select at least one row.")
            return
        ids = [self.tree.item(it, "values")[0] for it in sel if self.tree.item(it, "values")]
        if not ids: return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(ids)} employee(s)? This cannot be undone."):
            return
        self.records = [r for r in self.records if r.get("emp_id") not in ids]
        save_employees(self.records)
        self._refresh_tree(self.records)
        self.clear_form()

    def on_tree_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        self.emp_id.set(vals[0])
        self.name.set(vals[1])
        self.dept.set(vals[2])
        self.role.set(vals[3])
        self.base.set(str(vals[4]))
        self.join_date.set(vals[5])
        phone_value = vals[6]
        matched = False
        if phone_value:
            for code in sorted(self.COUNTRY_CODES, key=len, reverse=True):
                if phone_value.startswith(code):
                    self.country_code_var.set(code)
                    self.phone.set(phone_value[len(code):])
                    matched = True
                    break
        if not matched:
            self.country_code_var.set("+91")
            self.phone.set(phone_value)
        self.email.set(vals[7])

# ---------------------- Attendance Tab ----------------------

class AttendanceTab(ttk.Frame):
    COLS = ("Emp_Id", "Name", "Status (P/A)", "IP", "Overtime Hours")

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.date_str = tk.StringVar(value=get_current_date_in_india())
        self.rows = []
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self); header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Attendance", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(header, text=f"Date (IST): {get_current_date_in_india()}",
                  font=("Segoe UI", 9)).pack(side="right")

        bar = ttk.Frame(self); bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Date (YYYY-MM-DD):").pack(side="left")
        ttk.Entry(bar, textvariable=self.date_str, width=12).pack(side="left", padx=6)
        ttk.Button(bar, text="📅", command=lambda: CalendarPicker(self, self.date_str)).pack(side="left")
        ttk.Button(bar, text="Load", command=self.on_load).pack(side="left", padx=6)
        ttk.Button(bar, text="Mark All Present", command=lambda: self.mark_all("P")).pack(side="left", padx=6)
        ttk.Button(bar, text="Mark All Absent", command=lambda: self.mark_all("A")).pack(side="left")
        ttk.Button(bar, text="Export CSV", command=self.on_export).pack(side="left", padx=6)

        table = ttk.Frame(self); table.pack(fill="both", expand=True, pady=(8, 6))
        self.tree = ttk.Treeview(table, columns=self.COLS, show="headings", height=11)
        for c in self.COLS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=180 if c == "Name" else 120, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

        editor = ttk.LabelFrame(self, text="Edit Selected")
        editor.pack(fill="x", pady=(6, 2))
        self.sel_emp_id = tk.StringVar()
        self.sel_name = tk.StringVar()
        self.sel_status = tk.StringVar()
        self.sel_ip = tk.StringVar(value=get_host_ip())
        self.sel_ot = tk.StringVar(value="0")

        r1 = ttk.Frame(editor); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Emp ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(r1, textvariable=self.sel_emp_id, state="readonly", width=16).grid(row=0, column=1, padx=(6, 12))
        ttk.Label(r1, text="Name").grid(row=0, column=2, sticky="w")
        ttk.Entry(r1, textvariable=self.sel_name, state="readonly").grid(row=0, column=3, sticky="ew", padx=(6, 12))
        r1.columnconfigure(3, weight=1)

        r2 = ttk.Frame(editor); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="Status (P/A)").grid(row=0, column=0, sticky="w")
        ttk.Combobox(r2, textvariable=self.sel_status, values=("P", "A"), width=8).grid(row=0, column=1, padx=(6, 12))
        ttk.Label(r2, text="IP").grid(row=0, column=2, sticky="w")
        ttk.Entry(r2, textvariable=self.sel_ip, width=16).grid(row=0, column=3, padx=(6, 12))
        ttk.Label(r2, text="Overtime Hours").grid(row=0, column=4, sticky="w")
        vcmd_ot = (self.register(lambda P: P == "" or P.replace(".", "", 1).isdigit()), "%P")
        ttk.Entry(r2, textvariable=self.sel_ot, width=10, validate="key",
                  validatecommand=vcmd_ot).grid(row=0, column=5, padx=(6, 12))

        btn_frame = ttk.Frame(editor); btn_frame.pack(side="left", padx=6, pady=(4, 6))
        ttk.Button(btn_frame, text="Save Row", command=self.on_save_selected).pack(side="left")
        ttk.Button(btn_frame, text="Save All to File", command=self.on_save_all).pack(side="left", padx=6)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_load(self):
        day = self.date_str.get().strip()
        if not valid_date(day):
            messagebox.showerror("Date", "Please enter a valid date in YYYY-MM-DD format.")
            return
        existing = {r["emp_id"]: r for r in load_attendance(day)}
        emps = load_employees()
        self.rows = [{
            "Emp_Id": e.get("emp_id", ""),
            "Name": e.get("name", ""),
            "Status (P/A)": existing.get(e.get("emp_id", ""), {}).get("status", "A"),
            "IP": existing.get(e.get("emp_id", ""), {}).get("ip", get_host_ip()),
            "Overtime Hours": existing.get(e.get("emp_id", ""), {}).get("overtime", 0),
        } for e in emps]
        self._refresh_tree()
        messagebox.showinfo("Loaded", f"Attendance loaded for {day}.")

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            self.tree.insert("", "end", values=(
                r["Emp_Id"], r["Name"], r["Status (P/A)"], r["IP"], r["Overtime Hours"]
            ))

    def mark_all(self, status):
        if not self.rows: return
        for r in self.rows:
            r["Status (P/A)"] = status
        self._refresh_tree()

    def on_tree_select(self, _evt):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        self.sel_emp_id.set(vals[0])
        self.sel_name.set(vals[1])
        self.sel_status.set(vals[2])
        self.sel_ip.set(vals[3])
        self.sel_ot.set(str(vals[4]))

    def on_save_selected(self):
        emp_id = self.sel_emp_id.get()
        if not emp_id: return
        try:
            ot = float(self.sel_ot.get())
            if ot < 0: raise ValueError
        except:
            messagebox.showerror("Overtime", "Overtime Hours must be a non-negative number.")
            return
        for r in self.rows:
            if r["Emp_Id"] == emp_id:
                r["Status (P/A)"] = (self.sel_status.get() or "A").upper()[0]
                r["IP"] = self.sel_ip.get().strip() or get_host_ip()
                r["Overtime Hours"] = ot
                break
        self._refresh_tree()
        messagebox.showinfo("Saved", "Row updated (not yet written to file — click 'Save All to File').")

    def on_save_all(self):
        day = self.date_str.get().strip()
        if not valid_date(day):
            messagebox.showerror("Date", "Please enter a valid date in YYYY-MM-DD format.")
            return
        persist = [{
            "emp_id": r["Emp_Id"], "name": r["Name"], "status": r["Status (P/A)"],
            "ip": r["IP"], "overtime": float(r["Overtime Hours"]) if str(r["Overtime Hours"]).strip() else 0.0
        } for r in self.rows]
        save_attendance(day, persist)
        messagebox.showinfo("Saved", f"Attendance saved for {day}.")

    def on_export(self):
        day = self.date_str.get().strip()
        if not valid_date(day):
            messagebox.showerror("Date", "Please enter a valid date in YYYY-MM-DD format.")
            return
        rows = load_attendance(day)
        if not rows:
            messagebox.showinfo("Export", f"No attendance saved for {day}.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            initialfile=f"attendance-{day}.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path: return
        export_csv(path, ["emp_id", "name", "status", "ip", "overtime"], rows)
        messagebox.showinfo("Export", f"Exported to:\n{path}")

# ---------------------- Salary Tab ----------------------

class SalaryTab(ttk.Frame):
    COLS = ("Emp_Id", "Name", "Month", "Base Salary", "Working Days",
            "Present", "Absent", "Overtime Hours", "Net Pay")

    def __init__(self, master):
        super().__init__(master, padding=10)
        current_date = datetime.strptime(get_current_date_in_india(), "%Y-%m-%d")
        self.month_var = tk.StringVar(value=f"{current_date.year:04d}-{current_date.month:02d}")
        self.emp_var = tk.StringVar()
        self.rows = []
        self._build_ui()

    def _build_ui(self):
        header = ttk.Frame(self); header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Salary", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(header, text=f"Date (IST): {get_current_date_in_india()}",
                  font=("Segoe UI", 9)).pack(side="right")

        bar = ttk.Frame(self); bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Employee ID (blank = ALL)").pack(side="left")
        ttk.Entry(bar, textvariable=self.emp_var, width=18).pack(side="left", padx=6)
        ttk.Label(bar, text="Month").pack(side="left")
        current_date = datetime.strptime(get_current_date_in_india(), "%Y-%m-%d")
        self.month_name = tk.StringVar(value=calendar.month_name[current_date.month])
        self.year_spin = tk.IntVar(value=current_date.year)
        ttk.Combobox(bar, values=[calendar.month_name[i] for i in range(1, 13)],
                     textvariable=self.month_name, width=10).pack(side="left", padx=(6, 2))
        yf = ttk.Frame(bar); yf.pack(side="left", padx=(2, 6))
        ttk.Label(yf, text="Year:").pack(side="left", padx=2)
        current_year = current_date.year
        ttk.Combobox(yf, textvariable=self.year_spin,
                     values=list(range(current_year - 10, current_year + 11)),
                     width=8, state="readonly").pack(side="left", padx=2)
        ttk.Button(bar, text="Calculate", command=self.on_calculate).pack(side="left")
        ttk.Button(bar, text="Export CSV", command=self.on_export).pack(side="left", padx=6)

        table = ttk.Frame(self); table.pack(fill="both", expand=True, pady=(8, 0))
        self.tree = ttk.Treeview(table, columns=self.COLS, show="headings", height=12)
        for c in self.COLS:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=180 if c == "Name" else 120, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:
            self.tree.insert("", "end", values=(
                r["Emp_Id"], r["Name"], r["Month"], f'{r["Base Salary"]:.2f}',
                r["Working Days"], r["Present"], r["Absent"],
                f'{r["Overtime Hours"]:.2f}', f'{r["Net Pay"]:.2f}'
            ))

    def _gather_month_attendance(self, year, month):
        d = {}
        for day in month_days_iter(year, month):
            for r in load_attendance(day):
                emp = r.get("emp_id", "")
                if emp not in d:
                    d[emp] = {"present": 0, "absent": 0, "ot": 0.0}
                if (r.get("status", "A") or "A").upper().startswith("P"):
                    d[emp]["present"] += 1
                else:
                    d[emp]["absent"] += 1
                try:
                    d[emp]["ot"] += float(r.get("overtime", 0.0))
                except:
                    pass
        return d

    def on_calculate(self):
        try:
            month_idx = list(calendar.month_name).index(self.month_name.get())
        except ValueError:
            messagebox.showerror("Month", "Select a valid month.")
            return
        year = int(self.year_spin.get())
        month = month_idx
        month_str = f"{year:04d}-{month:02d}"
        self.month_var.set(month_str)
        working_days = business_days_in_month(year, month)
        att = self._gather_month_attendance(year, month)
        emp_filter = self.emp_var.get().strip()
        self.rows = []
        for e in load_employees():
            emp_id = e.get("emp_id", "")
            if emp_filter and emp_id != emp_filter:
                continue
            base = float(e.get("base_salary", 0.0))
            stats = att.get(emp_id, {"present": 0, "absent": 0, "ot": 0.0})
            present = stats["present"]
            ot_hours = stats["ot"]
            per_hour = base / 176.0 if base else 0.0
            prorated = base * (present / float(working_days) if working_days > 0 else 0.0)
            net = max(0.0, prorated + per_hour * ot_hours)
            self.rows.append({
                "Emp_Id": emp_id, "Name": e.get("name", ""), "Month": month_str,
                "Base Salary": base, "Working Days": working_days,
                "Present": present, "Absent": stats["absent"],
                "Overtime Hours": ot_hours, "Net Pay": net
            })
        if not self.rows:
            messagebox.showinfo("Salary", "No employees found or no matching Employee ID.")
        self._refresh()

    def on_export(self):
        if not self.rows:
            messagebox.showinfo("Export", "No salary data to export. Click Calculate first.")
            return
        month = self.month_var.get().strip()
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"salary-{month}.csv" if valid_month(month) else "salary.csv",
            initialdir=SAL_DIR if os.path.isdir(SAL_DIR) else os.getcwd(),
            filetypes=[("CSV files", "*.csv")]
        )
        if not path: return
        export_csv(path, list(self.COLS), self.rows)
        messagebox.showinfo("Export", f"Exported to:\n{path}")

# ---------------------- Main App ----------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Employee Management System")
        self.geometry("1024x640")
        self._style()
        self.notebook = None
        self._show_login()

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=4)

    def _show_login(self):
        self.withdraw()
        login = LoginWindow(self, on_success=self._on_login_success)
        self.wait_window(login)

    def _on_login_success(self):
        self.deiconify()
        self._build_tabs()

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        tab_emp = EmployeesTab(self.notebook)
        tab_att = AttendanceTab(self.notebook)
        tab_sal = SalaryTab(self.notebook)
        self.notebook.add(tab_emp, text="  Employees  ")
        self.notebook.add(tab_att, text="  Attendance  ")
        self.notebook.add(tab_sal, text="  Salary  ")


if __name__ == "__main__":
    ensure_dirs()
    app = App()
    app.mainloop()
