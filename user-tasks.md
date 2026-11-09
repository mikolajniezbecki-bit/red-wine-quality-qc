# Tasks for you (outside Codespaces)

Most of the project runs inside Codespaces and needs nothing from you. Only the **Azure cloud deployment (Phase 6)** needs your own account, so you'll do those steps yourself in a web browser. You can do Part A any time before Phase 6. It takes about 10 minutes and costs nothing.

The exact deployment commands come in `deploy/azure.md` during Phase 6. This file only gets your Azure account ready.

---

## Part A — Prepare your Azure account (do before Phase 6)

### A1. Check that your subscription is active
1. Open https://portal.azure.com and sign in with the Microsoft account that owns your personal Azure subscription.
2. Type **Subscriptions** in the search bar at the top and click it.
3. You should see at least one subscription with **Status: Active**. Write down its **name** (you'll need it in Phase 6).
   - If you see nothing, or the status is "Disabled", your subscription has expired. You can create a new free one at https://azure.microsoft.com/free.

### A2. Set a budget alert (a safety net against unexpected costs)
Azure Container Apps has a monthly free allowance, and this small app should stay within it. A budget alert will still email you if anything starts costing money.
1. In the portal search bar type **Cost Management** → open it → click **Budgets** in the left menu.
2. Click **+ Add**.
3. Scope = your subscription. Name: `wine-qc-budget`. Reset period: **Monthly**. Amount: **5** (in your currency).
4. Click **Next**. Under *Alert conditions* set **Type: Actual**, **% of budget: 50**. In *Alert recipients (email)* enter your email address.
5. Click **Create**.

### A3. Register the services the app needs (one-time)
New subscriptions sometimes have these "switched off". Turning them on is free.
1. In the portal search bar type **Subscriptions** → click your subscription.
2. In the left menu scroll to **Settings → Resource providers**.
3. Find each name below using the filter box. If its status isn't **Registered**, select it and click **Register** at the top:
   - `Microsoft.App`
   - `Microsoft.OperationalInsights`
   - `Microsoft.ContainerRegistry`
4. Registration can take a few minutes. Refresh the page until all three say **Registered**.

---

## Part B — During Phase 6 (preview; detailed steps will be in `deploy/azure.md`)

For reference, this is roughly what happens then:
1. In the Codespaces terminal you'll sign in to Azure with `az login --use-device-code`. The terminal shows a short code. Open https://microsoft.com/devicelogin in your browser, paste the code, and sign in. Your password never goes into Codespaces.
2. You'll run a few copy-paste commands that build the Docker image in Azure and start the app. Azure then gives you a public URL.
3. You'll take two **screenshots** for the reviewers and save them in `images/`:
   - the terminal running `test.py` against the cloud URL,
   - the `/docs` page of the cloud URL open in your browser.
4. After the course grading period ends, you'll delete everything with a single command so nothing keeps costing money.

---

## Part C — Decisions to confirm (SPEC.md §0)

Phase 1 used the defaults. Tell me if you want to change any of them before Phase 2:
- Red wine only, target `good = quality >= 7`
- Azure Container Apps for deployment (alternative: Fly.io)
- Python 3.12
