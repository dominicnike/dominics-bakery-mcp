# 🥐 Dominic's Bakery – Build a Custom MCP Server on Azure Functions and Connect it to Microsoft Foundry

This repository is a **complete, step-by-step record** of a live classroom demo. Starting from a Windows PC with nothing installed, we:

1. Installed every prerequisite
2. Signed in to Azure
3. Created Azure Blob Storage in the **Azure Portal** and uploaded bakery products
4. Ran a **Python MCP server on Azure Functions** locally
5. Tested it locally with **VS Code GitHub Copilot Chat** and the **MCP Inspector**
6. Created a **Function App** in the Azure Portal and **deployed** the code
7. Tested the **remote (Azure)** MCP server from VS Code and the MCP Inspector
8. Connected the MCP server to an **AI agent in Microsoft Foundry** and tested it in the Playground
9. Pushed the code to GitHub

Every command below is one that **was actually run successfully** during the demo, together with the output you should expect and the fixes for every error we hit.

> 🎥 Based on the video: <https://youtu.be/cDGBGHXal9M>

---

## 📚 Table of contents

- [What is MCP and what are we building?](#what-is-mcp-and-what-are-we-building)
- [Architecture](#architecture)
- [Names used in this demo](#names-used-in-this-demo)
- [Project files explained](#project-files-explained)
- [Part 0 – Install the prerequisites](#part-0--install-the-prerequisites)
- [Part 1 – Get the project and open it in VS Code](#part-1--get-the-project-and-open-it-in-vs-code)
- [Part 2 – Sign in to Azure (CLI)](#part-2--sign-in-to-azure-cli)
- [Part 3 – Create the Resource Group and Storage Account (Portal)](#part-3--create-the-resource-group-and-storage-account-portal)
- [Part 4 – Configure local.settings.json](#part-4--configure-localsettingsjson)
- [Part 5 – Create the Python virtual environment and install packages](#part-5--create-the-python-virtual-environment-and-install-packages)
- [Part 6 – Run the MCP server locally](#part-6--run-the-mcp-server-locally)
- [Part 7 – Test locally in VS Code Copilot Chat](#part-7--test-locally-in-vs-code-copilot-chat)
- [Part 8 – Test locally with the MCP Inspector](#part-8--test-locally-with-the-mcp-inspector)
- [Part 9 – Create the Function App in Azure (Portal)](#part-9--create-the-function-app-in-azure-portal)
- [Part 10 – Configure app settings](#part-10--configure-app-settings)
- [Part 11 – Deploy (publish) the code to Azure](#part-11--deploy-publish-the-code-to-azure)
- [Part 12 – Get the MCP key and prove the endpoint is protected](#part-12--get-the-mcp-key-and-prove-the-endpoint-is-protected)
- [Part 13 – Test the remote server in VS Code](#part-13--test-the-remote-server-in-vs-code)
- [Part 14 – Test the remote server in the MCP Inspector](#part-14--test-the-remote-server-in-the-mcp-inspector)
- [Part 15 – Create a Microsoft Foundry project and deploy a model](#part-15--create-a-microsoft-foundry-project-and-deploy-a-model)
- [Part 16 – Create the Foundry agent and connect the MCP server](#part-16--create-the-foundry-agent-and-connect-the-mcp-server)
- [Part 17 – Test the agent in the Foundry Playground](#part-17--test-the-agent-in-the-foundry-playground)
- [Part 18 – Push the code to GitHub](#part-18--push-the-code-to-github)
- [Part 19 – Clean up](#part-19--clean-up)
- [Troubleshooting – every error we hit and how we fixed it](#troubleshooting--every-error-we-hit-and-how-we-fixed-it)
- [Security checklist](#security-checklist)
- [References](#references)

---

## What is MCP and what are we building?

**Model Context Protocol (MCP)** is an open standard that lets AI applications (VS Code Copilot, Claude, Microsoft Foundry agents, …) discover and call **tools** on a server – like a USB-C port for AI.

**Dominic's Bakery** exposes its business as an MCP server with **4 tools**:

| Tool | What it does | Inputs |
|---|---|---|
| `hello_mcp` | Health check – returns *"Hello, I am the Dominic's Bakery MCP tool!"* | – |
| `list_products` | Reads all 10 product JSON files from the `products` blob container | – |
| `place_order` | Checks the item exists, calculates the total and saves a new order JSON into the `orders` container | `customer_name` (text), `item` (text), `quantity` (integer) |
| `list_orders` | Reads all orders from the `orders` container | – |

Because it is a standard MCP server, **the same code** works with VS Code, the MCP Inspector and Microsoft Foundry – without changes.

---

## Architecture

```
                    MCP over Streamable HTTP
┌──────────────────────┐   POST /runtime/webhooks/mcp    ┌───────────────────────────────┐        ┌──────────────────────────────┐
│ MCP clients          │ ──────────────────────────────▶ │ Azure Functions (Python 3.13) │ ─────▶ │ Azure Blob Storage           │
│ • VS Code Copilot    │   header: x-functions-key       │ Flex Consumption plan         │        │ stdominicsmcpserverdemo      │
│ • MCP Inspector      │                                 │ 4 × mcpToolTrigger functions  │        │  ├─ products/  (10 × JSON)   │
│ • Foundry agent      │ ◀────────────────────────────── │ func-dominics-bakery-demo     │ ◀───── │  └─ orders/    (new orders)  │
└──────────────────────┘          tool results           └───────────────────────────────┘        └──────────────────────────────┘
```

| Where | MCP endpoint | Key needed? |
|---|---|---|
| Local (your PC) | `http://localhost:7071/runtime/webhooks/mcp` | No |
| Azure | `https://<your-function-app-default-domain>/runtime/webhooks/mcp` | Yes – `mcp_extension` system key in header `x-functions-key` |

---

## Names used in this demo

Replace these with your own names if you rebuild it.

| Resource | Name used |
|---|---|
| Project folder | `C:\Users\<you>\dominics-bakery-mcp` |
| Resource group | `rg-dominics-bakery` |
| Region | **East US 2** (`eastus2`) |
| Storage account | `stdominicsmcpserverdemo` |
| Blob containers | `products`, `orders` |
| Function App | `func-dominics-bakery-demo` |
| Function App default domain | `func-dominics-bakery-demo-drgdeyhuc7dcczar.eastus2-01.azurewebsites.net` |
| Foundry project | `dominics-bakery-project` |
| Foundry model deployment | `gpt-5.4-mini` |
| Foundry agent | `dominics-bakery-agent` |
| Foundry MCP tool / connection | `dominics-bakery-mcp` |

---

## Project files explained

```
dominics-bakery-mcp/
├── function_app.py              # The 4 MCP tools (Python v2 programming model)
├── requirements.txt             # Python packages: azure-functions, azure-storage-blob
├── host.json                    # Functions host config + extension bundle (contains the MCP extension)
├── local.settings.sample.json   # Template – copy to local.settings.json and paste your connection string
├── products/                    # 10 product JSON files to upload to Blob Storage
├── .vscode/mcp.json             # MCP server definitions for VS Code (local + remote)
├── .funcignore                  # Files NOT uploaded to Azure when publishing
└── .gitignore                   # Keeps secrets (local.settings.json) and .venv out of GitHub
```

### `function_app.py` – how an MCP tool is written

```python
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.mcp_tool()
def hello_mcp() -> str:
    """Simple hello-world tool to confirm the MCP server is working."""
    return "Hello, I am the Dominic's Bakery MCP tool!"

@app.mcp_tool()
@app.mcp_tool_property(arg_name="customer_name", description="Name of the customer placing the order.")
@app.mcp_tool_property(arg_name="item", description="Exact product name to order, e.g. 'Snickerdoodle Cookie'.")
@app.mcp_tool_property(arg_name="quantity", description="How many of the item to order.",
                       property_type=McpPropertyType.INTEGER)
def place_order(customer_name: str, item: str, quantity: int) -> str:
    """Place a new order at Dominic's Bakery for a customer."""
    ...
```

Teaching points:

- `@app.mcp_tool()` turns an ordinary Python function into an MCP tool.
- The **docstring** becomes the tool **description** – the AI reads it to decide *when* to call the tool.
- `@app.mcp_tool_property(...)` describes each **input** so the AI knows *what* to send.
- Storage is reached with `BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])` – the same setting works locally (from `local.settings.json`) and in Azure (from the Function App settings).

### `requirements.txt`

```text
azure-functions>=2.2.0
azure-storage-blob
```

### `host.json` – extension bundle (includes the MCP extension)

```json
"extensionBundle": {
  "id": "Microsoft.Azure.Functions.ExtensionBundle",
  "version": "[4.*, 5.0.0)"
}
```

### A product file (`products/cinnamon-roll.json`)

```json
{ "id": "cinnamon-roll", "name": "Cinnamon Roll", "category": "pastry", "price": 4.0, "in_stock": true }
```

---

## Part 0 – Install the prerequisites

Open **VS Code → Terminal → New Terminal** (`Ctrl+``) – this is a **PowerShell** terminal. Run each command **one at a time**.

### 0.1 Check what is already installed

```powershell
py --list
func --version
az --version
node --version
git --version
gh --version
```

In the demo, **Azure CLI 2.91**, **Node.js v24**, **Git** and **GitHub CLI** were already installed. **Python 3.13** and **Azure Functions Core Tools** were missing (`func` was "not recognized").

### 0.2 Install Python 3.13

```powershell
winget install -e --id Python.Python.3.13
```

> ⚠️ **Use Python 3.13.** The package `azure-functions` 2.x requires Python **≥ 3.13**. We first tried 3.12 and `pip install` failed (see [Troubleshooting](#troubleshooting--every-error-we-hit-and-how-we-fixed-it)).

### 0.3 Install Azure Functions Core Tools

```powershell
winget install -e --id Microsoft.Azure.FunctionsCoreTools
```

### 0.4 (If missing) Azure CLI, Node.js, Git, GitHub CLI

```powershell
winget install -e --id Microsoft.AzureCLI
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Git.Git
winget install -e --id GitHub.cli
```

### 0.5 Reload the PATH

After `winget` installs, the open terminal still has the **old PATH** (`func : The term 'func' is not recognized…`). Either **close VS Code completely (File → Exit) and reopen it**, or reload the PATH in the current terminal:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
```

### 0.6 Verify

```powershell
py -3.13 --version     # Python 3.13.x
func --version         # 4.16.0 (any 4.x)
az --version           # azure-cli 2.x
node --version         # v18 or newer (demo: v24)
```

### 0.7 Install the VS Code extensions

```powershell
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-azurefunctions
code --install-extension GitHub.copilot-chat
```

You also need a **GitHub Copilot** subscription signed in to VS Code, and an **Azure subscription**.

---

## Part 1 – Get the project and open it in VS Code

```powershell
cd $HOME
git clone https://github.com/dominicnike/dominics-bakery-mcp.git
cd dominics-bakery-mcp
code .
```

In the **new VS Code window**, open a terminal (`Ctrl+``). All following commands run **inside the `dominics-bakery-mcp` folder**.

> 💡 Copy **only the lines inside the grey code boxes**. In the demo, part of an instruction sentence was pasted into the terminal and PowerShell tried to run it as a command – harmless, just re-run the correct line.

---

## Part 2 – Sign in to Azure (CLI)

```powershell
az login
```

A browser opens – sign in. When the subscription list appears, **type the number** of the subscription to use (or press **Enter** to keep the default).

If your subscription lives in a tenant that requires **MFA**, sign in to that tenant directly:

```powershell
az login --tenant <your-tenant-id>
# or, if the browser/MFA does not work:
az login --tenant <your-tenant-id> --use-device-code
```

Check which subscriptions you have and which one is active:

```powershell
az account list --query "[].{name:name, tenant:tenantId, default:isDefault}" -o table
az account show --query "{name:name, tenant:tenantId}" -o table
```

Switch subscription if needed:

```powershell
az account set --subscription "<subscription-name-or-id>"
```

> ℹ️ Messages like *"Authentication failed against tenant … AADSTS50076 … must use multi-factor authentication"* refer to **other** tenants you belong to. They can be ignored as long as the correct subscription is active.
>
> ℹ️ At the subscription prompt you can **only** type a number or press Enter – typing a command there gives *"Invalid selection"*. Press Enter first, then run the next command.

---

## Part 3 – Create the Resource Group and Storage Account (Portal)

We used the **Azure Portal** for this part so non-coders can follow. Go to <https://portal.azure.com> and check the correct directory/subscription in the top-right corner.

### 3.1 Resource group

1. Search **Resource groups → + Create**.
2. Subscription: *your subscription*.
3. Resource group: **`rg-dominics-bakery`** · Region: **East US 2**.
4. **Review + create → Create**.

### 3.2 Storage account

1. Search **Storage accounts → + Create**.
2. Resource group: **`rg-dominics-bakery`**.
3. Storage account name: **`stdominicsmcpserverdemo`** (lowercase letters and numbers only, must be globally unique).
4. Region: **East US 2**.
5. Primary service: **Azure Blob Storage or Azure Data Lake Storage Gen 2**.
6. Primary workload / *Compare workloads*: choose **General purpose**.
   - ❌ Not *AI Agent inferencing* – it uses Premium storage (more expensive, not supported by Functions).
   - ❌ Not *Big Data Analytics* – enables hierarchical namespace, not needed.
7. Performance: **Standard**.
8. Redundancy: change **RA-GRS** to **LRS (Locally-redundant storage)** – cheapest, fine for a demo.
9. **Review + create → Create → Go to resource**.

### 3.3 Create the blob containers

1. Storage account → **Data storage → Containers → + Container**.
2. Name **`products`** → **Create**.
3. **+ Container** again → Name **`orders`** → **Create**.

### 3.4 Upload the 10 product files

1. Open the **`products`** container → **Upload**.
2. Browse to the project's **`products`** folder (e.g. `C:\Users\<you>\dominics-bakery-mcp\products`).
3. Select **all 10** files (`Ctrl+A`):
   `banana-bread.json`, `butter-croissant.json`, `chocolate-chip-cookie.json`, `cinnamon-roll.json`, `fudgy-chocolate-brownie.json`, `oatmeal-raisin-cookie.json`, `red-velvet-cupcake.json`, `snickerdoodle-cookie.json`, `sourdough-loaf.json`, `whole-wheat-bread.json`
4. **Upload**.

> ⚠️ Upload **only** the files inside `products/` – never upload `local.settings.json` or other project files. Leave the **`orders`** container **empty**; `place_order` fills it.

### 3.5 Copy the connection string

1. Storage account → **Security + networking → Access keys**.
2. Under **key1 → Connection string**, click **Show** then **Copy**.

---

## Part 4 – Configure `local.settings.json`

Create your local settings from the template:

```powershell
Copy-Item local.settings.sample.json local.settings.json
```

Open `local.settings.json` and replace `<PASTE-YOUR-STORAGE-ACCOUNT-CONNECTION-STRING>` with the copied value (keep the quotes):

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=stdominicsmcpserverdemo;AccountKey=****;EndpointSuffix=core.windows.net"
  }
}
```

Save the file.

> 🔒 `local.settings.json` contains your storage key. It is listed in `.gitignore` so it is **never pushed to GitHub**. Never share it.

---

## Part 5 – Create the Python virtual environment and install packages

Run each line separately:

```powershell
py -3.13 -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt now starts with **`(.venv)`**.

> If you see *"running scripts is disabled on this system"*:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Answer **Y**, then run `.\.venv\Scripts\Activate.ps1` again. If asked *"Do you want to run software from this untrusted publisher?"* press **A** (Always run).

```powershell
python --version                 # Python 3.13.x
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Expected: `Successfully installed azure-functions-2.x … azure-storage-blob-12.x …`

> 💡 VS Code popups:
> - **"Select an environment manager" / "Quick Create"** – press **Esc**, or choose **Enter Interpreter Path…** and select `.venv\Scripts\python.exe`. Don't use *Quick Create* – it may create an environment with a different Python version.
> - **Pylance "enable type checking?"** – answer **No** (not needed for this demo).

---

## Part 6 – Run the MCP server locally

```powershell
func start
```

Expected output:

```
Azure Functions Core Tools
Core Tools Version:       4.16.0
Function Runtime Version: 4.1054.x

MCP server endpoint: http://localhost:7071/runtime/webhooks/mcp
MCP server legacy SSE endpoint: http://localhost:7071/runtime/webhooks/mcp/sse

Functions:
        hello_mcp: mcpToolTrigger
        list_orders: mcpToolTrigger
        list_products: mcpToolTrigger
        place_order: mcpToolTrigger

Worker process started and initialized.
Host lock lease acquired by instance ID '...'.
```

> ⚠️ If `func start` fails while **downloading the extension bundle** (a network blip), download it once and retry:
> ```powershell
> func bundles download
> func start
> ```
>
> ℹ️ Sometimes the `Functions:` list is not printed. If you see the **MCP server endpoint** line and *Host lock lease acquired*, the server is running.

**Leave this terminal running** for Parts 7 and 8.

---

## Part 7 – Test locally in VS Code Copilot Chat

### 7.1 Register the local server

The repo already contains `.vscode/mcp.json`:

```json
{
  "servers": {
    "my-mcp-local-server": {
      "url": "http://localhost:7071/runtime/webhooks/mcp",
      "type": "http"
    },
    "my-remote-mcp-server": {
      "url": "https://<your-function-app-default-domain>/runtime/webhooks/mcp",
      "type": "http",
      "headers": { "x-functions-key": "${input:functions-mcp-extension-system-key}" }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "functions-mcp-extension-system-key",
      "description": "Azure Functions mcp_extension system key",
      "password": true
    }
  ]
}
```

To add it yourself exactly like in the video: **Ctrl+Shift+P → MCP: Add Server… → HTTP** → URL `http://localhost:7071/runtime/webhooks/mcp` → name `my-mcp-local-server` → **Workspace**.

> ⚠️ Keep **one** config file: `.vscode/mcp.json`. In the demo, *Add Server* once created a second `.mcp.json` in the project root and moved entries into it – we deleted the root file and kept `.vscode/mcp.json`.

### 7.2 Start the server in VS Code

1. Open `.vscode/mcp.json`.
2. Above `"my-mcp-local-server"` click **▷ Start** → it shows **Running · 4 tools**.
   - No *Start* link? **Ctrl+Shift+P → MCP: List Servers → my-mcp-local-server → Start Server**.
   - Shows *Error*? Make sure `func start` is running, then click **Start** again. Click **Error** to open the log.

### 7.3 Chat with the tools

1. Open **Copilot Chat** (`Ctrl+Alt+I`) → start a **new chat (+)** → select **Agent** mode.
2. Choose the tools:
   - Older layout: click the 🛠 **tools icon** in the chat box and tick only `my-mcp-local-server`.
   - Newer layout (no tools icon): **Ctrl+Shift+P → Chat: Configure Tools** and tick only `my-mcp-local-server`.
   - Or type `#` in the chat box and pick a tool, e.g. `#list_products`.
3. Prompts used in the demo (click **Allow / Continue** when Copilot asks to run a tool):

```text
Say hello using the bakery MCP server.
```
```text
List the products for Dominic's Bakery.
```
```text
Create a new order for Mason for 5 Snickerdoodle Cookies.
```
```text
List the orders.
```

### 7.4 Show the proof

Azure Portal → **stdominicsmcpserverdemo → Containers → orders** → a new `<order_id>.json` file appears. The AI agent wrote real data through your tool.

> ℹ️ A message such as *"Foundry MCP … unable to sign in"* comes from the **AI Toolkit** extension's own server – unrelated to this project.

---

## Part 8 – Test locally with the MCP Inspector

With `func start` still running, open a **second terminal** (`+` in the terminal panel):

```powershell
npx @modelcontextprotocol/inspector
```

Answer **y** if npx asks to install the package. The Inspector opens in your browser (if not, open the printed `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=…` link).

1. **Add server** / connection settings:
   - Transport type: **Streamable HTTP**
   - URL: `http://localhost:7071/runtime/webhooks/mcp`
2. **Connect** → status **Connected**.
3. **Tools → List Tools** → `hello_mcp`, `list_orders`, `list_products`, `place_order`.
4. Run the tools:
   - `hello_mcp` → *Hello, I am the Dominic's Bakery MCP tool!*
   - `list_products` → JSON list of 10 products
   - `place_order` → `customer_name` = `Ada`, `item` = `Banana Bread`, `quantity` = `1` → *Order placed*
   - `list_orders` → shows Mason's and Ada's orders

Press **Ctrl+C** in the Inspector terminal when done.

---

## Part 9 – Create the Function App in Azure (Portal)

1. Portal → search **Function App → + Create**.
2. Hosting plan: **Flex Consumption** → **Select**.
3. **Basics**
   - Subscription: *your subscription*
   - Resource group: **`rg-dominics-bakery`**
   - Function App name: **`func-dominics-bakery-demo`**
   - Region: **East US 2**
   - Runtime stack: **Python** · Version: **3.13** (match your local Python)
   - Instance size: **2048 MB** (default)
4. **Storage** tab: Storage account → **`stdominicsmcpserverdemo`** (the one from Part 3).
5. **Monitoring** tab: Application Insights → **Yes** (default).
6. **Review + create → Create** (≈1–2 min) → **Go to resource**.
7. On **Overview**, copy the **Default domain**. Flex Consumption adds a random suffix, e.g.
   `func-dominics-bakery-demo-drgdeyhuc7dcczar.eastus2-01.azurewebsites.net`

> ⚠️ Always use the **exact Default domain** – `func-dominics-bakery-demo.azurewebsites.net` (without the suffix) does not work for Flex Consumption apps.

---

## Part 10 – Configure app settings

Add the recommended Python setting (back in the VS Code terminal):

```powershell
az functionapp config appsettings set -g rg-dominics-bakery -n func-dominics-bakery-demo --settings PYTHON_ISOLATE_WORKER_DEPENDENCIES=1
```

Portal alternative: **Function App → Settings → Environment variables → + Add** → Name `PYTHON_ISOLATE_WORKER_DEPENDENCIES`, Value `1` → **Apply → Apply → Confirm**.

List the settings:

```powershell
az functionapp config appsettings list -g rg-dominics-bakery -n func-dominics-bakery-demo --query "[].name" -o tsv
```

Expected (order may vary):

```
DEPLOYMENT_STORAGE_CONNECTION_STRING
APPLICATIONINSIGHTS_CONNECTION_STRING
AzureWebJobsStorage
PYTHON_ISOLATE_WORKER_DEPENDENCIES
```

> ✅ `AzureWebJobsStorage` **must** be present – our code uses it to reach the `products` and `orders` containers. The portal created it automatically because we chose our storage account in Part 9.

---

## Part 11 – Deploy (publish) the code to Azure

From the project folder, with `(.venv)` active:

```powershell
func azure functionapp publish func-dominics-bakery-demo
```

Output from the demo (shortened):

```
Getting site publishing info...
Starting the function app deployment...
Creating archive for current directory...
Performing remote build for functions project.
Uploading 2.11 KB [###########################]
Deployment in progress, please wait...
[Kudu-OryxBuildStep] completed.
[Kudu-UploadPackageStep] completed. Uploaded package to storage successfully.
Checking the app health... done
Host status: {"state":"Running", ... "extensionBundle":{"id":"Microsoft.Azure.Functions.ExtensionBundle","version":"4.41.2"}}
The deployment was successful!
Functions in func-dominics-bakery-demo:
    hello_mcp - [mcpToolTrigger]
    list_orders - [mcpToolTrigger]
    list_products - [mcpToolTrigger]
    place_order - [mcpToolTrigger]
```

> ℹ️ The warning *"Local python version '3.13.x' is different from the version expected for your deployed Function App … '3.14'"* is safe here – the remote build succeeded. Best practice: keep local and Azure Python versions identical.

Confirm in the portal: **Function App → Overview → Functions** tab lists the 4 functions.

---

## Part 12 – Get the MCP key and prove the endpoint is protected

### 12.1 Without a key → 401

```powershell
curl.exe -s -o NUL -w "%{http_code}" -X POST https://<your-function-app-default-domain>/runtime/webhooks/mcp
```

Expected: **`401`** (Unauthorized) – the server is protected. 🎓 Great moment to show students.

### 12.2 Get the `mcp_extension` system key

```powershell
az functionapp keys list -g rg-dominics-bakery -n func-dominics-bakery-demo --query systemKeys.mcp_extension -o tsv
```

Portal alternative: **Function App → Functions → App keys → System keys → `mcp_extension`** → show/copy.

> 🔒 Treat this key like a password. Don't paste it in chats, screenshots or GitHub.

---

## Part 13 – Test the remote server in VS Code

1. **Stop the local server** so you are sure the answers come from Azure:
   - Press **Ctrl+C** in the `func start` terminal.
   - In `.vscode/mcp.json` click **Stop** above `my-mcp-local-server`.
2. **Add / check the remote server** (as in the video): **Ctrl+Shift+P → MCP: Add Server… → HTTP** → paste
   `https://<your-function-app-default-domain>/runtime/webhooks/mcp` → name **`my-remote-mcp-server`** → **Workspace**.
   Then add the `headers` block so it looks like the `my-remote-mcp-server` entry in [Part 7.1](#71-register-the-local-server):
   ```json
   "headers": { "x-functions-key": "${input:functions-mcp-extension-system-key}" }
   ```
   > The video pastes the key directly (`"x-functions-key": "<mcp-extension-key>"`). That works, but then the key is saved in the file. Using `${input:…}` makes VS Code **ask for the key** in a password box instead – safer when you push to GitHub.
3. Click **▷ Start** above `my-remote-mcp-server` → paste the key in the prompt at the top → **Enter** → **Running · 4 tools**.
   - No prompt? **Ctrl+Shift+P → MCP: Reset Cached Inputs**, then **Start** again.
   - Check status: **Ctrl+Shift+P → MCP: List Servers**.
4. Copilot Chat → **new chat (+)** → **Agent** mode → **Chat: Configure Tools** → tick only `my-remote-mcp-server`.
5. Ask:

```text
#list_orders List all the orders for Dominic's Bakery.
```

You see the orders created locally (Mason, Ada) – now served by **Azure**.

---

## Part 14 – Test the remote server in the MCP Inspector

```powershell
npx @modelcontextprotocol/inspector
```

1. Transport type: **Streamable HTTP**
2. URL: `https://<your-function-app-default-domain>/runtime/webhooks/mcp`
3. 🎓 Click **Connect** first **without** a header → connection fails with **401**.
4. Open **Authentication / Headers / Custom Headers** (name depends on Inspector version) → add:
   - Header name: `x-functions-key`
   - Value: *your `mcp_extension` key*
5. **Connect** → **Tools → List Tools** → 4 tools.
6. Run `list_products`, `place_order` (e.g. `Ada`, `Banana Bread`, `1`) and `list_orders`.

---

## Part 15 – Create a Microsoft Foundry project and deploy a model

### 15.1 Create the project

1. Go to <https://ai.azure.com> and sign in with the **same account** as Azure.
2. Turn **New Foundry** **on** (toggle at the top).
3. Project picker (top-left) → **Create new project**:
   - Project name: **`dominics-bakery-project`**
   - Subscription: *your subscription*
   - Resource group: **`rg-dominics-bakery`**
   - Region: **East US 2**
4. **Create** (≈1–2 minutes). This also creates a Foundry resource (`dominics-bakery-project-resource`) in the resource group.

### 15.2 Deploy a chat model

**Models → Deploy a model** (or **Catalog**) → search **`gpt-5.4-mini`** → **Deploy** → **Global Standard** → **Deploy**.

CLI alternative (what we ran in the demo):

```powershell
az cognitiveservices account deployment create -g rg-dominics-bakery -n dominics-bakery-project-resource `
  --deployment-name gpt-5.4-mini --model-name gpt-5.4-mini --model-version 2026-03-17 `
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50
```

Expected: `Name: gpt-5.4-mini  State: Succeeded`.

> ⚠️ **Use a dedicated model – not `model-router`.** Our agent first used the default **model-router** and every request failed with *"There was an issue with your request. Please check your inputs and try again"*. Switching the agent to **gpt-5.4-mini** fixed it immediately.
>
> ⚠️ `gpt-4o-mini` could not be deployed (*ServiceModelDeprecating*). Choose a current model from the catalog.

---

## Part 16 – Create the Foundry agent and connect the MCP server

### 16.1 Create the agent

**Build → Agents → Create agent**

- Name: **`dominics-bakery-agent`**
- Model: **`gpt-5.4-mini`**
- Instructions:

```text
You are the friendly assistant for Dominic's Bakery.
Use the bakery tools to list products, place orders and list orders.
Always confirm the customer's name and the items before placing an order.
Only offer products returned by the list_products tool.
```

**Save**.

### 16.2 Add the MCP server as a tool

In the agent's **Playground** → left panel → **Tools → Add → Custom → Model Context Protocol (MCP) → Create**:

| Field | Value |
|---|---|
| Name | `dominics-bakery-mcp` |
| Remote MCP Server endpoint | `https://<your-function-app-default-domain>/runtime/webhooks/mcp` |
| Authentication | **Key-based** |
| Credential name | `x-functions-key` (lowercase, with hyphens) |
| Credential value | your `mcp_extension` key (no quotes or spaces) |

**Connect** → **Save** the agent.

The tool now also appears under **Tools** (left menu) → **Tools** tab as `dominics-bakery-mcp – Model Context Protocol (MCP)`. **Do not delete it there** – that is your working connection.

### 16.3 Remove the automatic toolbox (if present)

In the demo the portal also attached **`dominics-bakery-agent-toolbox` v1** to the agent. That toolbox did not exist anymore (404) and every chat failed with *"A user error occurred while executing a tool call."*

Fix: agent → **Playground → Tools** → on **`dominics-bakery-agent-toolbox`** open **⋯ → Remove** → keep **`dominics-bakery-mcp (https://func-dominics-bakery-…)`** → **Save**.

### 16.4 Make sure the agent uses the dedicated model

Agent → **Playground** → **Model:** select **`gpt-5.4-mini`** (not `model-router`) → **Save** (a new version is created, e.g. *Version 6*).

---

## Part 17 – Test the agent in the Foundry Playground

Click **⊕ (new chat)** in the chat pane, then send:

```text
List all Dominic's Bakery products and prices.
```

1. Foundry shows an **approval** request for `list_products` → click **Approve**. 🎓 *Human-in-the-loop*: the agent can't use a tool without your permission.
2. Expected answer:

| Product | Price |
|---|---|
| Banana Bread | $7.25 |
| Butter Croissant | $3.25 |
| Chocolate Chip Cookie | $1.75 |
| Cinnamon Roll | $4.00 |
| Fudgy Chocolate Brownie | $3.00 |
| Oatmeal Raisin Cookie | $1.50 |
| Red Velvet Cupcake | $3.50 |
| Snickerdoodle Cookie | $1.75 |
| Sourdough Loaf | $6.50 |
| Whole Wheat Bread | $5.00 |

Continue the conversation:

```text
I'm Grace, please order 2 Cinnamon Roll and 1 Banana Bread.
```
```text
Show me all the orders.
```

Approve each `place_order` / `list_orders` call.

**Proof for students:** Azure Portal → **stdominicsmcpserverdemo → Containers → orders** → Grace's new order files are there.

🎉 **The same MCP server now powers VS Code Copilot, the MCP Inspector and a Microsoft Foundry agent.**

---

## Part 18 – Push the code to GitHub

### 18.1 Sign in to GitHub CLI

```powershell
gh auth status
gh auth login          # only if not signed in
```

### 18.2 Make sure no secrets will be pushed

`.gitignore` contains:

```text
.venv/
__pycache__/
*.pyc
local.settings.json
.python_packages/
bin/
obj/
```

and `.vscode/mcp.json` uses `${input:…}` instead of a real key.

### 18.3 Commit and push

```powershell
git init -b main
git add -A
git status            # local.settings.json and .venv must NOT be listed
git commit -m "Dominic's Bakery MCP server on Azure Functions with Foundry agent guide"
gh repo create dominics-bakery-mcp --public --source . --remote origin --push
```

Result: <https://github.com/dominicnike/dominics-bakery-mcp>

Later changes:

```powershell
git add -A
git commit -m "Describe your change"
git push
```

---

## Part 19 – Clean up

After the class, delete everything to stop charges:

```powershell
az group delete -n rg-dominics-bakery --yes --no-wait
```

This removes the storage account, Function App, Application Insights, Foundry resource/project and model deployment.

---

## Troubleshooting – every error we hit and how we fixed it

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `py -3.12 --version` → *No suitable Python runtime found* | Python not installed | `winget install -e --id Python.Python.3.13` |
| 2 | `func : The term 'func' is not recognized` right after installing | Terminal still has the old PATH | Restart VS Code, or reload PATH (Part 0.5) |
| 3 | `az login` → *AADSTS50076 … must use multi-factor authentication* | Other tenants require MFA | Ignore if the right subscription is active, or `az login --tenant <id> --use-device-code` |
| 4 | Typing a command at the subscription prompt → *Invalid selection* | Prompt only accepts a number / Enter | Press Enter, then run the command |
| 5 | Terminal error after pasting instructions | Instruction text pasted together with the command | Copy only the code box lines, one at a time |
| 6 | `pip install -r requirements.txt` fails – *requires Python >=3.13* | venv was created with Python 3.12 | `deactivate` → `Remove-Item -Recurse -Force .venv` → install 3.13 → `py -3.13 -m venv .venv` → activate → install |
| 7 | `Activate.ps1 … running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| 8 | VS Code popup *Quick Create venv* | Python extension suggestion | Press Esc, or *Enter Interpreter Path…* → `.venv\Scripts\python.exe` |
| 9 | `func start` fails downloading the extension bundle | Temporary network issue | `func bundles download`, then `func start` |
| 10 | `func start` doesn't print the function list | Normal for some Core Tools runs | Server is running if you see the *MCP server endpoint* line |
| 11 | `mcp.json` shows **Error** above the server | VS Code connected before `func start` was ready | Click **Start** again; click **Error** to read the log |
| 12 | No **Start** link / entries moved to a new root `.mcp.json` | *MCP: Add Server* wrote a second config file | Keep only `.vscode/mcp.json`; use **MCP: List Servers → Start Server** |
| 13 | *Foundry MCP … unable to sign in* in VS Code | AI Toolkit extension's own server | Unrelated – ignore |
| 14 | No 🛠 tools icon in Copilot Chat | Newer Copilot Chat layout | **Ctrl+Shift+P → Chat: Configure Tools**, or type `#tool_name` |
| 15 | Copilot keeps using the local server / tool call *Failed* | Local server stopped but still selected | Stop local server, tick only `my-remote-mcp-server`, start a new chat |
| 16 | Remote endpoint returns **401** | Missing or wrong `x-functions-key` | Use the `mcp_extension` **system** key |
| 17 | `<app>.azurewebsites.net` doesn't resolve | Flex Consumption domain has a random suffix | Copy the exact **Default domain** from Overview |
| 18 | Publish warning: local Python 3.13 vs expected 3.14 | Version mismatch | Safe if the remote build succeeds; ideally match versions |
| 19 | Foundry: *"I can't access Dominic's Bakery's product list"* / *"A user error occurred while executing a tool call."* | A broken auto-created **toolbox** was attached to the agent | Remove the toolbox from the agent's Tools, keep `dominics-bakery-mcp`, Save |
| 20 | Foundry: *"There was an issue with your request. Please check your inputs and try again"* | Agent used **model-router** | Deploy `gpt-5.4-mini` and select it as the agent's model |
| 21 | `gpt-4o-mini` deployment → *ServiceModelDeprecating* | Model retired for new deployments | Use a current model, e.g. `gpt-5.4-mini` |

---

## Security checklist

- 🔒 `local.settings.json` (storage key) is **git-ignored** – never commit it.
- 🔒 `.vscode/mcp.json` uses `${input:functions-mcp-extension-system-key}` – VS Code prompts for the key; nothing secret is stored in the repo.
- 🔒 The Foundry connection stores the key securely in the project connection.
- 🔄 If a key is ever exposed: **Function App → App keys → System keys → `mcp_extension` → Renew key value**, then update VS Code, Inspector and the Foundry tool.
- 🏭 For production, use **Microsoft Entra ID (OAuth)** authentication instead of shared keys.

---

## References

- 🎥 Video: <https://youtu.be/cDGBGHXal9M>
- [Azure Functions MCP bindings](https://learn.microsoft.com/azure/azure-functions/functions-bindings-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [Use MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Microsoft Foundry – Connect agents to MCP servers](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/model-context-protocol)
- [Azure Functions Flex Consumption plan](https://learn.microsoft.com/azure/azure-functions/flex-consumption-plan)
