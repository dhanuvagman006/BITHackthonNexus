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
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

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

# ──────────────────────────────────────────────
#  State Management
# ──────────────────────────────────────────────

class DashboardState:
    def __init__(self):
        self.data: Optional[Dict[str, Any]] = None
        self.current_command = ""
        self.command_history: List[str] = []
        self.last_response = ""
        self.tick = 0
        self.lock = threading.Lock()
        self.running = True
        self.connected = False
        self.focused = True

    def update_data(self, new_data: Optional[Dict[str, Any]]):
        with self.lock:
            self.data = new_data
            self.connected = new_data is not None

    def add_char(self, char: str):
        with self.lock:
            self.current_command += char

    def backspace(self):
        with self.lock:
            if len(self.current_command) > 0:
                self.current_command = self.current_command[:-1]

    def submit_command(self):
        with self.lock:
            cmd = self.current_command.strip()
            if cmd:
                self.command_history.append(f"> {cmd}")
                if len(self.command_history) > 3:
                    self.command_history.pop(0)
                # Spawn command execution in background
                threading.Thread(target=self.execute_command, args=(cmd.lower(),), daemon=True).start()
            self.current_command = ""

    def execute_command(self, cmd: str):
        endpoints = {"attack": "/attack/start", "recover": "/attack/recover", "reset": "/attack/reset"}
        if cmd in endpoints:
            try:
                resp = httpx.post(f"{API_BASE}{endpoints[cmd]}", timeout=5)
                with self.lock:
                    if resp.status_code == 200:
                        self.last_response = f"[{Theme.GREEN}]SUCCESS: {cmd.upper()}[/]"
                    else:
                        self.last_response = f"[{Theme.RED}]FAILED: {resp.status_code}[/]"
            except Exception as e:
                with self.lock:
                    self.last_response = f"[{Theme.RED}]CONNECTION ERROR[/]"
        else:
            with self.lock:
                self.last_response = f"[{Theme.YELLOW}]UNKNOWN CMD: {cmd}[/]"

    def increment_tick(self):
        with self.lock:
            self.tick += 1

state = DashboardState()

# ──────────────────────────────────────────────
#  Background Workers
# ──────────────────────────────────────────────

def data_fetcher_loop():
    """Background thread to poll API status."""
    while state.running:
        try:
            resp = httpx.get(f"{API_BASE}/status/overview", timeout=2)
            if resp.status_code == 200:
                state.update_data(resp.json())
            else:
                state.update_data(None)
        except:
            state.update_data(None)
        time.sleep(0.5)  # Poll every 500ms

def input_handler():
    """Process keyboard input without blocking UI."""
    while state.running:
        if msvcrt.kbhit():
            char = msvcrt.getch()
            if char == b'\t':  # Tab - Toggle focus
                with state.lock:
                    state.focused = not state.focused
            elif state.focused:
                if char == b'\r':  # Enter
                    state.submit_command()
                elif char == b'\x08':  # Backspace
                    state.backspace()
                elif char == b'\x03':  # Ctrl+C
                    state.running = False
                    break
                else:
                    try:
                        state.add_char(char.decode('utf-8'))
                    except:
                        pass
            elif char == b'\x03':  # Still allow Ctrl+C even if not focused
                state.running = False
                break
        time.sleep(0.01)  # High frequency for responsive typing

# ──────────────────────────────────────────────
#  UI Components
# ──────────────────────────────────────────────

def make_header() -> Panel:
    with state.lock:
        data = state.data
        now = datetime.now().strftime("%H:%M:%S")
        is_attack = data and data.get("attack_active")
        connected = state.connected
        
        if not connected:
            color = Theme.DIM
            status = "○ OFFLINE"
        else:
            color = Theme.RED if is_attack else Theme.CYAN
            status = "⚠ BREACH DETECTED" if is_attack else "✓ SECURE"
        
        title = Text("PHOENIXVAULT SECURITY OPS", style="bold white")
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1); grid.add_column(ratio=1); grid.add_column(ratio=1)
        grid.add_row(
            Text(f"STATUS: {status}", style=color), 
            Align.center(title), 
            Align.right(Text(now, style=Theme.DIM))
        )
        
        return Panel(grid, border_style=color, box=box.ROUNDED)

def make_node_monitor() -> Panel:
    table = Table(box=box.SIMPLE, expand=True, header_style=f"bold {Theme.CYAN}")
    table.add_column("NODE NAME", ratio=3)
    table.add_column("STATUS", justify="center", ratio=2)
    table.add_column("HEALTH", justify="right", ratio=3)

    with state.lock:
        data = state.data
        if data:
            for s in data.get("systems", []):
                st, hp = s["status"], s["health_pct"]
                icon = f"[{Theme.GREEN}]ONLINE[/]" if st == "online" else (f"[bold {Theme.RED}]CRITICAL[/]" if st == "compromised" else f"[{Theme.BLUE}]RESTORED[/]")
                bar_color = Theme.GREEN if hp > 80 else (Theme.YELLOW if hp > 40 else Theme.RED)
                bar = f"[{bar_color}]{'█' * (hp // 10)}{'░' * (10 - hp // 10)} {hp}%[/]"
                table.add_row(s["name"], icon, bar)
        else:
            table.add_row("[grey50]NO DATA AVAILABLE[/]", "", "")
    
    return Panel(table, title="[bold white]SYSTEM NODES[/]", border_style=Theme.CYAN)

