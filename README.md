# Medicine Stock and Expiry Tracking System with DevOps Automation

A Flask and SQLite pharmacy-inventory demonstration for 23IT723 DevOps Laboratory. It tracks fictional medicine batches, expiry dates, minimum-stock thresholds and CSV reports. It does not collect patient information or provide medical advice.

## Quick start (Python)

Requirements: Python 3.10+ and pip.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SECRET_KEY = "local-demo-secret-change-this-value"
$env:DATABASE_PATH = ".\data\medicines.db"
python app.py
```

Open http://localhost:5000. Visit `/health` to check service and database connectivity. A fresh, empty database is automatically initialized with three fictional example batches, matching the dashboard demo. Existing inventories are preserved. To add any missing examples manually, run `python scripts/seed_demo_data.py`; it is safe to repeat. Set `SEED_DEMO_DATA=false` to disable automatic seeding. Local SQLite data lives under `data/` and is gitignored. Set a random `SECRET_KEY` outside a short-lived demo.

## Docker Compose and persistence

Install Docker Desktop or Docker Engine with Compose. From the project root:

```sh
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f medicine-stock
curl -fsS http://localhost:5000/health
```

Browse http://localhost:5000. On first start, Compose creates named volume `medicine-data` mounted at `/app/data`; the empty database is seeded with the three demo batches. Existing volume contents are preserved. Update with `docker compose build medicine-stock && docker compose up -d --no-deps medicine-stock`; the volume stays attached. For a persistence demo, add a batch in the UI, rebuild/recreate as above, then find the batch again. Do not run `docker compose down -v` during normal updates; `-v` removes persistent data. Back up a volume from a Linux shell with `docker run --rm -v medicine-data:/data -v "$PWD:/backup" alpine tar czf /backup/medicine-data-backup.tgz -C /data .`.

Container and host mapping use port 5000. If busy, change host mapping to `5001:5000`. For a Docker daemon error, start Docker and check `docker info`; on Linux, confirm authorized daemon access. If tags differ, rebuild with the same `APP_IMAGE`/`APP_TAG` passed to Ansible. If data appears missing, inspect `docker volume ls`, `docker inspect medicine-stock`, and confirm `medicine-data:/app/data`; do not delete the volume.

### Docker command reference

```sh
docker pull python:3.12-slim
docker images
docker build -t medicine-stock:demo .
docker run -d --name medicine-stock -p 5000:5000 -e SECRET_KEY=local-demo-secret -v medicine-data:/app/data medicine-stock:demo
docker ps -a
docker inspect medicine-stock
docker logs -f medicine-stock
docker stop medicine-stock
docker start medicine-stock
docker rm -f medicine-stock
curl -fsS http://localhost:5000/health
docker compose up -d --build
```

Removing a container is safe for inventory; removing the named volume is not.

## Automated tests

Tests use a temporary SQLite file per test and a fixed date; they do not touch the real database.

```sh
pytest -q
pytest -q --junitxml=test-results.xml
```

## Git and GitHub lab guide

The starter directory may not itself be a Git checkout; no remote is configured, and no push is performed automatically. Initialize it and replace the example remote with your own:

```sh
git init -b main
git status --short
git add .
git commit -m "Build medicine inventory and DevOps demo"
git remote add origin https://github.com/OWNER/REPOSITORY.git
git remote -v
git push -u origin main
git fetch origin
git pull --ff-only origin main
git clone https://github.com/OWNER/REPOSITORY.git
git log --oneline --decorate --graph -10
git switch -c feature/inventory
git switch main
git merge --no-ff feature/inventory
```

Use branches such as `feature/inventory`, `feature/expiry-alerts`, and `feature/devops`. Commit coherent work before merging. For a conflict, run `git status`, edit conflicted files to resolve `<<<<<<<`, `=======`, and `>>>>>>>`, then `git add <resolved-files>` and `git commit`. Review `git diff` before committing.

## Jenkins pipeline setup

The root `Jenkinsfile` checks out SCM, creates a Python environment, compiles application files, validates Ansible YAML, runs pytest, publishes `test-results.xml`, then builds `APP_IMAGE:APP_TAG`. Tests gate image build and deployment. `DEPLOY_ENABLED` defaults to false.

1. Install Jenkins LTS on Linux or use a lab server. On the selected agent install Git, Python 3, pip, Docker Engine/CLI, Ansible Core and `community.docker`. Install Pipeline, Git, and JUnit plugins.
2. Create a Pipeline job using **Pipeline script from SCM**, Git, your repository URL, branch `main`, and script path `Jenkinsfile`.
3. Add a Jenkins Secret Text credential with ID `medicine-stock-secret-key`. Configure `APP_IMAGE` as a Jenkins environment setting if needed. Supply the deployment key through Jenkins Credentials to `MEDICINE_STOCK_SECRET_KEY`; use SSH credentials for a real remote host, never committed secrets.
4. Give the agent only the Docker/Ansible access needed. Docker group access commonly grants host-root-equivalent control; prefer a dedicated controlled deployment agent.
5. For GitHub webhook builds, set the repository webhook to `https://<publicly-reachable-jenkins>/github-webhook/` and enable the GitHub hook trigger. GitHub cannot reach localhost-only Jenkins. A lab alternative is **Build Now** after a push.
6. Review **Console Output** and published **Test Result**. Failed tests stop later stages; failed deployment marks the build failed.

