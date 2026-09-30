"""Rich terminal visualization for Fate Engine simulation results."""

from __future__ import annotations

from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from fateengine.models import LifeArea, LifePath, OptionStatistics, SimulationResult

console = Console()

# ── Colour palette ──────────────────────────────────────────────────
_AREA_COLOURS: dict[LifeArea, str] = {
    LifeArea.CAREER: "bright_cyan",
    LifeArea.FINANCES: "green",
    LifeArea.HEALTH: "bright_red",
    LifeArea.RELATIONSHIPS: "magenta",
    LifeArea.SKILLS: "yellow",
    LifeArea.PERSONAL_GROWTH: "bright_blue",
}

_SCORE_COLOURS = [
    (8.0, "bright_green"),
    (6.0, "green"),
    (4.0, "yellow"),
    (2.0, "red"),
    (0.0, "bright_red"),
]


def _score_colour(score: float) -> str:
    for threshold, colour in _SCORE_COLOURS:
        if score >= threshold:
            return colour
    return "white"


def _bar(score: float, width: int = 20) -> str:
    filled = round(score / 10.0 * width)
    return "█" * filled + "░" * (width - filled)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Public render functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def render_banner() -> None:
    """Print the FATE ENGINE ASCII banner."""
    banner = Text(
        r"""
  ╔═══════════════════════════════════════════════╗
  ║   ███████╗ █████╗ ████████╗███████╗           ║
  ║   ██╔════╝██╔══██╗╚══██╔══╝██╔════╝           ║
  ║   █████╗  ███████║   ██║   █████╗             ║
  ║   ██╔══╝  ██╔══██║   ██║   ██╔══╝             ║
  ║   ██║     ██║  ██║   ██║   ███████╗           ║
  ║   ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝           ║
  ║          E  N  G  I  N  E                     ║
  ║     AI-Powered Life Path Simulator            ║
  ╚═══════════════════════════════════════════════╝
""",
        style="bold bright_cyan",
    )
    console.print(Align.center(banner))


def render_result(result: SimulationResult) -> None:
    """Render a full simulation result to the terminal."""
    render_banner()
    console.print()

    console.rule("[bold]Decision[/bold]")
    console.print(
        Panel(
            f"[bold]{result.decision.description}[/bold]\n\n"
            + "\n".join(f"  • {opt}" for opt in result.decision.options),
            title="🎯 The Question",
            border_style="bright_cyan",
        )
    )
    console.print()

    render_comparison(result.statistics)
    console.print()

    for option, paths in result.paths_by_option.items():
        render_life_paths(option, paths[:3])
        console.print()

    render_scores(result.statistics)
    console.print()

    if result.key_insights:
        render_insights(result.key_insights)
        console.print()

    if result.action_items:
        render_actions(result.action_items)
        console.print()

    if result.optimal_path:
        render_timeline(result.optimal_path)


def render_life_paths(option: str, paths: list[LifePath], *, max_display: int = 3) -> None:
    """Render a branching tree of life paths for one option."""
    tree = Tree(
        f"[bold bright_cyan]Option: {option}[/bold bright_cyan]",
        guide_style="bright_black",
    )

    for i, path in enumerate(paths[:max_display]):
        score_clr = _score_colour(path.overall_score)
        path_label = (
            f"[bold]Path {i + 1}[/bold]  "
            f"[{score_clr}]Overall: {path.overall_score:.1f}/10[/{score_clr}]"
        )
        branch = tree.add(path_label)

        for event in path.events:
            area_clr = _AREA_COLOURS.get(event.area, "white")
            impact_sign = "+" if event.impact_score >= 0 else ""
            branch.add(
                f"[dim]Year {event.year}[/dim]  "
                f"[{area_clr}][{event.area.value}][/{area_clr}]  "
                f"{event.description}  "
                f"[dim](impact {impact_sign}{event.impact_score:.2f}, "
                f"p={event.probability:.0%})[/dim]"
            )

    console.print(Panel(tree, title=f"🌳 Life Paths — {option}", border_style="green"))