def make_vault_status() -> Panel:
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("BACKUP ID"); table.add_column("INTEGRITY", justify="center"); table.add_column("STORAGE")
    
    with state.lock:
        data = state.data
        if data:
            for b in data.get("backups", []):
                i_str = f"[{Theme.GREEN}]VERIFIED[/]" if b["integrity"] == "VERIFIED" else f"[{Theme.YELLOW}]PENDING[/]"
                lock = "🔒 IMMUTABLE" if b["immutable"] else "🔓 MUTABLE"
                table.add_row(b["backup_id"], i_str, lock)
        else:
            table.add_row("[grey50]NO DATA[/]", "", "")
            
    return Panel(table, title="[bold white]IMMUTABLE VAULT[/]", border_style=Theme.BLUE)

def make_recovery_orchestrator() -> Panel:
    with state.lock:
        data = state.data
        if not data or not data.get("recovery", {}).get("active"):
            return Panel(Align.center(Text("ORCHESTRATOR STANDBY", style=Theme.DIM)), border_style=Theme.DIM)
        
        rec = data.get("recovery", {})
        progress = Progress(
            SpinnerColumn(), 
            TextColumn("[bold]{task.description}"), 
            BarColumn(complete_style=Theme.GREEN), 
            TextColumn("{task.percentage:>3.0f}%"), 
            expand=True
        )
        progress.add_task(rec.get("phase", "RECOVERING"), completed=rec.get("progress_pct", 0))
        return Panel(progress, title="[bold white]RECOVERY ORCHESTRATOR[/]", border_style=Theme.GREEN)

def make_event_feed() -> Panel:
    lines = Text()
    with state.lock:
        data = state.data
        if data:
            for a in data.get("alerts", [])[-6:]:
                color = Theme.RED if a["severity"] == "CRITICAL" else (Theme.YELLOW if a["severity"] == "WARNING" else Theme.DIM)
                lines.append(f"{a['timestamp'].split('T')[-1]} ", style=Theme.DIM)
                lines.append(f"{a['message']}\n", style=color)
        else:
            lines.append("WAITING FOR CONNECTION...", style=Theme.DIM)
            
    return Panel(lines, title="[bold white]EVENT LOG[/]", border_style=Theme.YELLOW)

def make_console() -> Panel:
    history = Text()
    with state.lock:
        for h in state.command_history:
            history.append(f" {h}\n", style=Theme.DIM)
        
        # Cursor effect: blinks every 500ms when focused
        if state.focused:
            show_cursor = (state.tick // 5) % 2 == 0
            cursor = "█" if show_cursor else " "
        else:
            cursor = "▯"
        
        prompt_style = Theme.CYAN if state.focused else Theme.DIM
        prompt = Text.assemble(
            (" > ", prompt_style), 
            (state.current_command, "white" if state.focused else Theme.DIM), 
            (cursor, prompt_style)
        )
        response = Text(f"\n {state.last_response}")
        
    return Panel(Group(history, prompt, response), title="[bold white]CONSOLE[/]", border_style=Theme.DIM)

# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    hWnd = None
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
    layout.split_column(
        Layout(name="header", size=3), 
        Layout(name="main", ratio=1), 
        Layout(name="footer", size=6)
    )
    layout["main"].split_row(Layout(name="left", ratio=1), Layout(name="right", ratio=1))
    layout["left"].split_column(Layout(name="nodes", ratio=1), Layout(name="recovery", size=5))
    layout["right"].split_column(Layout(name="vault", ratio=1), Layout(name="feed", ratio=1))
    
    # Start background threads
    threads = [
        threading.Thread(target=data_fetcher_loop, daemon=True),
        threading.Thread(target=input_handler, daemon=True)
    ]
    for t in threads:
        t.start()
    
    try:
        # High refresh rate for smooth cursor and input (10 FPS)
        with Live(layout, refresh_per_second=10, screen=True):
            while state.running:
                state.increment_tick()
                layout["header"].update(make_header())
                layout["nodes"].update(make_node_monitor())
                layout["recovery"].update(make_recovery_orchestrator())
                layout["vault"].update(make_vault_status())
                layout["feed"].update(make_event_feed())
                layout["footer"].update(make_console())
                time.sleep(0.1)
    except KeyboardInterrupt:
        state.running = False
    finally:
        state.running = False
        if sys.platform == "win32" and hWnd:
            try:
                import ctypes
                user32 = ctypes.WinDLL('user32')
                user32.PostMessageW(hWnd, 0x0010, 0, 0)
            except:
                pass

if __name__ == "__main__":
    if "--windowed" not in sys.argv:
        import subprocess
        subprocess.Popen("start cmd /c python dashboard.py --windowed", shell=True)
        sys.exit()
        
    main()
