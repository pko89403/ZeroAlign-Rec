"""Per-item taxonomy structuring using master taxonomy and neighbor context."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sid_reco.llm import MLXTextGenerator
from sid_reco.taxonomy.dictionary import _parse_taxonomy_json, _to_snake_case, load_taxonomy_items

DEFAULT_NEIGHBOR_COUNT = 5
DEFAULT_ITEM_MAX_TOKENS = 1024
DEFAULT_EMPTY_RETRY_ATTEMPTS = 5
UNKNOWN_TAXONOMY_VALUE = "empty"
ITEM_PROJECTION_REQUIRED_COLUMNS = [
    "source_recipe_id",
    "neighbor_rank",
    "neighbor_recipe_id",
]
ITEM_PROJECTION_SYSTEM_PROMPT = (
    "You are an expert in food recommendation item tagging. Return only valid JSON."
)


@dataclass(frozen=True, slots=True)
class ItemProjectionResources:
    """Normalized resources required to structure one or more items."""

    items_by_id: dict[int, dict[str, Any]]
    neighbor_context: pd.DataFrame
    taxonomy_dictionary: dict[str, list[str]]


@dataclass(frozen=True, slots=True)
class ItemProjectionContext:
    """Prompt-ready context for one target item."""

    recipe_id: int
    target_item: dict[str, Any]
    neighbors: list[dict[str, Any]]
    taxonomy_dictionary: dict[str, list[str]]


@dataclass(frozen=True, slots=True)
class ItemProjectionPromptBundle:
    """Prompt bundle for item taxonomy structuring."""

    recipe_id: int
    required_keys: tuple[str, ...]
    taxonomy_dictionary: dict[str, list[str]]
    system_prompt: str
    user_prompt: str


@dataclass(frozen=True, slots=True)
class StructuredTaxonomyItem:
    """Structured taxonomy output for one item."""

    recipe_id: int
    taxonomy: dict[str, list[str]]
    evidence: dict[str, Any] | None = None

    def to_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "recipe_id": self.recipe_id,
            "taxonomy": self.taxonomy,
        }
        if self.evidence is not None:
            record["evidence"] = self.evidence
        return record

    @property
    def tagged_value_count(self) -> int:
        return sum(len(values) for values in self.taxonomy.values())


@dataclass(frozen=True, slots=True)
class StructuredTaxonomyBatchSummary:
    """Summary of a batch item structuring run."""

    item_count: int
    taxonomy_key_count: int
    total_tagged_value_count: int
    output_path: Path


def load_item_projection_resources(
    *,
    recipes_path: Path,
    neighbor_context_path: Path,
    taxonomy_dictionary_path: Path,
) -> ItemProjectionResources:
    """Load the recipe catalog, neighbor table, and taxonomy master dictionary."""
    items_by_id = {int(item["recipe_id"]): item for item in load_taxonomy_items(recipes_path)}
    neighbor_context = load_neighbor_context(neighbor_context_path)
    taxonomy_dictionary = load_taxonomy_master_dictionary(taxonomy_dictionary_path)
    return ItemProjectionResources(
        items_by_id=items_by_id,
        neighbor_context=neighbor_context,
        taxonomy_dictionary=taxonomy_dictionary,
    )


def load_taxonomy_master_dictionary(taxonomy_dictionary_path: Path) -> dict[str, list[str]]:
    """Load the master taxonomy dictionary produced by taxonomy dictionary generation."""
    if not taxonomy_dictionary_path.exists():
        raise FileNotFoundError(f"Missing taxonomy dictionary file: {taxonomy_dictionary_path}")

    try:
        raw_taxonomy = json.loads(taxonomy_dictionary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Taxonomy dictionary file does not contain valid JSON: {taxonomy_dictionary_path}",
        ) from exc

    if not isinstance(raw_taxonomy, dict):
        raise ValueError("Taxonomy dictionary JSON must be a top-level object.")

    normalized: dict[str, list[str]] = {}
    for raw_key, raw_values in raw_taxonomy.items():
        key = _to_snake_case(str(raw_key))
        if not key:
            continue
        if isinstance(raw_values, str):
            iterable: list[Any] = [raw_values]
        elif isinstance(raw_values, list):
            iterable = raw_values
        else:
            raise ValueError(
                f"Taxonomy dictionary values for key '{key}' must be strings or arrays.",
            )

        values: set[str] = set()
        for raw_value in iterable:
            value = _to_snake_case(str(raw_value))
            if value:
                values.add(value)
        normalized[key] = sorted(values)

    if not normalized:
        raise ValueError("Taxonomy dictionary contains no usable taxonomy keys.")
    return normalized


def load_neighbor_context(neighbor_context_path: Path) -> pd.DataFrame:
    """Load the persisted taxonomy step 1 top-k neighbor table."""
    if not neighbor_context_path.exists():
        raise FileNotFoundError(f"Missing neighbor context file: {neighbor_context_path}")

    neighbor_context = pd.read_csv(neighbor_context_path)
    missing = sorted(set(ITEM_PROJECTION_REQUIRED_COLUMNS).difference(neighbor_context.columns))
    if missing:
        raise ValueError(f"Missing required neighbor context columns: {', '.join(missing)}")

    projection_columns = list(ITEM_PROJECTION_REQUIRED_COLUMNS)
    if "cosine_similarity" in neighbor_context.columns:
        projection_columns.append("cosine_similarity")
    normalized = neighbor_context.loc[:, projection_columns].copy(deep=False)
    for column in ITEM_PROJECTION_REQUIRED_COLUMNS:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized = normalized.dropna(subset=ITEM_PROJECTION_REQUIRED_COLUMNS).copy()
    for column in ITEM_PROJECTION_REQUIRED_COLUMNS:
        normalized[column] = normalized[column].astype(int)

    if normalized.empty:
        raise ValueError(f"Neighbor context is empty after normalization: {neighbor_context_path}")

    return normalized.sort_values(
        ["source_recipe_id", "neighbor_rank", "neighbor_recipe_id"],
        ascending=True,
        kind="mergesort",
    ).reset_index(drop=True)


def build_item_projection_context(
    *,
    recipe_id: int,
    recipes_path: Path | None = None,
    neighbor_context_path: Path | None = None,
    taxonomy_dictionary_path: Path | None = None,
    resources: ItemProjectionResources | None = None,
    top_k: int = DEFAULT_NEIGHBOR_COUNT,
) -> ItemProjectionContext:
    """Assemble the target item, top-k neighbors, and taxonomy master dictionary."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    resolved_resources = resources or load_item_projection_resources(
        recipes_path=_require_path(recipes_path, "recipes_path"),
        neighbor_context_path=_require_path(neighbor_context_path, "neighbor_context_path"),
        taxonomy_dictionary_path=_require_path(
            taxonomy_dictionary_path,
            "taxonomy_dictionary_path",
        ),
    )
    if recipe_id not in resolved_resources.items_by_id:
        raise ValueError(f"Recipe {recipe_id} was not found in the recipe catalog.")

    neighbor_rows = resolved_resources.neighbor_context.loc[
        resolved_resources.neighbor_context["source_recipe_id"] == recipe_id
    ].head(top_k)
    if len(neighbor_rows) < top_k:
        raise ValueError(
            f"Recipe {recipe_id} does not have the required top-{top_k} neighbor context.",
        )

    neighbors: list[dict[str, Any]] = []
    for row in neighbor_rows.itertuples(index=False):
        neighbor_recipe_id = int(row.neighbor_recipe_id)
        if neighbor_recipe_id not in resolved_resources.items_by_id:
            raise ValueError(
                f"Neighbor recipe {neighbor_recipe_id} referenced by recipe {recipe_id} "
                "is missing from the recipe catalog.",
            )
        neighbor_item = dict(resolved_resources.items_by_id[neighbor_recipe_id])
        neighbor_record: dict[str, Any] = {
            "recipe_id": neighbor_recipe_id,
            "neighbor_rank": int(row.neighbor_rank),
            "name": neighbor_item["name"],
            "description": neighbor_item["description"],
            "tags": neighbor_item["tags"],
            "ingredients": neighbor_item["ingredients"],
        }
        cosine_similarity = getattr(row, "cosine_similarity", None)
        if cosine_similarity is not None and not pd.isna(cosine_similarity):
            neighbor_record["cosine_similarity"] = float(cosine_similarity)
        neighbors.append(neighbor_record)

    return ItemProjectionContext(
        recipe_id=recipe_id,
        target_item=dict(resolved_resources.items_by_id[recipe_id]),
        neighbors=neighbors,
        taxonomy_dictionary=resolved_resources.taxonomy_dictionary,
    )


