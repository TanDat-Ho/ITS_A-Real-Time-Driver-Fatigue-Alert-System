# Contributing to Driver Fatigue Detection System

First off, thank you for considering contributing to our Driver Fatigue Detection System! 🎉 It's people like you that make this project a great tool for safer driving.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together and help each other
- **Be inclusive**: Welcome newcomers and different perspectives
- **Be patient**: Not everyone has the same level of experience

## 🚀 Getting Started

### Prerequisites

Before contributing, make sure you have:

- **Python 3.8-3.11** installed
- **Git** for version control
- A **webcam** for testing (optional but recommended)
- Basic knowledge of **computer vision** concepts (helpful but not required)

### Development Setup

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/driver-fatigue-detection.git
   cd driver-fatigue-detection
   ```

3. **Set up the development environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate it
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate # Linux/macOS
   
   # Install dependencies
   pip install -r requirements-dev.txt
   ```

4. **Run tests to verify setup**
   ```bash
   python -m pytest tests/
   ```

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed information**: OS, Python version, steps to reproduce
4. **Add logs and screenshots** if applicable

### ✨ Suggesting Features

1. **Check the roadmap** and existing feature requests
2. **Use the feature request template**
3. **Explain the use case** and why it would be valuable
4. **Consider implementation complexity**

### 💻 Code Contributions

We welcome contributions in these areas:

#### 🔥 High Priority
- **Algorithm improvements**: Better EAR/MAR calculations
- **Performance optimization**: Faster processing, lower CPU usage
- **Cross-platform compatibility**: macOS and Linux support
- **False positive reduction**: Smarter detection logic

#### 🎯 Medium Priority
- **UI/UX improvements**: Better user interface
- **Configuration options**: More customizable settings
- **Documentation**: Code comments, user guides
- **Testing**: Unit tests, integration tests

#### 🌟 Nice to Have
- **New alert types**: Different notification methods
- **Multi-language support**: Internationalization
- **Analytics**: Usage statistics and reporting
- **Accessibility features**: Better accessibility support

## 🛠️ Development Setup

### Project Structure

```
src/
├── input_layer/          # Camera handling, input validation
├── processing_layer/     # Core detection algorithms
├── output_layer/         # Alerts, UI, logging
└── app/                  # Main application
```

### Key Components

- **EAR Algorithm**: `src/processing_layer/detect_rules/eye_rules.py`
- **MAR Algorithm**: `src/processing_layer/detect_rules/mouth_rules.py`
- **Head Pose**: `src/processing_layer/detect_rules/head_rules.py`
- **Alert System**: `src/output_layer/alert_module.py`
- **Main UI**: `src/output_layer/ui/main_window.py`

### Running the Application

```bash
# Development mode
python launcher.py

# With debug logging
python launcher.py --debug

# Specific configuration
python launcher.py --config config/sensitive.json
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_detection_rules.py

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run performance tests
python -m pytest tests/test_performance.py -v
```

### Building

```bash
# Windows
.\build-windows.ps1

# Linux/macOS
./build-linux.sh

# All platforms
.\build-all.ps1
```

## 📝 Pull Request Process

### Before Submitting

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our style guidelines

3. **Add/update tests** for new functionality

4. **Update documentation** if needed

5. **Run the test suite**
   ```bash
   python -m pytest tests/
   ```

6. **Test manually** with different scenarios

### Submitting

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** using our template

3. **Respond to feedback** and make necessary changes

4. **Wait for review** from maintainers

### PR Requirements

- ✅ **All tests pass**
- ✅ **Code follows style guidelines**
- ✅ **Documentation is updated**
- ✅ **No merge conflicts**
- ✅ **Descriptive commit messages**

## 🎨 Style Guidelines

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# Use descriptive variable names
ear_threshold = 0.25  # Good
t = 0.25             # Bad

# Add type hints
def calculate_ear(landmarks: List[Tuple[int, int]]) -> float:
    pass

# Use docstrings for functions
def detect_fatigue(frame: np.ndarray) -> bool:
    """
    Detect fatigue signs in the given frame.
    
    Args:
        frame: Input video frame as numpy array
        
    Returns:
        True if fatigue detected, False otherwise
    """
    pass
```

### Code Formatting

We use **Black** for code formatting:

```bash
# Format code
black src/

# Check formatting
black --check src/
```

### Commit Messages

Use conventional commit format:

```
type(scope): description

feat(detection): add head pose estimation
fix(ui): resolve alert dialog positioning issue
docs(readme): update installation instructions
test(ear): add edge case tests for EAR calculation
```

### Documentation

- **Code comments**: Explain complex algorithms
- **Docstrings**: Document all public functions
- **README updates**: Keep documentation current
- **Type hints**: Use for better code clarity

## 🧪 Testing Guidelines

### Test Types

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Verify FPS and resource usage
4. **Manual Tests**: Real-world scenarios

### Writing Tests

```python
import pytest
from src.processing_layer.detect_rules.eye_rules import calculate_ear

def test_ear_calculation():
    """Test EAR calculation with known landmark points."""
    # Test data
    landmarks = [(0, 0), (10, 5), (20, 0), (30, 5), (40, 0), (50, 5)]
    
    # Expected result
    expected_ear = 0.5
    
    # Test
    actual_ear = calculate_ear(landmarks)
    
    # Assert
    assert abs(actual_ear - expected_ear) < 0.01
```

### Test Data

- Use synthetic test data when possible
- Include edge cases and error conditions
- Mock external dependencies (camera, file system)

## 🌟 Recognition

Contributors will be recognized in:

- **README.md**: Contributors section
- **Release notes**: Feature credits
- **GitHub**: Automatic contributor recognition
- **Documentation**: Author attribution

## 💬 Community

### Getting Help

- **GitHub Discussions**: Ask questions and share ideas
- **Issues**: Report bugs and request features
- **Discord** (coming soon): Real-time chat with developers

### Maintainers

- **Core Team**: Reviews and merges PRs
- **Community Leaders**: Help with support and guidance
- **Special Contributors**: Domain experts and heavy contributors

## 📧 Contact

Have questions? Reach out to us:

- **Email**: maintainers@driver-fatigue-detection.com
- **GitHub**: Create an issue or discussion
- **Social Media**: Follow us for updates

---

Thank you for contributing to make driving safer for everyone! 🚗💙