If the agent cannot reach Docker, Jenkins cannot automate that stage there. Use local Docker/Compose commands and state that image build/deploy was manual. Jenkins passes the same commit-tagged image to Ansible; deployment is opt-in.

## Ansible deployment

Ansible is not assumed to be native on Windows. Use WSL2 Ubuntu or Linux and install:

```sh
sudo apt update && sudo apt install -y ansible-core python3-pip
python3 -m pip install --user docker
ansible-galaxy collection install community.docker
docker info
```

The provided `ansible/inventory.ini` is a local Linux/WSL lab example. Ensure Docker is running and available to the user, and enable WSL integration in Docker Desktop if applicable.

```sh
cd /path/to/project
docker build -t medicine-stock:demo .
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml --extra-vars 'app_image=medicine-stock:demo'
ansible-playbook -i ansible/inventory.ini ansible/manage_container.yml --extra-vars 'app_image=medicine-stock:demo'
curl -fsS http://localhost:5000/health
```

For a remote Linux host, configure its address, SSH user/key, and privilege escalation in a separate inventory; install Docker and the Python Docker SDK on the target, and grant least necessary access. Store secrets in Ansible Vault, a secret store, or Jenkins credentials, never in committed playbooks. Jenkins invokes Ansible after a successful image build. Playbooks use modules and preserve the named volume.

## Troubleshooting

- **Port busy:** map host `5001:5000` or stop the conflicting service.
- **Docker daemon unavailable:** start Docker, check `docker info`, and confirm permitted daemon access.
- **Wrong image version:** compare `docker images` with the exact `app_image` passed to Ansible.
- **Missing inventory after update:** check the named volume mount; do not remove it during an update.
- **Missing Ansible module:** install `community.docker` and Python Docker SDK on the controller.
- **CSRF rejection:** submit a form loaded from the app with its session token; do not disable CSRF outside isolated tests.
- **Dependency installation failure:** check Python and package-index/network access, then retry `pip install -r requirements.txt`.

See [architecture diagrams](docs/architecture.md) and the [project report](docs/project_report.md). Configuration keys are `SECRET_KEY`, `DATABASE_PATH`, and `NEAR_EXPIRY_DAYS`.

The local run, dashboard, and verification evidence is in [Project Run and GitHub Handoff](docs/Project_Run_and_GitHub_Evidence.docx). Demo inventory is stored in the ignored local SQLite database; use the seed script after cloning to recreate fictional sample records.