def build_item_projection_prompt(context: ItemProjectionContext) -> ItemProjectionPromptBundle:
    """Build the item tagging prompt for one recipe."""
    required_keys = tuple(context.taxonomy_dictionary.keys())
    taxonomy_dictionary_text = json.dumps(
        context.taxonomy_dictionary,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    target_item_text = json.dumps(
        context.target_item,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    neighbors_text = json.dumps(
        context.neighbors,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    user_prompt = (
        "You are assigning taxonomy labels to a single food item.\n"
        "Return JSON only.\n\n"
        "Output contract:\n"
        f"- Return a top-level JSON object with exactly these keys: {', '.join(required_keys)}.\n"
        "- Every key must map to a non-empty array of snake_case strings.\n"
        "- Include every key and never return an empty array.\n"
        "- Within one key, collapse duplicates and near-synonyms into one best label.\n"
        "- Do not repeat the same concept across multiple keys unless the evidence "
        "clearly supports it.\n"
        "- Treat the provided master vocabulary as few-shot guidance, not as a closed label set.\n"
        "- Prefer labels from the provided master vocabulary for each key when they fit.\n"
        "- If the vocabulary examples are insufficient, you may add a short snake_case label.\n"
        f"- If you truly cannot infer a value for a key, return "
        f'["{UNKNOWN_TAXONOMY_VALUE}"] for that key.\n'
        "- Do not add extra keys, explanations, markdown, or code fences.\n\n"
        "Master taxonomy dictionary (few-shot guidance by key):\n"
        f"{taxonomy_dictionary_text}\n\n"
        "Target item:\n"
        f"{target_item_text}\n\n"
        "Top-5 neighbors:\n"
        f"{neighbors_text}"
    )
    return ItemProjectionPromptBundle(
        recipe_id=context.recipe_id,
        required_keys=required_keys,
        taxonomy_dictionary=context.taxonomy_dictionary,
        system_prompt=ITEM_PROJECTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


def generate_item_taxonomy(
    *,
    generator: MLXTextGenerator,
    prompt_bundle: ItemProjectionPromptBundle,
    context: ItemProjectionContext | None = None,
    max_tokens: int = DEFAULT_ITEM_MAX_TOKENS,
) -> dict[str, list[str]]:
    """Generate and validate taxonomy tags for one item."""
    taxonomy: dict[str, list[str]] | None = None
    for attempt in range(1, DEFAULT_EMPTY_RETRY_ATTEMPTS + 1):
        response = generator.generate(
            build_retry_prompt(prompt_bundle=prompt_bundle, attempt=attempt, taxonomy=taxonomy),
            system_prompt=prompt_bundle.system_prompt,
            max_tokens=max_tokens,
            temperature=0.0,
            top_p=1.0,
        )
        taxonomy = _parse_generated_taxonomy(
            generator=generator,
            raw_output=response,
            required_keys=prompt_bundle.required_keys,
            error_message=(
                "Item taxonomy structuring failed: both initial and repair attempts "
                "produced invalid projection JSON."
            ),
        )
        if _should_self_refine(
            taxonomy=taxonomy,
            taxonomy_dictionary=prompt_bundle.taxonomy_dictionary,
        ):
            taxonomy = refine_item_taxonomy(
                generator=generator,
                prompt_bundle=prompt_bundle,
                taxonomy=taxonomy,
                max_tokens=max_tokens,
            )
        finalized = finalize_item_taxonomy(
            taxonomy=taxonomy,
            taxonomy_dictionary=prompt_bundle.taxonomy_dictionary,
            context=context,
            fill_unknowns=False,
        )
        if not _empty_feature_keys(finalized):
            return fill_empty_features(finalized)
        taxonomy = finalized
    if taxonomy is None:
        raise ValueError("Item taxonomy structuring produced no usable taxonomy output.")
    return fill_empty_features(taxonomy)


def refine_item_taxonomy(
    *,
    generator: MLXTextGenerator,
    prompt_bundle: ItemProjectionPromptBundle,
    taxonomy: dict[str, list[str]],
    max_tokens: int = DEFAULT_ITEM_MAX_TOKENS,
) -> dict[str, list[str]]:
    """Ask the model to rewrite a draft taxonomy into a cleaner, less redundant JSON."""
    response = generator.generate(
        build_self_refine_prompt(prompt_bundle=prompt_bundle, taxonomy=taxonomy),
        system_prompt="You refine item taxonomy JSON. Return JSON only.",
        max_tokens=max_tokens,
        temperature=0.0,
        top_p=1.0,
    )
    return _parse_generated_taxonomy(
        generator=generator,
        raw_output=response,
        required_keys=prompt_bundle.required_keys,
    )


def finalize_item_taxonomy(
    *,
    taxonomy: dict[str, list[str]],
    taxonomy_dictionary: dict[str, list[str]],
    context: ItemProjectionContext | None = None,
    fill_unknowns: bool = True,
) -> dict[str, list[str]]:
    """Convert raw extraction labels into a final schema-consistent TID."""
    consolidated = consolidate_item_taxonomy(
        taxonomy=taxonomy,
        taxonomy_dictionary=taxonomy_dictionary,
    )
    if context is not None:
        consolidated = validate_item_taxonomy(
            taxonomy=consolidated,
            context=context,
        )
    if fill_unknowns:
        return fill_empty_features(consolidated)
    return consolidated


def repair_item_taxonomy_json(
    *,
    generator: MLXTextGenerator,
    raw_output: str,
    required_keys: tuple[str, ...],
) -> str:
    """Repair malformed or schema-invalid item projection output."""
    repair_prompt = (
        "Convert the following text into valid JSON only.\n"
        f"Schema: top-level object with exactly these keys: {', '.join(required_keys)}.\n"
        "Every key must map to a non-empty array of snake_case strings.\n"
        "Collapse duplicates and near-synonyms to one best label per key.\n"
        f'Include missing or empty keys with ["{UNKNOWN_TAXONOMY_VALUE}"] '
        "and drop unsupported extra keys.\n"
        "Keep open-vocabulary labels when needed, but keep them short and snake_case.\n\n"
        f"Text to repair:\n{raw_output}"
    )
    return generator.generate(
        repair_prompt,
        system_prompt="You repair malformed item taxonomy JSON. Return JSON only.",
        max_tokens=DEFAULT_ITEM_MAX_TOKENS,
        temperature=0.0,
        top_p=1.0,
    )


def structure_taxonomy_item(
    *,
    recipe_id: int,
    recipes_path: Path,
    neighbor_context_path: Path,
    taxonomy_dictionary_path: Path,
    llm_model: str,
    max_tokens: int = DEFAULT_ITEM_MAX_TOKENS,
    top_k: int = DEFAULT_NEIGHBOR_COUNT,
    include_evidence: bool = False,
    generator: MLXTextGenerator | None = None,
    resources: ItemProjectionResources | None = None,
) -> StructuredTaxonomyItem:
    """Run the full item structuring flow for a single recipe."""
    resolved_resources = resources or load_item_projection_resources(
        recipes_path=recipes_path,
        neighbor_context_path=neighbor_context_path,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
    )
    context = build_item_projection_context(
        recipe_id=recipe_id,
        resources=resolved_resources,
        top_k=top_k,
    )
    prompt_bundle = build_item_projection_prompt(context)
    resolved_generator = generator or MLXTextGenerator(model_id=llm_model)
    taxonomy = generate_item_taxonomy(
        generator=resolved_generator,
        prompt_bundle=prompt_bundle,
        context=context,
        max_tokens=max_tokens,
    )
    evidence = build_item_projection_evidence(context) if include_evidence else None
    return StructuredTaxonomyItem(recipe_id=recipe_id, taxonomy=taxonomy, evidence=evidence)


def write_structured_taxonomy_item(
    *,
    structured_item: StructuredTaxonomyItem,
    out_path: Path,
    overwrite: bool = False,
) -> None:
    """Persist one structured taxonomy item as JSON."""
    _ensure_writable_path(out_path, overwrite=overwrite)
    out_path.write_text(
        json.dumps(
            structured_item.to_record(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def structure_taxonomy_batch(
    *,
    recipes_path: Path,
    neighbor_context_path: Path,
    taxonomy_dictionary_path: Path,
    out_path: Path,
    llm_model: str,
    max_tokens: int = DEFAULT_ITEM_MAX_TOKENS,
    top_k: int = DEFAULT_NEIGHBOR_COUNT,
    include_evidence: bool = False,
    overwrite: bool = False,
    generator: MLXTextGenerator | None = None,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> StructuredTaxonomyBatchSummary:
    """Structure every recipe item and write the results as JSON Lines."""
    resources = load_item_projection_resources(
        recipes_path=recipes_path,
        neighbor_context_path=neighbor_context_path,
        taxonomy_dictionary_path=taxonomy_dictionary_path,
    )
    resolved_generator = generator or MLXTextGenerator(model_id=llm_model)
    _ensure_writable_path(out_path, overwrite=overwrite)

    structured_items: list[StructuredTaxonomyItem] = []
    ordered_recipe_ids = sorted(resources.items_by_id)
    total_items = len(ordered_recipe_ids)
    for completed_count, recipe_id in enumerate(ordered_recipe_ids, start=1):
        structured_items.append(
            structure_taxonomy_item(
                recipe_id=recipe_id,
                recipes_path=recipes_path,
                neighbor_context_path=neighbor_context_path,
                taxonomy_dictionary_path=taxonomy_dictionary_path,
                llm_model=llm_model,
                max_tokens=max_tokens,
                top_k=top_k,
                include_evidence=include_evidence,
                generator=resolved_generator,
                resources=resources,
            )
        )
        if progress_callback is not None:
            progress_callback(completed_count, total_items, recipe_id)

    lines = [
        json.dumps(item.to_record(), ensure_ascii=False, sort_keys=True)
        for item in structured_items
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return StructuredTaxonomyBatchSummary(
        item_count=len(structured_items),
        taxonomy_key_count=len(resources.taxonomy_dictionary),
        total_tagged_value_count=sum(item.tagged_value_count for item in structured_items),
        output_path=out_path,
    )


def build_item_projection_evidence(context: ItemProjectionContext) -> dict[str, Any]:
    """Build an optional evidence payload for structured item outputs."""
    evidence_neighbors = [
        {
            "neighbor_recipe_id": int(neighbor["recipe_id"]),
            "neighbor_rank": int(neighbor["neighbor_rank"]),
            "cosine_similarity": neighbor.get("cosine_similarity"),
            "name": neighbor["name"],
            "description": neighbor["description"],
            "tags": neighbor["tags"],
            "ingredients": neighbor["ingredients"],
        }
        for neighbor in context.neighbors
    ]
    return {
        "target_item": dict(context.target_item),
        "neighbors": evidence_neighbors,
    }


def build_retry_prompt(
    *,
    prompt_bundle: ItemProjectionPromptBundle,
    attempt: int,
    taxonomy: dict[str, list[str]] | None,
) -> str:
    """Append retry instructions when the previous attempt returned empty features."""
    if attempt == 1 or taxonomy is None:
        return prompt_bundle.user_prompt
    empty_features = _empty_feature_keys(taxonomy)
    if not empty_features:
        return prompt_bundle.user_prompt
    return (
        f"{prompt_bundle.user_prompt}\n\n"
        "Retry instruction:\n"
        "The previous response left some features empty.\n"
        f"Refill these keys with non-empty arrays: {', '.join(empty_features)}.\n"
        "Also remove duplicate or synonymous labels while retrying.\n"
        f"If you still cannot infer a value, return "
        f'["{UNKNOWN_TAXONOMY_VALUE}"] for those keys.\n'
    )


def build_self_refine_prompt(
    *,
    prompt_bundle: ItemProjectionPromptBundle,
    taxonomy: dict[str, list[str]],
) -> str:
    """Build a self-refine prompt that cleans a draft JSON without changing the schema."""
    taxonomy_text = json.dumps(taxonomy, ensure_ascii=False, indent=2, sort_keys=True)
    vocabulary_text = json.dumps(
        prompt_bundle.taxonomy_dictionary,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return (
        "Rewrite the draft item taxonomy JSON into a cleaner final draft.\n"
        f"Keep exactly these keys: {', '.join(prompt_bundle.required_keys)}.\n"
        "Rules:\n"
        "- Keep non-empty arrays of snake_case strings.\n"
        "- Remove duplicate labels and near-synonyms within each key.\n"
        "- Do not repeat the same concept across multiple keys unless the evidence "
        "clearly requires it.\n"
        "- Prefer master vocabulary labels when they clearly fit the evidence.\n"
        "- Keep open-vocabulary labels only when the master vocabulary does not fit.\n"
        f'- If a key is still unknowable, return ["{UNKNOWN_TAXONOMY_VALUE}"] for that key.\n'
        "- Return JSON only.\n\n"
        "Master taxonomy dictionary:\n"
        f"{vocabulary_text}\n\n"
        "Original item evidence:\n"
        f"{prompt_bundle.user_prompt}\n\n"
        "Draft taxonomy JSON:\n"
        f"{taxonomy_text}"
    )


def _parse_generated_taxonomy(
    *,
    generator: MLXTextGenerator,
    raw_output: str,
    required_keys: tuple[str, ...],
    error_message: str | None = None,
) -> dict[str, list[str]]:
    try:
        return _normalize_projected_taxonomy(
            _parse_taxonomy_json(raw_output),
            required_keys=required_keys,
        )
    except ValueError:
        repaired = repair_item_taxonomy_json(
            generator=generator,
            raw_output=raw_output,
            required_keys=required_keys,
        )
        try:
            return _normalize_projected_taxonomy(
                _parse_taxonomy_json(repaired),
                required_keys=required_keys,
            )
        except ValueError as exc:
            if error_message is None:
                raise
            raise ValueError(error_message) from exc


def _normalize_projected_taxonomy(
    raw_taxonomy: dict[str, Any],
    *,
    required_keys: tuple[str, ...],
) -> dict[str, list[str]]:
    normalized_required_keys = tuple(_to_snake_case(key) for key in required_keys)
    allowed_keys = set(normalized_required_keys)
    normalized: dict[str, list[str]] = {}
    unsupported_keys: list[str] = []

    for raw_key, raw_values in raw_taxonomy.items():
        key = _to_snake_case(str(raw_key))
        if key not in allowed_keys:
            unsupported_keys.append(key or str(raw_key))
            continue
        normalized[key] = _normalize_projected_values(key=key, raw_values=raw_values)

    if unsupported_keys:
        raise ValueError(
            "Projected taxonomy contains unsupported keys: "
            + ", ".join(sorted(unsupported_keys))
            + ".",
        )

    missing_keys = [key for key in normalized_required_keys if key not in normalized]
    if missing_keys:
        raise ValueError(
            "Projected taxonomy is missing required keys: " + ", ".join(missing_keys) + ".",
        )

    return {key: normalized[key] for key in normalized_required_keys}


def fill_empty_features(taxonomy: dict[str, list[str]]) -> dict[str, list[str]]:
    """Replace empty feature arrays with the sentinel value 'empty'."""
    return {key: values if values else [UNKNOWN_TAXONOMY_VALUE] for key, values in taxonomy.items()}


def _empty_feature_keys(taxonomy: dict[str, list[str]]) -> list[str]:
    return [key for key, values in taxonomy.items() if not values]


def _normalize_projected_values(*, key: str, raw_values: Any) -> list[str]:
    if raw_values is None:
        return []
    if isinstance(raw_values, str):
        iterable: list[Any] = [raw_values]
    elif isinstance(raw_values, list):
        iterable = raw_values
    else:
        raise ValueError(
            f"Projected taxonomy values for key '{key}' must be strings, arrays, or null.",
        )

    values: set[str] = set()
    for raw_value in iterable:
        value = _to_snake_case(str(raw_value))
        if value:
            values.add(value)
    return sorted(values)


def consolidate_item_taxonomy(
    *,
    taxonomy: dict[str, list[str]],
    taxonomy_dictionary: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Conservatively map draft labels toward the master vocabulary without closing recall."""
    consolidated: dict[str, list[str]] = {}
    for key, values in taxonomy.items():
        vocabulary = taxonomy_dictionary.get(key, [])
        resolved: list[str] = []
        seen: set[str] = set()
        for value in values:
            canonical = _canonicalize_feature_value(
                key=key,
                value=value,
                vocabulary=vocabulary,
            )
            if canonical not in seen:
                resolved.append(canonical)
                seen.add(canonical)
        consolidated[key] = resolved
    return consolidated


def validate_item_taxonomy(
    *,
    taxonomy: dict[str, list[str]],
    context: ItemProjectionContext,
) -> dict[str, list[str]]:
    """Apply lightweight feature-specific guards to reduce obvious contradictions."""
    validated = {key: list(values) for key, values in taxonomy.items()}

    if "cuisine" in validated:
        validated["cuisine"] = _validate_cuisine_values(
            values=validated["cuisine"],
            context=context,
        )

    if "dietary_style" in validated:
        validated["dietary_style"] = _validate_dietary_style_values(
            values=validated["dietary_style"],
            context=context,
        )

    return validated


def _should_self_refine(
    *,
    taxonomy: dict[str, list[str]],
    taxonomy_dictionary: dict[str, list[str]],
) -> bool:
    if _empty_feature_keys(taxonomy):
        return False

    if _has_cross_feature_duplicates(taxonomy):
        return True

    for key, values in taxonomy.items():
        vocabulary = taxonomy_dictionary.get(key, [])
        for value in values:
            if _canonicalize_feature_value(key=key, value=value, vocabulary=vocabulary) != value:
                return True
    return False


def _has_cross_feature_duplicates(taxonomy: dict[str, list[str]]) -> bool:
    seen: set[str] = set()
    for values in taxonomy.values():
        for value in values:
            if value == UNKNOWN_TAXONOMY_VALUE:
                continue
            if value in seen:
                return True
            seen.add(value)
    return False


def _canonicalize_feature_value(*, key: str, value: str, vocabulary: list[str]) -> str:
    if value == UNKNOWN_TAXONOMY_VALUE:
        return value

    vocabulary_set = set(vocabulary)
    if value in vocabulary_set:
        return value

    aliases = FEATURE_VALUE_ALIASES.get(key, {})
    alias = aliases.get(value)
    if alias is not None:
        return alias if alias in vocabulary_set else alias

    for candidate in _value_variants(value):
        if candidate in vocabulary_set:
            return candidate

    return value


def _value_variants(value: str) -> list[str]:
    tokens = [token for token in value.split("_") if token]
    variants: list[str] = []

    if tokens and tokens[-1] in GENERIC_SUFFIX_TOKENS:
        trimmed = "_".join(tokens[:-1])
        if trimmed:
            variants.append(trimmed)

    singular_tokens = [_singularize_token(token) for token in tokens]
    singular_value = "_".join(singular_tokens)
    if singular_value and singular_value != value:
        variants.append(singular_value)

    if len(tokens) == 1:
        verb_base = _verb_base_form(tokens[0])
        if verb_base and verb_base != value:
            variants.append(verb_base)

    return variants


def _singularize_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _verb_base_form(token: str) -> str:
    alias = COOKING_METHOD_ALIASES.get(token)
    if alias is not None:
        return alias
    if len(token) > 4 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 3 and token.endswith("ed"):
        trimmed = token[:-2]
        if trimmed.endswith("i"):
            return trimmed[:-1] + "y"
        return trimmed
    return token


def _validate_cuisine_values(
    *,
    values: list[str],
    context: ItemProjectionContext,
) -> list[str]:
    validated: list[str] = []
    evidence_text = _context_text(context)
    for value in values:
        if value == "american" and not _has_explicit_cuisine_evidence(
            label=value,
            evidence_text=evidence_text,
        ):
            continue
        validated.append(value)
    return validated


def _validate_dietary_style_values(
    *,
    values: list[str],
    context: ItemProjectionContext,
) -> list[str]:
    ingredient_tokens = _context_ingredient_tokens(context)
    return [
        value
        for value in values
        if not ingredient_tokens.intersection(DIETARY_STYLE_CONFLICT_TOKENS.get(value, set()))
    ]


def _has_explicit_cuisine_evidence(*, label: str, evidence_text: str) -> bool:
    search_terms = {
        "american": ("american", "usa", "united_states"),
    }
    return any(term in evidence_text for term in search_terms.get(label, (label,)))


def _context_text(context: ItemProjectionContext) -> str:
    target_text = json.dumps(context.target_item, ensure_ascii=False, sort_keys=True)
    neighbor_text = json.dumps(context.neighbors, ensure_ascii=False, sort_keys=True)
    return _to_snake_case(f"{target_text} {neighbor_text}")


def _context_ingredient_tokens(context: ItemProjectionContext) -> set[str]:
    tokens: set[str] = set()
    for item in [context.target_item, *context.neighbors]:
        for field in ("ingredients", "tags", "name", "description"):
            tokens.update(_extract_tokens(item.get(field)))
    return tokens


def _extract_tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        parts = value
    else:
        parts = [value]

    normalized_tokens: set[str] = set()
    for part in parts:
        text = _to_snake_case(str(part))
        if not text:
            continue
        normalized_tokens.update(token for token in text.split("_") if token)
        normalized_tokens.add(text)
    return normalized_tokens


GENERIC_SUFFIX_TOKENS = {
    "style",
    "dish",
    "food",
    "recipe",
    "cuisine",
    "meal",
    "method",
}

COOKING_METHOD_ALIASES = {
    "baked": "bake",
    "baking": "bake",
    "boiled": "boil",
    "braised": "braise",
    "fried": "fry",
    "grilled": "grill",
    "poached": "poach",
    "roasted": "roast",
    "sauteed": "saute",
    "steamed": "steam",
    "stir_fried": "stir_fry",
}

FEATURE_VALUE_ALIASES: dict[str, dict[str, str]] = {
    "cooking_method": {
        **COOKING_METHOD_ALIASES,
        "pan_fried": "pan_fry",
        "deep_fried": "deep_fry",
    },
    "dish_type": {
        "soups": "soup",
        "salads": "salad",
        "sandwiches": "sandwich",
        "appetizers": "appetizer",
    },
    "primary_ingredient": {
        "tomatoes": "tomato",
        "potatoes": "potato",
        "onions": "onion",
        "eggs": "egg",
    },
}

GLUTEN_INGREDIENT_TOKENS = {
    "bread",
    "bun",
    "cake",
    "cookie",
    "cracker",
    "flour",
    "macaroni",
    "noodle",
    "noodles",
    "pasta",
    "ramen",
    "spaghetti",
    "tortilla",
    "wheat",
}

MEAT_INGREDIENT_TOKENS = {
    "anchovy",
    "bacon",
    "beef",
    "chicken",
    "fish",
    "ham",
    "lamb",
    "meat",
    "pork",
    "salami",
    "sausage",
    "shrimp",
    "turkey",
    "tuna",
}

DAIRY_INGREDIENT_TOKENS = {
    "butter",
    "cheese",
    "cream",
    "milk",
    "mozzarella",
    "parmesan",
    "yogurt",
}

NON_VEGAN_INGREDIENT_TOKENS = (
    MEAT_INGREDIENT_TOKENS
    | DAIRY_INGREDIENT_TOKENS
    | {
        "egg",
        "eggs",
        "honey",
        "mayonnaise",
    }
)

DIETARY_STYLE_CONFLICT_TOKENS = {
    "gluten_free": GLUTEN_INGREDIENT_TOKENS,
    "vegetarian": MEAT_INGREDIENT_TOKENS,
    "vegan": NON_VEGAN_INGREDIENT_TOKENS,
    "dairy_free": DAIRY_INGREDIENT_TOKENS,
}


def _ensure_writable_path(path: Path, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")


def _require_path(path: Path | None, name: str) -> Path:
    if path is None:
        raise ValueError(f"{name} is required when projection resources are not preloaded.")
    return path
