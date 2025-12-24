# Auburn Easley HPC - Storage & Filesystems Guide

## Storage Locations

### 1. Home Directory (`~/` or `/home/username`)

**Path:** `/home/tzs0128`

**Quota:** Typically 50GB (check with `quota` command)

**Backed Up:** Yes

**Use For:**
- Source code
- Configuration files
- Small datasets
- Job scripts
- Modules and software installations

**Best Practices:**
- Keep code and scripts here
- Don't store large datasets
- Don't run jobs that write lots of output here

```bash
# Check your home directory
cd ~
pwd
# /home/tzs0128

# Check quota
quota
```

### 2. Scratch Space (`/scratch/username`)

**Path:** `/scratch/tzs0128` (typically)

**Quota:** Much larger (100GB-1TB+, varies)

**Backed Up:** NO - temporary storage

**Retention:** Files may be deleted after 30-90 days of inactivity

**Use For:**
- Large datasets
- Job output files
- Temporary processing files
- Model checkpoints
- Large results

**Best Practices:**
- Move large files here from home
- Copy important results back to home or download
- Don't rely on it for long-term storage
- Clean up old files regularly

```bash
# Check if scratch exists
ls -la /scratch/$USER

# If doesn't exist, create it
mkdir -p /scratch/$USER

# Navigate to scratch
cd /scratch/$USER
```

### 3. Project/Group Space (if applicable)

Some research groups have shared project directories.

**Contact:** Your PI or hpcadmin@auburn.edu

## Checking Storage Usage

### Check Home Directory Quota

```bash
quota
# or
quota -s
```

Example output:
```
Disk quotas for user tzs0128 (uid 12345):
     Filesystem  blocks   quota   limit   grace   files   quota   limit   grace
 /home          25000   50000   55000            5000   10000   11000
```

### Check Disk Usage

```bash
# Home directory usage
du -sh ~

# Scratch usage
du -sh /scratch/$USER

# Find largest directories
du -h ~ | sort -h | tail -20

# Find largest files
find ~ -type f -exec du -h {} + | sort -h | tail -20
```

## File Transfer

### From Local Machine to Easley

#### Using scp

```bash
# Single file
scp myfile.txt tzs0128@easley.auburn.edu:~/

# Directory
scp -r my_directory tzs0128@easley.auburn.edu:~/

# To scratch
scp -r large_data tzs0128@easley.auburn.edu:/scratch/tzs0128/
```

#### Using rsync (Recommended for large transfers)

```bash
# Sync directory (skips already transferred files)
rsync -avz --progress my_directory/ tzs0128@easley.auburn.edu:~/my_directory/

# Exclude certain files
rsync -avz --exclude 'runs/' --exclude '*.pyc' \
    FL_Project/ tzs0128@easley.auburn.edu:~/FL_Project/

# To scratch
rsync -avz --progress large_data/ \
    tzs0128@easley.auburn.edu:/scratch/tzs0128/large_data/
```

### From Easley to Local Machine

```bash
# Download file
scp tzs0128@easley.auburn.edu:~/results.tar.gz ./

# Download directory
scp -r tzs0128@easley.auburn.edu:~/results ./

# Sync with rsync
rsync -avz --progress tzs0128@easley.auburn.edu:~/results/ ./results/
```

### Between Easley Directories

```bash
# Copy from home to scratch
cp -r ~/FL_Project/data /scratch/$USER/

# Or move (if you don't need it in home)
mv ~/FL_Project/data /scratch/$USER/

# Create symlink (so code still finds it)
ln -s /scratch/$USER/data ~/FL_Project/data
```

## Best Practices

### 1. Organize Your Directories

```bash
# Recommended structure
/home/tzs0128/
├── FL_Project/           # Your code
│   ├── src/
│   ├── scripts/
│   ├── configs/
│   └── hpc_setup/
├── software/             # Custom software installations
└── bin/                  # Personal scripts

/scratch/tzs0128/
├── FL_Project_data/      # Large datasets
├── FL_Project_runs/      # Job outputs
└── checkpoints/          # Model checkpoints
```

### 2. Use Scratch for Job Output

In your job script:

```bash
#!/bin/bash
#SBATCH -o /scratch/tzs0128/logs/job_%j.out
#SBATCH -e /scratch/tzs0128/logs/job_%j.err

# Set output directory to scratch
export OUTPUT_DIR="/scratch/tzs0128/FL_Project_runs"
mkdir -p $OUTPUT_DIR

# Run job writing to scratch
python scripts/train.py --output $OUTPUT_DIR

# Copy important results back to home
cp $OUTPUT_DIR/final_model.pt ~/FL_Project/models/
```

### 3. Link Large Files to Scratch

```bash
# Move data to scratch
mv ~/FL_Project/data /scratch/$USER/FL_Project_data

# Create symlink
ln -s /scratch/$USER/FL_Project_data ~/FL_Project/data

# Your code still sees ~/FL_Project/data but it's actually on scratch
```

### 4. Clean Up Regularly

```bash
# Find old files in scratch (>30 days)
find /scratch/$USER -type f -mtime +30 -ls

# Delete old temporary files
find /scratch/$USER/tmp -type f -mtime +7 -delete

# Compress old results
tar -czf old_results_$(date +%Y%m%d).tar.gz old_results/
rm -rf old_results/
```

### 5. Monitor Your Quota

Add to `~/.bashrc`:
```bash
# Show quota on login
quota -s
```

## File Transfer Examples

### Transfer FL_Project to Easley

From your local machine:

```bash
cd /path/to/repos

# Initial transfer (exclude large files)
rsync -avz --exclude 'runs/' \
           --exclude 'data/' \
           --exclude '.git/' \
           --exclude '__pycache__/' \
           --exclude '*.pyc' \
           FL_Project/ tzs0128@easley.auburn.edu:~/FL_Project/

# Transfer data separately to scratch
rsync -avz FL_Project/data/ \
    tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_data/
```

### Download Results

```bash
# Download results from scratch
rsync -avz --progress \
    tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_runs/ \
    ./hpc_results/

# Download specific run
scp -r tzs0128@easley.auburn.edu:/scratch/tzs0128/FL_Project_runs/run_20251210/ ./
```

## Compression

### Compress Before Transfer

```bash
# On Easley (before downloading)
tar -czf results_$(date +%Y%m%d).tar.gz results/

# Download compressed file
scp tzs0128@easley.auburn.edu:~/results_20251210.tar.gz ./

# Extract locally
tar -xzf results_20251210.tar.gz
```

### Compress Old Data

```bash
# Compress old runs
tar -czf run_archive_2024.tar.gz runs_2024/
rm -rf runs_2024/

# Uncompress when needed
tar -xzf run_archive_2024.tar.gz
```

## Troubleshooting

### Out of Quota

```bash
# Check usage
quota -s

# Find largest files
du -h ~ | sort -h | tail -20

# Move to scratch
mv ~/large_file /scratch/$USER/

# Or delete old files
rm -rf ~/old_stuff/
```

### Slow File Operations

```bash
# Use scratch for I/O intensive operations
cd /scratch/$USER

# Avoid lots of small files - combine them
tar -czf many_files.tar.gz directory_with_many_files/

# Use larger block sizes for copying
rsync -avz --inplace --no-whole-file source/ dest/
```

### Transfer Interrupted

```bash
# Resume with rsync
rsync -avz --partial --progress source/ dest/

# Or use --append to resume transfer
rsync -avz --append source/large_file dest/
```

### Permission Denied

```bash
# Check ownership
ls -la /scratch/$USER

# If directory doesn't exist
mkdir -p /scratch/$USER
chmod 700 /scratch/$USER

# Check file permissions
chmod 644 file.txt    # Read for all
chmod 755 script.sh   # Execute for all
chmod 600 secret.txt  # Only you can read
```

## Quick Reference

```bash
# Storage Locations
~/                    # Home (50GB, backed up)
/scratch/$USER       # Scratch (large, temporary)

# Check Usage
quota                # Quota status
du -sh ~             # Home usage
du -sh /scratch/$USER # Scratch usage

# Transfer
scp file.txt tzs0128@easley.auburn.edu:~/
scp -r dir/ tzs0128@easley.auburn.edu:~/
rsync -avz source/ dest/

# Move to Scratch
mv ~/large_data /scratch/$USER/
ln -s /scratch/$USER/large_data ~/large_data

# Compress
tar -czf archive.tar.gz directory/
tar -xzf archive.tar.gz
```

## Contact

For storage issues or quota increases:
- Email: hpcadmin@auburn.edu
- Include your username and justification for increase
