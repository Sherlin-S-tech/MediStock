# Architecture and DevOps workflow

## Application runtime architecture

```mermaid
flowchart LR
  U[User] --> B[Browser]
  B --> UI[HTML / CSS / JavaScript and Bootstrap]
  UI --> R[Flask routes]
  R --> V[Server-side validation]
  V --> S[Expiry, stock and report services]
  S --> DB[(SQLite database)]
  S --> D[Dashboard statistics]
  S --> I[Inventory CRUD and filters]
  S --> E[Expiry alerts]
  S --> L[Low-stock list]
  S --> C[CSV reports]
```

The browser renders responsive templates and submits forms. Flask validates input and uses parameterized SQLite operations. Business rules compute expiry and low stock from records. SQLite persists in the Docker named volume.

## DevOps delivery architecture

```mermaid
flowchart LR
  Dev[Developer] --> Git[Git feature branch]
  Git --> GH[GitHub repository]
  GH --> J[Jenkins pipeline]
  J --> Setup[Dependencies and syntax checks]
  Setup --> Tests[pytest + JUnit report]
  Tests -->|pass| Build[Build tagged Docker image]
  Tests -->|fail| Stop[Fail pipeline; stop before image build or deployment]
  Build --> Gate{Deployment enabled?}
  Gate -->|yes| Ansible[Ansible deploy exact image tag]
  Gate -->|no| Done[Build verified]
  Ansible --> Run[Running container + persistent volume]
  Run --> Health[Health endpoint verification]
```

Jenkins checks out the source, runs syntax/config checks and pytest. A failure prevents image build and deployment. On success, Jenkins tags the image with the checked-out commit; Ansible receives that exact tag, updates the container while retaining its named data volume, and checks health. A public GitHub webhook requires an endpoint GitHub can reach.

## Component roles

| Component | Responsibility |
|---|---|
| Flask | Routes, forms, health and report endpoints |
| SQLite | Medicine batch records and indexes |
| pytest | Deterministic route, validation, date and CSV checks |
| Git/GitHub | Version history, branches and source collaboration |
| Jenkins | Test gate, image build and optional deployment orchestration |
| Docker | Repeatable image and persistent runtime volume |
| Ansible | Idempotent container deployment and health verification |

