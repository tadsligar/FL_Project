# Installing Ollama on Windows

## Method 1: Official Windows Installer (Recommended)

### Step 1: Download Ollama

1. Go to: **https://ollama.com/download/windows**
2. Click "Download for Windows"
3. This downloads `OllamaSetup.exe` (~200MB)

### Step 2: Install

1. Run `OllamaSetup.exe`
2. Follow the installation wizard
3. It installs to `C:\Users\<YourName>\AppData\Local\Programs\Ollama`
4. Automatically adds to PATH

### Step 3: Verify Installation

Open **PowerShell** or **Command Prompt** and run:

```powershell
ollama --version
```

You should see something like:
```
ollama version is 0.1.x
```

### Step 4: Start Ollama

Ollama should auto-start as a Windows service. Verify it's running:

```powershell
# Check if Ollama is running
Get-Process ollama

# Or try this
curl http://localhost:11434
```

If you see "Ollama is running", you're good!

### Step 5: Pull Your Model

```powershell
# Try Meditron first (medical-specific)
ollama pull meditron:70b

# OR if Meditron not available, use Llama3
ollama pull llama3:70b

# This will download ~42GB (takes 10-30 min depending on internet)
```

### Step 6: Test the Model

```powershell
# Quick test
ollama run llama3:70b "What is acute myocardial infarction? Answer in one sentence."
```

If you get a response, you're all set! ✅

---

## Method 2: Windows Subsystem for Linux (WSL)

If the Windows installer doesn't work, use WSL:

### Step 1: Install WSL (if not already)

```powershell
# Run PowerShell as Administrator
wsl --install
```

Restart your computer.

### Step 2: Install Ollama in WSL

```bash
# Open WSL terminal
wsl

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve &

# Pull model
ollama pull llama3:70b
```

---

## Method 3: Docker (Alternative)

If neither works, use Docker:

### Step 1: Install Docker Desktop for Windows

Download from: https://www.docker.com/products/docker-desktop/

### Step 2: Run Ollama in Docker

```powershell
# Pull Ollama image
docker pull ollama/ollama

# Run Ollama server
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull your model
docker exec -it ollama ollama pull llama3:70b
```

---

## Verification Checklist

After installation, verify:

```powershell
# 1. Check Ollama is installed
ollama --version

# 2. Check Ollama is running
curl http://localhost:11434

# 3. List installed models (should be empty initially)
ollama list

# 4. Pull a test model (small, ~4GB)
ollama pull llama3:8b

# 5. Test the model
ollama run llama3:8b "Hello, test message"

# 6. Pull your production model
ollama pull llama3:70b
```

---

## GPU Support (Important for Your RTX 4090!)

Ollama should automatically detect your RTX 4090. Verify:

```powershell
# Run this while Ollama is generating
nvidia-smi
```

You should see:
- GPU Memory Usage: ~20-24GB (for 70B model)
- GPU Utilization: 80-100%

If GPU is NOT being used:
1. Make sure CUDA drivers are installed
2. Check NVIDIA control panel shows RTX 4090
3. Reinstall Ollama

---

## Common Issues

### Issue 1: "ollama: command not found"

**Fix:**
1. Restart PowerShell/Terminal
2. Check PATH: `$env:PATH` should include Ollama folder
3. Manually add to PATH if needed:
   - Settings → System → About → Advanced system settings
   - Environment Variables → Path → Add `C:\Users\YourName\AppData\Local\Programs\Ollama`

### Issue 2: "Error: could not connect to ollama server"

**Fix:**
```powershell
# Start Ollama manually
ollama serve

# Or restart the Ollama service
# Services → Ollama → Restart
```

### Issue 3: Model download very slow

**Fix:**
- Check internet connection
- Use wired connection if possible
- The 70B model is 42GB, so 10-30 min is normal

### Issue 4: Out of disk space

**Fix:**
- 70B model needs ~42GB free space
- Check: `Get-PSDrive C`
- Clear space or use different drive

---

## Quick Start Commands (After Installation)

```powershell
# Pull model (one-time, 10-30 min)
ollama pull llama3:70b

# List installed models
ollama list

# Test model
ollama run llama3:70b "What is acute MI?"

# Keep model loaded (optional, for faster responses)
$env:OLLAMA_KEEP_ALIVE = "3600"  # Keep for 1 hour

# Start Ollama server (if not running)
ollama serve
```

---

## Next Steps (After Ollama is Installed)

1. **Pull model**: `ollama pull llama3:70b`
2. **Download MedQA**: `python scripts\download_medqa.py --split test --options 4`
3. **Test your system**: `python -m src.app run --config configs\llama3_70b.yaml --question "test"`
4. **Run comparison**: `python scripts\run_baseline_comparison.py --n 10`

---

## Alternative: Skip Ollama, Use API

If Ollama is too complex, you can try:

### Option A: Use Mock Provider (Testing Only)

Edit `configs/default.yaml`:
```yaml
provider: "mock"
model: "mock-model"
```

This lets you test the system without any model installed.

### Option B: Use OpenAI API (If safeguards allow)

Edit `configs/default.yaml`:
```yaml
provider: "openai"
model: "gpt-4o-mini"
```

Add to `.env`:
```
OPENAI_API_KEY=your_key_here
```

**BUT**: OpenAI may still block medical prompts. Try it first on one question.

### Option C: Use Claude API

Edit `configs/default.yaml`:
```yaml
provider: "anthropic"
model: "claude-3-5-sonnet-20241022"
```

Add to `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

**BUT**: Claude also has medical safeguards.

---

## Recommended Installation Order

1. **Try Method 1** (Windows Installer) - Easiest
2. If that fails, **try Method 2** (WSL) - More reliable
3. If that fails, **try Method 3** (Docker) - Most complex but works
4. If all fail, **use Mock provider** to test system logic

---

## Help Resources

- **Ollama Docs**: https://github.com/ollama/ollama/blob/main/docs/windows.md
- **Ollama Discord**: https://discord.gg/ollama
- **GitHub Issues**: https://github.com/ollama/ollama/issues

---

Let me know which method you want to try first!
