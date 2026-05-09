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
            self.last_response = "" # Clear response when typing to save space

    def backspace(self):
        with self.lock:
            if len(self.current_command) > 0:
                self.current_command = self.current_command[:-1]

    def submit_command(self):
        with self.lock:
            cmd = self.current_command.strip()
            if cmd:
                self.command_history.append(f"> {cmd}")
                if len(self.command_history) > 2: # Reduced from 3 to 2 for more space
                    self.command_history.pop(0)
                # Spawn command execution in background
                threading.Thread(target=self.execute_command, args=(cmd.lower(),), daemon=True).start()
            self.current_command = ""

    def execute_command(self, cmd: str):
        # Handle commands with arguments (like 'monitor https://google.com')
        parts = cmd.split(" ", 1)
        base_cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        endpoints = {"attack": "/attack/start", "recover": "/attack/recover", "reset": "/attack/reset"}
        
        if base_cmd == "monitor" and arg:
            try:
                # Ensure it has a scheme
                if not arg.startswith("http"):
                    arg = "https://" + arg
                resp = httpx.post(f"{API_BASE}/monitor/add", params={"url": arg}, timeout=5)
                with self.lock:
                    if resp.status_code == 200:
                        self.last_response = f"[{Theme.GREEN}]ADDED MONITOR: {arg}[/]"
                    else:
                        self.last_response = f"[{Theme.RED}]FAILED: {resp.status_code}[/]"
            except Exception as e:
                with self.lock:
                    self.last_response = f"[{Theme.RED}]CONNECTION ERROR[/]"
        elif base_cmd == "fix" and arg:
            try:
                # Find the full URL from the nickname/partial URL if needed
                target_url = arg
                with self.lock:
                    if self.data:
                        for s in self.data.get("external_sites", []):
                            if arg in s["url"] or arg in s["name"]:
                                target_url = s["url"]
                                break
                
                resp = httpx.post(f"{API_BASE}/monitor/fix", params={"url": target_url}, timeout=10)
                with self.lock:
                    if resp.status_code == 200:
                        res = resp.json()
                        if res.get("status") == "repair_initiated":
                            self.last_response = f"[{Theme.GREEN}]REPAIR INITIATED ON {target_url}[/]"
                        else:
                            self.last_response = f"[{Theme.RED}]REPAIR FAILED: {res.get('status')}[/]"
                    else:
                        self.last_response = f"[{Theme.RED}]FAILED: {resp.status_code}[/]"
            except Exception as e:
                with self.lock:
                    self.last_response = f"[{Theme.RED}]REPAIR ERROR[/]"
        elif base_cmd == "help":
            with self.lock:
                self.last_response = f"[{Theme.YELLOW}]CMDS: attack, recover, reset, monitor <url>, fix <url>, clear, refresh, help[/]"
        elif base_cmd == "clear":
            with self.lock:
                self.command_history = []
                self.last_response = ""
        elif base_cmd == "refresh":
            # Force an immediate poll
            data_fetcher_loop(once=True)
            with self.lock:
                self.last_response = f"[{Theme.CYAN}]DATA REFRESHED[/]"
        elif base_cmd in endpoints:
            try:
                resp = httpx.post(f"{API_BASE}{endpoints[base_cmd]}", timeout=5)
                with self.lock:
                    if resp.status_code == 200:
                        self.last_response = f"[{Theme.GREEN}]SUCCESS: {base_cmd.upper()}[/]"
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

