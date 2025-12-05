"""
FastAPI application and CLI entry point for Clinical MAS Planner.
"""

from pathlib import Path
from typing import Optional

import typer
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .aggregator import run_aggregator
from .config import Config, get_config
from .llm_client import create_llm_client
from .logging_utils import save_trace
from .medqa import evaluate_on_subset
from .orchestration import run_case
from .planner import run_planner
from .safety import DISCLAIMER, print_disclaimer
from .schemas import (
    AggregateRequest,
    CaseInput,
    ConsultRequest,
    EvaluationResult,
    FinalDecision,
    PlannerResult,
    SpecialistReport,
)
from .specialists import run_specialists

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Clinical MAS Planner",
    description="Multi-Agent Diagnostic Reasoning System for Clinical Decision Support",
    version=__version__,
)


@app.get("/")
def root():
    """Root endpoint with disclaimer."""
    return {
        "service": "Clinical MAS Planner",
        "version": __version__,
        "disclaimer": "Educational prototype - NOT for clinical use",
        "endpoints": ["/plan", "/consult", "/aggregate", "/run", "/eval/medqa"],
    }


@app.post("/plan", response_model=PlannerResult)
def plan_endpoint(case: CaseInput):
    """
    Run the planner to select Top-K specialties.

    Args:
        case: Clinical case input

    Returns:
        PlannerResult with selected specialties
    """
    try:
        config = get_config()
        llm_client = create_llm_client(config)

        planner_result, _ = run_planner(
            question=case.question,
            options=case.options,
            llm_client=llm_client,
            config=config,
        )

        return planner_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consult", response_model=list[SpecialistReport])
