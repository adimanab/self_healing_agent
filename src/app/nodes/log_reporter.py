import datetime
import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich import box

def print_healing_report(state: dict) -> None:
    console = Console()
    
    suggestion  = state.get("suggestion", "—")
    selector    = state.get("selector",   "—")
    confidence  = float(state.get("confidence", 0.0))
    step_passed = bool(state.get("step_passed", False))
    reason      = state.get("reason", "—")
    timestamp   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_short  = state.get("test_name", "—").split("::")[-1]

    error_lines = state.get("error", "—").splitlines() if state.get("error") else ["—"]
    error_short = next(
        (l.strip() for l in error_lines if "TimeoutError" in l or "Error:" in l),
        error_lines[0]
    )

    status       = "HEALED" if step_passed else "FAILED"
    status_style = "bold green" if step_passed else "bold red"

    # Header
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row(
        Text("SELF-HEALING AGENT  —  SELECTOR REPAIR", style="bold blue"),
        Text.assemble((status, status_style), f"  {timestamp}", style="dim")
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
    right_table.add_row("REASON", Text(reason, style="white"))
    
    right_panel = Panel(right_table, title="[dim]llm suggestion[/dim]", title_align="left", expand=True, border_style="dim")

    layout_table.add_row(left_panel, right_panel)
    console.print(layout_table)
    
    # footer
    footer = Table.grid(expand=True)
    footer.add_column()
    footer.add_column(justify="right")
    footer.add_row(
        Text("self-healing-agent  ·  langgraph + groq", style="dim"),
        Text("[C] copy fix   [Enter] continue", style="dim")
    )
    console.print(Panel(footer, border_style="dim", box=box.SQUARE))

    # Read input directly from the console to avoid pytest capture issues
    console.print("[dim]Press 'C' to copy fix, or Enter to continue... [/dim]", end="")
    try:
        if sys.platform == "win32":
            import msvcrt
            # Flush existing keys
            while msvcrt.kbhit():
                msvcrt.getch()
            # Wait for key
            key = msvcrt.getch()
            # If carriage return/enter, continue
            if key in (b'\r', b'\n'):
                console.print()
            else:
                try:
                    char = key.decode("utf-8").lower()
                except Exception:
                    char = ""
                console.print(char)
                if char == 'c':
                    _copy_to_clip(suggestion, console)
        else:
            # try to use simple input, might be captured by pytest, 
            # so we'll fallback to reading /dev/tty
            try:
                import tty, termios
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
                if ch.lower() == 'c':
                    console.print("\n")
                    _copy_to_clip(suggestion, console)
                else:
                    console.print("\n")
            except Exception:
                user_input = input("").strip().lower()
                if user_input == 'c':
                    _copy_to_clip(suggestion, console)
    except Exception as e:
        console.print(f"\n[dim]Continuing...[/dim]")

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