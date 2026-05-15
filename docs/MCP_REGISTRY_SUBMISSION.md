# Sentimatix — Official MCP Registry Submission Guide

> Submit to **registry.modelcontextprotocol.io** — the Anthropic-maintained, canonical registry
> that Claude Desktop, Cursor, and all MCP clients pull from.

---

## What We're Doing

The official MCP Registry (`registry.modelcontextprotocol.io`) is the **#1 distribution channel**
for MCP servers — above Smithery, PulseMCP, or Glama. Getting listed here means Sentimatix
appears natively in Claude Desktop's server browser and all future MCP-compatible clients.

Your server.json is already created at `apps/mcp/server.json`.

---

## Step 1 — Publish to PyPI

The registry hosts **metadata only** — not code. You must publish your MCP server as a
PyPI package first. The package name will be `sentimatix-mcp`.

### 1a. Create `apps/mcp/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sentimatix-mcp"
version = "1.0.0"
description = "Real-time Indian stock market sentiment intelligence MCP server (NSE/BSE)"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Rishav Dutta", email = "your@email.com" }
]
keywords = ["mcp", "stock", "sentiment", "NSE", "BSE", "india", "finance", "AI"]
classifiers = [
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Topic :: Office/Business :: Financial :: Investment",
]
dependencies = [
  "mcp>=1.0.0",
  "httpx>=0.27.0",
  "python-dotenv>=1.0.0",
  "uvicorn>=0.30.0",
  "starlette>=0.40.0",
]

[project.scripts]
sentimatix-mcp = "mcp_stdio:main"

[project.urls]
Homepage = "https://sentimatix-production.up.railway.app"
Repository = "https://github.com/Rishav0123/sentimatix"
Documentation = "https://sentimatix-production.up.railway.app/docs"
"Bug Tracker" = "https://github.com/Rishav0123/sentimatix/issues"

[tool.hatch.build.targets.wheel]
packages = ["server"]
include = ["mcp_stdio.py", "server/**/*.py"]
```

### 1b. Add Ownership Verification to `apps/mcp/README.md`

The registry verifies PyPI package ownership by looking for this **exact comment** in
your PyPI README. Add it anywhere — hidden in an HTML comment is fine:

```markdown
<!-- mcp-name: io.github.rishavdutta-kgp/sentimatix -->
```

Your `apps/mcp/README.md` should start with:

```markdown
# Sentimatix MCP Server

<!-- mcp-name: io.github.rishavdutta-kgp/sentimatix -->

Real-time Indian stock market sentiment intelligence for AI agents.
Provides live NSE/BSE news sentiment via MCP tools for Claude Desktop, Cursor, and more.

...rest of existing README content...
```

### 1c. Build and Publish

```powershell
cd d:\sentimatix\apps\mcp

# Install build tools
pip install hatchling build twine

# Build the package
python -m build

# Publish to PyPI (you need a PyPI account at pypi.org)
twine upload dist/*
```

After upload, verify at: `https://pypi.org/project/sentimatix-mcp/`

---

## Step 2 — Install `mcp-publisher` CLI

```powershell
# Windows (run in PowerShell)
$arch = if ([System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -eq "Arm64") { "arm64" } else { "amd64" }
Invoke-WebRequest -Uri "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_$arch.tar.gz" -OutFile "mcp-publisher.tar.gz"
tar xf mcp-publisher.tar.gz mcp-publisher.exe
rm mcp-publisher.tar.gz
# Move mcp-publisher.exe to a folder in your PATH (e.g. C:\Windows\System32 or any PATH dir)
Move-Item .\mcp-publisher.exe C:\Windows\System32\mcp-publisher.exe

# Verify install
mcp-publisher --help
```

---

## Step 3 — Authenticate with GitHub

```powershell
mcp-publisher login github
```

This will print a device code. Go to `https://github.com/login/device`, enter the code,
and authorize. Your server name MUST start with `io.github.rishavdutta-kgp/` because
you're using GitHub auth.

---

## Step 4 — Publish to the Official Registry

```powershell
cd d:\sentimatix\apps\mcp
mcp-publisher publish
```

Expected output:
```
Publishing to https://registry.modelcontextprotocol.io...
✓ Successfully published
✓ Server io.github.rishavdutta-kgp/sentimatix version 1.0.0
```

---

## Step 5 — Verify Your Listing

```powershell
curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=sentimatix"
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "Registry validation failed for package" | Ensure `<!-- mcp-name: io.github.rishavdutta-kgp/sentimatix -->` is in your PyPI README |
| "You do not have permission to publish this server" | Your server name must start with `io.github.rishavdutta-kgp/` |
| "Invalid or expired Registry JWT token" | Run `mcp-publisher login github` again |
| Package not found on PyPI | Wait 5-10 mins after `twine upload` for PyPI indexing |

---

## After Publishing — Update Claude Desktop Config

Your users will now be able to install via:

```json
{
  "mcpServers": {
    "sentimatix": {
      "command": "uvx",
      "args": ["sentimatix-mcp"],
      "env": {
        "BACKEND_API_URL": "https://sentimatix-production.up.railway.app/api"
      }
    }
  }
}
```

Or for the remote (no local install needed):
```json
{
  "mcpServers": {
    "sentimatix": {
      "url": "https://sentimatix-mcp.up.railway.app/mcp"
    }
  }
}
```

---

## Automate with GitHub Actions (Optional)

Add `.github/workflows/publish-mcp.yml`:

```yaml
name: Publish to MCP Registry

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Publish to PyPI
        run: |
          pip install build twine
          cd apps/mcp && python -m build
          twine upload dist/* -u __token__ -p ${{ secrets.PYPI_TOKEN }}
      - name: Publish to MCP Registry
        run: |
          curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_linux_amd64.tar.gz" | tar xz mcp-publisher
          ./mcp-publisher login github --token ${{ secrets.MCP_REGISTRY_TOKEN }}
          cd apps/mcp && ../mcp-publisher publish
```

---

## Summary Checklist

- [ ] Create `apps/mcp/pyproject.toml`
- [ ] Add `<!-- mcp-name: io.github.rishavdutta-kgp/sentimatix -->` to `apps/mcp/README.md`
- [ ] Create a PyPI account at pypi.org
- [ ] Run `python -m build && twine upload dist/*` in `apps/mcp/`
- [ ] Install `mcp-publisher` CLI
- [ ] Run `mcp-publisher login github`
- [ ] Run `mcp-publisher publish` from `apps/mcp/`
- [ ] Verify listing at `registry.modelcontextprotocol.io`
