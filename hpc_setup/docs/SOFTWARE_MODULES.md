# Auburn Easley HPC - Software & Modules Guide

## Module System Overview

Auburn's Easley Cluster uses **LMOD** as its environment module platform, supporting both TCL and LUA scripting languages.

The module system manages environment variables like:
- `$PATH` - Where to find executables
- `$LD_LIBRARY_PATH` - Where to find libraries
- `$PYTHONPATH` - Python package locations

This enables different software versions and configurations to coexist.

## Software Location

Global software binaries and libraries are in `/tools` directory with accompanying Environment Modules.

## Essential Module Commands

| Command | Function | Example |
|---------|----------|---------|
| `module avail` | List all available modules | `module avail` |
| `module avail <name>` | Search for specific module | `module avail python` |
| `module show <name>` | Display module details | `module show python/3.11` |
| `module load <name>` | Load a module | `module load python/3.11` |
| `module list` | Show loaded modules | `module list` |
| `module unload <name>` | Remove a module | `module unload python` |
| `module purge` | Remove ALL modules | `module purge` |
| `module spider <name>` | Search for module | `module spider cuda` |

## Common Software

### Python

```bash
# See available Python versions
module avail python

# Load Python 3.11
module load python/3.11

# Verify
python --version
which python

# Install packages to your home directory
pip install --user package_name

# See installed packages
pip list --user
```

### CUDA (GPU Computing)

```bash
# See available CUDA versions
module avail cuda

# Load CUDA 11.0
module load cuda11.0/toolkit

# Or CUDA 12.0 if available
module load cuda/12.0

# Verify
nvcc --version
```

### GCC Compilers

```bash
# See available GCC versions
module avail gcc

# Load GCC
module load gcc/9.3.0

# Verify
gcc --version
```

### OpenMPI (Parallel Computing)

```bash
# See available MPI versions
module avail openmpi

# Load OpenMPI
module load openmpi/4.0.3

# Verify
mpirun --version
```

## Example Workflow

### Setup for Python Project

```bash
# 1. Purge any loaded modules (clean slate)
module purge

# 2. Load Python
module load python/3.11

# 3. Verify
python --version

# 4. Install packages
pip install --user requests pyyaml tqdm

# 5. Check installed packages
pip list --user

# 6. Save loaded modules for later
module save my_python_env

# Later, restore this environment:
module restore my_python_env
```

### Setup for GPU Project

```bash
# 1. Clean slate
module purge

# 2. Load CUDA
module load cuda11.0/toolkit

# 3. Load Python
module load python/3.11

# 4. Install PyTorch (example)
pip install --user torch torchvision

# 5. Verify GPU support
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# 6. Save environment
module save pytorch_env
```

## Creating Custom Modules

You can create your own modulefiles for custom software.

### Setup Custom Module Directory

```bash
# 1. Create module directory
mkdir -p ~/.auhpc/modules

# 2. Tell LMOD about it
module use ~/.auhpc/modules

# Add to .bashrc to make permanent:
echo "module use ~/.auhpc/modules" >> ~/.bashrc
```

### Example Custom Module

Create file `~/.auhpc/modules/my_software/1.0.lua`:

```lua
-- My Software v1.0
help([[
Description: My custom software
Version: 1.0
]])

whatis("Name: My Software")
whatis("Version: 1.0")

local base = "/home/tzs0128/software/my_software"

prepend_path("PATH", pathJoin(base, "bin"))
prepend_path("LD_LIBRARY_PATH", pathJoin(base, "lib"))
prepend_path("PYTHONPATH", pathJoin(base, "python"))

setenv("MY_SOFTWARE_HOME", base)
```

Then load it:
```bash
module load my_software/1.0
```

## Module Hierarchies

Modules can be organized hierarchically:
```
~/.auhpc/modules/
├── compilers/
│   └── gcc/
│       └── 8.8.8.lua
├── python/
│   ├── 3.9.lua
│   └── 3.11.lua
└── my_tools/
    └── 1.0.lua
```

LMOD automatically recognizes this structure.

## Best Practices

### 1. Clean Environment

Always start with `module purge` to avoid conflicts:
```bash
module purge
module load python/3.11
```

### 2. List Loaded Modules

Check what's loaded:
```bash
module list
```

### 3. Save Environments

Save frequently used module combinations:
```bash
module purge
module load python/3.11 cuda11.0/toolkit
module save pytorch_gpu

# Restore later:
module restore pytorch_gpu
```

### 4. Check Dependencies

Some modules have dependencies:
```bash
# Some modules may auto-load dependencies
module show python/3.11
```

### 5. In Job Scripts

Always specify modules in job scripts:
```bash
#!/bin/bash
#SBATCH ...

# Clean environment
module purge

# Load required modules
module load python/3.11
module list

# Your code
python my_script.py
```

## Common Workflows

### Installing Python Packages

```bash
# DON'T use sudo (you don't have permissions)
# DON'T install globally

# DO use --user flag
pip install --user numpy pandas scikit-learn

# Or create virtual environment
python -m venv ~/myenv
source ~/myenv/bin/activate
pip install numpy pandas scikit-learn
```

### Compiling Software

```bash
# Request interactive job
salloc -N 1 -n 8 -t 02:00:00

# Load compiler
module load gcc/9.3.0

# Configure (install to home directory)
./configure --prefix=$HOME/software/myapp

# Compile with multiple cores
make -j 8

# Install
make install

# Create module for it (optional)
# See "Creating Custom Modules" above
```

### Using Singularity Containers

```bash
# See available Singularity
module avail singularity

# Load Singularity
module load singularity

# Run container
singularity exec my_container.sif python my_script.py
```

## Requesting New Software

**Open-source software:** Submit requests to OIT at https://aub.ie/hpcacct

**Licensed software:**
- Multi-user licenses: Coordinate with OIT
- Single-user licenses: Install in your home directory

**Contact:** hpcadmin@auburn.edu

## Troubleshooting

### Module Not Found

```bash
# Search for module
module spider python

# Maybe different name?
module avail | grep -i python

# Request installation if not available
# Email: hpcadmin@auburn.edu
```

### Module Conflicts

```bash
# Purge all and start fresh
module purge

# Load modules in correct order
# Usually: compiler → MPI → libraries → applications
module load gcc/9.3.0
module load openmpi/4.0.3
module load python/3.11
```

### Command Not Found After Loading Module

```bash
# Check if module actually loaded
module list

# Check PATH
echo $PATH

# Try reloading
module unload python/3.11
module load python/3.11

# Verify
which python
```

### Package Installation Fails

```bash
# Make sure Python module is loaded
module list

# Use --user flag
pip install --user package_name

# Check quota (might be out of space)
quota

# Try in virtual environment
python -m venv ~/myenv
source ~/myenv/bin/activate
pip install package_name
```

## Quick Reference Card

```bash
# Essential Commands
module avail              # List all modules
module avail python       # Search for Python
module load python/3.11   # Load Python 3.11
module list               # Show loaded modules
module purge              # Unload all
module save myenv         # Save environment
module restore myenv      # Restore environment

# In Job Scripts
module purge
module load python/3.11
module list

# Common Modules
python/3.11
cuda11.0/toolkit
gcc/9.3.0
openmpi/4.0.3
```
