# Contributing to Transcribe-Summarize 🎤📝

Thank you for your interest in contributing to Transcribe-Summarize! We welcome contributions from developers of all skill levels. This document provides guidelines and steps for contributing.

## Getting Started 🚀

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/transcribe-summarize.git
   cd transcribe-summarize
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Environment 💻

### Prerequisites
- Python 3.8+
- ffmpeg
- OpenAI API key

### Setting Up
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Set up your OpenAI API key:
   ```bash
   echo "OPENAI_API_KEY=your-key-here" > .env
   ```

## Making Changes 🛠️

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests:
   ```bash
   pytest
   ```
4. Update documentation if needed
5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add your clear commit message"
   ```

## Code Style 📋

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Testing 🧪

- Write tests for new features
- Update existing tests when modifying features
- Ensure all tests pass before submitting
- Run tests with:
  ```bash
  pytest
  ```

## Documentation 📚

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update example code if needed
- Keep documentation clear and concise

## Submitting Changes 📤

1. Push your changes:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Create a Pull Request
3. Fill in the PR template
4. Wait for review

## Pull Request Guidelines ✅

- Keep PRs focused on a single feature/fix
- Include tests for new features
- Update documentation
- Explain your changes clearly
- Reference related issues
- Follow the PR template

## Getting Help 🤝

- Create an issue for bug reports
- Ask questions in Discussions
- Join our community chat

## Code of Conduct 🤝

Please note that this project follows a Code of Conduct. By participating, you agree to uphold this code.

## License 📄

By contributing, you agree that your contributions will be licensed under the MIT License.