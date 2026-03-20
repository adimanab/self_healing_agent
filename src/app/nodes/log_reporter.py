import datetime
from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding


# ── Widgets ───────────────────────────────────────────────────────────────────

class SectionTitle(Static):
    DEFAULT_CSS = """
    SectionTitle {
        color: $text-muted;
        text-style: bold;
        padding: 0 0 1 0;
        border-bottom: solid $surface-lighten-2;
    }
    """

class FieldKey(Static):
    DEFAULT_CSS = "FieldKey { color: $text-disabled; padding: 1 0 0 0; }"

class ChipRed(Static):
    DEFAULT_CSS = """
    ChipRed {
        background: $error 15%;
        color: $error;
        padding: 0 2;
        width: auto;
    }
    """

class ChipGreen(Static):
    DEFAULT_CSS = """
    ChipGreen {
        background: $success 15%;
        color: $success;
        padding: 0 2;
        width: auto;
    }
    """

class ReasonBox(Static):
    DEFAULT_CSS = """
    ReasonBox {
        background: $surface;
        border: solid $surface-lighten-2;
        padding: 1 2;
        color: $text-muted;
        margin-top: 1;
    }
    """

class StatCard(Static):
    DEFAULT_CSS = """
    StatCard {
        background: $surface;
        border: solid $surface-lighten-1;
        padding: 1 2;
        width: 1fr;
        height: 5;
    }
    """


# ── App ───────────────────────────────────────────────────────────────────────

class HealingReportApp(App):

    CSS = """
    Screen { background: $background; }

    #header-bar {
        height: 3;
        background: $surface;
        border-bottom: solid $primary;
        padding: 0 2;
        align: left middle;
    }
    #header-title { color: $primary; text-style: bold; width: 1fr; }
    #header-status { padding: 0 2; }

    #body { height: 1fr; }

    #left-panel, #right-panel {
        width: 1fr;
        padding: 2 3;
        border-right: solid $surface-lighten-1;
    }

    #stat-row   { height: 5; margin-top: 2; }

    #confidence-row { height: 3; align: left middle; }
    #conf-bar-bg    { width: 22; height: 1; background: $surface-lighten-1; }
    #conf-bar-fill  { height: 1; background: $success; }
    #conf-pct       { color: $success; padding: 0 1; }
    #conf-label     { background: $primary 20%; color: $primary; padding: 0 1; }

    #footer-bar {
        height: 3;
        background: $surface;
        border-top: solid $surface-lighten-2;
        padding: 0 2;
        align: left middle;
    }
    #footer-left { color: $text-disabled; width: 1fr; }

    .warn { color: $warning; }
    .dim  { color: $text-disabled; }
    """

    BINDINGS = [
        Binding("q", "quit",     "Quit"),
        Binding("c", "copy_fix", "Copy fix"),
    ]

    def __init__(self, state: dict):
        super().__init__()
        self.state       = state
        self.suggestion  = state.get("suggestion", "—")
        self.selector    = state.get("selector",   "—")
        self.confidence  = float(state.get("confidence", 0.0))
        self.step_passed = bool(state.get("step_passed", False))
        self.reason      = state.get("reason", "—")
        self.timestamp   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.test_short  = state.get("test_name", "—").split("::")[-1]

        self.error_short = next(
            (l.strip() for l in state.get("error", "").splitlines()
             if "TimeoutError" in l or "Error:" in l),
            state.get("error", "—").splitlines()[0]
        )

    def compose(self) -> ComposeResult:
        status       = "HEALED" if self.step_passed else "FAILED"
        status_style = "green"  if self.step_passed else "red"
        bar_width    = int((self.confidence / 100) * 20)

        with Horizontal(id="header-bar"):
            yield Static(
                "SELF-HEALING AGENT  —  SELECTOR REPAIR",
                id="header-title"
            )
            yield Static(
                f"[{status_style} bold]{status}[/{status_style} bold]"
                f"  [dim]{self.timestamp}[/dim]",
                id="header-status"
            )

        with Horizontal(id="body"):

            with Vertical(id="left-panel"):
                yield SectionTitle("broken selector")
                yield FieldKey("SELECTOR")
                yield ChipRed(f" {self.selector} ")
                yield FieldKey("ERROR")
                yield Static(self.error_short, classes="warn")
                yield FieldKey("TEST")
                yield Static(self.test_short, classes="dim")
                with Horizontal(id="stat-row"):
                    yield StatCard(
                        "[red bold]1[/red bold]\n[dim]selectors failed[/dim]"
                    )
                    yield StatCard(
                        "[yellow bold]30s[/yellow bold]\n[dim]timeout duration[/dim]"
                    )

            with Vertical(id="right-panel"):
                yield SectionTitle("llm suggestion")
                yield FieldKey("FIX WITH")
                yield ChipGreen(f" {self.suggestion} ")
                yield FieldKey("CONFIDENCE")
                with Horizontal(id="confidence-row"):
                    with Static(id="conf-bar-bg"):
                        yield Static(" " * bar_width, id="conf-bar-fill")
                    yield Static(f"{self.confidence:.1f}%", id="conf-pct")
                    yield Static(
                        "HIGH" if self.confidence >= 70 else "MED",
                        id="conf-label"
                    )
                yield FieldKey("REASON")
                yield ReasonBox(self.reason)

        with Horizontal(id="footer-bar"):
            yield Static(
                "self-healing-agent  ·  langgraph + groq",
                id="footer-left"
            )
            yield Static("[dim]Q[/dim] quit    [dim]C[/dim] copy fix")

    def action_quit(self):
        self.exit()

    def action_copy_fix(self):
        import subprocess, sys as _sys
        try:
            if _sys.platform == "win32":
                subprocess.run("clip", input=self.suggestion.encode(), check=True)
            elif _sys.platform == "darwin":
                subprocess.run("pbcopy", input=self.suggestion.encode(), check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=self.suggestion.encode(), check=True)
            self.notify(f"Copied: {self.suggestion}", severity="information")
        except Exception:
            self.notify("Could not copy to clipboard", severity="warning")


# ── Entry point ───────────────────────────────────────────────────────────────

def print_healing_report(state: dict) -> None:
    """Called from main.py inside its own thread — no asyncio conflict."""
    app = HealingReportApp(state)
    app.run()