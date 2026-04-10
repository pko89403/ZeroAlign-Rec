"""SID compilation helpers."""

from sid_reco.sid.compiler import (
    CompiledSIDItem,
    CompiledSIDItems,
    ResidualKMeansLevel,
    TrainedResidualCodebooks,
    assign_trained_residual_kmeans,
    compile_residual_kmeans,
    train_residual_codebooks,
)
from sid_reco.sid.embed_backend import (
    EmbeddedSIDItems,
    EmbeddedSIDWriteSummary,
    encode_serialized_items,
    encode_serialized_items_with_mlx,
    write_embedded_items,
)
from sid_reco.sid.indexing import SIDIndexWriteSummary, write_sid_index_outputs
from sid_reco.sid.serialization import (
    SerializedSIDItem,
    SerializedSIDWriteSummary,
    serialize_structured_items,
    serialize_taxonomy_text,
    write_serialized_items,
)
from sid_reco.sid.stats import (
    RecommendationStats,
    RecommendationStatsWriteSummary,
    build_recommendation_stats,
    write_recommendation_stats,
)

__all__ = [
    "CompiledSIDItem",
    "CompiledSIDItems",
    "EmbeddedSIDItems",
    "EmbeddedSIDWriteSummary",
    "ResidualKMeansLevel",
    "RecommendationStats",
    "RecommendationStatsWriteSummary",
    "SIDIndexWriteSummary",
    "SerializedSIDItem",
    "SerializedSIDWriteSummary",
    "TrainedResidualCodebooks",
    "assign_trained_residual_kmeans",
    "build_recommendation_stats",
    "compile_residual_kmeans",
    "encode_serialized_items",
    "encode_serialized_items_with_mlx",
    "serialize_structured_items",
    "serialize_taxonomy_text",
    "train_residual_codebooks",
    "write_recommendation_stats",
    "write_embedded_items",
    "write_sid_index_outputs",
    "write_serialized_items",
]
