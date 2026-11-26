# FraudLink architecture

The browser calls FastAPI over same-origin REST through nginx. Vite proxies the same paths during development. FastAPI validates each upload and invokes the analysis service. MongoDB stores immutable runs and a single active-run pointer. Cases reference the run that supplied their evidence.

| Directory | Responsibility |
| --- | --- |
| frontend/src | React console, Recharts, Cytoscape interaction, accessible native dialogs |
| backend/routes | REST resources, filtering, evidence validation, CSV and PDF serialization |
| backend/models | Case commands with constrained fields and optimistic revisions |
| backend/utils | UTF-8 CSV schema, amount and identifier validation, UTC normalization |
| backend/ml | Scaled feature matrix, Isolation Forest, DBSCAN, NetworkX topology |
| backend/services | Period aggregation and chronological circular-exchange evidence |
| backend/database | MongoDB indexes, run publication and retrieval |
| datasets | Reproducible synthetic USD transfer ledger |
| tests | Dependency-light graph and ingestion tests, full-stack HTTP smoke test |

## Analysis semantics

The model measures atypical activity within the imported batch. Scaling and fitting occur on that batch. The raw Isolation Forest score is transformed by a fixed monotone scaling and augmented with cycle and density-outlier signals. Thresholds of 0.36, 0.60 and 0.78 define Medium, High and Critical risk. High and Critical transfers are flagged. Scores have no calibrated probability interpretation.

A strong component identifies directed cyclical connectivity even when the transfers did not occur in chronological order. A separate chronological rule records time-ordered three-account loops within two hours, retaining transfers within 20% of the largest leg and examining up to 64 recent incoming transfers per account. Such loops receive a high-risk score floor. Weak components of flagged edges form the suspicious account clusters. DBSCAN labels describe behavioral similarity in transaction feature space. Displayed multi-hop graph paths describe reachability. Evidence timelines preserve event order.

Daily frequency, pair repetition and distinct-counterparty counts are batch features. In the demo, ordinary merchant accounts can exhibit high fan-in. An alert is a lead for human review. Optional labels are excluded from features and used to compute descriptive precision and recall on the active dataset. These are in-sample metrics. Feature sensitivity measures mean absolute changes to the forest score after substituting a feature median. It does not estimate a causal effect.

## Persistence and operations

Each run has a unique ID and a corresponding trusted local Joblib file. MongoDB publishes the pointer after all records and the model are written. Concurrent completed imports use last-publication-wins semantics. A failed write can leave an inactive run or model for later cleanup. Investigation cases keep their original run even after a replacement dataset. Case edits require the expected revision to prevent lost updates. Back up both named volumes and preserve all runs referenced by cases.

This distribution targets a trusted, single-analyst workstation. The Compose network exposes the web console and API only on loopback. Sharing outside that boundary requires authentication, case-level authorization, TLS, authenticated database access, audit logging, import rate limits and a tested backup/restore procedure. Upload limit is 4 MB and 10,000 transactions. Graph rendering and synchronous batch scoring target analyst-scale datasets.

