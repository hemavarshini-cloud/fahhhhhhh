from collections import defaultdict

class Product:
    def __init__(self, product_id, name, reorder_level):
        self.product_id = product_id
        self.name = name
        self.reorder_level = reorder_level
        self.suppliers = []

class Warehouse:
    def __init__(self, name):
        self.name = name
        self.stock = defaultdict(int)  # product_id -> quantity

class InventoryManager:
    def __init__(self):
        self.products = {}  # product_id -> Product object
        self.warehouses = {}  # warehouse_name -> Warehouse object
        self.warehouse_priority = []  # Ordered list for fulfillment selection

    def add_warehouse(self, name):
        if name not in self.warehouses:
            self.warehouses[name] = Warehouse(name)
            self.warehouse_priority.append(name)

    def add_product(self, product_id, name, reorder_level):
        if product_id not in self.products:
            self.products[product_id] = Product(product_id, name, reorder_level)

    def add_supplier(self, product_id, supplier_name):
        if product_id in self.products:
            self.products[product_id].suppliers.append(supplier_name)

    def add_stock(self, warehouse_name, product_id, quantity):
        if warehouse_name in self.warehouses and product_id in self.products:
            self.warehouses[warehouse_name].stock[product_id] += quantity

    def remove_stock(self, warehouse_name, product_id, quantity):
        if warehouse_name in self.warehouses:
            current_stock = self.warehouses[warehouse_name].stock[product_id]
            if current_stock >= quantity:
                self.warehouses[warehouse_name].stock[product_id] -= quantity
                return True
        return False

    def transfer_stock(self, source_wh, target_wh, product_id, quantity):
        if self.remove_stock(source_wh, product_id, quantity):
            self.add_stock(target_wh, product_id, quantity)
            print(f"Transferred {quantity} units of {product_id} from {source_wh} to {target_wh}.")
            return True
        print(f"Transfer failed: Insufficient stock in {source_wh}.")
        return False

    def select_warehouse_for_fulfillment(self, product_id, quantity):
        """Finds the first warehouse in the priority list that can fulfill the full quantity."""
        for wh_name in self.warehouse_priority:
            if self.warehouses[wh_name].stock[product_id] >= quantity:
                return wh_name
        return None

    def fulfill_order(self, product_id, quantity):
        wh_name = self.select_warehouse_for_fulfillment(product_id, quantity)
        if wh_name:
            self.remove_stock(wh_name, product_id, quantity)
            print(f"Order fulfilled: {quantity} units of {product_id} shipped from {wh_name}.")
            self.check_low_stock(product_id)
            return True
        print(f"Order failed: No single warehouse has {quantity} units of {product_id}.")
        return False

    def check_low_stock(self, product_id):
        total_stock = sum(wh.stock[product_id] for wh in self.warehouses.values())
        product = self.products[product_id]
        if total_stock <= product.reorder_level:
            print(f"ALERT: Low stock for '{product.name}' (Total: {total_stock}, Reorder Threshold: {product.reorder_level})")
            self.reorder(product_id)

    def reorder(self, product_id):
        product = self.products[product_id]
        suppliers = ", ".join(product.suppliers) if product.suppliers else "No assigned suppliers"
        print(f"REORDER NOTICE: Contact suppliers [{suppliers}] to replenish Product '{product.name}'.")


# --- Execution Example ---
if __name__ == "__main__":
    system = InventoryManager()

    # Initialize Warehouses
    system.add_warehouse("Warehouse A")
    system.add_warehouse("Warehouse B")
    system.add_warehouse("Warehouse C")

    # Add Product & Suppliers
    system.add_product("P101", "Wireless Mouse", reorder_level=15)
    system.add_supplier("P101", "TechDistro Inc.")
    system.add_supplier("P101", "Global Logistics Co.")

    # Stock Setup
    system.add_stock("Warehouse A", "P101", 5)
    system.add_stock("Warehouse B", "P101", 20)
    system.add_stock("Warehouse C", "P101", 10)

    print("--- Stock Transfer ---")
    system.transfer_stock("Warehouse B", "Warehouse A", "P101", 5)

    print("\n--- Automatic Warehouse Selection & Fulfillment ---")
    # Needs 12 units. Warehouse A has 10, Warehouse B has 15 -> Picks Warehouse B
    system.fulfill_order("P101", 12)

    print("\n--- Triggering Low Stock Detection ---")
    # Fulfill 10 units -> Total stock drops below threshold (15)
    system.fulfill_order("P101", 10)
