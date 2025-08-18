Custom Test Runner for Parallel/Serial Execution
==============================================

The `ChannelsParallelTestRunner` is a custom Django test runner that intelligently separates test execution based on test case types when running tests with the `--parallel` flag.

## Overview

When running tests with `--parallel`, this runner:

1. **First runs regular tests in parallel** - All test cases that don't inherit from WebSocket-related test classes
2. **Then runs WebSocket tests serially** - Test cases that inherit from `ChannelsLiveServerTestCase` or `StaticLiveServerTestCase`

This approach solves common issues with WebSocket and Selenium tests that can have port conflicts and connection issues when run in parallel.

## Detected WebSocket Test Classes

The runner automatically detects and runs serially:

- `channels.testing.ChannelsLiveServerTestCase` - Django Channels WebSocket tests
- `django.contrib.staticfiles.testing.StaticLiveServerTestCase` - Selenium/browser tests

## Usage

The runner is automatically used when the `TEST_RUNNER` setting points to `openwisp_utils.metric_collection.tests.runner.MockRequestPostRunner`.

### Running tests normally (serial)
```bash
python manage.py test
```

### Running tests with parallel execution
```bash
python manage.py test --parallel
# or with specific number of processes
python manage.py test --parallel 4
```

### Behavior differences

**Without `--parallel`:**
- All tests run serially in the order discovered
- No special handling of WebSocket tests

**With `--parallel`:**
- Regular tests run in parallel first (e.g., model tests, API tests, admin tests)
- WebSocket/Selenium tests run serially after regular tests complete
- Maintains test isolation and prevents port conflicts

## Example Output

```
Found 100 test(s).
Running 85 regular tests in parallel...
...
Running 15 WebSocket/Selenium tests serially...
...
```

## Technical Details

The runner works by:

1. **Test Detection**: Inspects each test case class to determine if it inherits from WebSocket-related base classes
2. **Suite Splitting**: Separates the discovered test suite into two groups
3. **Sequential Execution**: Runs regular tests in parallel first, then WebSocket tests serially
4. **Result Merging**: Combines results from both execution phases

## Benefits

- **Improved Reliability**: Prevents port conflicts and race conditions in WebSocket tests
- **Faster Execution**: Regular tests still benefit from parallel execution
- **Backward Compatibility**: Works with existing test infrastructure
- **Automatic Detection**: No manual test tagging required