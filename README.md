# CloudShelf — Cloud File Storage Portal

A cloud computing mini project built with Flask and Amazon S3. Upload, browse, download and delete files from a single dashboard. The app uses Amazon S3 when `S3_BUCKET` is configured and switches to local demo storage when it is blank.

## Features

- Upload files up to 16 MB, list stored files, download and delete.
- Amazon S3 object storage with a configurable AWS region.
- Local storage mode for a quick classroom demo without AWS credentials.
- Docker image runs as a non-root user and includes a `/health` endpoint.
- Responsive dashboard and flash messages.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. Uploads are saved under `data/` in local demo mode. Check the health endpoint at http://localhost:5000/health.

## Run with Docker

```bash
docker build -t cloudshelf .
docker run --rm -p 5000:5000 -v cloudshelf-data:/app/data cloudshelf
```

Open http://localhost:5000. The named Docker volume keeps local demo files between container restarts.

## Connect Amazon S3

1. Create a private S3 bucket in your AWS account. Keep Block Public Access enabled.
2. Create an IAM role/user with only the required `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, and `s3:DeleteObject` access to that bucket. Prefer workload IAM roles over long-lived access keys.
3. Set `S3_BUCKET` to your bucket name and `AWS_DEFAULT_REGION` to its region. Provide AWS credentials through the standard AWS credential chain (for example, an IAM role or local AWS profile).
4. Start the app again. The storage badge should show Amazon S3.

For a local AWS profile, configure it with `aws configure` and run with `AWS_PROFILE=your-profile` (PowerShell: `$env:AWS_PROFILE="your-profile"`). Never commit credentials or a real `.env` file.

## Cloud deployment outline

Build and push the Docker image to Amazon ECR, then deploy it to AWS App Runner or ECS Fargate. Set the container port to `5000`, attach an instance/task role with the bucket permissions above, and add `S3_BUCKET` and `AWS_DEFAULT_REGION` as service environment variables. Configure the platform health check to use `/health`. Store `FLASK_SECRET_KEY` as a managed secret. Do not expose the S3 bucket publicly.

## Architecture

```text
Browser → Flask web app (Docker) → Amazon S3 private bucket
                            └────→ Local disk (demo mode when S3_BUCKET is empty)
```

The browser sends file uploads to the Flask server over HTTP. Flask uses the AWS SDK and its IAM identity to store objects in S3. The browser never receives AWS credentials.

## Project structure

```text
app.py                 Flask routes and S3/local storage adapter
templates/index.html   Responsive file dashboard
Dockerfile             Container image definition
requirements.txt       Python dependencies
.env.example           Example configuration (no secrets)
```

## Limitations and next steps

This is a learning project, not a production file service. It does not include user login, per-user access controls, malware scanning, encryption key management, or pagination for very large buckets. Add authentication and CSRF protection before exposing it to untrusted users.

## Learning outcomes

- Object storage concepts and S3 bucket access.
- IAM least privilege and role based cloud credentials.
- Containerization and managed container deployment.
- Health checks, environment based configuration, and local cloud service fallback.
