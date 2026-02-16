# When to Reinstall the Package

## ✅ You DON'T Need to Reinstall If:

1. **You've made changes to Python source code** (`.py` files in `src/`)
   - Package is installed in **editable mode** (`-e` flag)
   - Changes to `.py` files take effect immediately
   - Just restart the server if it's running

2. **You've updated configuration** (`.env` file)
   - Configuration is loaded at runtime
   - No installation needed
   - Just restart the server

3. **You see subprocess errors but the package already works**
   ```bash
   # Check if installed:
   peer-review-mcp version
   # If this works, you're good!
   ```

## ⚠️ You NEED to Reinstall If:

1. **You've modified `pyproject.toml`**
   - Added/removed dependencies
   - Changed package metadata
   - Modified entry points

2. **You've added new dependencies**
   - Updated `dependencies` list in `pyproject.toml`
   - Need to install new packages

3. **You've changed package structure**
   - Added/removed top-level modules
   - Changed package name
   - Modified `src/` directory structure

## 🔧 How to Reinstall (Corporate Environment)

### Step 1: Install Build Dependencies
```bash
python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade
```

### Step 2: Reinstall Package
```bash
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e . --force-reinstall --no-deps
```

### Step 3: Install Updated Dependencies (if needed)
```bash
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r <(python3 -c "import tomli; print('\n'.join(tomli.load(open('pyproject.toml', 'rb'))['project']['dependencies']))")
```

Or simply:
```bash
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
```

## 🐛 Troubleshooting Reinstall Errors

### Error: "subprocess-exited-with-error"

**Check first**: Is the package already working?
```bash
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
peer-review-mcp version
```

If it works, **you don't need to reinstall!**

If you must reinstall:
1. Install build dependencies first (Step 1 above)
2. Use `--trusted-host` flags (corporate firewall)
3. Use `--no-build-isolation` if still failing:
   ```bash
   python3 -m pip install --no-build-isolation --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
   ```

### Error: "ModuleNotFoundError: No module named 'setuptools'"

Install build dependencies:
```bash
python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade
```

### Error: Pydantic validation errors

This usually means configuration file issues, not installation issues.

Check your `.env` file:
```bash
peer-review-mcp config-check
```

## 📝 Quick Reference

| Scenario | Action Needed | Command |
|----------|---------------|---------|
| Changed `.py` files | None (editable mode) | Just restart server |
| Changed `.env` | None | Just restart server |
| Changed `pyproject.toml` | Reinstall | See "How to Reinstall" |
| Added dependencies | Reinstall | See "How to Reinstall" |
| Subprocess error but works | None | Package already installed |
| Fresh installation | Full install | See [INSTALL.md](INSTALL.md) |

## ✅ Verify Installation

After any reinstall:
```bash
./verify-install.sh
```

Or manually:
```bash
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
peer-review-mcp version
peer-review-mcp config-check
```
