"""
Person 3 — Terminal Monitoring Dashboard (Simplified)
=====================================================
A clean, focused TUI for monitoring ransomware recovery.
Focuses on: Node Status, Backup Integrity, and Recovery Orchestration.

Run:  python dashboard.py
"""

import time
import sys
import random
import msvcrt
from datetime import datetime

import httpx
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

# ──────────────────────────────────────────────
#  Theme & Constants
# ──────────────────────────────────────────────

API_BASE = "http://127.0.0.1:8000"
console = Console()

class Theme:
    CYAN = "bright_cyan"
    BLUE = "deep_sky_blue1"
    GREEN = "spring_green3"
    YELLOW = "gold1"
    RED = "bright_red"
    DIM = "grey50"

_current_command = ""
_command_history = []
_last_response = ""
_tick = 0

# ──────────────────────────────────────────────
#  Logic & API
# ──────────────────────────────────────────────

def fetch_overview() -> dict:
    try:
        resp = httpx.get(f"{API_BASE}/status/overview", timeout=2)
        return resp.json() if resp.status_code == 200 else None
    except: return None

def send_command(cmd: str):
    global _last_response
    endpoints = {"attack": "/attack/start", "recover": "/attack/recover", "reset": "/attack/reset"}
    if cmd in endpoints:
        try:
            httpx.post(f"{API_BASE}{endpoints[cmd]}")
            _last_response = f"[green]SUCCESS: {cmd.upper()}[/]"
        except: _last_response = "[red]FAILED TO CONNECT[/]"
    else: _last_response = f"[yellow]UNKNOWN CMD: {cmd}[/]"

def process_input():
    global _current_command, _command_history
    if msvcrt.kbhit():
        char = msvcrt.getch()
        if char == b'\r':
            cmd = _current_command.strip().lower()
            if cmd:
                _command_history.append(f"> {cmd}")
                if len(_command_history) > 3: _command_history.pop(0)
                send_command(cmd)
            _current_command = ""
        elif char == b'\x08': _current_command = _current_command[:-1]
        elif char == b'\x03': raise KeyboardInterrupt
        else:
            try: _current_command += char.decode('utf-8')
            except: pass

# ──────────────────────────────────────────────
#  UI Components
# ──────────────────────────────────────────────

def make_header(data: dict | None) -> Panel:
    global _tick
    _tick += 1
    now = datetime.now().strftime("%H:%M:%S")
    is_attack = data and data.get("attack_active")
    color = Theme.RED if is_attack else Theme.CYAN
    status = "⚠ BREACH DETECTED" if is_attack else "✓ SECURE"
    
    title = Text("PHOENIXVAULT SECURITY OPS", style="bold white")
    grid = Table.grid(expand=True)
    grid.add_column(ratio=1); grid.add_column(ratio=1); grid.add_column(ratio=1)
    grid.add_row(Text(f"STATUS: {status}", style=color), Align.center(title), Align.right(Text(now, style=Theme.DIM)))
    
    return Panel(grid, border_style=color, box=box.ROUNDED)

def make_node_monitor(data: dict | None) -> Panel:
    table = Table(box=box.SIMPLE, expand=True, header_style=f"bold {Theme.CYAN}")
    table.add_column("NODE NAME", ratio=3)
    table.add_column("STATUS", justify="center", ratio=2)
    table.add_column("HEALTH", justify="right", ratio=3)

    if data:
        for s in data.get("systems", []):
            st, hp = s["status"], s["health_pct"]
            icon = f"[{Theme.GREEN}]ONLINE[/]" if st == "online" else (f"[bold {Theme.RED}]CRITICAL[/]" if st == "compromised" else f"[{Theme.BLUE}]RESTORED[/]")
            bar_color = Theme.GREEN if hp > 80 else (Theme.YELLOW if hp > 40 else Theme.RED)
            bar = f"[{bar_color}]{'█' * (hp // 10)}{'░' * (10 - hp // 10)} {hp}%[/]"
            table.add_row(s["name"], icon, bar)
    
    return Panel(table, title="[bold white]SYSTEM NODES[/]", border_style=Theme.CYAN)

