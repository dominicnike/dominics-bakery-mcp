# 🎬 Dominic's Bakery MCP – Live Demo Runbook

A step-by-step script for the class demo. Each step tells you:

- 💡 **What this step does**: a one-line, plain-English explanation
- 🎬 **DO**: what to click or type
- 📍 **GO TO**: where to look
- ✅ **CONFIRM**: what you must see before moving on
- ❌ **IF NOT**: the fix

> **Rule for the demo:** don't move to the next step until the ✅ CONFIRM box is true.
> Copy **only** the lines inside the grey code boxes, and run them **one at a time** in the **VS Code terminal (PowerShell)**.

Total time: **about 60–75 minutes**.

---

## 🧁 The big picture (read this to the class first)

**Dominic's Bakery is a pretend business.** We're building an **AI receptionist** that can read the bakery's menu and take orders by safely using the bakery's computer system.

| Real bakery | In our project |
|---|---|
| 📋 Menu with prices | 10 product files (`products\*.json`) stored in Azure Storage |
| 📒 Order book | The `orders` folder in Azure Storage |
| 👩‍🍳 Kitchen rules ("look up the price, write the order") | `function_app.py`, plain Python code that is **not** AI |
| 🙋 Receptionist who talks to customers | The **AI**: GitHub Copilot or the Foundry agent |
| 🔑 Lock on the back door | The key (`x-functions-key`) |

**Key words:**
- **MCP (Model Context Protocol):** a standard "plug" that lets any AI app use any set of tools, like USB for AI.
- **MCP server:** our program that offers the tools (`list_products`, `place_order`, `list_orders` and `hello_mcp`).
- **Tool:** one action the AI is allowed to do.
- **Azure Functions:** runs our code in the cloud without us managing a server.
- **Microsoft Foundry:** where we build the AI agent.

**The journey:**
1. 🖥️ Build and test on our PC (Steps 1–11).
2. ☁️ Move it to Azure (Steps 12–17).
3. 🤖 Connect an AI agent in Foundry (Steps 18–22).
4. 🧹 Clean up (Step 23).

---

## 📝 Before class (5 minutes, not in front of students)

Write these names on a sticky note. You'll type them many times.

| What | Name to use |
|---|---|
| Resource group | `rg-dominics-bakery` |
| Region | `East US 2` |
| Storage account | `stdominicsmcpserverdemo` (if taken, add digits, e.g. `stdominicsmcp2011`) |
| Function App | `func-dominics-bakery-demo` (if taken, add digits) |
| Foundry project | `dominics-bakery-project` |
| Model | `gpt-5.4-mini` |
| Agent | `dominics-bakery-agent` |
| MCP tool in Foundry | `dominics-bakery-mcp` |

> ⚠️ If you change a name, use **your** name everywhere the runbook shows the default.

---

## STEP 1: Check the tools on your PC (video: prerequisites)

> 💡 **What this step does:** We check that the 4 programs we need are installed: **Python** (the language our code is written in), **Func Core Tools** (runs Azure Functions on your PC), **Azure CLI** (lets us control Azure by typing commands) and **Node.js** (needed for the MCP Inspector test tool).

🎬 **DO:** open **VS Code**, then **Terminal → New Terminal**, and run:

```powershell
py -3.13 --version
```
```powershell
func --version
```
```powershell
az --version
```
```powershell
node --version
```

✅ **CONFIRM:**

| Command | Must show |
|---|---|
| `py -3.13 --version` | `Python 3.13.x` |
| `func --version` | `4.x` (e.g. `4.16.0`) |
| `az --version` | `azure-cli 2.x` |
| `node --version` | `v18` or higher |

❌ **IF NOT:** install only what is missing. Run each command in a terminal, and accept any **Yes / license** prompts.

| Missing tool | Install command |
|---|---|
| Python 3.13 | `winget install -e --id Python.Python.3.13` |
| Azure Functions Core Tools v4 | `winget install -e --id Microsoft.Azure.FunctionsCoreTools` |
| Azure CLI | `winget install -e --id Microsoft.AzureCLI` |
| Node.js (LTS) | `winget install -e --id OpenJS.NodeJS.LTS` |
| Git (needed to download the project in Step 2) | `winget install -e --id Git.Git` |
| VS Code (if not installed) | `winget install -e --id Microsoft.VisualStudioCode` |

