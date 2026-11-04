# Architecture

```mermaid
flowchart LR
    A[Canonical catalog JSON] --> B[Runtime loader]
    L[Retailer listings JSON] --> B
    B --> N[Normalization]
    N --> U[Unit conversion]
    U --> E[Exact/signature comparison]
    E -->|unique compatible signature| M
    E -->|no unique signature| V[Token-index candidate retrieval]
    V --> C[Candidate scoring]
    C --> G[Compatibility safeguards]
    G --> D{Confidence and margin}
    D -->|safe| M[Approved canonical match]
    D -->|uncertain/conflict| R[Abstain and human review]
    M --> I[Startup search index]
    I --> S[Search ranking and deduplication]
    M --> K[Canonical category safeguard]
    W[Optional upstream category worker] --> K
    K --> API[FastAPI /match and /search]
    R --> API
    T[Independent ground truth] --> Q[Evaluation metrics]
    M --> Q
```

## Boundaries

- `normalization.py` handles text, aliases, units, and multipacks.
- `matcher.py` owns candidate scoring, hard incompatibilities, thresholds, and abstention.
- `category.py` prevents uncertain, timed-out, or conflicting upstream output from replacing a known canonical category.
- `search.py` indexes only approved identity matches and exposes ranking components.
- `evaluation.py` compares predictions with independently authored truth.
- `api.py` is a thin delivery layer over the same tested core used by the CLI.

The prototype intentionally uses immutable local JSON. It does not claim production durability, authentication, or distributed consistency.
