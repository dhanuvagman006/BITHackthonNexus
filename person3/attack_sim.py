"""
Person 3 — Ransomware Attack Simulation CLI
=============================================
A standalone CLI tool to drive the attack/recovery demo.
Sends commands to the FastAPI backend running on localhost:8000.

Usage:
    python attack_sim.py login        Log in as admin (with MFA)
    python attack_sim.py attack       Trigger ransomware simulation
    python attack_sim.py recover      Start recovery orchestration
    python attack_sim.py reset        Reset simulation to clean state
    python attack_sim.py status       Print current system overview
"""

import sys
import time
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box

API_BASE = "http://127.0.0.1:8000"
console = Console()

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _call(method: str, path: str, **kwargs):
    url = f"{API_BASE}{path}"
    try:
        resp = httpx.request(method, url, timeout=10, **kwargs)
        return resp
    except httpx.ConnectError:
        console.print("[bold red]ERROR:[/] Cannot connect to backend at " + API_BASE)
        console.print("       Make sure the backend is running: [cyan]python app.py[/]")
        sys.exit(1)

# ──────────────────────────────────────────────
#  Commands
# ──────────────────────────────────────────────

def cmd_login():
    """Simulate admin login with MFA."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]PhoenixVault — CLI Login[/]",
        border_style="cyan",
    ))
    username = console.input("[bold green]Username:[/] ")
    password = console.input("[bold green]Password:[/] ", password=True)

    totp = None
    if username == "admin":
        totp = console.input("[bold yellow]MFA Code (6 digits):[/] ")

    resp = _call("POST", "/auth/login", json={
        "username": username,
        "password": password,
        "totp_code": totp,
    })

    if resp.status_code == 200:
        data = resp.json()
        console.print(f"\n[bold green]✓ Login successful![/]  Role: [bold]{data['role']}[/]")
    else:
        console.print(f"\n[bold red]✗ Login failed:[/] {resp.json().get('detail', 'Unknown error')}")


def cmd_attack():
    """Trigger the ransomware simulation."""
    console.print()
    console.print(Panel(
        "[bold red blink]⚠  RANSOMWARE ATTACK SIMULATION  ⚠[/]\n\n"
        "This will simulate a 3-stage ransomware attack:\n"
        "  [red]1.[/] File encryption on the File Server\n"
        "  [red]2.[/] Backup deletion attempt (blocked by immutable storage)\n"
        "  [red]3.[/] Lateral movement across internal network\n",
        border_style="red",
        title="[bold white on red] DANGER ",
        title_align="center",
    ))

    confirm = console.input("\n[bold yellow]Proceed? (y/N):[/] ")
    if confirm.lower() != "y":
        console.print("[dim]Attack cancelled.[/]")
        return

    console.print()
    resp = _call("POST", "/attack/start")
    if resp.status_code == 200:
        console.print("[bold red]🔴 Attack sequence initiated![/]\n")

        # Poll and display stages
        stages_seen = set()
        with Progress(
            SpinnerColumn("dots", style="red"),
            TextColumn("[bold red]{task.description}[/]"),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for attack stages...", total=None)

            for _ in range(40):  # poll for up to ~40 seconds
                time.sleep(1)
                overview = _call("GET", "/status/overview").json()
                stage = overview.get("attack_stage", "NONE")

                if stage not in stages_seen and stage != "NONE":
                    stages_seen.add(stage)
                    if stage == "ENCRYPTION":
                        progress.update(task, description="Stage 1: Encrypting files...")
                    elif stage == "BACKUP_DELETION":
                        progress.update(task, description="Stage 2: Attempting backup deletion...")
                    elif stage == "LATERAL_MOVEMENT":
                        progress.update(task, description="Stage 3: Lateral movement in progress...")
                    elif stage == "COMPLETE":
                        progress.update(task, description="Attack complete — all systems compromised!")
                        time.sleep(1)
                        break

        console.print("\n[bold red]★ Attack simulation finished.[/]")
        console.print("[bold yellow]Run [cyan]python attack_sim.py recover[/] to start recovery.[/]")
    else:
        console.print(f"[bold red]Error:[/] {resp.json().get('detail')}")


def cmd_recover():
    """Trigger the recovery process."""
    console.print()
    console.print(Panel(
        "[bold green]🛡 RECOVERY ORCHESTRATION[/]\n\n"
        "Restoring systems from immutable backups\n"
        "in dependency order...",
        border_style="green",
        title="[bold white on green] RECOVERY ",
        title_align="center",
    ))

    resp = _call("POST", "/attack/recover")
    if resp.status_code != 200:
        console.print(f"[bold red]Error:[/] {resp.json().get('detail')}")
        return

    console.print("[bold green]Recovery initiated![/]\n")

    with Progress(
        SpinnerColumn("dots", style="green"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
        TextColumn("[bold]{task.description}[/]"),
        TextColumn("[cyan]{task.percentage:>3.0f}%[/]"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing...", total=100)

        prev_pct = 0
        for _ in range(60):
            time.sleep(0.5)
            overview = _call("GET", "/status/overview").json()
            rec = overview.get("recovery", {})
            pct = rec.get("progress_pct", 0)
            phase = rec.get("phase", "")

            if pct != prev_pct:
                progress.update(task, completed=pct, description=phase)
                prev_pct = pct

            if phase == "COMPLETE":
                progress.update(task, completed=100, description="RECOVERY COMPLETE")
                break

    # Final summary
    overview = _call("GET", "/status/overview").json()
    rec = overview.get("recovery", {})
    elapsed = rec.get("elapsed_sec", 0)

    console.print()
    console.print(Panel(
        f"[bold green]★ ALL SYSTEMS RESTORED[/]\n\n"
        f"  Recovery Time:  [bold cyan]{elapsed}s[/]\n"
        f"  Systems Online: [bold cyan]{rec.get('systems_recovered', 0)}/{rec.get('systems_total', 0)}[/]\n"
        f"  Integrity:      [bold green]VERIFIED[/]",
        border_style="green",
        title="[bold white on green] RESULT ",
        title_align="center",
    ))


def cmd_status():
    """Print current system status."""
    overview = _call("GET", "/status/overview").json()

    # Systems table
    table = Table(title="System Status", box=box.ROUNDED, border_style="cyan")
    table.add_column("System", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Health", justify="center")

    for s in overview["systems"]:
        status = s["status"]
        if status == "online":
            status_str = "[green]● ONLINE[/]"
        elif status == "compromised":
            status_str = "[red]◉ COMPROMISED[/]"
        elif status == "recovering":
            status_str = "[yellow]◎ RECOVERING[/]"
        elif status == "restored":
            status_str = "[blue]● RESTORED[/]"
        else:
            status_str = status

        health = s["health_pct"]
        if health >= 80:
            health_str = f"[green]{health}%[/]"
        elif health >= 50:
            health_str = f"[yellow]{health}%[/]"
        else:
            health_str = f"[red]{health}%[/]"

        table.add_row(s["name"], status_str, health_str)

    console.print()
    console.print(table)

    # Backup table
    btable = Table(title="Backup Records", box=box.ROUNDED, border_style="blue")
    btable.add_column("ID", style="bold")
    btable.add_column("Created", style="dim")
    btable.add_column("Size (MB)", justify="right")
    btable.add_column("Integrity", justify="center")
    btable.add_column("Immutable", justify="center")

    for b in overview["backups"]:
        integrity = b["integrity"]
        if integrity == "VERIFIED":
            i_str = "[green]VERIFIED[/]"
        elif integrity == "CORRUPTED":
            i_str = "[red]CORRUPTED[/]"
        else:
            i_str = "[yellow]PENDING[/]"

        imm = "[green]✓[/]" if b["immutable"] else "[red]✗[/]"
        btable.add_row(b["backup_id"], b["created_at"], str(b["size_mb"]), i_str, imm)

    console.print(btable)

    # Attack state
    if overview["attack_active"]:
        console.print(f"\n[bold red]⚠ ATTACK ACTIVE — Stage: {overview['attack_stage']}[/]")
    else:
        console.print("\n[bold green]✓ No active threats[/]")

    # Recent alerts
    alerts = overview.get("alerts", [])
    if alerts:
        console.print(f"\n[bold]Last {min(5, len(alerts))} Alerts:[/]")
        for a in alerts[-5:]:
            sev = a["severity"]
            if sev == "CRITICAL":
                color = "red"
            elif sev == "WARNING":
                color = "yellow"
            else:
                color = "dim"
            console.print(f"  [{color}]{a['timestamp']} [{a['severity']}] {a['source']}: {a['message']}[/]")


def cmd_reset():
    """Reset the simulation."""
    resp = _call("POST", "/attack/reset")
    if resp.status_code == 200:
        console.print("[bold green]✓ Simulation environment reset to clean state[/]")
    else:
        console.print(f"[bold red]Error:[/] {resp.json().get('detail')}")

# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────

COMMANDS = {
    "login": cmd_login,
    "attack": cmd_attack,
    "recover": cmd_recover,
    "reset": cmd_reset,
    "status": cmd_status,
}

def main():
    console.print(Panel.fit(
        "[bold cyan]PhoenixVault[/] — [dim]Ransomware Simulation CLI[/]",
        border_style="bright_cyan",
    ))

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        console.print("\n[bold]Available commands:[/]")
        console.print("  [cyan]login[/]    — Authenticate (admin requires MFA)")
        console.print("  [red]attack[/]   — Start ransomware simulation")
        console.print("  [green]recover[/]  — Initiate recovery orchestration")
        console.print("  [yellow]status[/]   — Show current system overview")
        console.print("  [blue]reset[/]    — Reset simulation environment")
        console.print("\n[dim]Example: python attack_sim.py attack[/]")
        return

    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