Or install everything in one go (already-installed tools are simply skipped):

```powershell
winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
winget install -e --id Microsoft.Azure.FunctionsCoreTools --accept-package-agreements --accept-source-agreements
winget install -e --id Microsoft.AzureCLI --accept-package-agreements --accept-source-agreements
winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
```

Then add the VS Code extensions the demo uses (Python, Azure Functions, GitHub Copilot Chat):

```powershell
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-azurefunctions
code --install-extension GitHub.copilot-chat
```

Then **close VS Code completely (File → Exit)**, reopen it, and run Step 1 again. The new tools only appear in a fresh terminal.

> 🛟 **If `winget` is not recognised:** install **App Installer** from the Microsoft Store, or download the tools manually:
> [Python 3.13](https://www.python.org/downloads/) (tick **Add python.exe to PATH**) ·
> [Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools) ·
> [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-windows) ·
> [Node.js LTS](https://nodejs.org/) ·
> [Git](https://git-scm.com/download/win)

👉 All ✅? **Go to Step 2.**

---

## STEP 2: Open the project

> 💡 **What this step does:** We open the bakery project in VS Code. This folder holds all the code (`function_app.py`), the menu files (`products`) and the settings.

🎬 **DO:**

**Students (first time only):** download the project from GitHub into your user folder:

```powershell
cd $HOME
git clone https://github.com/dominicnike/dominics-bakery-mcp.git
```

Then everyone runs:

```powershell
cd "$HOME\dominics-bakery-mcp"
```
```powershell
code .
```

📍 **GO TO:** the **new VS Code window** that opens, then **Terminal → New Terminal**.

✅ **CONFIRM:** the Explorer (left) shows `function_app.py`, `host.json`, `requirements.txt`, the `products` folder and `.vscode\mcp.json`. The terminal path ends in `\dominics-bakery-mcp>`.

🎓 **SHOW STUDENTS:** open `function_app.py`, then point at `@app.mcp_tool()` and the docstrings. *"The docstring is what the AI reads to decide when to use the tool."*

👉 **Go to Step 3.**

---

## STEP 3: Sign in to Azure

> 💡 **What this step does:** We sign in to our Azure account from the terminal, so the commands we type later are allowed to create and manage things in **our** subscription.

🎬 **DO:**

```powershell
az login
```

A browser opens, so sign in. Back in the terminal, **type the number** of your subscription and press **Enter**.

Then run:

```powershell
az account show --query "{name:name, tenant:tenantId}" -o table
```

✅ **CONFIRM:** it shows your **Visual Studio Enterprise Subscription** in the **Netlinks** tenant (`51abf51d-…`).

❌ **IF NOT:**

```powershell
az login --tenant 51abf51d-04ca-4e54-9418-fe1979e43fbb --use-device-code
```

- Ignore red *AADSTS50076 … multi-factor* messages about **other** tenants.
- At the subscription prompt you can only type a **number** or press **Enter**.

👉 **Go to Step 4.**

---

## STEP 4: Create the resource group (Portal)

> 💡 **What this step does:** A **resource group** is like a labelled box in Azure. Everything we create today goes inside it, so after class we can delete the whole box in one go.

🎬 **DO:**

1. Open <https://portal.azure.com>.
2. Search **Resource groups**, then click **+ Create**.
3. Fill in:
   - Subscription: **Visual Studio Enterprise Subscription**
   - Resource group: **`rg-dominics-bakery`**
   - Region: **East US 2**
4. Click **Review + create**, then **Create**.

✅ **CONFIRM:** the notification (bell icon) says *Resource group created*, and **Resource groups** lists `rg-dominics-bakery`.

👉 **Go to Step 5.**

---

## STEP 5: Create the storage account (Portal)

> 💡 **What this step does:** A **storage account** is our bakery's online filing cabinet in Azure. It holds the menu (products) and the order book (orders).

🎬 **DO:**

1. Search **Storage accounts**, then click **+ Create**.
2. Fill in:
   - Resource group: **`rg-dominics-bakery`**
   - Storage account name: **`stdominicsmcpserverdemo`**
   - Region: **East US 2**
   - Primary service: **Azure Blob Storage or Azure Data Lake Storage Gen 2**
   - Workload (*Compare workloads*): **General purpose**
   - Performance: **Standard**
   - Redundancy: **LRS (Locally-redundant storage)**
3. Click **Review + create**, then **Create**. Wait about a minute, then click **Go to resource**.

✅ **CONFIRM:** the storage account **Overview** page opens.

❌ **IF NOT:** if *"name already taken"* appears, add digits to the name (e.g. `stdominicsmcp2011`). Don't choose *AI Agent inferencing*; it uses Premium storage, which Functions doesn't support.

👉 **Go to Step 6.**

---

## STEP 6: Create containers and upload products (Portal)

> 💡 **What this step does:** **Containers** are folders inside the filing cabinet. `products` is the menu, where we upload the 10 product files. `orders` is the empty order book that the AI will fill in.

🎬 **DO:**

1. In the storage account, go to **Data storage → Containers → + Container**. Enter the name **`products`** and click **Create**.
2. Click **+ Container** again. Enter the name **`orders`** and click **Create**.
3. Open **`products`** and click **Upload → Browse for files**.
4. Go to `C:\Users\The Iortyer\dominics-bakery-mcp\products`, press **Ctrl+A** to select all **10** files, then click **Open** and **Upload**.

✅ **CONFIRM:** the `products` container shows **10 JSON files** (banana-bread … whole-wheat-bread), and `orders` is **empty**.

🎓 **SHOW STUDENTS:** open `cinnamon-roll.json` and click **Edit**. *"This is our product database."*

👉 **Go to Step 7.**

---

## STEP 7: Connect the code to storage

> 💡 **What this step does:** The **connection string** is the address and password of the filing cabinet. We paste it into `local.settings.json` so our code on the PC knows where the menu and order book are.

🎬 **DO:**

1. In the storage account, go to **Security + networking → Access keys**.
2. Under **key1 → Connection string**, click **Show** and then **Copy**.
3. In VS Code, open **`local.settings.json`**.
   - If it doesn't exist, run `Copy-Item local.settings.sample.json local.settings.json` first.
4. Replace the value of `"AzureWebJobsStorage"` with the copied string, keeping the quotes.
   - ⚠️ The file still holds the **old** string from last time. Replace it, because the old storage account is deleted.
5. Save with **Ctrl+S**.

✅ **CONFIRM:** the file looks like this:

```json
"AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=stdominicsmcpserverdemo;AccountKey=....;EndpointSuffix=core.windows.net"
```

🔒 **TELL STUDENTS:** *"Never share this. `.gitignore` keeps this file off GitHub."* Don't show the AccountKey on the projector.

👉 **Go to Step 8.**

---

## STEP 8: Create the Python environment and install packages

> 💡 **What this step does:** A **virtual environment** (`.venv`) is a private toolbox just for this project. `pip install` puts the libraries our code needs (Azure Functions and Azure Storage) into that toolbox.

🎬 **DO** (one line at a time):

```powershell
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
```
```powershell
py -3.13 -m venv .venv
```
```powershell
.\.venv\Scripts\Activate.ps1
```
```powershell
pip install -r requirements.txt
```

✅ **CONFIRM:**
- The prompt starts with **`(.venv)`**.
- pip ends with `Successfully installed … azure-functions-2.x … azure-storage-blob-12.x …`.

❌ **IF NOT:**
- If you see *"running scripts is disabled"*, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer **Y**, then re-run the Activate line.
- If you see *"untrusted publisher"*, press **A**.
- If a VS Code popup asks to *Quick Create* an environment, press **Esc**.

👉 **Go to Step 9.**

---

## STEP 9: Run the MCP server locally

> 💡 **What this step does:** `func start` switches our bakery **MCP server** on, on our own PC. It now offers 4 tools (hello, list products, place order and list orders) at a local web address that AI apps can call.

🎬 **DO:**

```powershell
func start
```

✅ **CONFIRM** that the terminal shows:

```
MCP server endpoint: http://localhost:7071/runtime/webhooks/mcp
Functions:
        hello_mcp: mcpToolTrigger
        list_orders: mcpToolTrigger
        list_products: mcpToolTrigger
        place_order: mcpToolTrigger
```

The function list sometimes doesn't print. Seeing the **MCP server endpoint** line plus *Host lock lease acquired* is enough.

❌ **IF NOT:** if the extension bundle download fails, press **Ctrl+C**, then run:

```powershell
func bundles download
```
```powershell
func start
```

⚠️ **Leave this terminal running** for Steps 10 and 11.

### 🩺 Health check: prove the server works (show students)

> 💡 **What this does:** we talk to the MCP server **directly**, with no AI in between. If these work, the server is healthy, and any later problem is in VS Code or the AI, not our code.

🎬 **DO:** open a **second** terminal (**Terminal → New Terminal**; leave `func start` running) and paste these one at a time.

**Check 1: is the server alive?** (must print `200`)

```powershell
$u = "http://localhost:7071/runtime/webhooks/mcp"; $h = @{Accept="application/json, text/event-stream"}
(Invoke-WebRequest -UseBasicParsing $u -Method Post -ContentType "application/json" -Headers $h -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}').StatusCode
```

**Check 2: what tools does it offer?** (must list 4 tools)

```powershell
$r = Invoke-WebRequest -UseBasicParsing $u -Method Post -ContentType "application/json" -Headers $h -Body '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
(($r.Content -split "data: ")[1] | ConvertFrom-Json).result.tools | Format-Table name, description -Wrap
```

**Check 3: call a tool and get real data** (must show the 10 products from Blob Storage)

```powershell
$r = Invoke-WebRequest -UseBasicParsing $u -Method Post -ContentType "application/json" -Headers $h -Body '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_products","arguments":{}}}'
(($r.Content -split "data: ")[1] | ConvertFrom-Json).result.content[0].text | ConvertFrom-Json | Format-Table name, category, price
```

✅ **CONFIRM:** `200`, then `hello_mcp`, `list_orders`, `list_products` and `place_order`, then a table of 10 products with prices.

🎓 **SHOW STUDENTS:** *"This is exactly what Copilot and Foundry send behind the scenes: `tools/list` to discover the tools, then `tools/call` to use one. The AI just picks which tool to call."* Also point at the `func start` terminal: a new log line appears for each call.

❌ **IF NOT:**

| You see | Meaning | Fix |
|---|---|---|
| *"Unable to connect to the remote server"* | `func start` is not running | Go back to the first terminal and run `func start` |
| Check 3 returns an error about storage | Wrong or old connection string | Redo **Step 7** and restart `func start` |
| Check 3 shows an empty list | No product files in the container | Redo **Step 6** (upload the `products` files) |

👉 **Go to Step 10.**

---

## STEP 10: Test locally in VS Code Copilot Chat

> 💡 **What this step does:** We let **GitHub Copilot** (an AI) use our tools. `mcp.json` tells VS Code where our server is. When we chat, Copilot decides which tool to call. It's the AI receptionist using our bakery system.

🎬 **DO (part A: add the local server to `mcp.json`, as in the video):**

> If `.vscode\mcp.json` already lists `my-mcp-local-server`, you can skip part A. To show students how it's built, delete the file first and do part A live.

1. Press **Ctrl+Shift+P**, type **MCP: Add Server**, and press **Enter**.
   - Or open `.vscode\mcp.json` and click the blue **Add Server…** button at the bottom right.
2. Choose **HTTP (HTTP or Server-Sent Events)**.
3. In the URL box at the top, type the address and press **Enter**:

   ```text
   http://localhost:7071/runtime/webhooks/mcp
   ```
4. In the **Server ID** box, type the name and press **Enter**:

   ```text
   my-mcp-local-server
   ```
5. If asked where to save it, choose **Workspace** (it saves to `.vscode\mcp.json` in this project).

✅ **CONFIRM:** `.vscode\mcp.json` opens and contains:

```json
{
	"servers": {
		"my-mcp-local-server": {
			"url": "http://localhost:7071/runtime/webhooks/mcp",
			"type": "http"
		}
	}
}
```

🎓 **SHOW STUDENTS:** *"`7071` is the port `func start` printed in Step 9. This file tells VS Code where our MCP server lives."*

🎬 **DO (part B: start it and chat):**

1. Make sure `func start` from Step 9 is **still running** in the terminal.
2. Above **`"my-mcp-local-server"`**, click **▷ Start**.
   - If there's no Start link, press **Ctrl+Shift+P**, run **MCP: List Servers**, pick `my-mcp-local-server`, then **Start Server**.
3. Open **Copilot Chat** (**Ctrl+Alt+I**), click **+** (new chat), and choose **Agent** mode.
4. Press **Ctrl+Shift+P**, run **Chat: Configure Tools**, and tick **only `my-mcp-local-server`**.
5. Send each prompt and click **Allow** when asked:

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

✅ **CONFIRM:**
- `mcp.json` shows **Running · 4 tools**.
- The chat lists the 10 products, creates Mason's order and lists it.

📍 **GO TO** the Portal: **stdominicsmcpserverdemo → Containers → orders**.

✅ **CONFIRM:** one new order file is there. 🎓 *"The AI just wrote real data through our tool."*

❌ **IF NOT:**
- **"Error" above the server (most common).** VS Code tried to connect **before** `func start` was ready, and the old error stays on screen. Fix:
  1. Check that the terminal running `func start` shows **"Worker process started and initialized."**
  2. Check that the server answers. In a **second** terminal, run the command below. It must print `200`:

     ```powershell
     (Invoke-WebRequest -UseBasicParsing http://localhost:7071/runtime/webhooks/mcp -Method Post -ContentType "application/json" -Headers @{Accept="application/json, text/event-stream"} -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}').StatusCode
     ```
  3. Press **Ctrl+Shift+P**, run **MCP: List Servers**, pick `my-mcp-local-server`, then **Restart Server**. (If it still fails, click **Error → Show Output** to read the log.)
- **Don't add the same local URL twice** under different names. One local entry is enough; duplicates give Copilot duplicate tools.
- **Golden rule:** start `func start` **first**, wait for "Worker process started", **then** click Start in `mcp.json`.
- Ignore *"Foundry MCP … sign in"*. It comes from another extension.

👉 **Go to Step 11.**

---

## STEP 11: Test locally with the MCP Inspector

> 💡 **What this step does:** The **MCP Inspector** is a testing tool **without AI**. We click the tools ourselves to prove they work on their own, like testing the kitchen without the waiter.

🎬 **DO:** open a **second terminal** with the **+** in the terminal panel. Keep `func start` running in the first one. Then run:

```powershell
npx @modelcontextprotocol/inspector
```

Type **y** if asked. A browser tab opens.

In the Inspector:
1. Transport Type: **Streamable HTTP**
2. URL: `http://localhost:7071/runtime/webhooks/mcp`
3. Click **Connect**.
4. Click **Tools → List Tools**.
5. Click **`place_order`** and enter `customer_name` = `Ada`, `item` = `Banana Bread`, `quantity` = `1`. Click **Run Tool**.
6. Click **`list_orders`**, then **Run Tool**.

✅ **CONFIRM:**
- The status shows **Connected**, and the 4 tools are listed.
- `list_orders` shows **Mason** and **Ada**.

🎬 **DO:** to finish the local part, press **Ctrl+C** in **both** terminals. The Inspector and `func start` stop.

👉 **Local part done. Go to Step 12.**

---

## STEP 12: Create the Function App (Portal)

> 💡 **What this step does:** So far the server only runs on our PC and stops when the PC is off. A **Function App** is a home for our code in the Azure cloud, so it runs 24/7 and anyone with the key can reach it.

🎬 **DO:**

1. In the Portal, search **Function App** and click **+ Create**.
2. Select **Flex Consumption**.
3. **Basics** tab:
   - Resource group: **`rg-dominics-bakery`**
   - Function App name: **`func-dominics-bakery-demo`**
   - Region: **East US 2**
   - Runtime stack: **Python**
   - Version: **3.13**
4. **Storage** tab: choose **`stdominicsmcpserverdemo`**.
5. **Monitoring** tab: set Application Insights to **Yes**.
6. Click **Review + create**, then **Create**. Wait 1–2 minutes, then click **Go to resource**.

📍 **GO TO:** the Function App **Overview** page and find **Default domain**.

✅ **CONFIRM:** the **Default domain** looks like `func-dominics-bakery-demo-xxxxxxxx.eastus2-01.azurewebsites.net`.

📝 **Copy it into Notepad.** The random part is new every time, so you need it for Steps 15, 16, 17 and 20.

👉 **Go to Step 13.**

---

## STEP 13: Check the app settings

> 💡 **What this step does:** **App settings** are the cloud version of `local.settings.json`. We check that the Function App knows the address of our filing cabinet (`AzureWebJobsStorage`).

🎬 **DO** in the VS Code terminal:

```powershell
az functionapp config appsettings list -g rg-dominics-bakery -n func-dominics-bakery-demo --query "[].name" -o tsv
```

✅ **CONFIRM** that the output includes:

```
DEPLOYMENT_STORAGE_CONNECTION_STRING
APPLICATIONINSIGHTS_CONNECTION_STRING
AzureWebJobsStorage
```

`AzureWebJobsStorage` **must** be there, because the code uses it to read products and save orders.

👉 **Go to Step 14.**

---

## STEP 14: Deploy the code to Azure

> 💡 **What this step does:** **Publish** copies our code from the PC up into the Function App. After this, the bakery MCP server is live on the internet.

🎬 **DO:** check that **`(.venv)`** shows in the prompt, then run:

```powershell
func azure functionapp publish func-dominics-bakery-demo
```

This takes about 2 minutes.

✅ **CONFIRM** that it ends with:

```
The deployment was successful!
Functions in func-dominics-bakery-demo:
    hello_mcp - [mcpToolTrigger]
    list_orders - [mcpToolTrigger]
    list_products - [mcpToolTrigger]
    place_order - [mcpToolTrigger]
```

📍 **GO TO:** Portal → Function App → **Overview → Functions** tab. ✅ It lists 4 functions.

ℹ️ The warning *"Local python version '3.13' is different … '3.14'"* is **safe to ignore**.

👉 **Go to Step 15.**

---

## STEP 15: Prove the server is protected and get the key

> 💡 **What this step does:** First we prove the cloud server is **locked** (401 means "not allowed"). Then we get the **key**, the password that AI apps must send to use our tools.

🎬 **DO:** run the command below, replacing `<DEFAULT-DOMAIN>` with your domain from Step 12:

```powershell
curl.exe -s -o NUL -w "%{http_code}" -X POST https://<DEFAULT-DOMAIN>/runtime/webhooks/mcp
```

✅ **CONFIRM:** it prints **`401`**. 🎓 *"Nobody can use our tools without the key."*

🎬 **DO:** get the key:

```powershell
az functionapp keys list -g rg-dominics-bakery -n func-dominics-bakery-demo --query systemKeys.mcp_extension -o tsv
```

✅ **CONFIRM:** a long key is printed. 📝 Copy it into Notepad.

🔒 Don't show the key on the projector for long, and never commit it.

👉 **Go to Step 16.**

---

## STEP 16: Test the remote server in VS Code

> 💡 **What this step does:** This is the same test as Step 10, but now VS Code talks to the **cloud** server (with the key) instead of our PC. It proves the deployment works.

🎬 **DO:**

1. Open **`.vscode\mcp.json`** and click **Stop** above `my-mcp-local-server`.
2. **Add the remote server** (skip if `my-remote-mcp-server` is already in the file):
   - Click **Add Server…** (or **Ctrl+Shift+P → MCP: Add Server**) and choose **HTTP**.
   - URL: `https://<your-default-domain>/runtime/webhooks/mcp`
   - Server ID: `my-remote-mcp-server`, then choose **Workspace**.
   - Then add the key header and the `inputs` section **by hand** so the file looks like this (everything after `"type": "http"` is new):

   ```json
   "my-remote-mcp-server": {
       "url": "https://<your-default-domain>/runtime/webhooks/mcp",
       "type": "http",
       "headers": {
           "x-functions-key": "${input:functions-mcp-extension-system-key}"
       }
   }
   ```
   ```json
   "inputs": [
       {
           "type": "promptString",
           "id": "functions-mcp-extension-system-key",
           "description": "Azure Functions mcp_extension system key",
           "password": true
       }
   ]
   ```
   `"inputs"` goes at the same level as `"servers"` (after its closing `}` and a comma).
3. If the server was already there, just replace the old domain in its `"url"` line with **your new Default domain**. Keep `/runtime/webhooks/mcp` at the end. Save with **Ctrl+S**.
4. Press **Ctrl+Shift+P** and run **MCP: Reset Cached Inputs**. This clears the old key.
5. Click **▷ Start** above `my-remote-mcp-server`, paste the **key** from Step 15 into the box at the top, and press **Enter**.
6. In Copilot Chat, click **+** (new chat), choose **Agent** mode, run **Chat: Configure Tools**, and tick **only `my-remote-mcp-server`**.
7. Send:

```text
List the orders for Dominic's Bakery.
```

✅ **CONFIRM:**
- `mcp.json` shows **Running · 4 tools** above `my-remote-mcp-server`.
- The chat shows Mason's and Ada's orders, now coming **from Azure**.

❌ **IF NOT:** if it fails with 401, the key is wrong. Run **MCP: Reset Cached Inputs**, then Start again and paste the key carefully.

⚠️ Don't commit `mcp.json` with a real key. The file only uses `${input:…}`, so it's safe.

👉 **Go to Step 17.**

---

## STEP 17: Test the remote server in the MCP Inspector

> 💡 **What this step does:** This is the same test as Step 11, but against the **cloud** server. We show that it fails without the key and works with it.

🎬 **DO:**

```powershell
npx @modelcontextprotocol/inspector
```

1. Transport: **Streamable HTTP**
2. URL: `https://<DEFAULT-DOMAIN>/runtime/webhooks/mcp`
3. 🎓 Click **Connect** with **no header**. ✅ It fails (401).
4. Open **Authentication / Custom Headers** and add the header name **`x-functions-key`** with your key as the value.
5. Click **Connect**, then **Tools → List Tools**, then run **`list_products`**.

✅ **CONFIRM:** the status is **Connected**, the 4 tools are listed, and you see the 10 products.

🎬 **DO:** press **Ctrl+C** in the terminal to stop the Inspector.

👉 **Azure part done. Go to Step 18.**

---

## STEP 18: Create the Foundry project

> 💡 **What this step does:** **Microsoft Foundry** is Microsoft's website for building AI agents. A **project** is our workspace there for the bakery agent.

🎬 **DO:**

1. Open <https://ai.azure.com> and sign in with the same account.
2. Turn on the **New Foundry** toggle at the top.
3. In the project picker (top-left), choose **Create new project**:
   - Name: **`dominics-bakery-project`**
   - Subscription: **Visual Studio Enterprise Subscription**
   - Resource group: **`rg-dominics-bakery`**
   - Region: **East US 2**
4. Click **Create** and wait 1–2 minutes.

✅ **CONFIRM:** the project home page opens, and the top-left shows **dominics-bakery-project**.

👉 **Go to Step 19.**

---

## STEP 19: Deploy the model gpt-5.4-mini

> 💡 **What this step does:** An agent needs a **brain**, which is an AI model. We deploy `gpt-5.4-mini`, which understands customers' messages and decides which bakery tool to use.

🎬 **DO:** in Foundry, go to **Discover → Models** (or **Models → Deploy a model**). Search **`gpt-5.4-mini`**, click **Deploy**, choose **Global Standard**, and click **Deploy**.

✅ **CONFIRM:** under **Build → Models**, `gpt-5.4-mini` shows status **Succeeded**.

⚠️ **Do NOT use `model-router`.** Last time it caused *"There was an issue with your request"*. Also, `gpt-4o-mini` can't be deployed anymore.

❌ **IF the portal fails**, use the CLI:

```powershell
az cognitiveservices account list -g rg-dominics-bakery --query "[].name" -o tsv
```

The command above prints your Foundry resource name. Put it in place of `<RESOURCE-NAME>` below:

```powershell
az cognitiveservices account deployment create -g rg-dominics-bakery -n <RESOURCE-NAME> --deployment-name gpt-5.4-mini --model-name gpt-5.4-mini --model-version 2026-03-17 --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50
```

👉 **Go to Step 20.**

---

## STEP 20: Create the agent and add the MCP tool

> 💡 **What this step does:** We create the **agent** (our AI receptionist), give it **instructions** (its job description) and connect our bakery MCP server as its **tool**, with the key so it's allowed in.

🎬 **DO:**

1. Go to **Build → Agents → Create agent**.
   - Name: **`dominics-bakery-agent`**
   - Model: **`gpt-5.4-mini`**
2. Paste these **Instructions**:

```text
You are the friendly assistant for Dominic's Bakery.
Use the bakery tools to list products, place orders and list orders.
Always confirm the customer's name and the items before placing an order.
Only offer products returned by the list_products tool.
```

3. Under **Tools**, click **Add**, choose **Custom**, then **Model Context Protocol (MCP)** and **Create**. Fill in:

| Field | Value |
|---|---|
| Name | `dominics-bakery-mcp` |
| Remote MCP Server endpoint | `https://<DEFAULT-DOMAIN>/runtime/webhooks/mcp` |
| Authentication | **Key-based** |
| Credential name | `x-functions-key` |
| Credential value | your key from Step 15 |

4. Click **Connect**, then **Save**.

✅ **CONFIRM:**
- The agent's **Tools** list shows **only** `dominics-bakery-mcp`.
- **Model** shows **gpt-5.4-mini**.

❌ **IF NOT:**
- If you also see **`dominics-bakery-agent-toolbox`**, click **⋯ → Remove** on it, then **Save**. That toolbox caused *"A user error occurred while executing a tool call"* last time.
- If Model shows `model-router`, change it to **gpt-5.4-mini** and click **Save**.
- Don't delete `dominics-bakery-mcp` on the **Tools** page in the left menu.

👉 **Go to Step 21.**

---

## STEP 21: Test the agent in the Playground

> 💡 **What this step does:** We chat with the agent the way a customer would. It reads the menu and writes real orders by calling our tools, and we approve each action first.

🎬 **DO:** in the agent **Playground**, click **⊕ New chat** and send:

```text
List all Dominic's Bakery products and prices.
```

Click **Approve** when the tool approval appears.

✅ **CONFIRM:** you see the 10 products. Banana Bread is $7.25, Cinnamon Roll is $4.00, and so on.

🎬 **DO:**

```text
I'm Grace, please order 2 Cinnamon Roll and 1 Banana Bread.
```

The agent asks you to confirm, so answer `Yes` and **Approve**. Then send:

```text
Show me all the orders.
```

✅ **CONFIRM:** the list includes Mason, Ada and Grace.

📍 **GO TO** the Portal: **stdominicsmcpserverdemo → Containers → orders**. ✅ Grace's order files are there.

🎉 *"The same MCP server now powers VS Code, the MCP Inspector and a Foundry agent."*

👉 **Go to Step 22.**

---

## STEP 22: Security and governance (end of video)

> 💡 **What this step does:** We show how to keep the agent **safe**: limit **which** tools it can use, and require a human to **approve** before it changes anything.

🎬 **DO:** in the agent, go to **Tools**, then click **dominics-bakery-mcp** (or ⋯ → **Edit**).

1. **Restrict tools:** set **Allowed tools** to only `list_products` and `list_orders`, then **Save**.
   - 🎓 Ask: *"Place an order for Tom for 1 Sourdough Loaf."* ✅ The agent **can't** place it.
   - Then set Allowed tools back to all 4 and click **Save**.
2. **Approval:** set **Require approval** to **Always**. That's what produced the **Approve** button in Step 21.
   - 🎓 *"Human-in-the-loop: the agent can't change data without your permission."*

✅ **CONFIRM:** students understand *who* can call the server (the key), *which* tools the agent can use (allowed tools), and *when* a human must approve (approval).

👉 **Demo complete. Go to Step 23 after class.**

---

## STEP 23: Clean up after class (stops all charges)

> 💡 **What this step does:** Azure charges for resources while they exist. Deleting the resource group (the labelled box) removes everything we created today.

🎬 **DO:**

```powershell
az group delete -n rg-dominics-bakery --yes --no-wait
```

A few minutes later, run:

```powershell
az group exists -n rg-dominics-bakery
```

✅ **CONFIRM:** it prints **`false`**.

ℹ️ The Foundry resource stays *soft-deleted* for 48 hours. That's free, and Azure then removes it automatically.

---

## 🆘 Quick rescue table

| Problem | Fix |
|---|---|
| `func` / `py` not recognized | Close VS Code fully and reopen it |
| Prompt has no `(.venv)` | `.\.venv\Scripts\Activate.ps1` |
| `func start` bundle error | `func bundles download`, then `func start` |
| VS Code server shows **Error** | Make sure `func start` is running, then click **Start** |
| No 🛠 tools icon in chat | **Ctrl+Shift+P → Chat: Configure Tools** |
| Remote returns **401** | Wrong or missing `x-functions-key`. Use the `mcp_extension` key and run **MCP: Reset Cached Inputs** |
| Domain doesn't work | Use the exact **Default domain**, including the random suffix |
| Foundry: *"A user error occurred while executing a tool call"* | Remove `…-toolbox` from the agent's tools and click Save |
| Foundry: *"There was an issue with your request"* | Change the model from `model-router` to `gpt-5.4-mini` |