def data_fetcher_loop(once=False):
    """Background thread to poll API status."""
    while True:
        try:
            resp = httpx.get(f"{API_BASE}/status/overview", timeout=2)
            if resp.status_code == 200:
                state.update_data(resp.json())
            else:
                state.update_data(None)
        except:
            state.update_data(None)
        
        if once or not state.running:
            break
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
        
        # Global Status: Check if local OR any remote site is breached
        local_attack = data and data.get("attack_active")
        remote_attack = False
        if data:
            for s in data.get("external_sites", []):
                if s["status"] == "compromised":
                    remote_attack = True
                    break
        
        is_attack = local_attack or remote_attack
        connected = state.connected
        
        if not connected:
            color = Theme.DIM
            status = "○ OFFLINE"
        else:
            color = Theme.RED if is_attack else Theme.CYAN
            status = "⚠ BREACH DETECTED" if is_attack else "✓ NETWORK SECURE"
        
        title = Text("PHOENIXVAULT NETWORK OPS CENTER", style="bold white")
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
            # External Sites (Primary Focus)
            ext_sites = data.get("external_sites", [])
            if ext_sites:
                for s in ext_sites:
                    st, hp = s["status"], s["health_pct"]
                    icon = f"[{Theme.GREEN}]LIVE[/]" if st == "online" else (f"[bold {Theme.RED}]BREACH?[/]" if st == "compromised" else f"[{Theme.DIM}]OFFLINE[/]")
                    bar_color = Theme.GREEN if hp > 80 else (Theme.YELLOW if hp > 40 else Theme.RED)
                    bar = f"[{bar_color}]{'█' * (hp // 10)}{'░' * (10 - hp // 10)} {hp}%[/]"
                    table.add_row(s["name"][:20], icon, bar)
                    
                    # Show sub-components
                    comp_data = s.get("components")
                    if isinstance(comp_data, list):
                        for comp in comp_data:
                            if not isinstance(comp, dict): continue
                            c_name = comp.get("name", "Unknown")
                            c_status = comp.get("status", "unknown")
                            c_hp = comp.get("health_pct", 0)
                            
                            c_icon = f"[{Theme.GREEN}]●[/]" if c_status in ["online", "restored", "healthy"] else (f"[{Theme.RED}]✖[/]" if c_status == "compromised" else "[grey50]○[/]")
                            table.add_row(f"  └ {c_name}", c_icon, f"[{Theme.DIM}]{c_hp}%[/]")
            else:
                table.add_row("[grey50]NO REMOTE ASSETS ADDED[/]", "", "")
                table.add_row("[grey50]USE: monitor <url>[/]", "", "")
        else:
            table.add_row("[grey50]CONNECTING TO CORE...[/]", "", "")
    
    return Panel(table, title="[bold white]REMOTE ASSETS MONITOR[/]", border_style=Theme.CYAN)

def make_vault_status() -> Panel:
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("ASSET / DATASET", ratio=2)
    table.add_column("INTEGRITY", justify="center", ratio=2)
    table.add_column("STORAGE", ratio=2)
    
    with state.lock:
        data = state.data
        if data:
            # Show remote backup summaries
            ext_sites = data.get("external_sites", [])
            if ext_sites:
                for s in ext_sites:
                    status_style = Theme.GREEN if s["status"] == "online" else Theme.RED
                    
                    # Dataset details
                    records = s.get('backup_records', 0)
                    size = s.get('backup_size_kb', 0)
                    dataset_details = f"[bold]{s['name'][:20]}[/]\n[{Theme.DIM}]{records} Records ({size} KB)[/]"
                    
                    # Integrity Details
                    hash_val = s.get('backup_hash', 'N/A')
                    if s["status"] == "online":
                        integrity = f"[{status_style}]VERIFIED (SHA-256)[/]\n[{Theme.DIM}]SHA: {hash_val}[/]"
                    else:
                        integrity = f"[{status_style}]AWAITING REPAIR[/]\n[{Theme.DIM}]SHA: {hash_val}[/]"
                        
                    # Storage details (Simulated Cloud/Device)
                    storage = f"🔒 PhoenixVault Storage\n[{Theme.DIM}]Local Disk Snapshot[/]"
                    
                    table.add_row(dataset_details, integrity, storage)
            else:
                table.add_row("[grey50]NO REMOTE VAULTS CONNECTED[/]", "", "")
        else:
            table.add_row("[grey50]NO DATA[/]", "", "")
            
    return Panel(table, title="[bold white]NETWORK VAULT STATUS[/]", border_style=Theme.BLUE)

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
            # Show latest logs at the top
            for a in reversed(data.get("alerts", [])[-6:]):
                msg = a["message"]
                msg_lower = msg.lower()
                
                # Apply requested color coding
                if "corrupt" in msg_lower and "fix" not in msg_lower and "restored" not in msg_lower and "clear" not in msg_lower:
                    color = Theme.RED
                elif "restored" in msg_lower or "fix" in msg_lower or "recover" in msg_lower or "clear" in msg_lower:
                    color = Theme.GREEN
                else:
                    color = Theme.BLUE
                    
                lines.append(f"{a['timestamp'].split('T')[-1]} ", style=Theme.DIM)
                lines.append(f"{msg}\n", style=color)
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
            (cursor, "bold white" if state.focused else Theme.DIM)
        )
        
        # Only show response if it exists to save space
        res_text = Text(f"\n {state.last_response}") if state.last_response else Text("")
        
    return Panel(Group(history, prompt, res_text), title=f"[bold {prompt_style}]CONSOLE {'(ACTIVE)' if state.focused else '(INACTIVE - TAB TO FOCUS)'}[/]", border_style=prompt_style)

