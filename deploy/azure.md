# Deploying to Azure Container Apps

This guide puts the Docker image from this repo on **Azure Container Apps** and gives it a public HTTPS URL.
All commands run in the **Codespaces terminal**, from the repo root. Copy them one block at a time.

Checked against Azure CLI **2.92.0** (`az version`).

**Before you start:** do Part A of [`user-tasks.md`](../user-tasks.md) (active subscription, budget alert, resource providers).

## What gets created

Everything goes into one resource group, so a single command deletes it all at the end.

| Resource | Name | Why |
|----------|------|-----|
| Resource group | `wine-qc-rg` | container for everything below |
| Container registry (Basic) | `wineqc<8 characters>` | stores the Docker image |
| Container Apps environment | `wine-qc-env` | the network/runtime the app runs in (created by `az containerapp up`) |
| Log Analytics workspace | auto-generated name | container logs (created by `az containerapp up`) |
| Container app | `wine-qc` | runs the image and gives it a public URL |

**Cost.** Container Apps has a monthly free allowance (vCPU-seconds, memory and requests), and the app scales to
zero when idle, so the app itself should cost nothing. The **container registry (Basic tier) is billed per day**,
roughly USD 5 per month, whether you use it or not. Log Analytics charges only for logs above a free amount, and this
app writes very little. Check current prices on the
[Container Apps](https://azure.microsoft.com/pricing/details/container-apps/) and
[Container Registry](https://azure.microsoft.com/pricing/details/container-registry/) pricing pages.
**Delete everything after grading** (step 9).

---

## 1. Install the Azure CLI (once per Codespace)

```bash
uv tool install azure-cli
az version
```

`uv tool install` puts `az` in `~/.local/bin`, outside the project's virtual environment. If `az version` already
works, skip this step.

## 2. Sign in

```bash
az login --use-device-code
```

The terminal shows a code. Open <https://microsoft.com/devicelogin> in your browser, paste the code and sign in.
Your password never goes into Codespaces.

If you have more than one subscription, select the right one (the name from `user-tasks.md` step A1):

```bash
az account list -o table
az account set --subscription "<your subscription name>"
az account show --query name -o tsv     # check
```

## 3. Set the names

```bash
RG=wine-qc-rg
LOCATION=westeurope
APP=wine-qc
ENV_NAME=wine-qc-env
# registry names must be globally unique: add the first 8 characters of your subscription ID
ACR=wineqc$(az account show --query id -o tsv | cut -c1-8)
IMAGE=$ACR.azurecr.io/red-wine-quality-qc:v1
echo $ACR $IMAGE
```

These are shell variables: **if you open a new terminal, run this block again** (it always gives the same names).

## 4. Make sure the resource providers are registered

You did this in the portal (`user-tasks.md` A3). These commands do the same and are harmless if already done:

```bash
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
```

## 5. Create the resource group and the container registry

```bash
az group create --name $RG --location $LOCATION -o table
az acr create --name $ACR --resource-group $RG --location $LOCATION --sku Basic --admin-enabled true -o table
```

`--admin-enabled true` turns on a username/password for the registry, which the container app uses to pull the image.

## 6. Build the image and push it to the registry

```bash
docker build --platform linux/amd64 -t $IMAGE .
az acr login --name $ACR
docker push $IMAGE
```

This is the same Dockerfile you ran locally in Phase 5. `--platform linux/amd64` matches what Azure runs (it only
matters if you ever build on an Apple Silicon Mac). The push uploads about 130 MB.

## 7. Create the container app

```bash
ACR_USER=$(az acr credential show --name $ACR --query username -o tsv)
ACR_PASS=$(az acr credential show --name $ACR --query "passwords[0].value" -o tsv)

az containerapp up \
  --name $APP \
  --resource-group $RG \
  --location $LOCATION \
  --environment $ENV_NAME \
  --image $IMAGE \
  --registry-server $ACR.azurecr.io \
  --registry-username $ACR_USER \
  --registry-password $ACR_PASS \
  --ingress external \
  --target-port 9696
```

- `--ingress external`: the app gets a public HTTPS address.
- `--target-port 9696`: the port uvicorn listens on inside the container (see the Dockerfile).
- Azure terminates HTTPS and forwards to port 9696, so the public URL has **no port number**.

The first run takes a few minutes, because it also creates the environment and the Log Analytics workspace.

## 8. Get the URL and test it

```bash
URL=https://$(az containerapp show --name $APP --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv)
echo $URL

curl $URL/health
uv run python test.py $URL/predict
```

Expected: `{"status":"ok"}`, then the quality-8 wine gets a high probability ("send to premium tasting panel") and
the quality-5 wine a low one ("standard line"), the same numbers as locally.

The app scales to zero when idle, so **the first request after a pause can take 10–30 seconds** while a container
starts. `test.py` waits up to 30 seconds per request.

### Screenshots for the reviewers

The URL may be shut down after grading, so the README shows screenshots as evidence. Save them in `images/`:

1. **`images/cloud_test.png`**: the terminal showing the `echo $URL` output and `uv run python test.py $URL/predict`
   with its result.
2. **`images/cloud_docs.png`**: `<URL>/docs` open in your browser (print the full link with `echo $URL/docs`), ideally
   with `POST /predict` expanded and a "Try it out" response visible.

To get them into the repo, drag the files into the `images/` folder in the Codespaces file explorer.

## Useful extras

**Logs** (for example if `test.py` fails):

```bash
az containerapp logs show --name $APP --resource-group $RG --tail 50
az containerapp logs show --name $APP --resource-group $RG --follow    # live; Ctrl+C to stop
```

**Deploy a new version** (after retraining or changing `predict.py`): build and push with a new tag, then point the
app at it:

```bash
IMAGE=$ACR.azurecr.io/red-wine-quality-qc:v2
docker build --platform linux/amd64 -t $IMAGE .
docker push $IMAGE
az containerapp update --name $APP --resource-group $RG --image $IMAGE
```

**No cold starts during grading** (optional): keep one container always running. That uses more of the free allowance
and can cost money once the allowance is used up. Set it back to 0 afterwards.

```bash
az containerapp update --name $APP --resource-group $RG --min-replicas 1    # always on
az containerapp update --name $APP --resource-group $RG --min-replicas 0    # back to scale-to-zero
```

## 9. Delete everything (after grading)

```bash
az group delete --name $RG --yes --no-wait
```

This deletes the resource group and **everything in it**: the app, environment, registry and logs. It runs in the
background for a few minutes. Afterwards `az group exists --name wine-qc-rg` should print `false`. The README keeps
the screenshots, so reviewers can still see that the deployment worked.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `MissingSubscriptionRegistration` | a resource provider isn't registered yet: re-run step 4 and wait |
| `The registry name ... is already in use` | very unlikely with the subscription-ID suffix; change `ACR=` to another lowercase name (5–50 letters/digits) |
| `docker push` → `unauthorized` | the registry login expired: run `az acr login --name $ACR` again |
| `test.py` times out on the first call | cold start: run it again |
| `test.py` → 404 | the URL is missing `/predict` at the end |
| Variables are empty (`echo $ACR` prints nothing) | new terminal: re-run step 3 |
