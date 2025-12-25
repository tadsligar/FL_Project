# Transferring Local Ollama Model to HPC

Since Ollama isn't available on Auburn's Easley HPC, you can transfer your local Qwen 2.5 32B model from your Windows machine.

## Step 1: Locate Your Local Ollama Model

Ollama stores models on Windows at:
```
C:\Users\<username>\.ollama\models\
```

For you specifically:
```
C:\Users\Tad\.ollama\models\
```

The actual model files are in subdirectories with hash-based names. To find Qwen 2.5 32B:

**On your Windows machine (PowerShell):**
```powershell
# Navigate to Ollama models directory
cd C:\Users\Tad\.ollama\models

# Look for model manifests
dir manifests\registry.ollama.ai\library\qwen2.5\

# Look for blobs (actual model files)
dir blobs\
```

The model files will be in the `blobs/` directory with names like `sha256-xxxxx`.

## Step 2: Identify the Correct Files

You need:
1. **Model weights** - Large file (typically 18-20GB for Q4_K_M quantization)
2. **Manifest file** - JSON file describing the model
3. **Config files** - Model architecture and tokenizer

**Find your exact model:**
```powershell
# Check what models you have pulled
ollama list

# This should show something like:
# qwen2.5:32b    <hash>    19.8 GB    <date>
```

## Step 3: Alternative - Use llama.cpp Format

Instead of transferring Ollama's format, you can use the GGUF file directly with llama.cpp:

**Download GGUF directly (if you don't have it):**
```powershell
# You may already have this from Ollama
# Check your downloads or look for .gguf files
dir C:\Users\Tad\.ollama\models\blobs\ | Select-String "gguf"
```

## Step 4: Transfer to HPC

**Option A: Transfer via SCP (Recommended)**

On your Windows machine:
```powershell
# Transfer the model file (replace with actual filename)
scp C:\Users\Tad\.ollama\models\blobs\sha256-XXXXX `
    tzs0128@easley.auburn.edu:/scratch/tzs0128/models/qwen25-32b.gguf
```

**Option B: Use rsync (if available)**
```powershell
rsync -avz --progress `
    C:\Users\Tad\.ollama\models\blobs\sha256-XXXXX `
    tzs0128@easley.auburn.edu:/scratch/tzs0128/models/qwen25-32b.gguf
```

**Note:** This transfer will take a while (18-20GB file). Ensure stable connection.

## Step 5: Set Up llama.cpp on HPC

Once the model is transferred, use llama.cpp for inference:

**On Easley:**
```bash
# Navigate to your HPC directory
cd ~/FL_Project

# Verify model transferred
ls -lh /scratch/tzs0128/models/qwen25-32b.gguf

# Set up llama.cpp (if not already done)
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Test the model
./main -m /scratch/tzs0128/models/qwen25-32b.gguf -p "Test prompt" -n 50
```

## Step 6: Create HPC Config for llama.cpp

You'll need to modify your config to use llama.cpp instead of Ollama:

**On Easley:**
```bash
cd ~/FL_Project

cat > configs/hpc_llamacpp.yaml << 'EOF'
model: "qwen2.5:32b"
provider: "llamacpp"
model_path: "/scratch/tzs0128/models/qwen25-32b.gguf"
temperature: 1.0
max_output_tokens: 2048
timeout: 300
threads: 16
EOF
```

## Step 7: Update LLM Client (if needed)

You may need to modify `src/llm_client.py` to support llama.cpp as a provider. This would involve:

1. Detecting `provider: "llamacpp"`
2. Using subprocess to call `llama.cpp/main`
3. Parsing the output

Alternatively, use **llama-cpp-python**:
```bash
# On Easley
pip install --user llama-cpp-python
```

Then modify config:
```yaml
model: "qwen2.5:32b"
provider: "llama-cpp-python"
model_path: "/scratch/tzs0128/models/qwen25-32b.gguf"
```

## Quick Reference

```bash
# Find local model on Windows
cd C:\Users\Tad\.ollama\models\blobs
dir

# Transfer to HPC
scp <model_file> tzs0128@easley.auburn.edu:/scratch/tzs0128/models/

# Verify on HPC
ssh tzs0128@easley.auburn.edu
ls -lh /scratch/tzs0128/models/

# Test with llama.cpp
cd ~/llama.cpp
./main -m /scratch/tzs0128/models/qwen25-32b.gguf -p "Test" -n 50
```

## Expected File Sizes

- **Qwen 2.5 32B (Q4_K_M)**: ~18-20 GB
- **Transfer time**: 30-90 minutes (depends on connection speed)
- **Disk space needed**: ~20 GB on `/scratch/tzs0128/`

## Troubleshooting

### Transfer Interrupted
```bash
# Resume with rsync
rsync -avz --partial --progress <source> <destination>
```

### Permission Denied
```bash
# Ensure scratch directory exists
mkdir -p /scratch/tzs0128/models
chmod 755 /scratch/tzs0128/models
```

### Model File Corrupted
```bash
# Verify file size matches original
ls -lh /scratch/tzs0128/models/qwen25-32b.gguf

# Compare checksums (on both Windows and HPC)
# Windows:
certutil -hashfile <filename> SHA256

# HPC:
sha256sum /scratch/tzs0128/models/qwen25-32b.gguf
```
