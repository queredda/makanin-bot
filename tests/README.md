# Test Suite for Makanin Bot

This directory contains the test suite for the Makanin bot system.

## Test Structure

```
tests/
├── __init__.py
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_agent.py             # Agent core functionality
│   ├── test_nlu_tool.py          # NLU tool tests
│   ├── test_conversation_tool.py # Conversation tool tests
│   ├── test_tools.py             # Base tool system tests
│   ├── test_memory.py            # Memory and context tests
│   └── test_place_extraction.py  # Place extraction tests
├── functional/                   # Functional/integration tests
│   ├── __init__.py
│   ├── test_agent_integration.py # End-to-end agent tests
│   └── test_tool_integration.py  # Tool integration tests
└── README.md                     # This file
```

## Running Tests

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Unit Tests Only

```bash
python -m pytest tests/unit/ -v
```

### Run Functional Tests Only

```bash
python -m pytest tests/functional/ -v
```

### Run Specific Test File

```bash
python -m pytest tests/unit/test_agent.py -v
```

### Run with Coverage

```bash
python -m pytest tests/ --cov=agent --cov=tools --cov-report=html
```

### Run Specific Test Class

```bash
python -m pytest tests/unit/test_nlu_tool.py::TestNLUTool -v
```

### Run Specific Test Method

```bash
python -m pytest tests/unit/test_nlu_tool.py::TestNLUTool::test_detect_language_indonesian -v
```

## Test Coverage

The test suite covers:

### Unit Tests (6 test files)

1. **Agent Tests** (`test_agent.py`)
    - Agent initialization
    - Error handling (Indonesian/English)
    - Tool status management
    - Plan creation

2. **NLU Tool Tests** (`test_nlu_tool.py`)
    - Language detection
    - Input validation
    - Gemini API integration
    - Fallback handling

3. **Conversation Tool Tests** (`test_conversation_tool.py`)
    - Input validation
    - Conversation history handling
    - Multi-language support

4. **Base Tool System Tests** (`test_tools.py`)
    - Tool registration and execution
    - Input validation
    - Error handling
    - Execution history tracking

5. **Memory/Context Tests** (`test_memory.py`)
    - Session management
    - Conversation history
    - User preferences
    - Data cleanup

6. **Place Extraction Tests** (`test_place_extraction.py`)
    - Place name extraction
    - Hashtag processing
    - Text cleaning
    - Gemini API integration

### Functional Tests (2 test files)

1. **Agent Integration Tests** (`test_agent_integration.py`)
    - End-to-end message processing
    - Food search workflows
    - Conversation handling
    - Multi-language support
    - Error scenarios

2. **Tool Integration Tests** (`test_tool_integration.py`)
    - Cross-tool workflows
    - Tool orchestration
    - Error handling across tools
    - Performance tracking

## Test Dependencies

Tests require these additional packages:

```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

## Mock Strategy

The tests use extensive mocking to avoid dependencies on:

- External APIs (Gemini, TikTok, Google Maps)
- Redis database
- Network connections

All external services are mocked using `unittest.mock`.

## Test Data

Tests use predefined test data:

- Sample user messages in Indonesian and English
- Mock API responses
- Example tool outputs
- Test session data

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    python -m pytest tests/ --cov=agent --cov=tools --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Mocking**: External dependencies are always mocked
3. **Coverage**: Aim for >80% code coverage
4. **Fast**: Tests run quickly without network calls
5. **Clear**: Test names describe what they test
6. **Maintainable**: Tests are easy to understand and modify

## Adding New Tests

When adding new functionality:

1. Create unit tests for individual components
2. Add functional tests for integration scenarios
3. Mock all external dependencies
4. Test both success and failure cases
5. Include edge cases and error conditions
6. Update this README

## Debugging Failed Tests

### Run with verbose output:

```bash
python -m pytest tests/ -v -s
```

### Run with debugging:

```bash
python -m pytest tests/ --pdb
```

### Run specific failing test:

```bash
python -m pytest tests/unit/test_agent.py::TestMakaninAgent::test_agent_initialization -v -s
```