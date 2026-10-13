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

The public project repository is https://github.com/Sherlin-S-tech/MediStock on branch `main`. Clone it or update an existing checkout with:

```sh
git clone https://github.com/Sherlin-S-tech/MediStock.git
cd MediStock
git pull --ff-only origin main
git status --short --branch
git log --oneline --decorate --graph -10
git switch -c feature/inventory
git switch main
git merge --no-ff feature/inventory
```

Use branches such as `feature/inventory`, `feature/expiry-alerts`, and `feature/devops`. Commit coherent work before merging. For a conflict, run `git status`, edit conflicted files to resolve `<<<<<<<`, `=======`, and `>>>>>>>`, then `git add <resolved-files>` and `git commit`. Review `git diff` before committing.

## Jenkins continuous integration and delivery

The root `Jenkinsfile` checks out the selected revision, installs Python dependencies, validates Python, Ansible YAML/playbooks, and Docker Compose configuration, then runs pytest. A test failure marks the build failed, publishes `test-results.xml` when pytest produced it, and skips the Docker build and deployment. After successful tests it builds the configurable `APP_IMAGE:APP_TAG` image. `APP_TAG` defaults to the checked-out commit's 12-character SHA; `APP_TAG_OVERRIDE` can set a valid Docker tag. `DEPLOY_ENABLED` defaults to false. When enabled, Ansible deploys that same tagged image and Jenkins checks `/health` on the target.

### Jenkins agent requirements

Install Jenkins LTS by following the [official Linux installation guide](https://www.jenkins.io/doc/book/installing/linux/); the current guide lists Java 21 or later as a prerequisite. Use a controlled Linux Jenkins agent, or WSL2 with Docker Desktop integration for a local lab. The agent needs Git, Python 3 and pip, Docker CLI with the Compose plugin, Ansible Core, and the `community.docker` Ansible collection. Install the Jenkins Pipeline, Git, GitHub, JUnit, and Credentials Binding plugins. Confirm the agent can run `git --version`, `python3 --version`, `docker info`, `docker compose version`, and `ansible-playbook --version`.

### Create and configure a Pipeline job

1. In Jenkins, choose **New Item**, enter a job name, select **Pipeline**, and choose **Pipeline script from SCM** in the job configuration.
2. Select **Git** and set the repository URL to `https://github.com/Sherlin-S-tech/MediStock.git`, branch to `*/main`, and script path to `Jenkinsfile`. The repository is public, so checkout does not need a GitHub token.
3. Enable **GitHub hook trigger for GITScm polling** in the job's build triggers. The Jenkinsfile also declares the GitHub push trigger.
4. Save, then select **Build with Parameters**. Set `APP_IMAGE` (default `medicine-stock`), optionally set `APP_TAG_OVERRIDE`, and leave `DEPLOY_ENABLED` off for a CI-only build.

For deployments, create a Jenkins **Secret Text** credential with ID `medicine-stock-secret-key`. It is only read when `DEPLOY_ENABLED` is on and is passed to Ansible through the environment; no secret belongs in the repository. The checked-in inventory targets `localhost`, so Ansible uses the same Docker engine as the Jenkins agent and does not need SSH credentials. For a remote host, configure Ansible's SSH access with Jenkins-managed credentials and make the tested image available to that host; the current playbooks use `pull: false` and do not publish the image to a registry.

### GitHub webhook and manual builds

In the GitHub repository, open **Settings → Webhooks → Add webhook**. Set the payload URL to an HTTPS Jenkins endpoint ending in `/github-webhook/`, choose `application/json`, and send push events. GitHub must be able to reach that endpoint. A Jenkins server available only at `localhost` cannot receive GitHub webhooks directly; use a properly secured, publicly reachable reverse proxy or webhook relay. Do not expose an unprotected Jenkins server to the internet.

For a local lab without an accessible webhook, push code and select **Build Now** in Jenkins (or **Build with Parameters** to choose the image tag and deployment setting). Open the build's **Console Output** for stage logs. Open **Test Result** for the JUnit report. A failed Syntax Validation stage points to Python, Ansible, YAML, or Compose configuration; a failed Automated Tests stage skips image build and deployment; Docker or Ansible failures identify agent permissions or deployment configuration problems.

### Docker access and manual alternative

The Jenkins agent needs permission to contact the Docker daemon for Compose configuration and image builds. Docker group membership can grant host-root-equivalent control. Prefer an isolated, controlled Jenkins agent or a restricted/rootless Docker service; do not casually add a shared Jenkins service account to the host's Docker group. The Ansible target also needs Docker access to deploy containers. The local example uses the same Docker engine for both operations.

If Docker is unavailable to the Jenkins agent, CI can still run through test reporting, but the Docker build and deployment stages are not automated. On a controlled machine with Docker access, build and run the app manually with `docker compose up --build -d`, then check `http://localhost:5000/health`. The Ansible deployment is only automated by Jenkins when `DEPLOY_ENABLED` is selected and its target and credentials are configured.

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

The local run and dashboard evidence is in [Project Run and GitHub Handoff](docs/Project_Run_and_GitHub_Evidence.docx). SQLite databases are gitignored; a fresh database automatically gets the fictional sample records.

