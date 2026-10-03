def decode_signed_tdoa(raw_tdoa, bits=41):
    """Decode a two's-complement field. Width is configured, never inferred silently."""
    if not isinstance(bits, int) or not 2 <= bits <= 64:
        raise ValueError("TDoA width must be an integer between 2 and 64.")
    value = int(raw_tdoa)
    if not -(1 << (bits - 1)) <= value < (1 << bits):
        raise ValueError(f"TDoA value {value} does not fit {bits} bits.")
    return value - (1 << bits) if value >= (1 << (bits - 1)) else value
