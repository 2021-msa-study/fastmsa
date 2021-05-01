import uuid


def random_suffix() -> str:
    """랜덤 ID뒤에 붙일 UUID 기반의 6자리 임의의 ID를 생성합니다."""
    return uuid.uuid4().hex[:6]


def random_sku(name: str = "") -> str:
    """임의의 SKU를 생성합니다."""
    return f"sku-{name}-{random_suffix()}"


def random_batchref(num: int = 1) -> str:
    """임의의 Batch reference를 생성합니다."""
    return f"batch-{num}-{random_suffix()}"


def random_orderid(name: str = "") -> str:
    """임의의 order_id 를 생성합니다."""
    return f"order-{name}-{random_suffix()}"