def render_comparison(stats: list[OptionStatistics]) -> None:
    """Side-by-side comparison table of option statistics."""
    table = Table(
        title="📊 Option Comparison",
        show_header=True,
        header_style="bold bright_cyan",
        border_style="bright_black",
        expand=True,
    )
    table.add_column("Metric", style="bold")
    for s in stats:
        table.add_column(s.option, justify="center")

    rows: list[tuple[str, ...]] = [
        ("Mean Overall",) + tuple(f"{s.mean_overall:.1f}" for s in stats),
        ("Median Overall",) + tuple(f"{s.median_overall:.1f}" for s in stats),
        ("Best Case",) + tuple(f"{s.best_case:.1f}" for s in stats),
        ("Worst Case",) + tuple(f"{s.worst_case:.1f}" for s in stats),
        ("Std Dev (risk)",) + tuple(f"{s.std_dev:.2f}" for s in stats),
        ("Happiness",) + tuple(f"{s.mean_happiness:.1f}" for s in stats),
        ("Financial",) + tuple(f"{s.mean_financial:.1f}" for s in stats),
        ("Career",) + tuple(f"{s.mean_career:.1f}" for s in stats),
        ("Relationships",) + tuple(f"{s.mean_relationship:.1f}" for s in stats),
        ("Health",) + tuple(f"{s.mean_health:.1f}" for s in stats),
        ("Upside P(>7)",) + tuple(f"{s.upside_probability:.0%}" for s in stats),
        ("Downside P(<4)",) + tuple(f"{s.downside_probability:.0%}" for s in stats),
    ]

    for row in rows:
        table.add_row(*row)

    console.print(table)


def render_timeline(path: LifePath) -> None:
    """Year-by-year timeline for a single path."""
    console.rule(f"[bold]🗓  Optimal Path Timeline — {path.option}[/bold]")
    events_by_year: dict[int, list] = {}
    for ev in path.events:
        events_by_year.setdefault(ev.year, []).append(ev)

    for year in sorted(events_by_year):
        console.print(f"\n  [bold bright_cyan]━━ Year {year} ━━[/bold bright_cyan]")
        for ev in events_by_year[year]:
            area_clr = _AREA_COLOURS.get(ev.area, "white")
            icon = "▲" if ev.impact_score >= 0 else "▼"
            impact_clr = "green" if ev.impact_score >= 0 else "red"
            console.print(
                f"    [{impact_clr}]{icon}[/{impact_clr}] "
                f"[{area_clr}]{ev.area.value:<18}[/{area_clr}] "
                f"{ev.description}  "
                f"[dim](p={ev.probability:.0%})[/dim]"
            )


def render_scores(stats: list[OptionStatistics]) -> None:
    """Render bar-chart-style scores for each option."""
    panels: list[Panel] = []
    for s in stats:
        dimensions = [
            ("Happiness", s.mean_happiness),
            ("Financial", s.mean_financial),
            ("Career", s.mean_career),
            ("Relations", s.mean_relationship),
            ("Health", s.mean_health),
            ("OVERALL", s.mean_overall),
        ]
        lines: list[str] = []
        for label, score in dimensions:
            clr = _score_colour(score)
            bar = _bar(score)
            lines.append(f"  {label:<12} [{clr}]{bar} {score:.1f}[/{clr}]")
        body = "\n".join(lines)
        panels.append(
            Panel(body, title=f"[bold]{s.option}[/bold]", border_style="bright_black", width=48)
        )

    console.print(Panel(Columns(panels, equal=True), title="📈 Score Breakdown", border_style="cyan"))


def render_insights(insights: list[str]) -> None:
    """Render key insights panel."""
    body = "\n".join(f"  💡 {i}" for i in insights)
    console.print(Panel(body, title="[bold]🔍 Key Insights[/bold]", border_style="yellow"))


def render_actions(actions: list[str]) -> None:
    """Render action items panel."""
    body = "\n".join(f"  → {a}" for a in actions)
    console.print(Panel(body, title="[bold]✅ Recommended Actions[/bold]", border_style="green"))
