# Cloud Run Deployment Setup

This guide walks through setting up automated deployment to Google Cloud Run using GitHub Actions with Workload Identity Federation (recommended security best practice).

## Prerequisites

- Google Cloud Project: `upbeat-lexicon-411217`
- GitHub repository access
- `gcloud` CLI installed locally

## Setup Steps

### 1. Enable Required APIs

```bash
gcloud config set project upbeat-lexicon-411217

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iamcredentials.googleapis.com
```

### 2. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create rehearsed-images \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for Rehearsed Multi-Student API"
```

### 3. Create Service Account for Cloud Run

```bash
# Create service account
gcloud iam service-accounts create rehearsed-cloudrun-sa \
  --display-name="Rehearsed Cloud Run Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding upbeat-lexicon-411217 \
  --member="serviceAccount:rehearsed-cloudrun-sa@upbeat-lexicon-411217.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Grant Vertex AI permissions (for Gemini API)
gcloud projects add-iam-policy-binding upbeat-lexicon-411217 \
  --member="serviceAccount:rehearsed-cloudrun-sa@upbeat-lexicon-411217.iam.gserviceaccount.com" \
  --role="roles/ml.developer"
```

### 4. Set Up Workload Identity Federation

This allows GitHub Actions to authenticate without storing service account keys.

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-actions-pool \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner == 'meganzinka'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions Service Account"

# Grant permissions to deploy
gcloud projects add-iam-policy-binding upbeat-lexicon-411217 \
  --member="serviceAccount:github-actions-sa@upbeat-lexicon-411217.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding upbeat-lexicon-411217 \
  --member="serviceAccount:github-actions-sa@upbeat-lexicon-411217.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding upbeat-lexicon-411217 \
  --member="serviceAccount:github-actions-sa@upbeat-lexicon-411217.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Allow GitHub Actions to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding github-actions-sa@upbeat-lexicon-411217.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe upbeat-lexicon-411217 --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/meganzinka/mulit-agent-student-flow"
```

### 5. Get Workload Identity Provider Name

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --format="value(name)"
```

Copy the output (format: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`)

### 6. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `WIF_PROVIDER` | The full provider name from step 5 |
| `WIF_SERVICE_ACCOUNT` | `github-actions-sa@upbeat-lexicon-411217.iam.gserviceaccount.com` |
| `CLOUD_RUN_SERVICE_ACCOUNT` | `rehearsed-cloudrun-sa@upbeat-lexicon-411217.iam.gserviceaccount.com` |

### 7. Deploy

Push to `main` branch or trigger manually:

```bash
git add .
git commit -m "Add Cloud Run deployment"
git push origin main
```

Or manually trigger from GitHub Actions UI.

## Testing Deployment

Once deployed, test the endpoints:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe rehearsed-multi-student-api \
  --region us-central1 \
  --format 'value(status.url)')

# Health check
curl $SERVICE_URL/

# List students
curl $SERVICE_URL/students
```

## Monitoring

View logs:
```bash
gcloud run services logs read rehearsed-multi-student-api \
  --region us-central1 \
  --limit 50
```

View service details:
```bash
gcloud run services describe rehearsed-multi-student-api \
  --region us-central1
```

## Updating the Service

Just push changes to the `backend/` directory on the `main` branch. The workflow automatically:
1. Builds a new Docker image
2. Pushes to Artifact Registry
3. Deploys to Cloud Run
4. Outputs the service URL

## Cost Optimization

Current settings:
- **Min instances**: 0 (scales to zero when idle)
- **Max instances**: 10
- **Memory**: 2Gi (adjust based on load)
- **CPU**: 2 (adjust based on performance needs)
- **Timeout**: 300s (for longer SSE streams)
- **Concurrency**: 80 requests per instance

## Troubleshooting

### Authentication Errors
Ensure Workload Identity Federation is set up correctly and GitHub secrets are configured.

### Image Not Found
Check Artifact Registry:
```bash
gcloud artifacts docker images list us-central1-docker.pkg.dev/upbeat-lexicon-411217/rehearsed-images
```

### Deployment Fails
Check Cloud Run logs and ensure service account has necessary permissions.

### Gemini API Errors
Verify the Cloud Run service account has `roles/aiplatform.user` and `roles/ml.developer` roles.
