import os
import sys
import datetime
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from src.app.state import AgentState

def human_approval(state: AgentState) -> dict:
    console = Console()
    
    suggestion  = state["suggestion"]
    selector    = state["selector"]
    confidence  = float(state["confidence"])
    reason      = state["reason"]
    timestamp   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_short  = state["test_name"].split("::")[-1]

    error_lines = state.get("error", "—").splitlines() if state.get("error") else ["—"]
    error_short = next(
        (l.strip() for l in error_lines if "TimeoutError" in l or "Error:" in l),
        error_lines[0]
    )

    file_path = state.get("file_path")
    line_number = state.get("line_number")
    base_dir = Path(__file__).parent.parent.parent.parent

    # Header
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row(
        Text("SELF-HEALING AGENT  —  HUMAN APPROVAL", style="bold blue"),
        Text(f"  {timestamp}", style="dim")
    )
    console.print(Panel(header, style="blue", box=box.SQUARE))

    layout_table = Table.grid(expand=True)
    layout_table.add_column(ratio=1)
    layout_table.add_column(ratio=1)

    # Left Panel
    left_table = Table.grid(padding=(0, 2))
    left_table.add_column(style="dim")
    left_table.add_column()
    left_table.add_row("SELECTOR", Text(f" {selector} ", style="bold white on red"))
    left_table.add_row("ERROR", Text(error_short, style="yellow"))
    left_table.add_row("TEST", Text(test_short, style="dim"))
    if file_path:
        try:
            rel_path = os.path.relpath(file_path, base_dir)
            left_table.add_row("FILE", Text(f"{rel_path}:{line_number}", style="dim"))
        except ValueError:
            left_table.add_row("FILE", Text(f"{file_path}:{line_number}", style="dim"))
    
    left_panel = Panel(left_table, title="[dim]broken selector[/dim]", title_align="left", expand=True, border_style="dim")

    # Right Panel
    right_table = Table.grid(padding=(0, 2))
    right_table.add_column(style="dim")
    right_table.add_column()
    right_table.add_row("FIX WITH", Text(f" {suggestion} ", style="bold white on green"))
    
    bar_width = int((confidence / 100) * 20)
    conf_bar = "█" * bar_width + "░" * (20 - bar_width)
    conf_label = "HIGH" if confidence >= 70 else "MED"
    right_table.add_row("CONFIDENCE", Text.assemble(
        (conf_bar, "green"), " ", 
        (f"{confidence:.1f}%", "bold green"), " ", 
        (conf_label, "bold white on blue")
    ))
    # line 77 — wrap every field that could be None
    right_table.add_row("REASON",     Text(reason     or "N/A", style="white"))
    right_table.add_row("SUGGESTION", Text(suggestion or "N/A", style="white"))
    right_table.add_row("CONFIDENCE", Text(str(confidence) if confidence is not None else "0.0", style="white"))
    right_panel = Panel(right_table, title="[dim]llm suggestion[/dim]", title_align="left", expand=True, border_style="dim")

    layout_table.add_row(left_panel, right_panel)
    console.print(layout_table)
    
    # footer interaction
    footer = Table.grid(expand=True)
    footer.add_column()
    footer.add_column(justify="right")
    footer.add_row(
        Text("self-healing-agent  ·  langgraph + groq", style="dim"),
        Text("[A]ccept Fix   [R]eject Fix   [C]opy Fix", style="bold")
    )
    console.print(Panel(footer, border_style="dim", box=box.SQUARE))

    approved = False

    # Read input
    console.print("[dim]Action [(A)ccept / (R)eject / (C)opy]: [/dim]", end="")
    try:
        if sys.platform == "win32":
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
            key = msvcrt.getch()
            try:
                char = key.decode("utf-8").lower()
            except Exception:
                char = ""
        else:
            try:
                import tty, termios
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    char = sys.stdin.read(1).lower()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except Exception:
                char = input("").strip().lower()
                
        console.print(char.upper())

        if char == 'a':
            approved = True
            console.print("[bold green]✓ Fix accepted. Applying...[/bold green]")
        elif char == 'r':
            console.print("[bold red]✗ Fix rejected.[/bold red]")
        elif char == 'c':
            _copy_to_clip(suggestion, console)
            console.print("[dim]Continuing without applying fix (copied to clipboard)[/dim]")
    except Exception as e:
        console.print(f"\n[dim]Continuing...[/dim]")

    return {
        "approved": approved,
        "file_path": file_path,
        "line_number": line_number
    }

def _copy_to_clip(text: str, console: Console):
    import subprocess, sys
    try:
        if sys.platform == "win32":
            subprocess.run("clip", input=text.encode(), check=True)
        elif sys.platform == "darwin":
            subprocess.run("pbcopy", input=text.encode(), check=True)
        else:
            subprocess.run(["xclip", "-selection", "clipboard"],
                           input=text.encode(), check=True)
        console.print(f"[bold green]✓ Copied to clipboard:[/bold green] {text}")
    except Exception:
        console.print("[bold red]✗ Could not copy to clipboard[/bold red]")
