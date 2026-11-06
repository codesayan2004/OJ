# Deploying CodeSphere on AWS (EC2 + ECR)

Production layout on a single EC2 instance:

```
Internet ──► EC2 security group (80, 443)
               │
               ▼
        nginx:1.27  (container)   TLS, /static/, rate limiting
               │ http://web:8000
               ▼
        codesphere-web (container)   Gunicorn + Django
               │ /var/run/docker.sock
               ▼
        codesphere-runner (one short-lived container per run / test case)

Images: Amazon ECR  ──docker pull──►  EC2
Data:   Docker volume app-data (SQLite + test cases), survives redeploys
```

## 1. One-time AWS setup

1. **ECR**: nothing to click; `deploy/ecr_push.sh` creates the `codesphere-web`
   and `codesphere-runner` repositories (with scan-on-push) if missing.
2. **IAM role for EC2**: create a role with the managed policy
   `AmazonEC2ContainerRegistryReadOnly` and attach it to the instance, so the
   server can pull images without AWS keys on disk.
3. **EC2**: Ubuntu 24.04 (or Amazon Linux 2023), t3.small or larger
   (compilers need RAM), 20 GB disk. Allocate an **Elastic IP**.
4. **Security group**: inbound 22 from *your IP only*, 80 and 443 from anywhere.
5. **DNS**: A records `codespher.me` and `www.codespher.me` → Elastic IP.

## 2. Build and push images to ECR (laptop or GitHub Actions)

```bash
aws configure                     # credentials with ECR push rights
AWS_ACCOUNT_ID=123456789012 AWS_REGION=ap-south-1 ./deploy/ecr_push.sh
```

What it does: `aws ecr get-login-password | docker login`, builds both images for
`linux/amd64`, tags them with the git commit and `latest`, pushes both.
GitHub Actions can do the same: *Actions → CI / Deploy → Run workflow* (needs the
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ACCOUNT_ID` repository secrets).

## 3. Prepare the EC2 instance (once)

```bash
scp -r deploy docker-compose.yml .env.example ubuntu@<elastic-ip>:~/codesphere/
ssh ubuntu@<elastic-ip>
cd codesphere
sudo ./deploy/ec2_bootstrap.sh     # Docker + compose plugin, AWS CLI, swap, /var/lib/codesphere/runs
exit && ssh ubuntu@<elastic-ip>    # re-login so the docker group applies
cp .env.example .env && nano .env  # DJANGO_SECRET_KEY, GEMINI_API_KEY, hosts
```

## 4. Deploy / redeploy

```bash
cd ~/codesphere
AWS_ACCOUNT_ID=123456789012 AWS_REGION=ap-south-1 ./deploy/ec2_deploy.sh
```

`docker compose pull` fetches the new images from ECR, `docker compose up -d`
restarts only what changed. On start the web container runs `migrate` and
`collectstatic`, then `exec`s Gunicorn (`backend/gunicorn.conf.py`:
2 × CPU + 1 workers, gthread, 120 s timeout, logs to stdout).

## 5. HTTPS (once)

```bash
EMAIL=you@example.com ./deploy/init_letsencrypt.sh
```

Nginx starts on `deploy/nginx/local.conf` (HTTP, serves the ACME challenge),
certbot obtains the certificate with the webroot method, then the script
switches `NGINX_CONF=codesphere.conf` (HTTP → HTTPS redirect, TLS 1.2/1.3, HSTS).
Add the renewal cron line printed at the end of the script.

## Operations cheat sheet

| Task | Command |
| --- | --- |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f web nginx` |
| Django shell | `docker compose exec web python manage.py shell` |
| Create admin | `docker compose exec web python manage.py createsuperuser` |
| Back up data | `docker run --rm -v codesphere_app-data:/d -v $PWD:/b alpine tar czf /b/backup.tgz -C /d .` |
| Reload Nginx | `docker compose exec nginx nginx -s reload` |
| Roll back | `./deploy/ec2_deploy.sh <previous-git-sha>` |

## Security notes

* Secrets live only in `.env` on the server (git-ignored).
* The web container talks to the Docker daemon through the socket; that is
  powerful, so the web container runs as a non-root user and user code never
  runs in it. A further step would be a separate judge host or a rootless
  Docker / gVisor runtime for the sandbox containers.
* Test-case files are never served by Nginx (`/media/` → 404); authors
  download them through an authenticated Django view.
