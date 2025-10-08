"""Test queries for DuckLake documentation retrieval evaluation."""

# Each query has:
# - query: The search query string
# - category: Type of query (factual, conceptual, procedural, complex)
# - expected_keywords: Keywords that should appear in relevant chunks
# - expected_topics: High-level topics that should be covered

DUCKLAKE_TEST_QUERIES = [
    {
        "query": "What primitive data types does DuckLake support?",
        "category": "factual",
        "expected_keywords": [
            "int8", "int16", "int32", "int64", "float32", "float64",
            "boolean", "varchar", "decimal", "timestamp", "date", "blob"
        ],
        "expected_topics": ["data types", "primitive types"]
    },
    {
        "query": "What is a DuckLake snapshot?",
        "category": "conceptual",
        "expected_keywords": [
            "snapshot", "snapshot_id", "ducklake_snapshot", "version", "transaction"
        ],
        "expected_topics": ["snapshot", "versioning", "time travel"]
    },
    {
        "query": "How to list tables in DuckLake?",
        "category": "procedural",
        "expected_keywords": [
            "ducklake_table", "SELECT", "schema_id", "table_id", "table_name"
        ],
        "expected_topics": ["queries", "list tables"]
    },
    {
        "query": "What nested types are supported?",
        "category": "factual",
        "expected_keywords": [
            "list", "struct", "map", "nested", "child type"
        ],
        "expected_topics": ["nested types", "data types"]
    },
    {
        "query": "How does DuckLake handle geometry types?",
        "category": "complex",
        "expected_keywords": [
            "geometry", "point", "linestring", "polygon", "multipoint", "spatial"
        ],
        "expected_topics": ["geometry types", "spatial"]
    },
    {
        "query": "What is file pruning in DuckLake?",
        "category": "conceptual",
        "expected_keywords": [
            "prune", "ducklake_file_column_stats", "min_value", "max_value", "filter"
        ],
        "expected_topics": ["file pruning", "optimization", "statistics"]
    },
    {
        "query": "How to create a new snapshot?",
        "category": "procedural",
        "expected_keywords": [
            "INSERT INTO ducklake_snapshot", "snapshot_id", "snapshot_timestamp",
            "ducklake_snapshot_changes"
        ],
        "expected_topics": ["snapshot creation", "writing data"]
    },
    {
        "query": "What are the catalog database requirements?",
        "category": "conceptual",
        "expected_keywords": [
            "catalog database", "transactions", "primary key", "SQL-92"
        ],
        "expected_topics": ["catalog", "requirements", "database"]
    },
    {
        "query": "How to query table columns in DuckLake?",
        "category": "procedural",
        "expected_keywords": [
            "ducklake_column", "column_id", "column_name", "column_type", "table_id"
        ],
        "expected_topics": ["columns", "table structure", "queries"]
    },
    {
        "query": "What is schema evolution?",
        "category": "conceptual",
        "expected_keywords": [
            "schema evolution", "ALTER", "column", "add", "drop", "schema_version"
        ],
        "expected_topics": ["schema evolution", "schema changes"]
    },
    {
        "query": "How does DuckLake store data files?",
        "category": "conceptual",
        "expected_keywords": [
            "Parquet", "ducklake_data_file", "data storage", "path", "object storage"
        ],
        "expected_topics": ["data storage", "Parquet files"]
    },
    {
        "query": "What maintenance operations are recommended?",
        "category": "factual",
        "expected_keywords": [
            "maintenance", "merge", "expire snapshots", "cleanup", "checkpoint"
        ],
        "expected_topics": ["maintenance", "operations"]
    },
    {
        "query": "How to handle deleted rows in DuckLake?",
        "category": "procedural",
        "expected_keywords": [
            "delete", "ducklake_delete_file", "DELETE", "remove rows"
        ],
        "expected_topics": ["delete operations", "delete files"]
    },
    {
        "query": "What is time travel in DuckLake?",
        "category": "conceptual",
        "expected_keywords": [
            "time travel", "snapshot", "historical", "AS OF", "version"
        ],
        "expected_topics": ["time travel", "versioning", "snapshots"]
    },
    {
        "query": "How to connect to a DuckLake catalog?",
        "category": "procedural",
        "expected_keywords": [
            "ATTACH", "connect", "catalog", "database", "CONNECTION"
        ],
        "expected_topics": ["connecting", "catalog", "usage"]
    }
]


def get_query_by_category(category: str):
    """Get all queries of a specific category."""
    return [q for q in DUCKLAKE_TEST_QUERIES if q["category"] == category]


def get_all_queries():
    """Get all test queries."""
    return DUCKLAKE_TEST_QUERIES
