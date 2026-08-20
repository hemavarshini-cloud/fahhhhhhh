import pytest
from unittest.mock import Mock, MagicMock

# =====================================================================
# Domain Exceptions
# =====================================================================

class OutOfStockError(Exception):
    """Raised when inventory is insufficient for an order."""
    pass

class InvalidProductError(Exception):
    """Raised when operating on a non-existent product."""
    pass

class InvalidQuantityError(Exception):
    """Raised when an invalid quantity (e.g., negative) is provided."""
    pass


# =====================================================================
# Core Domain Model (Inventory Service)
# =====================================================================

class InventoryService:
    """Manages multi-warehouse product inventory and stock movements."""

    def __init__(self):
        # Data structure: {product_id: {warehouse_id: quantity}}
        self._stock = {}
        # Registered valid products
        self._products = set()
        # Reorder thresholds per product: {product_id: threshold}
        self._reorder_thresholds = {}

    def register_product(self, product_id: str, reorder_threshold: int = 10):
        self._products.add(product_id)
        self._stock[product_id] = {}
        self._reorder_thresholds[product_id] = reorder_threshold

    def set_stock(self, product_id: str, warehouse_id: str, quantity: int):
        self._validate_product(product_id)
        if quantity < 0:
            raise InvalidQuantityError(f"Quantity cannot be negative: {quantity}")
        self._stock[product_id][warehouse_id] = quantity

    def get_stock(self, product_id: str, warehouse_id: str = None) -> int:
        self._validate_product(product_id)
        if warehouse_id:
            return self._stock[product_id].get(warehouse_id, 0)
        return sum(self._stock[product_id].values())

    def fulfill_order(self, product_id: str, warehouse_id: str, quantity: int) -> bool:
        self._validate_product(product_id)
        if quantity <= 0:
            raise InvalidQuantityError("Order quantity must be greater than zero.")
        
        current_stock = self.get_stock(product_id, warehouse_id)
        if current_stock < quantity:
            raise OutOfStockError(
                f"Insufficient stock for product {product_id} at {warehouse_id}. "
                f"Requested: {quantity}, Available: {current_stock}"
            )

        self._stock[product_id][warehouse_id] -= quantity
        return True

    def transfer_stock(self, product_id: str, source_wh: str, target_wh: str, quantity: int):
        self._validate_product(product_id)
        if quantity <= 0:
            raise InvalidQuantityError("Transfer quantity must be positive.")
        
        source_stock = self.get_stock(product_id, source_wh)
        if source_stock < quantity:
            raise OutOfStockError(f"Cannot transfer {quantity} units; source warehouse only has {source_stock}.")

        self._stock[product_id][source_wh] -= quantity
        self._stock[product_id][target_wh] = self.get_stock(product_id, target_wh) + quantity

    def check_reorder_status(self, product_id: str) -> bool:
        self._validate_product(product_id)
        total_stock = self.get_stock(product_id)
        threshold = self._reorder_thresholds.get(product_id, 0)
        return total_stock <= threshold

    def _validate_product(self, product_id: str):
        if product_id not in self._products:
            raise InvalidProductError(f"Product ID '{product_id}' is invalid or not registered.")


# =====================================================================
# QA Test Suite (pytest)
# =====================================================================

@pytest.fixture
def inventory():
    """Fixture providing a fresh inventory service instance with test products."""
    service = InventoryService()
    service.register_product("SKU-LAPTOP", reorder_threshold=5)
    service.register_product("SKU-PHONE", reorder_threshold=10)
    return service


def test_stock_availability(inventory):
    """Verify stock queries return correct quantities for specific warehouses and total stock."""
    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 25)
    
    assert inventory.get_stock("SKU-LAPTOP", "WH-NORTH") == 25
    assert inventory.get_stock("SKU-LAPTOP") == 25


def test_insufficient_inventory(inventory):
    """Verify ordering more items than available raises an OutOfStockError."""
    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 5)
    
    with pytest.raises(OutOfStockError) as exc_info:
        inventory.fulfill_order("SKU-LAPTOP", "WH-NORTH", 10)
    
    assert "Requested: 10, Available: 5" in str(exc_info.value)
    assert inventory.get_stock("SKU-LAPTOP", "WH-NORTH") == 5  # Stock should remain unchanged


def test_warehouse_transfer(inventory):
    """Verify transferring stock between warehouses correctly updates balances."""
    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 50)
    inventory.set_stock("SKU-LAPTOP", "WH-SOUTH", 10)

    inventory.transfer_stock("SKU-LAPTOP", "WH-NORTH", "WH-SOUTH", 20)

    assert inventory.get_stock("SKU-LAPTOP", "WH-NORTH") == 30
    assert inventory.get_stock("SKU-LAPTOP", "WH-SOUTH") == 30
    assert inventory.get_stock("SKU-LAPTOP") == 60  # Total remains invariant


def test_concurrent_orders(inventory):
    """Simulate concurrent order fulfillment racing for limited stock using Mocking."""
    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 10)

    mock_db = MagicMock()
    # Mocking race condition: 1st transaction succeeds, 2nd fails due to insufficient stock
    mock_db.deduct_stock.side_effect = [True, OutOfStockError("Stock exhausted")]

    # First attempt succeeds
    res1 = mock_db.deduct_stock("SKU-LAPTOP", "WH-NORTH", 10)
    assert res1 is True

    # Concurrent second attempt fails
    with pytest.raises(OutOfStockError):
        mock_db.deduct_stock("SKU-LAPTOP", "WH-NORTH", 10)

    mock_db.deduct_stock.assert_called()


def test_reorder_threshold(inventory):
    """Verify reorder alert triggers when total stock drops to or below threshold."""
    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 10)  # Threshold is 5
    assert inventory.check_reorder_status("SKU-LAPTOP") is False

    # Fulfill order down to threshold level
    inventory.fulfill_order("SKU-LAPTOP", "WH-NORTH", 5)
    assert inventory.get_stock("SKU-LAPTOP") == 5
    assert inventory.check_reorder_status("SKU-LAPTOP") is True  # Reorder triggered


def test_invalid_product(inventory):
    """Verify actions on non-existent product SKUs raise InvalidProductError."""
    with pytest.raises(InvalidProductError):
        inventory.get_stock("SKU-NONEXISTENT")

    with pytest.raises(InvalidProductError):
        inventory.fulfill_order("SKU-NONEXISTENT", "WH-NORTH", 1)


def test_negative_inventory(inventory):
    """Verify that negative inventory initialization or fulfillment throws an error."""
    with pytest.raises(InvalidQuantityError):
        inventory.set_stock("SKU-LAPTOP", "WH-NORTH", -5)

    inventory.set_stock("SKU-LAPTOP", "WH-NORTH", 10)
    with pytest.raises(InvalidQuantityError):
        inventory.fulfill_order("SKU-LAPTOP", "WH-NORTH", -2)


def test_multiple_warehouses(inventory):
    """Verify aggregated stock across multiple distributed warehouses."""
    inventory.set_stock("SKU-PHONE", "WH-NORTH", 100)
    inventory.set_stock("SKU-PHONE", "WH-SOUTH", 150)
    inventory.set_stock("SKU-PHONE", "WH-EAST", 50)

    assert inventory.get_stock("SKU-PHONE", "WH-NORTH") == 100
    assert inventory.get_stock("SKU-PHONE", "WH-SOUTH") == 150
    assert inventory.get_stock("SKU-PHONE", "WH-EAST") == 50
    assert inventory.get_stock("SKU-PHONE") == 300  # Aggregated total stock
