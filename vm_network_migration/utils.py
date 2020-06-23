import time
def generate_timestamp_string() -> str:
    """Generate the current timestamp.

    Returns: current timestamp string

    """
    return str(time.strftime("%s", time.gmtime()))