"""Taxonomy dictionary generation helpers."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sid_reco.llm import MLXTextGenerator

TAXONOMY_ITEM_COLUMNS = ["recipe_id", "name", "description", "tags", "ingredients"]
DEFAULT_MAX_TOKENS = 4096
DEFAULT_REPAIR_MAX_TOKENS = 2048
DEFAULT_MAX_PROMPT_ITEMS = 1000
DEFAULT_MAX_PAYLOAD_CHARS = 200000
FULL_CATALOG_SAMPLING_STRATEGY = "full_catalog"
EVENLY_SPACED_SAMPLING_STRATEGY = "evenly_spaced"

SYSTEM_PROMPT = (
    "You are an expert in food recommendations and domain taxonomy design. "
    "Return only valid JSON."
)

FEW_SHOT_EXAMPLES: tuple[dict[str, Any], ...] = (
    {
        "items": [
            {
                "recipe_id": 1,
                "name": "classic tomato basil soup",
                "description": "A simple Italian-style tomato soup for lunch.",
                "tags": ["italian", "soup", "vegetarian", "stovetop"],
                "ingredients": ["tomato", "basil", "garlic", "olive oil"],
            },
            {
                "recipe_id": 2,
                "name": "grilled lemon chicken",
                "description": "American dinner recipe with grilled chicken breast.",
                "tags": ["american", "grilled", "dinner"],
                "ingredients": ["chicken breast", "lemon", "black pepper"],
            },
        ],
        "taxonomy": {
            "cuisine": ["american", "italian"],
            "dish_type": ["soup"],
            "cooking_method": ["grilled", "stovetop"],
            "primary_ingredient": ["chicken_breast", "tomato"],
            "dietary_style": ["vegetarian"],
        },
    },
    {
        "items": [
            {
                "recipe_id": 10,
                "name": "thai peanut noodles",
                "description": "Quick noodle bowl with Thai-inspired peanut sauce.",
                "tags": ["thai", "noodles", "quick", "vegetarian"],
                "ingredients": ["rice noodles", "peanut butter", "soy sauce"],
            },
            {
                "recipe_id": 11,
                "name": "baked cheddar potato casserole",
                "description": "Comfort-food side dish baked in the oven.",
                "tags": ["baked", "casserole", "side_dish", "comfort_food"],
                "ingredients": ["potato", "cheddar cheese", "milk"],
            },
        ],
        "taxonomy": {
            "cuisine": ["thai"],
            "dish_type": ["casserole", "noodles", "side_dish"],
            "cooking_method": ["baked"],
            "primary_ingredient": ["cheddar_cheese", "potato", "rice_noodles"],
            "dietary_style": ["vegetarian"],
            "taste_mood": ["comfort_food"],
        },
    },
)


@dataclass(frozen=True, slots=True)
class TaxonomyPayload:
    """Bounded taxonomy payload metadata used before prompt construction."""

    items_count: int
    sampled_items_count: int
    max_prompt_items: int
    sampling_strategy: str
    dataset_payload: str


@dataclass(frozen=True, slots=True)
class TaxonomyPromptBundle:
    """Prompt payload used to generate the taxonomy dictionary."""

    items_count: int
    sampled_items_count: int
    max_prompt_items: int
    sampling_strategy: str
    dataset_payload: str
    system_prompt: str
    user_prompt: str


@dataclass(frozen=True, slots=True)
class TaxonomyDictionarySummary:
    """High-level summary for taxonomy dictionary generation."""

    items_count: int
    sampled_items_count: int
    feature_count: int
    total_value_count: int


def load_taxonomy_items(recipes_path: Path) -> list[dict[str, Any]]:
    """Load processed recipe metadata for taxonomy generation."""
    if not recipes_path.exists():
        raise FileNotFoundError(f"Missing recipe catalog file: {recipes_path}")

    catalog = pd.read_csv(recipes_path)
    missing = sorted(set(TAXONOMY_ITEM_COLUMNS).difference(catalog.columns))
    if missing:
        raise ValueError(f"Missing required recipe catalog columns: {', '.join(missing)}")

    items: list[dict[str, Any]] = []
    normalized = catalog.loc[:, TAXONOMY_ITEM_COLUMNS].copy()
    normalized["recipe_id"] = pd.to_numeric(normalized["recipe_id"], errors="coerce")
    normalized = normalized.loc[normalized["recipe_id"].notna()].copy()
    normalized["recipe_id"] = normalized["recipe_id"].astype(int)
    normalized = normalized.sort_values("recipe_id", kind="mergesort").drop_duplicates("recipe_id")

    for row in normalized.itertuples(index=False):
        items.append(
            {
                "recipe_id": int(row.recipe_id),
                "name": str(row.name or "").strip(),
                "description": str(row.description or "").strip(),
                "tags": _parse_string_list(row.tags),
                "ingredients": _parse_string_list(row.ingredients),
            }
        )

    if not items:
        raise ValueError(f"Recipe catalog is empty after normalization: {recipes_path}")
    return items


def serialize_taxonomy_payload(items: list[dict[str, Any]]) -> str:
    """Serialize item metadata into a compact JSON prompt payload."""
    return json.dumps(items, ensure_ascii=False, separators=(",", ":"))


def build_bounded_taxonomy_payload(
    items: list[dict[str, Any]],
    *,
    max_prompt_items: int = DEFAULT_MAX_PROMPT_ITEMS,
    max_payload_chars: int = DEFAULT_MAX_PAYLOAD_CHARS,
) -> TaxonomyPayload:
    """Bound the taxonomy payload to a deterministic sample size."""
    if max_prompt_items < 1:
        raise ValueError("max_prompt_items must be at least 1.")
    if max_payload_chars < 1:
        raise ValueError("max_payload_chars must be at least 1.")

    items_count = len(items)
    if items_count < 1:
        raise ValueError("Cannot build a taxonomy payload from an empty item list.")

    sample_size = min(items_count, max_prompt_items)
    while True:
        if sample_size == items_count:
            sampled_items = items
        else:
            sampled_items = [
                items[index]
                for index in _evenly_spaced_indices(items_count, sample_size)
            ]
        dataset_payload = serialize_taxonomy_payload(sampled_items)
        if len(dataset_payload) <= max_payload_chars:
            break
        if sample_size == 1:
            raise ValueError("Taxonomy payload exceeds the configured maximum payload size.")
        sample_size = max(1, sample_size // 2)

    if sample_size == items_count:
        sampling_strategy = FULL_CATALOG_SAMPLING_STRATEGY
    else:
        sampling_strategy = EVENLY_SPACED_SAMPLING_STRATEGY

    return TaxonomyPayload(
        items_count=items_count,
        sampled_items_count=len(sampled_items),
        max_prompt_items=max_prompt_items,
        sampling_strategy=sampling_strategy,
        dataset_payload=dataset_payload,
    )


def build_taxonomy_dictionary_prompt(payload: TaxonomyPayload) -> TaxonomyPromptBundle:
    """Build the one-shot taxonomy dictionary generation prompt."""
    examples_text = "\n\n".join(
        (
            f"Example {index}\n"
            f"Dataset:\n{json.dumps(example['items'], ensure_ascii=False, indent=2)}\n"
            f"Taxonomy JSON:\n"
            f"{json.dumps(example['taxonomy'], ensure_ascii=False, indent=2, sort_keys=True)}"
        )
        for index, example in enumerate(FEW_SHOT_EXAMPLES, start=1)
    )
    if payload.sampling_strategy == FULL_CATALOG_SAMPLING_STRATEGY:
        input_scope = f"The model input includes all {payload.sampled_items_count} recipes.\n\n"
    else:
        input_scope = (
            "The model input includes a deterministic evenly spaced sample of "
            f"{payload.sampled_items_count} recipes out of {payload.items_count} total recipes.\n"
            "Infer taxonomy features from the sampled records only.\n\n"
        )

    user_prompt = (
        "You are an expert in food recommendations.\n"
        "I have a food recipe dataset.\n"
        "Generate a taxonomy dictionary for this food dataset in JSON format.\n"
        "This taxonomy must include feature names and the possible values for each feature.\n"
        "It will be used for a food recommendation system to tag each item later.\n\n"
        "Output requirements:\n"
        "- Return JSON only.\n"
        "- The top-level JSON must be an object mapping feature_name -> array of possible values.\n"
        "- Infer the feature names from the dataset metadata itself.\n"
        "- Use snake_case for every feature name and every value.\n"
        "- Use recommendation-relevant concepts only.\n"
        "- Do not output explanations, markdown, or code fences.\n"
        "- Do not include empty features.\n\n"
        f"The dataset contains {payload.items_count} recipes.\n"
        f"{input_scope}"
        "Few-shot examples:\n"
        f"{examples_text}\n\n"
        "Now analyze the following Food.com recipe metadata and return the final taxonomy "
        "dictionary JSON only.\n\n"
        f"Dataset:\n{payload.dataset_payload}"
    )
    return TaxonomyPromptBundle(
        items_count=payload.items_count,
        sampled_items_count=payload.sampled_items_count,
        max_prompt_items=payload.max_prompt_items,
        sampling_strategy=payload.sampling_strategy,
        dataset_payload=payload.dataset_payload,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


def generate_taxonomy_dictionary(
    *,
    generator: MLXTextGenerator,
    prompt_bundle: TaxonomyPromptBundle,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, list[str]]:
    """Generate and normalize the taxonomy dictionary JSON."""
    response = generator.generate(
        prompt_bundle.user_prompt,
        system_prompt=prompt_bundle.system_prompt,
        max_tokens=max_tokens,
        temperature=0.0,
        top_p=1.0,
    )
    try:
        parsed = _parse_taxonomy_json(response)
    except ValueError:
        repaired = repair_taxonomy_json(generator=generator, raw_output=response)
        try:
            parsed = _parse_taxonomy_json(repaired)
        except ValueError as exc:
            raise ValueError(
                "Taxonomy generation failed: both initial and repair attempts "
                "produced invalid JSON.",
            ) from exc
    taxonomy_dictionary = normalize_taxonomy_dictionary(parsed)
    return validate_taxonomy_dictionary(taxonomy_dictionary)


def repair_taxonomy_json(*, generator: MLXTextGenerator, raw_output: str) -> str:
    """Ask the model to repair malformed taxonomy JSON output."""
    repair_prompt = (
        "Convert the following text into valid JSON only.\n"
        "Schema: top-level object mapping feature_name -> array of possible values.\n"
        "Use snake_case for keys and values.\n"
        "Drop commentary, markdown fences, and invalid trailing text.\n\n"
        f"Text to repair:\n{raw_output}"
    )
    return generator.generate(
        repair_prompt,
        system_prompt="You repair malformed JSON for taxonomy dictionaries. Return JSON only.",
        max_tokens=DEFAULT_REPAIR_MAX_TOKENS,
        temperature=0.0,
        top_p=1.0,
    )


def normalize_taxonomy_dictionary(raw_taxonomy: dict[str, Any]) -> dict[str, list[str]]:
    """Normalize keys and values into deterministic snake_case JSON."""
    normalized: dict[str, set[str]] = {}
    for raw_key, raw_values in raw_taxonomy.items():
        key = _to_snake_case(str(raw_key))
        if not key:
            continue

        if isinstance(raw_values, str):
            iterable: list[Any] = [raw_values]
        elif isinstance(raw_values, list):
            iterable = raw_values
        else:
            continue

        bucket = normalized.setdefault(key, set())
        for raw_value in iterable:
            value = _to_snake_case(str(raw_value))
            if value:
                bucket.add(value)

    return {
        key: sorted(values)
        for key, values in sorted(normalized.items(), key=lambda item: item[0])
        if values
    }


def validate_taxonomy_dictionary(
    taxonomy_dictionary: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Reject empty or degenerate taxonomy outputs before writing artifacts."""
    if not taxonomy_dictionary:
        raise ValueError("Taxonomy generation produced no usable features or values.")
    return taxonomy_dictionary


