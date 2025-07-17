# Qwen3-8B Special Token Training

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive toolkit for enhancing Qwen3-8B model with special debugging tokens `<|AGENT|>` and `<|EDIT|>` through fine-tuning on real programming problems.

## 🎯 Overview

This project extends the Qwen3-8B language model with specialized tokens for code debugging and editing tasks. By training on 128 real programming problems from HuggingFace's LiveCodeBench dataset, the model learns to use special tokens for intelligent code analysis and direct code fixes.

### Special Tokens

- **`<|AGENT|>`** - Triggers exploratory debugging mode for complex analysis
- **`<|EDIT|>`** - Triggers direct fix mode when specific error information is available

## ✨ Features

- 🔧 **Tokenizer Enhancement**: Seamlessly integrates special tokens into Qwen3-8B tokenizer
- 📊 **Real Dataset**: Utilizes 128 programming problems from `livecodebench/code_generation_lite`
- 🤖 **AI-Powered Generation**: Uses GPT-4.1 via ChatAnywhere API for diverse training data
- 🔄 **Multi-threaded Processing**: High-performance data generation with 32 concurrent threads
- ✅ **Quality Validation**: Comprehensive data validation and quality reporting
- 📁 **Organized Output**: Clean directory structure for different output types
- 🚀 **Easy Training**: One-command training pipeline with monitoring

## 🗃️ Dataset

The project uses **128 programming problems** from HuggingFace's [`livecodebench/code_generation_lite`](https://huggingface.co/datasets/livecodebench/code_generation_lite) dataset. These problems cover:

- Algorithm implementation
- Data structure manipulation  
- Mathematical computations
- String processing
- Edge case handling

## 🚀 Quick Start

### Prerequisites

```bash
# Required Python packages
pip install transformers torch openai pandas pathlib
```

### API Configuration

```bash
# Set your ChatAnywhere API key
export OPENAI_API_KEY="your-chatanywhere-api-key"
```

### Basic Usage

1. **Integrate Special Tokens**
   ```bash
   python hw3_1.py  # Adds special tokens to tokenizer
   ```

2. **Generate Training Data**
   ```bash
   # Small-scale test (10 samples)
   ./script/test_small.sh
   
   # Full training data (128 samples)
   ./script/run_full.sh
   ```

3. **Validate Data Quality**
   ```bash
   python batch_validator.py outputs/training_data/training_data_full_128.json
   ```

4. **Train the Model**
   ```bash
   ./script/run_train.sh
   ```

## 📋 Detailed Usage

### Token Integration

```bash
# Step 1: Add special tokens to Qwen3-8B tokenizer
python hw3_1.py

# Step 2: Design system prompts for special token usage
python hw3_2.py
```

### Training Data Generation

```bash
# Generate training data with custom parameters
python data_constructor.py \
    --samples 500 \
    --threads 32 \
    --output outputs/training_data/custom_data.json

# Parameters:
# --samples: Number of training samples (default: 100)
# --threads: Concurrent threads (default: 32) 
# --output: Output file path (default: outputs/training_data/training_data_from_parquet.json)
```

### Data Validation

```bash
# Validate and filter training data
python batch_validator.py outputs/training_data/your_data.json

# Check specific task outputs
python output_checker.py outputs/tasks/hw3_2.json
```

## 🎓 Training Pipeline

### Training Script

The training process is managed by `script/run_train.sh`:

```bash
./script/run_train.sh
```

**Training Objectives:**
- **Token Integration**: Ensure special tokens are properly recognized
- **Token Reinforcement**: Strengthen the model's ability to use special tokens appropriately
- **Contextual Understanding**: Train the model to choose between `<|AGENT|>` and `<|EDIT|>` modes
- **Output Format**: Maintain consistent output formatting with special tokens

### Training Logs

Training progress and metrics are saved in the `training_log/` directory:
- Loss curves
- Token usage statistics  
- Validation metrics
- Training hyperparameters

## 📁 Project Structure

