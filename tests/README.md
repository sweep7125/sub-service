# Test Suite for Web-Panel

Comprehensive test suite for the VPN/Proxy configuration management system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── test_models.py           # Tests for User and Server models
├── test_repositories.py     # Tests for data access layer
├── test_services.py         # Tests for business logic layer
├── test_builders.py         # Tests for configuration builders
├── test_utils.py            # Tests for utility functions
└── test_web_integration.py  # Integration tests for web endpoints
```

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_models.py
pytest tests/test_repositories.py
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow
```

### Verbose Output

```bash
pytest -v
```

### Stop on First Failure

```bash
pytest -x
```

## Test Coverage

The test suite covers:

- **Models** (`test_models.py`)
  - UserInfo model creation, methods, and immutability
  - Server model creation, properties, and immutability
  - Group-based access control logic

- **Repositories** (`test_repositories.py`)
  - UserRepository: Loading users from files, parsing, prefix matching
  - ServerRepository: Loading servers, parsing, type detection
  - File caching and error handling

- **Services** (`test_services.py`)
  - ConfigService: Initialization, server/user retrieval, config building
  - ServerFilterService: Group-based filtering, access control
  - GeoFileService: Timestamp management, routing headers

- **Builders** (`test_builders.py`)
  - MihomoBuilder: YAML generation, template substitution, filtering
  - V2RayBuilder: Subscription links, spider-x generation, URL encoding
  - LegacyJsonBuilder: JSON configuration generation

- **Utilities** (`test_utils.py`)
  - SpiderXGenerator: Path generation, uniqueness, collision avoidance
  - FileCache: Caching, invalidation, thread safety
  - Text utilities: Unicode decoding, escape sequences
  - Network utilities: IP extraction from headers

- **Web Integration** (`test_web_integration.py`)
  - Flask app creation and configuration
  - Security middleware (localhost/HTTPS checks)
  - Route handling for different config formats
  - User authentication and authorization
  - Error handling (404, 403, 503)

## Fixtures

### Common Fixtures (conftest.py)

- `temp_dir`: Temporary directory for test files
- `sample_users_file`: Sample users configuration file
- `sample_servers_file`: Sample servers configuration file
- `sample_v2ray_template`: V2Ray URL template
- `sample_mihomo_template`: Mihomo YAML template
- `sample_v2ray_json_template`: V2Ray JSON template
- `app_config`: Complete AppConfig for testing
- `sample_user`: Sample UserInfo instance
- `sample_server`: Sample Server instance
- `spiderx_generator`: SpiderXGenerator instance
- `multiple_servers`: List of servers with different configurations

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test

```python
def test_user_has_access_to_server(sample_user, sample_server):
    """Test that user with matching group has access to server."""
    # Arrange
    user = sample_user  # Has 'premium' group
    server = sample_server  # Has 'premium' group
    
    # Act
    has_access = user.has_access_to_groups(server.groups)
    
    # Assert
    assert has_access is True
```

### Using Fixtures

```python
def test_config_generation(app_config: AppConfig):
    """Test using app_config fixture."""
    service = ConfigService(app_config)
    servers = service.get_servers()
    assert len(servers) > 0
```

## Continuous Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

Make sure you're running tests from the project root:

```bash
cd e:\web-panel
pytest
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Cache Issues

Clear pytest cache:

```bash
pytest --cache-clear
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Use descriptive test names and docstrings
3. **Coverage**: Aim for >80% code coverage
4. **Speed**: Keep tests fast; mock external dependencies
5. **Fixtures**: Reuse fixtures to avoid duplication
6. **Assertions**: Use specific assertions with clear messages
7. **Arrange-Act-Assert**: Follow AAA pattern for test structure
