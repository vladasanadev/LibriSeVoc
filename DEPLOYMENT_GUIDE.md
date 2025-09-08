# LibriSeVoc Deployment Guide - Fresh Ubuntu Server

This guide provides step-by-step commands to deploy the synthetic voice detection system on a completely fresh Ubuntu server.

## Prerequisites
- Fresh Ubuntu server (18.04, 20.04, 22.04, or 24.04)
- Root or sudo access
- Internet connection

## Step 1: Update System and Install Basic Tools

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git build-essential
```

## Step 2: Install Python 3.12 and Development Tools

```bash
# Install Python 3.12 and related packages
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Verify Python installation
python3.12 --version
```

## Step 3: Install System Dependencies for Audio Processing

```bash
# Install audio processing system libraries
sudo apt install -y \
    libsndfile1-dev \
    libfftw3-dev \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    sox \
    libsox-fmt-all

# Install additional dependencies for ML libraries
sudo apt install -y \
    libblas3 \
    liblapack3 \
    liblapack-dev \
    libblas-dev \
    gfortran \
    libhdf5-serial-dev \
    pkg-config
```

## Step 4: Clone the Repository

```bash
# Clone the project repository
git clone https://github.com/vladasanadev/LibriSeVoc.git

# Navigate to project directory
cd LibriSeVoc

# Verify files are present
ls -la
```

## Step 5: Set Up Python Virtual Environment

```bash
# Create virtual environment with Python 3.12
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip

# Verify virtual environment
which python
python --version
```

## Step 6: Install Python Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# Verify key packages are installed
python -c "import torch; import librosa; import numpy; import yaml; print('All dependencies installed successfully!')"
```

## Step 7: Test the Installation

```bash
# Test main script
python main.py --help

# Test evaluation script
python eval.py --help

# Check available models and configurations
cat model_config_RawNet.yaml
```

## Step 8: Prepare for Model Training/Evaluation

```bash
# Create directories for models and data (if needed)
mkdir -p models
mkdir -p data
mkdir -p results

# Set proper permissions
chmod +x main.py
chmod +x eval.py
```

## Usage Examples

### Training the Model
```bash
# Activate environment (if not already active)
source venv/bin/activate

# Train model with custom parameters
python main.py \
    --data_path /path/to/your/audio/data \
    --model_save_path ./models/rawnet_model.pth \
    --batch_size 32 \
    --num_epochs 100 \
    --lr 0.001 \
    --weight_decay 0.0001
```

### Evaluating Audio Files
```bash
# Activate environment (if not already active)
source venv/bin/activate

# Evaluate a single audio file
python eval.py \
    --input_path /path/to/audio/file.wav \
    --model_path ./models/rawnet_model.pth
```

## Troubleshooting

### If you encounter permission issues:
```bash
sudo chown -R $USER:$USER LibriSeVoc
```

### If Python 3.12 is not available:
```bash
# Use Python 3.8+ as fallback
sudo apt install -y python3.8 python3.8-venv python3.8-dev
python3.8 -m venv venv
```

### If audio libraries fail to install:
```bash
# Install additional audio codecs
sudo apt install -y ubuntu-restricted-extras
sudo apt install -y libavcodec-extra
```

### If PyTorch installation fails:
```bash
# Install PyTorch CPU version explicitly
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 10GB free space
- **CPU**: Multi-core processor recommended for training
- **GPU**: Optional, will use CPU by default

## Security Notes

- Always run the application in a virtual environment
- Don't run training scripts as root
- Ensure proper file permissions for audio data
- Consider using tmux or screen for long-running training sessions

## Complete Setup Script

For convenience, here's a complete setup script you can run:

```bash
#!/bin/bash
set -e

echo "🚀 Setting up LibriSeVoc on Ubuntu..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y curl wget git build-essential software-properties-common

# Install Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Install system dependencies
sudo apt install -y \
    libsndfile1-dev libfftw3-dev libasound2-dev portaudio19-dev \
    libportaudio2 libportaudiocpp0 ffmpeg sox libsox-fmt-all \
    libblas3 liblapack3 liblapack-dev libblas-dev gfortran \
    libhdf5-serial-dev pkg-config

# Clone repository
git clone https://github.com/vladasanadev/LibriSeVoc.git
cd LibriSeVoc

# Setup virtual environment
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Test installation
python -c "import torch; import librosa; import numpy; import yaml; print('✅ Setup completed successfully!')"

echo "🎉 LibriSeVoc is ready to use!"
echo "To activate: source venv/bin/activate"
echo "To train: python main.py --help"
echo "To evaluate: python eval.py --help"
```

Save this as `setup.sh`, make it executable with `chmod +x setup.sh`, and run with `./setup.sh`.