```
qwen3-special-token-training/
├── 📄 README.md                     # Project documentation
├── 🔧 hw3_1.py                      # Special token integration
├── 🔧 hw3_2.py                      # System prompt design
├── 📊 data_constructor.py            # Training data generator
├── ✅ batch_validator.py             # Data quality validator
├── 🔍 output_checker.py             # Output format checker
├── 📁 data/                         # Input datasets
│   └── test-00000-of-00001.parquet  # LiveCodeBench problems
├── 📁 script/                       # Execution scripts
│   ├── test_small.sh               # Small-scale testing
│   ├── run_full.sh                 # Full data generation
│   ├── run_train.sh                # Model training
│   └── README.md                   # Script documentation
├── 📁 outputs/                      # Generated outputs
│   ├── tasks/                      # Task-specific outputs
│   ├── training_data/              # Training datasets
│   ├── reports/                    # Quality reports
│   └── validation/                 # Validation results
├── 📁 tokenizer_with_special_tokens/ # Enhanced tokenizer
├── 📁 training_log/                 # Training logs and metrics
├── 📄 query_and_output.json        # Sample input data
├── 📄 query_only.json              # Query-only samples
└── 📄 .gitignore                   # Git ignore rules
```

## 🔧 Configuration

### API Settings

The project uses **ChatAnywhere** as the OpenAI API proxy for stable access:

```bash
# API Configuration (automatically handled)
BASE_URL: https://api.chatanywhere.tech/v1
MODEL: gpt-4.1
```

### Performance Tuning

```bash
# High-performance configuration (recommended)
--threads 32        # Optimal for most systems
--samples 128       # Full dataset utilization

# Conservative configuration (limited API quota)
--threads 16        # Reduced API pressure  
--samples 50        # Smaller dataset
```

## 📊 Data Quality

### Validation Metrics

- **Format Compliance**: Ensures proper special token usage
- **Content Quality**: Validates meaningful code problems and solutions
- **Token Distribution**: Monitors balanced usage of `<|AGENT|>` vs `<|EDIT|>`
- **Alpaca Compatibility**: Verifies training data format standards

### Output Examples

**Agent Mode (Debugging Analysis):**
```json
{
  "instruction": "This code isn't working as expected. Can you help debug it?",
  "output": "<think>No specific error provided, need exploratory analysis</think>\n<|AGENT|>\nI'll analyze this code step by step..."
}
```

**Edit Mode (Direct Fix):**
```json
{
  "instruction": "Fix this IndexError in my Python function.",
  "output": "<think>Specific error provided, can directly fix</think>\n<|EDIT|>\nI'll fix the IndexError by updating the boundary check..."
}
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/qwen3-special-token-training.git
cd qwen3-special-token-training

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## 📈 Performance Metrics

### Training Performance
- **Data Generation**: ~5-15 minutes for 128 samples (32 threads)
- **Token Integration**: <1 minute
- **Validation**: <5 minutes for full dataset

### Quality Metrics
- **Valid Data Rate**: >95% (with proper API configuration)
- **Token Balance**: ~50% AGENT / 50% EDIT distribution
- **Format Compliance**: 100% (with validation pipeline)

## 🐛 Troubleshooting

### Common Issues

**API Rate Limits:**
```bash
# Reduce thread count
python data_constructor.py --threads 16
```

**Invalid Data Generation:**
```bash
# Check validation report
python batch_validator.py your_data.json
```

**Training Issues:**
```bash
# Check training logs
tail -f training_log/latest.log
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Qwen3-8B](https://github.com/QwenLM/Qwen) - Base language model
- [LiveCodeBench](https://huggingface.co/datasets/livecodebench/code_generation_lite) - Programming problems dataset
- [ChatAnywhere](https://chatanywhere.tech/) - Stable OpenAI API proxy
- [Transformers](https://huggingface.co/transformers/) - Model handling framework

## 📞 Support

- 📧 Create an issue for bug reports
- 💬 Start a discussion for questions
- 📖 Check the documentation in `outputs/README.md`

---

**⭐ Star this repository if it helps your research!** 