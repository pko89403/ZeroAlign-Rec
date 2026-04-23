"""SID compilation helpers."""

from sid_reco.sid.compiler import (
    ItemSID,
    QuerySID,
    ResidualKMeansLevel,
    TrainedResidualCodebooks,
    build_item_sids,
    build_query_sid,
    load_codebooks,
    train_codebooks,
    write_codebooks,
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
    "EmbeddedSIDItems",
    "EmbeddedSIDWriteSummary",
    "ItemSID",
    "QuerySID",
    "RecommendationStats",
    "RecommendationStatsWriteSummary",
    "ResidualKMeansLevel",
    "SIDIndexWriteSummary",
    "SerializedSIDItem",
    "SerializedSIDWriteSummary",
    "TrainedResidualCodebooks",
    "build_item_sids",
    "build_query_sid",
    "build_recommendation_stats",
    "encode_serialized_items",
    "encode_serialized_items_with_mlx",
    "load_codebooks",
    "serialize_structured_items",
    "serialize_taxonomy_text",
    "train_codebooks",
    "write_codebooks",
    "write_embedded_items",
    "write_recommendation_stats",
    "write_serialized_items",
    "write_sid_index_outputs",
]
