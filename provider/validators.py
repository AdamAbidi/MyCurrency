def validate_priority(priority: str) -> int:
    # Validate priority value
    try:
        new_priority = int(priority)
    except ValueError:
        # Raise an error if priority is missing or not an integer
        raise ValueError("Priority must be an integer.")

    # Check the new priority is greater or equal to 0
    if new_priority < 0:
        raise ValueError("Priority must be greater or equal than 0.")

    return new_priority