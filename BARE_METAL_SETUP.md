# LibriSeVoc - Bare Metal Setup Guide

This guide is for completely fresh systems where even basic tools like `sudo`, `git`, `curl` are not installed.

## Option 1: If You Are Root User

```bash
# Check if you're root
whoami

# If you're root, you can install packages directly
apt update
apt upgrade -y
apt install -y sudo curl wget git build-essential software-properties-common

# Create a regular user (recommended for security)
adduser librisevoc
usermod -aG sudo librisevoc
su - librisevoc

# Now continue with the regular setup...
```

## Option 2: No Root Access - User-Space Installation

If you don't have root access, we'll install everything in your home directory:

### Step 1: Download and Install Miniconda (Python Package Manager)

```bash
# Go to home directory
cd ~

# Download Miniconda installer (if wget/curl not available, download manually)
# For x86_64 systems:
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# For ARM64 systems (if applicable):
# wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O miniconda.sh

# If wget is not available, try curl:
# curl -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make installer executable
chmod +x miniconda.sh

# Install Miniconda
bash miniconda.sh -b -p $HOME/miniconda3

# Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"

# Initialize conda
$HOME/miniconda3/bin/conda init bash

# Reload shell configuration
source ~/.bashrc

# Verify installation
conda --version
python --version
```

### Step 2: Install Git (if not available system-wide)

```bash
# Create local bin directory
mkdir -p ~/local/bin

# Download and compile git from source
cd ~/local
wget https://github.com/git/git/archive/v2.42.0.tar.gz
tar -xzf v2.42.0.tar.gz
cd git-2.42.0

# Configure and compile
make configure
./configure --prefix=$HOME/local
make all
make install

# Add to PATH
export PATH="$HOME/local/bin:$PATH"
echo 'export PATH="$HOME/local/bin:$PATH"' >> ~/.bashrc

# Verify git installation
git --version
```

### Step 3: Create Python Environment and Install Dependencies

```bash
# Create conda environment with Python 3.12
conda create -n librisevoc python=3.12 -y

# Activate environment
conda activate librisevoc

# Install system-level dependencies via conda
conda install -y \
    numpy \
    scipy \
    matplotlib \
    pyyaml \
    tqdm

# Install audio processing libraries
conda install -y -c conda-forge \
    librosa \
    soundfile \
    numba

# Install PyTorch
conda install -y pytorch torchaudio cpuonly -c pytorch
```

### Step 4: Clone Repository and Setup

```bash
# Clone the repository
git clone https://github.com/vladasanadev/LibriSeVoc.git
cd LibriSeVoc

# Verify all dependencies work
python -c "import torch; import librosa; import numpy; import yaml; print('All dependencies working!')"

# Test the scripts
python main.py --help
python eval.py --help
```

## Option 3: Manual Download Without Git

If even git installation fails, download the repository manually:

```bash
# Download repository as zip (if curl/wget available)
curl -L https://github.com/vladasanadev/LibriSeVoc/archive/main.zip -o librisevoc.zip

# Or using wget
wget https://github.com/vladasanadev/LibriSeVoc/archive/main.zip -o librisevoc.zip

# If no download tools available, you'll need to:
# 1. Download the zip file from GitHub web interface on another machine
# 2. Transfer it to the server (scp, sftp, or physical media)

# Extract the archive (if unzip is available)
unzip librisevoc.zip
mv LibriSeVoc-main LibriSeVoc
cd LibriSeVoc

# If unzip is not available, try:
python -m zipfile -e librisevoc.zip .
```

## Option 4: Complete Offline Installation

If the server has no internet access:

### Prepare on a Connected Machine:

```bash
# On a machine with internet access:
# 1. Download Miniconda installer
# 2. Clone the LibriSeVoc repository
# 3. Create conda environment and download all packages:

conda create -n librisevoc python=3.12
conda activate librisevoc
conda install -y numpy scipy matplotlib pyyaml tqdm
conda install -y -c conda-forge librosa soundfile numba
conda install -y pytorch torchaudio cpuonly -c pytorch

# Create offline package archive
conda pack -n librisevoc -o librisevoc-env.tar.gz

# Transfer these files to the offline server:
# - miniconda installer
# - librisevoc-env.tar.gz
# - LibriSeVoc repository (as zip)
```

### Install on Offline Server:

```bash
# Install Miniconda
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
export PATH="$HOME/miniconda3/bin:$PATH"

# Extract pre-built environment
mkdir -p $HOME/miniconda3/envs/librisevoc
tar -xzf librisevoc-env.tar.gz -C $HOME/miniconda3/envs/librisevoc

# Activate environment
conda activate librisevoc

# Extract project
unzip LibriSeVoc-main.zip
cd LibriSeVoc-main

# Test installation
python main.py --help
```

## Option 5: Docker-based Installation (if Docker is available)

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-venv python3-pip git \
    libsndfile1-dev libfftw3-dev libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Clone repository
RUN git clone https://github.com/vladasanadev/LibriSeVoc.git .

# Install Python dependencies
RUN python3.12 -m venv venv && \
    . venv/bin/activate && \
    pip install -r requirements.txt

# Set default command
CMD ["/bin/bash"]
EOF

# Build and run container
docker build -t librisevoc .
docker run -it librisevoc

# Inside container:
source venv/bin/activate
python main.py --help
```

## Troubleshooting

### If you get "Permission denied" errors:
```bash
# Check your permissions
ls -la
whoami
groups

# Make sure you're in your home directory
cd ~
pwd
```

### If downloads fail:
```bash
# Try different download methods
# Method 1: wget
wget https://example.com/file

# Method 2: curl
curl -O https://example.com/file

# Method 3: curl with different options
curl -L -o filename https://example.com/file

# Method 4: Use python (if available)
python3 -c "import urllib.request; urllib.request.urlretrieve('https://example.com/file', 'filename')"
```

### If Python/conda installation fails:
```bash
# Try installing Python from source
cd ~
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar -xzf Python-3.12.0.tgz
cd Python-3.12.0
./configure --prefix=$HOME/local/python
make && make install
export PATH="$HOME/local/python/bin:$PATH"
```

## Environment Variables to Set

Add these to your `~/.bashrc` file:

```bash
# Add to ~/.bashrc
export PATH="$HOME/local/bin:$PATH"
export PATH="$HOME/miniconda3/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/local/lib:$LD_LIBRARY_PATH"

# Reload configuration
source ~/.bashrc
```

## Minimal Requirements

If all else fails, here's the absolute minimum you need:
1. Python 3.8+ (any version)
2. pip (Python package installer)
3. The LibriSeVoc source code

```bash
# Minimal installation with just pip
python3 -m pip install --user numpy torch librosa soundfile pyyaml matplotlib tqdm numba

# Download source code manually and extract
# Then run:
python3 main.py --help
```

Choose the option that best fits your server's constraints!
