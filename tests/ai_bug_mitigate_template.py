import pytest
from hypothesis import given, strategies as st
from typing import Dict, Any

"""
This production-ready pytest script implements Property-Based Testing via hypothesis alongside structured Negative Testing 
and Boundary Value Assertions to smoke out logic errors common to AI reviews.
"""
# =====================================================================
# Target Functions (Simulating AI-generated code with hidden bugs)
# =====================================================================

def calculate_tier_discount(item_count: int, base_price: float) -> float:
    """AI-generated calculation containing hidden boundary flaws."""
    if item_count <= 0 or base_price <= 0:
        raise ValueError("Inputs must be strictly positive numeric values.")

    if item_count > 100:
        return base_price * 0.20  # AI bug: returns discount value instead of final price
    elif item_count >= 10:
        return base_price * 0.90
    return base_price


def process_user_payload(payload: Dict[str, Any]) -> str:
    """AI-generated transaction engine prone to missing key exceptions."""
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary structural layout.")

    user_id = payload.get("user_id")
    role = payload.get("role", "guest")

    if not user_id:
        raise ValueError("Missing critical identification string: user_id")

    return f"User {user_id} parsed successfully as status: {role}"


# =====================================================================
# Automated Test Suite for AI Defect Mitigation
# =====================================================================

# 1. Property-Based Testing (Flooding boundaries with randomized inputs)
@given(
    item_count=st.integers(min_value=1, max_value=1000),
    base_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_discount_properties(item_count, base_price):
    result = calculate_tier_discount(item_count, base_price)

    # Structural assertion: Final price must never exceed the initial baseline cost
    assert result <= base_price, f"AI Logic Failure: Price expanded from {base_price} to {result}"
    assert result > 0


# 2. Negative Integration Testing (Enforcing resilience against unmapped fields)
@pytest.mark.parametrize("malformed_input", [
    None,
    [],
    "string_instead_of_dict",
    {"role": "admin"}  # Missing critical user_id field
])
def test_payload_negative_scenarios(malformed_input):
    with pytest.raises((ValueError, TypeError)):
        process_user_payload(malformed_input)


# 3. Boundary Value Assertions (Verifying strict limits)
def test_strict_boundaries():
    with pytest.raises(ValueError):
        calculate_tier_discount(0, 100.0)
    with pytest.raises(ValueError):
        calculate_tier_discount(5, -10.50)