def make_vault_status(data: dict | None) -> Panel:
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("BACKUP ID"); table.add_column("INTEGRITY", justify="center"); table.add_column("STORAGE")
    if data:
        for b in data.get("backups", []):
            i_str = f"[{Theme.GREEN}]VERIFIED[/]" if b["integrity"] == "VERIFIED" else f"[{Theme.YELLOW}]PENDING[/]"
            lock = "🔒 IMMUTABLE" if b["immutable"] else "🔓 MUTABLE"
            table.add_row(b["backup_id"], i_str, lock)
    return Panel(table, title="[bold white]IMMUTABLE VAULT[/]", border_style=Theme.BLUE)

def make_recovery_orchestrator(data: dict | None) -> Panel:
    if not data or not data.get("recovery", {}).get("active"):
        return Panel(Align.center(Text("ORCHESTRATOR STANDBY", style=Theme.DIM)), border_style=Theme.DIM)
    
    rec = data.get("recovery", {})
    progress = Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(complete_style=Theme.GREEN), TextColumn("{task.percentage:>3.0f}%"), expand=True)
    progress.add_task(rec.get("phase", "RECOVERING"), completed=rec.get("progress_pct", 0))
    return Panel(progress, title="[bold white]RECOVERY ORCHESTRATOR[/]", border_style=Theme.GREEN)

def make_event_feed(data: dict | None) -> Panel:
    lines = Text()
    if data:
        for a in data.get("alerts", [])[-6:]:
            color = Theme.RED if a["severity"] == "CRITICAL" else (Theme.YELLOW if a["severity"] == "WARNING" else Theme.DIM)
            lines.append(f"{a['timestamp'].split('T')[-1]} ", style=Theme.DIM)
            lines.append(f"{a['message']}\n", style=color)
    return Panel(lines, title="[bold white]EVENT LOG[/]", border_style=Theme.YELLOW)

def make_console() -> Panel:
    history = Text()
    for h in _command_history: history.append(f" {h}\n", style=Theme.DIM)
    prompt = Text.assemble((" > ", Theme.CYAN), (_current_command, "white"), ("█" if _tick % 2 == 0 else " ", Theme.CYAN))
    return Panel(Group(history, prompt, Text(f"\n {_last_response}")), title="[bold white]CONSOLE[/]", border_style=Theme.DIM)

# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    # Maximize terminal window on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            user32 = ctypes.WinDLL('user32')
            hWnd = kernel32.GetConsoleWindow()
            if hWnd:
                user32.ShowWindow(hWnd, 3)  # SW_MAXIMIZE
        except:
            pass

    layout = Layout()
    layout.split_column(Layout(name="header", size=3), Layout(name="main", ratio=1), Layout(name="footer", size=6))
    layout["main"].split_row(Layout(name="left", ratio=1), Layout(name="right", ratio=1))
    layout["left"].split_column(Layout(name="nodes", ratio=1), Layout(name="recovery", size=5))
    layout["right"].split_column(Layout(name="vault", ratio=1), Layout(name="feed", ratio=1))
    
    try:
        with Live(layout, refresh_per_second=4, screen=True):
            while True:
                process_input()
                data = fetch_overview()
                layout["header"].update(make_header(data))
                layout["nodes"].update(make_node_monitor(data))
                layout["recovery"].update(make_recovery_orchestrator(data))
                layout["vault"].update(make_vault_status(data))
                layout["feed"].update(make_event_feed(data))
                layout["footer"].update(make_console())
                time.sleep(0.1)
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    # Check if we should relaunch in a new standalone window
    if "--windowed" not in sys.argv:
        import subprocess
        # Using 'start' to open in a new CMD window
        subprocess.Popen("start cmd /k python dashboard.py --windowed", shell=True)
        sys.exit()
        
    main()