def write_taxonomy_outputs(
    *,
    out_dir: Path,
    taxonomy_dictionary: dict[str, list[str]],
    prompt_bundle: TaxonomyPromptBundle,
    model_id: str,
    max_tokens: int,
    overwrite: bool = False,
) -> TaxonomyDictionarySummary:
    """Write the taxonomy dictionary JSON and prompt snapshot."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dictionary_path = out_dir / "food_taxonomy_dictionary.json"
    prompt_snapshot_path = out_dir / "prompt_snapshot.json"

    if not overwrite:
        for path in (dictionary_path, prompt_snapshot_path):
            if path.exists():
                raise FileExistsError(
                    f"Refusing to overwrite existing file without --overwrite: {path}",
                )

    dictionary_path.write_text(
        json.dumps(taxonomy_dictionary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prompt_snapshot = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_id": model_id,
        "generation_params": {
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "top_p": 1.0,
        },
        "items_count": prompt_bundle.items_count,
        "sampled_items_count": prompt_bundle.sampled_items_count,
        "max_prompt_items": prompt_bundle.max_prompt_items,
        "sampling_strategy": prompt_bundle.sampling_strategy,
        "system_prompt": prompt_bundle.system_prompt,
        "user_prompt": prompt_bundle.user_prompt,
        "dataset_payload": prompt_bundle.dataset_payload,
    }
    prompt_snapshot_path.write_text(
        json.dumps(prompt_snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return TaxonomyDictionarySummary(
        items_count=prompt_bundle.items_count,
        sampled_items_count=prompt_bundle.sampled_items_count,
        feature_count=len(taxonomy_dictionary),
        total_value_count=sum(len(values) for values in taxonomy_dictionary.values()),
    )


def build_taxonomy_dictionary(
    *,
    recipes_path: Path,
    out_dir: Path,
    llm_model: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overwrite: bool = False,
) -> TaxonomyDictionarySummary:
    """Run the full taxonomy dictionary generation pipeline."""
    items = load_taxonomy_items(recipes_path)
    payload = build_bounded_taxonomy_payload(items)
    prompt_bundle = build_taxonomy_dictionary_prompt(payload)
    generator = MLXTextGenerator(model_id=llm_model)
    taxonomy_dictionary = generate_taxonomy_dictionary(
        generator=generator,
        prompt_bundle=prompt_bundle,
        max_tokens=max_tokens,
    )
    return write_taxonomy_outputs(
        out_dir=out_dir,
        taxonomy_dictionary=taxonomy_dictionary,
        prompt_bundle=prompt_bundle,
        model_id=llm_model,
        max_tokens=max_tokens,
        overwrite=overwrite,
    )


def _parse_string_list(raw_value: Any) -> list[str]:
    """Parse a JSON-like list field into a stable list of strings."""
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        values = raw_value
    else:
        text = str(raw_value).strip()
        if not text:
            return []
        try:
            values = json.loads(text)
        except json.JSONDecodeError:
            values = ast.literal_eval(text)

    if not isinstance(values, list):
        raise ValueError(f"Expected list-like metadata field, received: {raw_value!r}")
    return [str(value).strip() for value in values if str(value).strip()]


def _parse_taxonomy_json(raw_text: str) -> dict[str, Any]:
    """Extract and parse a taxonomy JSON object from model output."""
    start_index = raw_text.find("{")
    if start_index < 0:
        raise ValueError("Model output does not contain a JSON object.")

    decoder = json.JSONDecoder()
    try:
        parsed, _ = decoder.raw_decode(raw_text, idx=start_index)
    except json.JSONDecodeError as exc:
        raise ValueError("Model output does not contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Taxonomy output must be a top-level JSON object.")
    return parsed


def _to_snake_case(raw_value: str) -> str:
    """Normalize free text into snake_case."""
    normalized = raw_value.strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_")


def _evenly_spaced_indices(total_items: int, sample_size: int) -> list[int]:
    """Select deterministic evenly spaced indices across an ordered item list."""
    if sample_size < 1:
        raise ValueError("sample_size must be at least 1.")
    if total_items < sample_size:
        raise ValueError("sample_size cannot exceed total_items.")
    if sample_size == 1:
        return [0]
    return [((total_items - 1) * index) // (sample_size - 1) for index in range(sample_size)]