def consult_endpoint(request: ConsultRequest):
    """
    Run specialist consultations.

    Args:
        request: Consultation request with planner result

    Returns:
        List of specialist reports
    """
    try:
        config = get_config()
        llm_client = create_llm_client(config)

        specialist_results = run_specialists(
            selected_specialties=request.planner_result.selected_specialties,
            question=request.question,
            options=request.options,
            planner_result=request.planner_result,
            llm_client=llm_client,
            config=config,
        )

        reports = [report for report, _ in specialist_results]
        return reports

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/aggregate", response_model=FinalDecision)
def aggregate_endpoint(request: AggregateRequest):
    """
    Aggregate specialist reports into final decision.

    Args:
        request: Aggregation request with specialist reports

    Returns:
        Final decision
    """
    try:
        config = get_config()
        llm_client = create_llm_client(config)

        final_decision, _ = run_aggregator(
            question=request.question,
            options=request.options,
            specialist_reports=request.specialist_reports,
            llm_client=llm_client,
            config=config,
        )

        return final_decision

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run", response_model=FinalDecision)
def run_endpoint(case: CaseInput):
    """
    Run complete case through the multi-agent system.

    Args:
        case: Clinical case input

    Returns:
        Final decision with trace saved
    """
    try:
        config = get_config()

        final_decision, trace = run_case(
            question=case.question,
            options=case.options,
            config=config,
        )

        # Save trace
        save_trace(trace, config)

        return final_decision

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/eval/medqa", response_model=EvaluationResult)
def eval_medqa_endpoint(
    config_name: str = "eval_medqa.yaml",
    n_samples: Optional[int] = None,
):
    """
    Evaluate on MedQA subset.

    Args:
        config_name: Config file name (in configs/ directory)
        n_samples: Number of samples (overrides config)

    Returns:
        Evaluation results
    """
    try:
        config_path = Path("configs") / config_name

        # Load eval config
        if config_path.exists():
            config = Config.from_yaml(config_path)
            dataset_path = config.model_dump().get("dataset", {}).get("path")
            n = n_samples or config.model_dump().get("dataset", {}).get("n_samples", 100)
        else:
            dataset_path = None
            n = n_samples or 10

        result = evaluate_on_subset(
            n=n,
            config_path=config_path if config_path.exists() else None,
            dataset_path=dataset_path,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLI App (Typer)
# ============================================================================

cli = typer.Typer(
    name="mas",
    help="Clinical MAS Planner - Multi-Agent Diagnostic Reasoning System",
    add_completion=False,
)

console = Console()


@cli.command()
def run(
    question: str = typer.Option(..., "--question", "-q", help="Clinical question or case"),
    options: Optional[str] = typer.Option(None, "--options", "-o", help="Options separated by ||"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config YAML file"),
):
    """Run a complete case through the multi-agent system."""
    print_disclaimer()

    try:
        # Parse options
        options_list = options.split("||") if options else None

        # Load config
        cfg = Config.from_yaml(config) if config else get_config()

        # Run case
        console.print("\n[bold cyan]Running multi-agent diagnostic system...[/bold cyan]\n")

        final_decision, trace = run_case(
            question=question,
            options=options_list,
            config=cfg,
        )

        # Save trace
        trace_path = save_trace(trace, cfg)

        # Display results
        console.print(Panel(
            f"[bold green]Final Answer:[/bold green] {final_decision.final_answer}\n\n"
            f"[bold]Justification:[/bold]\n{final_decision.justification}",
            title="Final Decision",
            border_style="green"
        ))

        if final_decision.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in final_decision.warnings:
                console.print(f"  • {warning}")

        console.print(f"\n[dim]Trace saved to: {trace_path}[/dim]\n")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@cli.command()
def plan(
    question: str = typer.Option(..., "--question", "-q", help="Clinical question"),
    options: Optional[str] = typer.Option(None, "--options", "-o", help="Options separated by ||"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config YAML file"),
):
    """Run planner only to select specialties."""
    try:
        options_list = options.split("||") if options else None
        cfg = Config.from_yaml(config) if config else get_config()
        llm_client = create_llm_client(cfg)

        planner_result, _ = run_planner(
            question=question,
            options=options_list,
            llm_client=llm_client,
            config=cfg,
        )

        console.print(Panel(
            f"[bold]Triage:[/bold] {planner_result.triage_generalist}\n\n"
            f"[bold]Selected Specialties:[/bold]\n" +
            "\n".join(f"  • {s}" for s in planner_result.selected_specialties) +
            f"\n\n[bold]Rationale:[/bold]\n{planner_result.rationale}",
            title="Planner Result",
            border_style="cyan"
        ))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@cli.command()
def eval(
    config: str = typer.Option("configs/eval_medqa.yaml", "--config", "-c", help="Eval config file"),
    n: Optional[int] = typer.Option(None, "--n", help="Number of samples"),
):
    """Evaluate on MedQA subset."""
    print_disclaimer()

    try:
        console.print("\n[bold cyan]Starting MedQA evaluation...[/bold cyan]\n")

        config_path = Path(config)
        result = evaluate_on_subset(
            n=n or 100,
            config_path=config_path if config_path.exists() else None,
        )

        # Display results
        table = Table(title="Evaluation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Samples", str(result.n_samples))
        table.add_row("Correct", str(result.n_correct))
        table.add_row("Accuracy", f"{result.accuracy:.2%}")
        table.add_row("Avg Latency", f"{result.avg_latency_seconds:.2f}s")
        if result.avg_tokens_used:
            table.add_row("Avg Tokens", f"{result.avg_tokens_used:.0f}")
        table.add_row("Traces", result.traces_path)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@cli.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code changes"),
):
    """Start the FastAPI server."""
    print_disclaimer()
    console.print(f"\n[bold green]Starting API server on {host}:{port}[/bold green]\n")
    console.print(f"[dim]API docs: http://{host}:{port}/docs[/dim]\n")

    uvicorn.run(
        "src.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def version():
    """Show version information."""
    console.print(f"Clinical MAS Planner v{__version__}")


def cli_app():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    cli_app()
