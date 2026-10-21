import re
def norm(t):
    """Lowercase letters and digits only, so punctuation and spacing differences still count as the same joke."""
    return re.sub(r"[^a-z0-9]+", "", t.lower())
