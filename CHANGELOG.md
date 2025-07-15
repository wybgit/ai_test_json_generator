# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-15

### Added
- Initial release of AI JSON Generator
- Template-based generation with variable substitution
- Support for file-based replacement values
- JSON validation and automatic retry for malformed responses
- Detailed error feedback for invalid JSON
- Debug mode for saving prompts and responses
- Configurable LLM backend
- Detailed logging of generation process
- Command-line tools for generation: `ai-json-generate` and `ai-json-operator`

### Changed
- Restructured project as a Python package
- Improved resource file discovery with pkg_resources
- Better error handling and validation
- Enhanced command-line interface with more options

### Fixed
- Resource path resolution when installed as package
- JSON extraction algorithm improvements 