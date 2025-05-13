# Delivery Platform Test Suite

This directory contains comprehensive tests for the Delivery Platform API.

## Test Structure

The tests are organized as follows:

- `test_users.py`: Tests for user registration, authentication, and profile management
- `test_integration.py`: End-to-end integration tests covering complete order flows

## Running Tests

To run the tests, use the following command:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run with verbose output
pytest -v

# Run a specific test
pytest tests/test_users.py::TestUserRegistration::test_customer_registration

# Run tests by marker
pytest -m unit
pytest -m integration
```

## Test Categories

### User Tests

These tests cover:
- User registration for all types (customer, driver, restaurant)
- Login and JWT token issuance
- Profile retrieval and updates
- Password change functionality
- Role-based access control

### Integration Tests

These tests cover complete flows through the system:
- Customer: Browse restaurants, place orders, track status
- Restaurant: Accept/reject orders, update preparation status
- Driver: Manage availability, accept tasks, update delivery status, track earnings

## Test Fixtures

The tests use fixtures to set up test data:
- `create_users`: Creates a set of test users (customer, driver, restaurant, admin)
- `setup_restaurant`: Creates a restaurant with menu categories and items
- `setup_driver`: Sets up a driver with availability and location
- `auth_client`: Helper to get an authenticated API client for a user

## Adding New Tests

When adding new tests:
1. Use the existing fixtures where possible
2. Follow the naming convention: `test_<functionality>.py`
3. Group related tests in classes
4. Use descriptive test method names
5. Add appropriate assertions for both status codes and response content