# ──────────────────────────────────────────────
#  Startup Sequence
# ──────────────────────────────────────────────

def show_startup_sequence():
    """Professional boot sequence with ASCII art and simulated logs."""
    logo = """
    ██████╗ ██╗  ██╗ ██████╗ ███████╗███╗   ██╗██╗██╗  ██╗
    ██╔══██╗██║  ██║██╔═══██╗██╔════╝████╗  ██║██║╚██╗██╔╝
    ██████╔╝███████║██║   ██║█████╗  ██╔██╗ ██║██║ ╚███╔╝ 
    ██╔═══╝ ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║██║ ██╔██╗ 
    ██║     ██║  ██║╚██████╔╝███████╗██║ ╚████║██║██╔╝ ██╗
    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
    [bold cyan]S E C U R I T Y   O P S   C E N T E R[/]
    """
    
    boot_logs = [
        "INITIALIZING SECURE KERNEL...",
        "MOUNTING ENCRYPTED VOLUMES...",
        "ESTABLISHING HANDSHAKE WITH VAULT ALPHA...",
        "SYNCING IMMUTABLE BACKUP INDEX...",
        "LOADING NETWORK TOPOLOGY...",
        "STARTING HEURISTIC ENGINE...",
        "DECRYPTING DASHBOARD ASSETS...",
        "SYSTEM CHECK: [bold green]OK[/]",
    ]

    with Live(Align.center(Group(Text(""))), screen=True, refresh_per_second=10) as live:
        # 1. Show Logo with Fade-In Effect
        for i in range(10):
            opacity = i / 10
            styled_logo = Text(logo, style=f"bold {Theme.CYAN}")
            live.update(Align.center(Group(
                styled_logo,
                Text("\n" * 2),
                Text("BOOTING...", style=Theme.DIM)
            )))
            time.sleep(0.05)

        # 2. Simulated Logs & Progress
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, complete_style=Theme.CYAN),
            TextColumn("[bold cyan]{task.percentage:>3.0f}%"),
        )
        task = progress.add_task("BOOTING SYSTEM...", total=len(boot_logs))
        
        current_logs = []
        for i, log in enumerate(boot_logs):
            current_logs.append(f"[{Theme.DIM}]>[/] {log}")
            if len(current_logs) > 5:
                current_logs.pop(0)
            
            log_text = Text("\n".join(current_logs))
            
            for _ in range(5): # Smooth progress between logs
                progress.update(task, advance=0.2)
                live.update(Align.center(Group(
                    Text(logo, style=f"bold {Theme.CYAN}"),
                    Text("\n"),
                    progress,
                    Text("\n"),
                    Panel(log_text, border_style=Theme.DIM, width=60, title="[bold]BOOT LOG[/]")
                )))
                time.sleep(0.05 + random.random() * 0.1)

        time.sleep(0.5)
        live.update(Align.center(Text("READY", style=f"bold {Theme.GREEN}")))
        time.sleep(0.5)

# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    # Always show startup sequence for the demo
    show_startup_sequence()


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

if __name__ == "__main__":
    main()
