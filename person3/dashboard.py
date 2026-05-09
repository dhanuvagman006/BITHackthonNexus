"""
Person 3 — Terminal Monitoring Dashboard (Rich TUI)
=====================================================
A live-updating, cyberpunk-themed "Mission Control" terminal interface.
Polls the FastAPI backend (/status/overview) and renders:

  ┌─────────────────────────────────────────────┐
  │  PHOENIXVAULT — SECURITY OPERATIONS CENTER  │
  ├──────────────────────┬──────────────────────┤
  │  System Health       │  Backup Integrity    │
  ├──────────────────────┼──────────────────────┤
  │  Recovery Progress   │  Threat Alert Banner │
  ├──────────────────────┴──────────────────────┤
  │           Security Event Feed               │
  └─────────────────────────────────────────────┘

Run:  python dashboard.py
(Requires backend: python app.py)
"""

import time
import sys
from datetime import datetime

import httpx
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from rich.progress_bar import ProgressBar
from rich.columns import Columns

API_BASE = "http://127.0.0.1:8000"
console = Console()

# ──────────────────────────────────────────────
#  API Client
# ──────────────────────────────────────────────

def fetch_overview() -> dict:
    """Fetch the unified overview from the backend."""
    try:
        resp = httpx.get(f"{API_BASE}/status/overview", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

# ──────────────────────────────────────────────
#  Panel Builders
# ──────────────────────────────────────────────

_tick = 0  # global animation tick

def make_header(data: dict | None) -> Panel:
    """Top banner with title and clock."""
    global _tick
    _tick += 1

    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    if data and data.get("attack_active"):
        # Alternate colors for blinking effect
        if _tick % 2 == 0:
            title_style = "bold white on red"
            border = "red"
            status_txt = "⚠  THREAT DETECTED  ⚠"
        else:
            title_style = "bold red on black"
            border = "bright_red"
            status_txt = "⚠  THREAT DETECTED  ⚠"
    else:
        title_style = "bold cyan"
        border = "bright_cyan"
        status_txt = "✓ ALL SYSTEMS NOMINAL"

    header_text = Text()
    header_text.append("  ╔═══════════════════════════════════════╗\n", style="cyan")
    header_text.append("  ║  ", style="cyan")
    header_text.append("PHOENIXVAULT", style="bold bright_cyan")
    header_text.append("  —  ", style="dim")
    header_text.append("Security Operations Center", style="dim cyan")
    header_text.append("  ║\n", style="cyan")
    header_text.append("  ╚═══════════════════════════════════════╝", style="cyan")

    status_line = Text()
    status_line.append(f"\n  🕐 {now}    ", style="dim")
    status_line.append(status_txt, style=title_style)

    content = Text()
    content.append_text(header_text)
    content.append_text(status_line)

    return Panel(
        Align.center(content),
        border_style=border,
        padding=(0, 1),
        height=6,
    )


def make_system_health(data: dict | None) -> Panel:
    """Panel showing system health table."""
    table = Table(box=box.SIMPLE_HEAVY, expand=True, show_header=True, header_style="bold cyan")
    table.add_column("System", style="bold white", ratio=3)
    table.add_column("Status", justify="center", ratio=2)
    table.add_column("Health", justify="center", ratio=1)

    if data:
        for s in data.get("systems", []):
            status = s["status"]
            health = s["health_pct"]

            if status == "online":
                s_icon = "[green]● ONLINE[/]"
            elif status == "compromised":
                s_icon = "[bold red]◉ COMPROMISED[/]" if _tick % 2 == 0 else "[red]◉ COMPROMISED[/]"
            elif status == "recovering":
                s_icon = "[yellow]◎ RECOVERING[/]"
            elif status == "restored":
                s_icon = "[bright_blue]● RESTORED[/]"
            else:
                s_icon = f"[dim]{status}[/]"

            if health >= 80:
                h_bar = f"[green]{'█' * (health // 10)}{'░' * (10 - health // 10)} {health}%[/]"
            elif health >= 50:
                h_bar = f"[yellow]{'█' * (health // 10)}{'░' * (10 - health // 10)} {health}%[/]"
            else:
                h_bar = f"[red]{'█' * (health // 10)}{'░' * (10 - health // 10)} {health}%[/]"

            table.add_row(s["name"], s_icon, h_bar)
    else:
        table.add_row("[dim]Waiting for data...[/]", "", "")

    return Panel(
        table,
        title="[bold cyan]⚡ System Health[/]",
        border_style="cyan",
        padding=(0, 1),
    )


def make_backup_panel(data: dict | None) -> Panel:
    """Panel showing backup integrity."""
    table = Table(box=box.SIMPLE, expand=True, show_header=True, header_style="bold blue")
    table.add_column("Backup ID", style="bold")
    table.add_column("Size", justify="right", style="dim")
    table.add_column("Integrity", justify="center")
    table.add_column("🔒", justify="center")

    if data:
        for b in data.get("backups", []):
            integrity = b["integrity"]
            if integrity == "VERIFIED":
                i_str = "[green]✓ VERIFIED[/]"
            elif integrity == "CORRUPTED":
                i_str = "[red]✗ CORRUPTED[/]"
            else:
                i_str = "[yellow]⧖ PENDING[/]"

            lock = "[green]IMMUTABLE[/]" if b["immutable"] else "[red]MUTABLE[/]"
            table.add_row(b["backup_id"], f"{b['size_mb']} MB", i_str, lock)

        # Summary
        verified = sum(1 for b in data["backups"] if b["integrity"] == "VERIFIED")
        total = len(data["backups"])
        pct = int((verified / total) * 100) if total else 0
        summary = Text(f"\n  Overall Integrity: {pct}% ({verified}/{total} verified)", style="bold green" if pct == 100 else "bold yellow")
    else:
        table.add_row("[dim]...[/]", "", "", "")
        summary = Text("")

    content = Text()
    table_text = Text()

    return Panel(
        table,
        title="[bold blue]🛡 Backup Integrity[/]",
        border_style="blue",
        padding=(0, 1),
    )


def make_recovery_panel(data: dict | None) -> Panel:
    """Panel showing recovery progress."""
    if not data:
        content = Text("  No data available", style="dim")
        return Panel(content, title="[bold green]🔄 Recovery[/]", border_style="green")

    rec = data.get("recovery", {})
    active = rec.get("active", False)
    phase = rec.get("phase", "IDLE")
    pct = rec.get("progress_pct", 0)
    elapsed = rec.get("elapsed_sec", 0)
    recovered = rec.get("systems_recovered", 0)
    total = rec.get("systems_total", 5)

    lines = []

    if phase == "IDLE" and not data.get("attack_active"):
        lines.append(Text("  Status: ", style="dim"))
        lines.append(Text("STANDBY — No recovery needed\n", style="green"))
        lines.append(Text(f"  Systems Online: {total}/{total}\n", style="dim"))
    elif phase == "IDLE" and data.get("attack_active"):
        lines.append(Text("  Status: ", style="dim"))
        lines.append(Text("AWAITING RECOVERY COMMAND\n", style="bold yellow"))
        lines.append(Text("  Run: python attack_sim.py recover\n", style="dim italic"))
    elif phase == "COMPLETE":
        lines.append(Text("  Status: ", style="dim"))
        lines.append(Text("★ RECOVERY COMPLETE\n", style="bold green"))
        lines.append(Text(f"  Recovery Time: {elapsed}s\n", style="bold cyan"))
        lines.append(Text(f"  Systems Restored: {recovered}/{total}\n", style="green"))
    else:
        lines.append(Text("  Phase: ", style="dim"))
        lines.append(Text(f"{phase}\n", style="bold yellow"))
        lines.append(Text(f"  Elapsed: {elapsed}s\n", style="dim"))

        # ASCII progress bar
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        lines.append(Text(f"\n  [{bar}] {pct}%\n", style="green"))
        lines.append(Text(f"  Systems: {recovered}/{total} restored\n", style="cyan"))

    content = Text()
    for l in lines:
        content.append_text(l)

    border = "green"
    if active:
        border = "yellow"

    return Panel(
        content,
        title="[bold green]🔄 Recovery Status[/]",
        border_style=border,
        padding=(0, 1),
    )


def make_threat_panel(data: dict | None) -> Panel:
    """Panel showing current threat level and attack stage."""
    if not data:
        return Panel("[dim]No data[/]", title="[bold red]🔴 Threat Level[/]", border_style="red")

    attack = data.get("attack_active", False)
    stage = data.get("attack_stage", "NONE")

    if not attack and stage == "NONE":
        content = Text()
        content.append("  Threat Level: ", style="dim")
        content.append("LOW\n\n", style="bold green")
        content.append("  ████████████████████████████\n", style="green")
        content.append("  No active threats detected.\n", style="dim")
        content.append("  Perimeter secure.\n", style="dim green")
        border = "green"
    else:
        content = Text()
        content.append("  Threat Level: ", style="dim")
        content.append("CRITICAL\n\n", style="bold red")

        if stage == "ENCRYPTION":
            content.append("  ██████░░░░░░░░░░░░░░░░░░░░░░\n", style="red")
            content.append("  ⚠ FILE ENCRYPTION IN PROGRESS\n", style="bold red")
            content.append("  File Server under attack!\n", style="red")
        elif stage == "BACKUP_DELETION":
            content.append("  ████████████████░░░░░░░░░░░░░\n", style="red")
            content.append("  ⚠ BACKUP DELETION ATTEMPTED\n", style="bold red")
            content.append("  Immutable storage HELD!\n", style="bold green")
        elif stage == "LATERAL_MOVEMENT":
            content.append("  ██████████████████████░░░░░░░\n", style="red")
            content.append("  ⚠ LATERAL MOVEMENT DETECTED\n", style="bold red")
            content.append("  Network scanning in progress\n", style="red")
        elif stage == "COMPLETE":
            content.append("  ████████████████████████████\n", style="bold red")
            content.append("  ★ ALL SYSTEMS COMPROMISED\n", style="bold red")
            content.append("  Initiate recovery!\n", style="bold yellow")
        else:
            content.append("  Unknown stage\n", style="dim")

        border = "red" if _tick % 2 == 0 else "bright_red"

    return Panel(
        content,
        title="[bold red]🔴 Threat Level[/]",
        border_style=border,
        padding=(0, 1),
    )


def make_alert_feed(data: dict | None) -> Panel:
    """Scrolling security event feed."""
    if not data:
        return Panel("[dim]No alerts[/]", title="[bold yellow]📡 Security Feed[/]", border_style="yellow")

    alerts = data.get("alerts", [])
    # Show last 12 alerts (most recent at bottom)
    recent = alerts[-12:] if len(alerts) > 12 else alerts

    lines = Text()
    for a in recent:
        sev = a["severity"]
        ts = a["timestamp"].split("T")[-1] if "T" in a["timestamp"] else a["timestamp"]

        if sev == "CRITICAL":
            lines.append(f"  {ts} ", style="dim")
            lines.append(f"[{sev}] ", style="bold red")
            lines.append(f"{a['source']}: ", style="red")
            lines.append(f"{a['message']}\n", style="bold red")
        elif sev == "WARNING":
            lines.append(f"  {ts} ", style="dim")
            lines.append(f"[{sev}] ", style="bold yellow")
            lines.append(f"{a['source']}: ", style="yellow")
            lines.append(f"{a['message']}\n", style="yellow")
        else:
            lines.append(f"  {ts} ", style="dim")
            lines.append(f"[{sev}] ", style="dim green")
            lines.append(f"{a['source']}: ", style="dim")
            lines.append(f"{a['message']}\n", style="dim")

    if not recent:
        lines.append("  No events yet.", style="dim")

    return Panel(
        lines,
        title="[bold yellow]📡 Security Event Feed[/]",
        border_style="yellow",
        padding=(0, 1),
    )


def make_footer() -> Panel:
    """Bottom bar with keyboard shortcuts."""
    text = Text()
    text.append("  Ctrl+C", style="bold cyan")
    text.append(" Exit   ", style="dim")
    text.append("│  ", style="dim")
    text.append("python attack_sim.py attack", style="bold red")
    text.append(" Trigger Attack   ", style="dim")
    text.append("│  ", style="dim")
    text.append("python attack_sim.py recover", style="bold green")
    text.append(" Start Recovery   ", style="dim")
    text.append("│  ", style="dim")
    text.append("python attack_sim.py reset", style="bold blue")
    text.append(" Reset", style="dim")

    return Panel(text, border_style="dim", height=3)


# ──────────────────────────────────────────────
#  Layout Builder
# ──────────────────────────────────────────────

def build_layout() -> Layout:
    """Create the dashboard layout structure."""
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="main", ratio=1),
        Layout(name="feed", size=16),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1),
    )

    layout["left"].split_column(
        Layout(name="systems", ratio=1),
        Layout(name="recovery", ratio=1),
    )

    layout["right"].split_column(
        Layout(name="backups", ratio=1),
        Layout(name="threat", ratio=1),
    )

    return layout


def update_layout(layout: Layout, data: dict | None):
    """Update all panels with fresh data."""
    layout["header"].update(make_header(data))
    layout["systems"].update(make_system_health(data))
    layout["backups"].update(make_backup_panel(data))
    layout["recovery"].update(make_recovery_panel(data))
    layout["threat"].update(make_threat_panel(data))
    layout["feed"].update(make_alert_feed(data))
    layout["footer"].update(make_footer())


# ──────────────────────────────────────────────
#  Main Loop
# ──────────────────────────────────────────────

def main():
    console.clear()
    layout = build_layout()

    # Initial render
    data = fetch_overview()
    update_layout(layout, data)

    try:
        with Live(layout, console=console, refresh_per_second=2, screen=True):
            while True:
                data = fetch_overview()
                update_layout(layout, data)
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.clear()
        console.print("\n[bold cyan]PhoenixVault[/] dashboard stopped. Goodbye! 👋\n")


if __name__ == "__main__":
    main()
