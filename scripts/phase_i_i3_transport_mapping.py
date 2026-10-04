"""Explicit I3 research-runner identity to reviewed transport-key boundary."""

CANONICAL_TO_TRANSPORT_MARKET = {"TWSE": "TWSE", "TPEX": "TPEx"}


def transport_market_key(canonical_market: str) -> str:
    if type(canonical_market) is not str or canonical_market not in CANONICAL_TO_TRANSPORT_MARKET:
        raise ValueError("unsupported_canonical_market")
    return CANONICAL_TO_TRANSPORT_MARKET[canonical_market]
