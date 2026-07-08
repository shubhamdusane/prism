# Prism - Architecture

## System Overview

Prism is a multi-modal data pipeline orchestrator that ingests, transforms, and routes data across diverse formats (structured, unstructured, streaming, batch). It provides a visual pipeline builder, format adapters, and a unified transformation engine.

```
┌──────────────────────────────────────────────────────────────────┐
│                      Pipeline Builder (Web UI)                   │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Drag &   │  │ Transform  │  │ Preview    │  │ Schedule   │  │
│  │ Drop     │  │ Library    │  │ Panel      │  │ Manager    │  │
│  └─────┬────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  │
├────────┼──────────────┼───────────────┼───────────────┼──────────┤
│                      Pipeline Engine                             │
│  ┌─────▼──────────────▼───────────────▼───────────────▼──────┐  │
│  │              PipelineOrchestrator                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ DAG      │  │ Transform│  │ Monitor  │  │ Scheduler│  │  │
│  │  │ Builder  │  │ Runner   │  │          │  │          │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                      Format Adapters                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  JSON    │  │  CSV     │  │  Parquet │  │  Avro        │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  XML     │  │  YAML    │  │  Binary  │  │  Stream      │   │
│  │          │  │          │  │  (Proto) │  │  (Kafka)     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Transform Layer │  │  Connector     │  │  Metadata      │  │
│  │  (Map/Filter/    │  │  Registry      │  │  Store         │  │
│  │   Aggregate)     │  │                │  │                │  │
│  └──────────────────┘  └────────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Pipeline Builder
Visual interface for designing data pipelines with drag-and-drop nodes.

| Component | Responsibility |
|-----------|---------------|
| `DragDrop` | Node palette and canvas for pipeline construction |
| `TransformLibrary` | Reusable transformation components catalog |
| `PreviewPanel` | Real-time data preview at each pipeline stage |
| `ScheduleManager` | Cron-based and event-triggered pipeline scheduling |

### Pipeline Engine

| Component | Responsibility |
|-----------|---------------|
| `PipelineOrchestrator` | Executes pipelines as DAGs with parallel branches |
| `DAGBuilder` | Validates pipeline topology and resolves execution order |
| `TransformRunner` | Executes transformation functions with resource limits |
| `Monitor` | Tracks pipeline progress, errors, and performance metrics |
| `Scheduler` | Manages cron schedules and event-triggered executions |

### Format Adapters
Bidirectional format converters for data ingestion and output.

- **JSON/JSONL**: Streaming JSON parser with schema validation
- **CSV**: Header detection, type inference, and encoding handling
- **Parquet**: Columnar format with predicate pushdown
- **Avro**: Schema evolution support
- **XML**: XPath-based extraction
- **Binary**: Protocol Buffers and custom binary formats
- **Stream**: Kafka, Redis Streams, and NATS adapters

## Data Flow

```
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ Source   │────▶│ Format    │────▶│ DAG          │
│ (file/   │     │ Adapter   │     │ Orchestrator │
│  stream) │     │ (ingest)  │     │              │
└──────────┘     └───────────┘     └──────┬───────┘
                                          │
                    ┌─────────────────────▼──────────────────┐
                    │         Parallel Transform Branches     │
                    │  ┌────────┐  ┌────────┐  ┌────────┐   │
                    │  │Branch 1│  │Branch 2│  │Branch 3│   │
                    │  │(map)   │  │(filter)│  │(agg)   │   │
                    │  └───┬────┘  └───┬────┘  └───┬────┘   │
                    └──────┼───────────┼───────────┼─────────┘
                           │           │           │
                           ▼           ▼           ▼
                    ┌─────────────────────────────────────────┐
                    │         Merge & Output Format           │
                    └─────────────────────────────────────────┘
```

## Directory Structure

```
prism/
├── src/
│   ├── web/                 # Pipeline builder UI
│   │   ├── components/
│   │   │   ├── Canvas/
│   │   │   ├── NodePalette/
│   │   │   ├── Preview/
│   │   │   └── Schedule/
│   │   └── hooks/
│   ├── engine/              # Pipeline execution
│   │   ├── orchestrator.ts
│   │   ├── dagBuilder.ts
│   │   ├── transformRunner.ts
│   │   ├── monitor.ts
│   │   └── scheduler.ts
│   ├── adapters/            # Format adapters
│   │   ├── base.ts
│   │   ├── json.ts
│   │   ├── csv.ts
│   │   ├── parquet.ts
│   │   ├── avro.ts
│   │   ├── xml.ts
│   │   └── stream.ts
│   ├── transforms/          # Transform functions
│   │   ├── map.ts
│   │   ├── filter.ts
│   │   ├── aggregate.ts
│   │   ├── join.ts
│   │   └── deduplicate.ts
│   ├── connectors/          # Source/sink connectors
│   │   ├── s3.ts
│   │   ├── kafka.ts
│   │   ├── database.ts
│   │   └── http.ts
│   └── metadata/            # Schema and lineage
│       ├── schemaStore.ts
│       └── lineageTracker.ts
├── tests/
├── docs/
├── package.json
└── tsconfig.json
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| DAG-based pipelines | Enables parallelism, validation, and clear data flow |
| Format adapters | Uniform interface for diverse data formats |
| Visual builder | Low-code entry point for non-technical users |
| Streaming-first | Handles real-time and batch with same pipeline definitions |
| Metadata tracking | Data lineage and schema evolution for governance |

## Dependencies

- **Engine**: `apache-arrow`, `fast-csv`, `node-parquet`
- **Stream**: `kafkajs`, `ioredis`
- **Web**: `react`, `reactflow`
- **Build**: `typescript`, `vite`
- **Testing**: `vitest`

## Security Considerations

- Pipeline definitions version-controlled with access control
- Data preview sanitized to prevent PII leakage in UI
- Source/sink credentials encrypted at rest
- Rate limiting on connector endpoints
- Audit trail for all pipeline executions
- Transform functions sandboxed for untrusted code

## Performance Characteristics

- Streaming throughput: 100K records/second
- Batch processing: 1M records in <30 seconds
- Pipeline startup: <500ms
- Format conversion: <10ms per 1000 records
- Memory efficiency: streaming mode uses <100MB for any pipeline size

## Extension Points

| Extension | Mechanism |
|-----------|-----------|
| Custom formats | Implement `FormatAdapter` interface |
| Custom transforms | Register new transform functions |
| Custom connectors | Build source/sink connectors for new systems |
| Custom schedulers | Plugin alternative scheduling strategies |
| Metadata providers | Extend lineage tracking with custom metadata |
