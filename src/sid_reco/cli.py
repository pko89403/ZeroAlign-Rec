"""CLI entry points for local development."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from sid_reco.config import Settings, ensure_project_directories
from sid_reco.datasets.foodcom import (
    DEFAULT_CORE_K,
    DEFAULT_POSITIVE_THRESHOLD,
    prepare_foodcom_dataset,
)
from sid_reco.embedding import MLXEmbeddingEncoder
from sid_reco.llm import MLXTextGenerator
from sid_reco.mlx_runtime import get_runtime_environment_summary, probe_mlx_runtime
from sid_reco.taxonomy.dictionary import DEFAULT_MAX_TOKENS, build_taxonomy_dictionary
from sid_reco.taxonomy.item_projection import (
    DEFAULT_ITEM_MAX_TOKENS,
    structure_taxonomy_batch,
    structure_taxonomy_item,
    write_structured_taxonomy_item,
)
from sid_reco.taxonomy.step1 import DEFAULT_TOP_K, build_taxonomy_step1

console = Console()
DEFAULT_FOODCOM_RAW_DIR = Path("data/raw/foodcom")
DEFAULT_FOODCOM_OUT_DIR = Path("data/processed/foodcom")
DEFAULT_TAXONOMY_RECIPES_PATH = DEFAULT_FOODCOM_OUT_DIR / "recipes.csv"
DEFAULT_TAXONOMY_OUT_DIR = DEFAULT_FOODCOM_OUT_DIR / "taxonomy_step1"
DEFAULT_TAXONOMY_DICTIONARY_OUT_DIR = DEFAULT_FOODCOM_OUT_DIR / "taxonomy_dictionary"
DEFAULT_TAXONOMY_NEIGHBOR_CONTEXT_PATH = DEFAULT_TAXONOMY_OUT_DIR / "neighbor_context.csv"
DEFAULT_TAXONOMY_DICTIONARY_PATH = (
    DEFAULT_TAXONOMY_DICTIONARY_OUT_DIR / "food_taxonomy_dictionary.json"
)
DEFAULT_TAXONOMY_STRUCTURED_OUT_PATH = (
    DEFAULT_FOODCOM_OUT_DIR / "taxonomy_structured" / "items.jsonl"
)
app = typer.Typer(
    help="Utilities for the SID-based training-free recommender.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """CLI entry point."""


@app.command()
def doctor() -> None:
    """Print local environment status."""
    ensure_project_directories()
    settings = Settings.from_env()

    table = Table(title="SID Reco Environment")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Platform", platform.platform())
    table.add_row("Project root", str(settings.project_root))
    table.add_row("LLM backend", settings.llm_backend)
    table.add_row("LLM model", settings.llm_model)
    table.add_row("Embedding model", settings.embed_model)
    table.add_row("Catalog path", str(settings.sid_catalog_path))
    table.add_row("Cache dir", str(settings.sid_cache_dir))
    table.add_row("Default max tokens", str(settings.llm_max_tokens))
    table.add_row("Default temperature", str(settings.llm_temperature))
    table.add_row("Default top_p", str(settings.llm_top_p))
    console.print(table)


@app.command("smoke-mlx")
def smoke_mlx() -> None:
    """Diagnose whether the current environment can initialize MLX safely."""
    environment = get_runtime_environment_summary()
    probes = [
        probe_mlx_runtime(imports=("mlx.core",)),
        probe_mlx_runtime(imports=("mlx.core", "mlx_lm")),
        probe_mlx_runtime(imports=("mlx.core", "mlx_embeddings")),
    ]

    env_table = Table(title="MLX Environment")
    env_table.add_column("Key", style="cyan", no_wrap=True)
    env_table.add_column("Value", overflow="fold")
    env_table.add_row("Platform", environment.platform_name)
    env_table.add_row("Machine", environment.machine)
    env_table.add_row("Python", environment.python_version)
    env_table.add_row("Session", environment.session_kind)
    env_table.add_row("Terminal", environment.term_program)
    env_table.add_row("Supported", "yes" if environment.supported else "no")
    env_table.add_row("Reason", environment.support_reason)
    console.print(env_table)

    probe_table = Table(title="MLX Probes")
    probe_table.add_column("Probe", style="cyan", no_wrap=True)
    probe_table.add_column("Status", no_wrap=True)
    probe_table.add_column("Metal", no_wrap=True)
    probe_table.add_column("Default device", overflow="fold")
    probe_table.add_column("Diagnostic", overflow="fold")
    for probe in probes:
        probe_table.add_row(
            ", ".join(probe.imports),
            "ok" if probe.ok else "fail",
            "-" if probe.metal_available is None else ("yes" if probe.metal_available else "no"),
            probe.default_device or "-",
            probe.diagnostic,
        )
    console.print(probe_table)

    if not environment.supported or any(not probe.ok for probe in probes):
        raise typer.Exit(code=1)


@app.command("smoke-llm")
def smoke_llm(
    prompt: str = typer.Argument(..., help="Prompt to send to the local MLX LLM."),
    system_prompt: str | None = typer.Option(
        None,
        "--system-prompt",
        help="Optional system prompt.",
    ),
    max_tokens: int | None = typer.Option(
        None,
        "--max-tokens",
        min=1,
        help="Override the default max token setting.",
    ),
) -> None:
    """Run a single prompt against the configured local MLX LLM."""
    settings = Settings.from_env()
    llm = MLXTextGenerator.from_settings(settings)
    response = llm.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens or settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        top_p=settings.llm_top_p,
    )
    console.print(response)


@app.command("smoke-embed")
def smoke_embed(
    text: str = typer.Argument(..., help="Text to encode with the local embedding model."),
) -> None:
    """Generate an embedding preview for one input string."""
    settings = Settings.from_env()
    encoder = MLXEmbeddingEncoder.from_settings(settings)
    vector = encoder.encode_one(text)

    table = Table(title="Embedding Preview")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Model", settings.embed_model)
    table.add_row("Dimension", str(len(vector)))
    table.add_row("Preview", ", ".join(f"{value:.4f}" for value in vector[:8]))
    console.print(table)


@app.command("prepare-foodcom")
def prepare_foodcom(
    raw_dir: Annotated[
        Path,
        typer.Option(
            "--raw-dir",
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Directory containing RAW_recipes.csv and RAW_interactions.csv.",
        ),
    ] = DEFAULT_FOODCOM_RAW_DIR,
    out_dir: Annotated[
        Path,
        typer.Option(
            "--out-dir",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where the processed dataset will be written.",
        ),
    ] = DEFAULT_FOODCOM_OUT_DIR,
    top_recipes: Annotated[
        int,
        typer.Option(
            "--top-recipes",
            min=1,
            help="Number of recipes to keep based on interaction count.",
        ),
    ] = 3000,
    core_k: Annotated[
        int,
        typer.Option(
            "--core-k",
            min=1,
            help="Minimum positive interactions required for both users and items.",
        ),
    ] = DEFAULT_CORE_K,
    positive_threshold: Annotated[
        float,
        typer.Option(
            "--positive-threshold",
            help="Ratings at or above this value are retained and binarized to 1.",
        ),
    ] = DEFAULT_POSITIVE_THRESHOLD,
) -> None:
    """Prepare a downsampled Food.com dataset for local recommendation experiments."""
    ensure_project_directories()
    try:
        summary = prepare_foodcom_dataset(
            raw_dir=raw_dir,
            out_dir=out_dir,
            top_recipes=top_recipes,
            core_k=core_k,
            positive_threshold=positive_threshold,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    table = Table(title="Prepared Food.com Dataset")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Output dir", str(out_dir))
    table.add_row("Recipes", str(summary.recipes_rows))
    table.add_row("Interactions", str(summary.interactions_rows))
    table.add_row("Train rows", str(summary.train_rows))
    table.add_row("Valid rows", str(summary.valid_rows))
    table.add_row("Test rows", str(summary.test_rows))
    table.add_row("Unique users", str(summary.unique_users))
    table.add_row("Unique recipes", str(summary.unique_recipes))
    console.print(table)


@app.command("build-taxonomy-step1")
def build_taxonomy_step1_command(
    recipes_path: Annotated[
        Path,
        typer.Option(
            "--recipes-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Processed recipe catalog path used to build item embeddings.",
        ),
    ] = DEFAULT_TAXONOMY_RECIPES_PATH,
    out_dir: Annotated[
        Path,
        typer.Option(
            "--out-dir",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where taxonomy step 1 outputs will be written.",
        ),
    ] = DEFAULT_TAXONOMY_OUT_DIR,
    top_k: Annotated[
        int,
        typer.Option(
            "--top-k",
            min=1,
            help="Number of item neighbors to keep for each source item.",
        ),
    ] = DEFAULT_TOP_K,
    batch_size: Annotated[
        int | None,
        typer.Option(
            "--batch-size",
            min=1,
            help="Optional embedding batch size override. Defaults to adaptive batching.",
        ),
    ] = None,
) -> None:
    """Build item embeddings and a FAISS top-k neighbor index for taxonomy step 1."""
    ensure_project_directories()
    settings = Settings.from_env()
    try:
        summary = build_taxonomy_step1(
            recipes_path=recipes_path,
            out_dir=out_dir,
            embed_model=settings.embed_model,
            top_k=top_k,
            batch_size=batch_size,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    table = Table(title="Taxonomy Step 1")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Output dir", str(out_dir))
    table.add_row("Embedding model", settings.embed_model)
    table.add_row("Items", str(summary.items_rows))
    table.add_row("Neighbor rows", str(summary.neighbor_rows))
    table.add_row("Embedding dim", str(summary.embedding_dim))
    table.add_row("Top-k", str(summary.top_k))
    table.add_row("Initial batch size", str(summary.initial_batch_size))
    table.add_row("Final batch size", str(summary.final_batch_size))
    console.print(table)


@app.command("build-taxonomy-dictionary")
def build_taxonomy_dictionary_command(
    recipes_path: Annotated[
        Path,
        typer.Option(
            "--recipes-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Processed recipe catalog path used to build the taxonomy dictionary.",
        ),
    ] = DEFAULT_TAXONOMY_RECIPES_PATH,
    out_dir: Annotated[
        Path,
        typer.Option(
            "--out-dir",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Directory where taxonomy dictionary outputs will be written.",
        ),
    ] = DEFAULT_TAXONOMY_DICTIONARY_OUT_DIR,
    max_tokens: Annotated[
        int,
        typer.Option(
            "--max-tokens",
            min=1,
            help="Maximum number of tokens for taxonomy dictionary generation.",
        ),
    ] = DEFAULT_MAX_TOKENS,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing taxonomy dictionary files in the output directory.",
        ),
    ] = False,
) -> None:
    """Generate a TaxRec-style taxonomy dictionary JSON from recipe metadata."""
    ensure_project_directories()
    settings = Settings.from_env()
    try:
        summary = build_taxonomy_dictionary(
            recipes_path=recipes_path,
            out_dir=out_dir,
            llm_model=settings.llm_model,
            max_tokens=max_tokens,
            overwrite=overwrite,
        )
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    table = Table(title="Taxonomy Dictionary")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Output dir", str(out_dir))
    table.add_row("LLM model", settings.llm_model)
    table.add_row("Catalog items", str(summary.items_count))
    table.add_row("Prompt items", str(summary.sampled_items_count))
    table.add_row("Features", str(summary.feature_count))
    table.add_row("Total values", str(summary.total_value_count))
    console.print(table)


@app.command("structure-taxonomy-item")
def structure_taxonomy_item_command(
    recipe_id: Annotated[
        int,
        typer.Option(
            "--recipe-id",
            min=1,
            help="Target recipe identifier to structure into taxonomy JSON.",
        ),
    ],
    recipes_path: Annotated[
        Path,
        typer.Option(
            "--recipes-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Processed recipe catalog path used to load target item metadata.",
        ),
    ] = DEFAULT_TAXONOMY_RECIPES_PATH,
    neighbor_context_path: Annotated[
        Path,
        typer.Option(
            "--neighbor-context-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Taxonomy step 1 neighbor_context.csv path.",
        ),
    ] = DEFAULT_TAXONOMY_NEIGHBOR_CONTEXT_PATH,
    taxonomy_dictionary_path: Annotated[
        Path,
        typer.Option(
            "--taxonomy-dictionary-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Master taxonomy dictionary JSON path.",
        ),
    ] = DEFAULT_TAXONOMY_DICTIONARY_PATH,
    out_path: Annotated[
        Path | None,
        typer.Option(
            "--out-path",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Optional file path to persist the structured item JSON.",
        ),
    ] = None,
    max_tokens: Annotated[
        int,
        typer.Option(
            "--max-tokens",
            min=1,
            help="Maximum number of tokens for single-item taxonomy structuring.",
        ),
    ] = DEFAULT_ITEM_MAX_TOKENS,
    include_evidence: Annotated[
        bool,
        typer.Option(
            "--include-evidence",
            help="Include target item metadata and top-5 neighbor references in the JSON output.",
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite the single-item JSON output when --out-path already exists.",
        ),
    ] = False,
) -> None:
    """Structure one recipe item into taxonomy-aligned JSON."""
    ensure_project_directories()
    settings = Settings.from_env()
    try:
        structured_item = structure_taxonomy_item(
            recipe_id=recipe_id,
            recipes_path=recipes_path,
            neighbor_context_path=neighbor_context_path,
            taxonomy_dictionary_path=taxonomy_dictionary_path,
            llm_model=settings.llm_model,
            max_tokens=max_tokens,
            include_evidence=include_evidence,
        )
        if out_path is not None:
            write_structured_taxonomy_item(
                structured_item=structured_item,
                out_path=out_path,
                overwrite=overwrite,
            )
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(
        json.dumps(structured_item.to_record(), ensure_ascii=False, sort_keys=True),
        soft_wrap=True,
    )


@app.command("structure-taxonomy-batch")
def structure_taxonomy_batch_command(
    recipes_path: Annotated[
        Path,
        typer.Option(
            "--recipes-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Processed recipe catalog path used to load item metadata.",
        ),
    ] = DEFAULT_TAXONOMY_RECIPES_PATH,
    neighbor_context_path: Annotated[
        Path,
        typer.Option(
            "--neighbor-context-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Taxonomy step 1 neighbor_context.csv path.",
        ),
    ] = DEFAULT_TAXONOMY_NEIGHBOR_CONTEXT_PATH,
    taxonomy_dictionary_path: Annotated[
        Path,
        typer.Option(
            "--taxonomy-dictionary-path",
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Master taxonomy dictionary JSON path.",
        ),
    ] = DEFAULT_TAXONOMY_DICTIONARY_PATH,
    out_path: Annotated[
        Path,
        typer.Option(
            "--out-path",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="Output JSONL path for the structured item batch.",
        ),
    ] = DEFAULT_TAXONOMY_STRUCTURED_OUT_PATH,
    max_tokens: Annotated[
        int,
        typer.Option(
            "--max-tokens",
            min=1,
            help="Maximum number of tokens for each item taxonomy structuring call.",
        ),
    ] = DEFAULT_ITEM_MAX_TOKENS,
    include_evidence: Annotated[
        bool,
        typer.Option(
            "--include-evidence",
            help="Include target item metadata and top-5 neighbor references in each JSONL record.",
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite the batch JSONL output when it already exists.",
        ),
    ] = False,
) -> None:
    """Structure the full recipe catalog into per-item taxonomy JSON Lines."""
    ensure_project_directories()
    settings = Settings.from_env()

    def log_progress(completed: int, total: int, recipe_id: int) -> None:
        if completed == 1 or completed == total or completed % 10 == 0:
            console.print(f"Progress {completed}/{total} (recipe_id={recipe_id})")

    try:
        summary = structure_taxonomy_batch(
            recipes_path=recipes_path,
            neighbor_context_path=neighbor_context_path,
            taxonomy_dictionary_path=taxonomy_dictionary_path,
            out_path=out_path,
            llm_model=settings.llm_model,
            max_tokens=max_tokens,
            include_evidence=include_evidence,
            overwrite=overwrite,
            progress_callback=log_progress,
        )
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    table = Table(title="Taxonomy Item Structuring Batch")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", overflow="fold")
    table.add_row("Output path", str(summary.output_path))
    table.add_row("Items", str(summary.item_count))
    table.add_row("Taxonomy keys", str(summary.taxonomy_key_count))
    table.add_row("Tagged values", str(summary.total_tagged_value_count))
    console.print(table)


if __name__ == "__main__":
    app()
