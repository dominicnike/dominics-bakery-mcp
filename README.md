# 🥐 Dominic's Bakery – Custom MCP Server on Azure Functions + Microsoft Foundry

A complete, beginner-friendly walkthrough of building a **custom Model Context Protocol (MCP) server** in Python with **Azure Functions**, testing it locally (VS Code Copilot Chat + MCP Inspector), deploying it to Azure, and finally connecting it to an **AI agent in Microsoft Foundry**.

> Based on the video [Build a custom MCP server with Azure Functions](https://youtu.be/cDGBGHXal9M) and adapted as a classroom demo.

---

## 📚 Table of contents

1. [What we are building](#1-what-we-are-building)
2. [Architecture](#2-architecture)
3. [Project structure](#3-project-structure)
4. [Prerequisites](#4-prerequisites)
5. [Step 1 – Get the code & create a Python environment](#step-1--get-the-code--create-a-python-environment)
6. [Step 2 – Create the Azure Storage account (Portal)](#step-2--create-the-azure-storage-account-portal)
7. [Step 3 – Configure local settings](#step-3--configure-local-settings)
8. [Step 4 – Run the MCP server locally](#step-4--run-the-mcp-server-locally)
9. [Step 5 – Test locally in VS Code Copilot Chat](#step-5--test-locally-in-vs-code-copilot-chat)
10. [Step 6 – Test locally with MCP Inspector](#step-6--test-locally-with-mcp-inspector)
11. [Step 7 – Create the Function App in Azure (Portal)](#step-7--create-the-function-app-in-azure-portal)
12. [Step 8 – Deploy the code to Azure](#step-8--deploy-the-code-to-azure)
13. [Step 9 – Get the MCP key & test the remote server](#step-9--get-the-mcp-key--test-the-remote-server)
14. [Step 10 – Connect the MCP server to a Microsoft Foundry agent](#step-10--connect-the-mcp-server-to-a-microsoft-foundry-agent)
15. [Troubleshooting (real issues we hit)](#troubleshooting-real-issues-we-hit)
16. [Clean up](#clean-up)
17. [Security notes](#security-notes)

---

## 1. What we are building

**Dominic's Bakery** wants an AI assistant that can answer questions about products and take orders. Instead of hard-coding this into one chatbot, we expose the bakery's capabilities as an **MCP server** – a standard "plug" any AI client (VS Code Copilot, MCP Inspector, Microsoft Foundry agents, …) can use.

The server exposes **4 MCP tools**:

| Tool | What it does | Inputs |
|---|---|---|
| `hello_mcp` | Health check – returns a greeting | – |
| `list_products` | Reads all product JSON files from Blob Storage | – |
| `place_order` | Validates the item and saves a new order JSON to Blob Storage | `customer_name`, `item`, `quantity` |
| `list_orders` | Reads all orders from Blob Storage | – |

---

## 2. Architecture

```
┌────────────────────┐      MCP (Streamable HTTP)       ┌──────────────────────────────┐      ┌───────────────────────────┐
│ MCP clients        │  ─────────────────────────────▶  │ Azure Functions (Python)     │ ───▶ │ Azure Blob Storage         │
│ • VS Code Copilot  │   /runtime/webhooks/mcp          │ Flex Consumption plan        │      │  • products/ (10 JSON)     │
│ • MCP Inspector    │   header: x-functions-key        │ 4 x mcpToolTrigger functions │      │  • orders/   (new orders)  │
│ • Foundry agent    │                                  └──────────────────────────────┘      └───────────────────────────┘
└────────────────────┘
```

- **Local endpoint:** `http://localhost:7071/runtime/webhooks/mcp` (no key needed)
- **Azure endpoint:** `https://<your-function-app-host>/runtime/webhooks/mcp` (requires the `mcp_extension` system key in the `x-functions-key` header)

---

## 3. Project structure

```
dominics-bakery-mcp/
├── function_app.py              # The 4 MCP tools (Python v2 programming model)
├── requirements.txt             # azure-functions, azure-storage-blob
├── host.json                    # Functions host + extension bundle (includes the MCP extension)
├── local.settings.sample.json   # Copy to local.settings.json and add your connection string
├── products/                    # 10 sample product JSON files to upload to Blob Storage
├── .vscode/mcp.json             # MCP servers for VS Code (local + remote)
├── .funcignore                  # Files NOT deployed to Azure
└── .gitignore                   # Keeps secrets (local.settings.json) and .venv out of Git
```

How a tool is defined (from `function_app.py`):

```python
@app.mcp_tool()
@app.mcp_tool_property(arg_name="customer_name", description="Name of the customer placing the order.")
@app.mcp_tool_property(arg_name="item", description="Exact product name to order, e.g. 'Snickerdoodle Cookie'.")
@app.mcp_tool_property(arg_name="quantity", description="How many of the item to order.",
                       property_type=McpPropertyType.INTEGER)
def place_order(customer_name: str, item: str, quantity: int) -> str:
    """Place a new order at Dominic's Bakery for a customer."""
```

- `@app.mcp_tool()` turns a normal Python function into an MCP tool.
- The **docstring** becomes the tool description the AI reads to decide when to use it.
- `@app.mcp_tool_property` describes each input so the AI knows what to pass.

---

## 4. Prerequisites

| Tool | Version used | Install (Windows) |
|---|---|---|
| Azure subscription | – | <https://azure.microsoft.com/free> |
| **Python** | **3.13** (`azure-functions` 2.x needs ≥ 3.13) | `winget install Python.Python.3.13` |
| Azure Functions Core Tools | 4.x | `winget install Microsoft.Azure.FunctionsCoreTools` |
| Azure CLI | 2.x | `winget install Microsoft.AzureCLI` |
| Node.js (for MCP Inspector) | 18+ | `winget install OpenJS.NodeJS.LTS` |
| VS Code + GitHub Copilot + Azure Functions extension | latest | <https://code.visualstudio.com> |
| Git | latest | `winget install Git.Git` |

> 💡 After installing with `winget`, **close and reopen** the VS Code terminal so the new `PATH` is picked up.

Verify:

```powershell
python --version      # Python 3.13.x
func --version        # 4.x
az --version
node --version
```

Sign in to Azure:

```powershell
az login
az account show --query "{name:name, id:id}" -o table   # confirm the right subscription
```

---

## Step 1 – Get the code & create a Python environment

```powershell
git clone https://github.com/dominicnike/dominics-bakery-mcp.git
cd dominics-bakery-mcp

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ If `pip install` fails with *"requires Python >=3.13"*, your venv was created with an older Python. Delete `.venv` and recreate it with `py -3.13`.

---

## Step 2 – Create the Azure Storage account (Portal)

The tools read products from and write orders to **Blob Storage**.

1. **Azure Portal → Resource groups → + Create**
   - Name: `rg-dominics-bakery` · Region: **East US 2** → **Review + create**.
2. **Storage accounts → + Create**
   - Resource group: `rg-dominics-bakery`
   - Name: e.g. `stdominicsmcpserverdemo` (must be globally unique, lowercase)
   - Region: **East US 2** · Primary service: *Azure Blob Storage* · Performance: **Standard** · Redundancy: **LRS**
   - **Review + create → Create**.
3. Open the storage account → **Data storage → Containers → + Container**
   - Create **`products`** and **`orders`** (private access).
4. Open **products → Upload** → select all 10 files in the `products/` folder → **Upload**.
5. **Security + networking → Access keys → Show** → copy **Connection string** (key1).

---

## Step 3 – Configure local settings

```powershell
Copy-Item local.settings.sample.json local.settings.json
```

Open `local.settings.json` and paste your connection string:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
  }
}
```

> 🔒 `local.settings.json` is in `.gitignore` – **never commit it**.

---

## Step 4 – Run the MCP server locally

```powershell
func start
```

Expected output:

```
MCP server endpoint: http://localhost:7071/runtime/webhooks/mcp
...
Functions:
    hello_mcp: mcpToolTrigger
    list_orders: mcpToolTrigger
    list_products: mcpToolTrigger
    place_order: mcpToolTrigger
```

> ⚠️ If `func start` fails downloading the extension bundle, run `func bundles download` and try again.
> Sometimes the function list is not printed – the server is still running if you see the *MCP server endpoint* line.

Keep this terminal running for Steps 5 and 6.

---

## Step 5 – Test locally in VS Code Copilot Chat

`.vscode/mcp.json` already contains two servers:

```json
{
  "servers": {
    "my-mcp-local-server":  { "type": "http", "url": "http://localhost:7071/runtime/webhooks/mcp" },
    "my-remote-mcp-server": {
      "type": "http",
      "url": "https://<your-function-app-host>/runtime/webhooks/mcp",
      "headers": { "x-functions-key": "${input:functions-mcp-extension-system-key}" }
    }
  },
  "inputs": [
    { "type": "promptString", "id": "functions-mcp-extension-system-key",
      "description": "Azure Functions mcp_extension system key", "password": true }
  ]
}
```

1. Open `.vscode/mcp.json` → click **Start** above `my-mcp-local-server` → it shows **Running · 4 tools**.
   *(You can also add servers yourself with **Ctrl+Shift+P → MCP: Add Server… → HTTP**.)*
2. Open **Copilot Chat** → switch to **Agent** mode.
3. Pick tools: click the 🛠 tools icon, or **Ctrl+Shift+P → Chat: Configure Tools**, and tick only `my-mcp-local-server`.
4. Try:
   ```text
   Say hello using the bakery MCP server.
   What products does Dominic's Bakery sell and how much are they?
   Place an order for 2 Cinnamon Roll for Mason.
   List all the orders.
   ```
5. Click **Allow/Continue** when Copilot asks to run a tool.
6. ✅ Proof: Azure Portal → storage account → **Containers → orders** → a new `<order_id>.json` appears.

> 💡 Tip: type `#` in the chat box to reference a specific tool, e.g. `#list_orders`.

---

## Step 6 – Test locally with MCP Inspector

With `func start` still running, open a **second** terminal:

```powershell
npx @modelcontextprotocol/inspector
```

1. The Inspector opens in the browser (use the printed URL with the token if it doesn't).
2. **Transport type:** `Streamable HTTP`
3. **URL:** `http://localhost:7071/runtime/webhooks/mcp`
4. **Connect → Tools → List Tools** → you see the 4 tools.
5. Run `hello_mcp`, `list_products`, then `place_order` (e.g. `customer_name=Ada`, `item=Banana Bread`, `quantity=1`) and `list_orders`.

---

## Step 7 – Create the Function App in Azure (Portal)

1. **Azure Portal → Function App → + Create → Flex Consumption**.
2. **Basics**
   - Resource group: `rg-dominics-bakery`
   - Function App name: e.g. `func-dominics-bakery-demo`
   - Region: **East US 2**
   - Runtime stack: **Python** · Version: **3.13**
   - Instance size: 2048 MB (default)
3. **Storage:** choose the storage account from Step 2 (`stdominicsmcpserverdemo`).
4. **Monitoring:** Application Insights **On** (default).
5. **Review + create → Create**, then **Go to resource**.

Add the recommended Python setting:

```powershell
az functionapp config appsettings set -g rg-dominics-bakery -n func-dominics-bakery-demo --settings PYTHON_ISOLATE_WORKER_DEPENDENCIES=1
```

Verify settings (`AzureWebJobsStorage` must be present – our code uses it to reach Blob Storage):

```powershell
az functionapp config appsettings list -g rg-dominics-bakery -n func-dominics-bakery-demo --query "[].name" -o tsv
```

> 📝 Flex Consumption apps get a host name with a **random suffix**, e.g.
> `func-dominics-bakery-demo-xxxxxxxx.eastus2-01.azurewebsites.net`. Copy the exact **Default domain** from the Function App **Overview** page.

---

## Step 8 – Deploy the code to Azure

From the project folder (venv active):

```powershell
func azure functionapp publish func-dominics-bakery-demo
```

Successful output ends with:

```
The deployment was successful!
Functions in func-dominics-bakery-demo:
    hello_mcp - [mcpToolTrigger]
    list_orders - [mcpToolTrigger]
    list_products - [mcpToolTrigger]
    place_order - [mcpToolTrigger]
```

> ⚠️ A warning like *"Local python version '3.13' is different from the version expected '3.14'"* is safe to ignore as long as the remote build succeeds – but ideally keep local and Azure Python versions the same.

Confirm in the portal: **Function App → Overview → Functions** tab shows the 4 functions.

---

## Step 9 – Get the MCP key & test the remote server

The remote MCP endpoint is protected by a **system key** called `mcp_extension`.

**9a. Prove it is protected (expect `401`):**

```powershell
curl.exe -s -o NUL -w "%{http_code}" -X POST https://<your-function-app-host>/runtime/webhooks/mcp
```

**9b. Get the key** (keep it secret!):

```powershell
az functionapp keys list -g rg-dominics-bakery -n func-dominics-bakery-demo --query systemKeys.mcp_extension -o tsv
```

Portal alternative: **Function App → Functions → App keys → System keys → `mcp_extension`**.

**9c. Test in VS Code**

1. Stop the local server (**Ctrl+C** in the `func start` terminal) and click **Stop** above `my-mcp-local-server`.
2. Put your real host name in the `url` of `my-remote-mcp-server` in `.vscode/mcp.json`.
3. Click **Start** above `my-remote-mcp-server` → paste the key in the password prompt → **Running · 4 tools**.
4. In Copilot Chat (Agent mode, only `my-remote-mcp-server` tools ticked) ask: `List all the orders for Dominic's Bakery.`

> If the key prompt doesn't appear: **Ctrl+Shift+P → MCP: Reset Cached Inputs**, then Start again.

**9d. Test in MCP Inspector**

```powershell
npx @modelcontextprotocol/inspector
```

- Transport: **Streamable HTTP**
- URL: `https://<your-function-app-host>/runtime/webhooks/mcp`
- **Authentication / Custom headers:** add header `x-functions-key` = *your mcp_extension key*
- **Connect → List Tools →** run the tools.

> 🎓 Classroom tip: connect once **without** the header to show the `401 Unauthorized`, then add the key.

---

## Step 10 – Connect the MCP server to a Microsoft Foundry agent

**10a. Open/create a Foundry project**

1. Go to <https://ai.azure.com> and sign in with the same account. Turn **New Foundry** on (top right).
2. Project picker (top left) → **Create new project**
   - Name: `dominics-bakery-project` · Resource group: `rg-dominics-bakery` · Region: **East US 2** → **Create**.

**10b. Deploy a chat model**

- **Models → Deploy a model →** search a current model, e.g. **`gpt-5.4-mini`** → **Deploy** (Global Standard).

> ⚠️ **Use a fixed model, not `model-router`.** In our demo, `model-router` caused
> *"There was an issue with your request. Please check your inputs and try again"* when the agent used MCP tools.
> Switching the agent to a dedicated model (`gpt-5.4-mini`) fixed it immediately.

CLI alternative:

```powershell
az cognitiveservices account deployment create -g rg-dominics-bakery -n <foundry-resource-name> `
  --deployment-name gpt-5.4-mini --model-name gpt-5.4-mini --model-version 2026-03-17 `
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50
```

**10c. Create the agent**

**Build → Agents → Create agent**

- Name: `dominics-bakery-agent`
- Model: `gpt-5.4-mini`
- Instructions:
  ```text
  You are the friendly assistant for Dominic's Bakery.
  Use the bakery tools to list products, place orders and list orders.
  Always confirm the customer's name and the items before placing an order.
  Only offer products returned by the list_products tool.
  ```

**10d. Add the MCP server as a tool**

In the agent: **Tools → Add → Custom → Model Context Protocol (MCP) → Create**

| Field | Value |
|---|---|
| Name | `dominics-bakery-mcp` |
| Remote MCP Server endpoint | `https://<your-function-app-host>/runtime/webhooks/mcp` |
| Authentication | **Key-based** |
| Credential name | `x-functions-key` |
| Credential value | your `mcp_extension` key |

→ **Connect** → **Save** the agent.

> ⚠️ If the portal also adds an automatic **"…-toolbox"** entry under Tools, **remove it from the agent** and keep only `dominics-bakery-mcp`. In our demo the auto toolbox did not exist anymore (404) and caused
> *"A user error occurred while executing a tool call."*
> Do **not** delete `dominics-bakery-mcp` on the **Tools** page – that is your working connection.

**10e. Test in the Playground**

Start a **new chat** (⊕) and try:

```text
List all Dominic's Bakery products and prices.
I'm Grace, please order 2 Cinnamon Roll and 1 Banana Bread.
Show me all the orders.
```

- When Foundry shows **Approve** for a tool call, click **Approve** – a great moment to teach *human-in-the-loop* control.
- ✅ Proof: Azure Portal → storage account → **Containers → orders** → Grace's new order files.

🎉 **Done!** The same MCP server now powers VS Code Copilot, MCP Inspector **and** a Microsoft Foundry agent.

---

## Troubleshooting (real issues we hit)

| Symptom | Cause | Fix |
|---|---|---|
| `pip install` → *requires Python >=3.13* | `azure-functions` 2.x needs Python 3.13+ | Recreate `.venv` with `py -3.13 -m venv .venv` |
| `func` / `python` not recognized after install | Terminal has old `PATH` | Close and reopen the terminal / VS Code |
| `func start` fails to download extension bundle | Temporary network issue | `func bundles download`, then `func start` |
| VS Code created a second `.mcp.json` in the project root | **MCP: Add Server** chose a different config location | Keep only `.vscode/mcp.json`; delete the root `.mcp.json` |
| No 🛠 tools icon in Copilot Chat | Newer Copilot Chat layout | **Ctrl+Shift+P → Chat: Configure Tools**, or type `#tool_name` |
| Copilot keeps using the local server | Both servers enabled | Stop `my-mcp-local-server`, untick its tools, start a new chat |
| *"Foundry MCP … unable to sign in"* in VS Code | AI Toolkit extension's own Foundry server | Unrelated to this project – ignore or sign in to the extension |
| Remote endpoint returns **401** | Missing/wrong `x-functions-key` header | Use the `mcp_extension` **system** key |
| `<app>.azurewebsites.net` doesn't resolve | Flex Consumption uses a host name with a random suffix | Copy the exact **Default domain** from the Overview page |
| Foundry: *"A user error occurred while executing a tool call."* | Broken auto-created toolbox attached to the agent | Remove the toolbox from the agent's Tools, keep the MCP tool, Save |
| Foundry: *"There was an issue with your request…"* | Agent uses `model-router` | Deploy a model (e.g. `gpt-5.4-mini`) and select it in the agent |
| Foundry: `gpt-4o-mini` deployment fails *ServiceModelDeprecating* | Old model retired for new deployments | Pick a current model (e.g. `gpt-5.4-mini`) |

---

## Clean up

To avoid charges after the class, delete everything in one go:

```powershell
az group delete -n rg-dominics-bakery --yes --no-wait
```

---

## Security notes

- 🔒 **Never commit** `local.settings.json` or any key. Both are excluded by `.gitignore`.
- `.vscode/mcp.json` uses `${input:...}` so VS Code **prompts** for the key instead of storing it in the file.
- If a key is ever exposed, rotate it: **Function App → App keys → System keys → `mcp_extension` → Renew key value**, then update VS Code, Inspector and the Foundry connection.
- For production, consider **Microsoft Entra ID (OAuth) authentication** on the Function App instead of shared keys.

---

## 📖 References

- Video: <https://youtu.be/cDGBGHXal9M>
- [Azure Functions MCP bindings](https://learn.microsoft.com/azure/azure-functions/functions-bindings-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Microsoft Foundry – Connect to MCP servers](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/model-context-protocol)
