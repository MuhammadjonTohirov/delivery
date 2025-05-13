import pytest
from django.db.models.signals import post_save
from users.models import CustomUser

# Helper to manually disconnect and reconnect signals
@pytest.fixture
def disconnect_signals():
    """Temporarily disconnect post_save signals for testing."""
    # Store registered signal receivers
    receivers = []
    for receiver in post_save.receivers:
        if post_save.receivers[receiver][1].__module__.startswith('users'):
            receivers.append((receiver, post_save.receivers[receiver]))
    
    # Disconnect signals
    for receiver, _ in receivers:
        post_save.receivers.pop(receiver)
    
    yield
    
    # Reconnect signals after test
    for receiver, receiver_data in receivers:
        post_save.receivers[receiver] = receiver_data