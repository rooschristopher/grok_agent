# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- 

## [0.1.0] - 2024-10-01
### Added
- Autonomous Agent with list_dir, read_file, write_file, run_shell tools
- Unit tests for all tools with pytest
- Project setup: .gitignore, pyproject.toml, tests dir
- README.md with installation and usage
- Ticket system in tickets/ with TDD workflow
- Logging setup
- Ruff linting config

### Changed
- Efficient write_file append using open('a')

### Tests
- Full coverage for tools
- Project setup tests- Added `web_search` tool using Serper.dev API for web research with snippets and source links (008-add-web-search-tool).