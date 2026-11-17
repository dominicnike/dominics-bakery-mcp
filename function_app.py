import json
import logging
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
from azure.functions.decorators.core import McpPropertyType
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

PRODUCTS_CONTAINER = "products"
ORDERS_CONTAINER = "orders"


def _container(name: str):
    """Return a blob container client using the Function App's storage connection."""
    service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container = service.get_container_client(name)
    if not container.exists():
        container.create_container()
    return container


def _read_all_json(container_name: str) -> list[dict]:
    container = _container(container_name)
    items = []
    for blob in container.list_blobs():
        data = container.download_blob(blob.name).readall()
        items.append(json.loads(data))
    return items


@app.mcp_tool()
def hello_mcp() -> str:
    """Simple hello-world tool to confirm the MCP server is working."""
    return "Hello, I am the Dominic's Bakery MCP tool!"


@app.mcp_tool()
def list_products() -> str:
    """List all products sold by Dominic's Bakery, including name, category and price."""
    products = _read_all_json(PRODUCTS_CONTAINER)
    logging.info("Returned %d products", len(products))
    return json.dumps(products)


@app.mcp_tool()
@app.mcp_tool_property(arg_name="customer_name", description="Name of the customer placing the order.")
@app.mcp_tool_property(arg_name="item", description="Exact product name to order, e.g. 'Snickerdoodle Cookie'.")
@app.mcp_tool_property(
    arg_name="quantity",
    description="How many of the item to order.",
    property_type=McpPropertyType.INTEGER,
)
def place_order(customer_name: str, item: str, quantity: int) -> str:
    """Place a new order at Dominic's Bakery for a customer."""
    quantity = int(quantity)
    if quantity <= 0:
        return "Quantity must be greater than zero."

    products = {p["name"].lower(): p for p in _read_all_json(PRODUCTS_CONTAINER)}
    product = products.get(item.strip().lower())
    if product is None:
        return f"'{item}' is not on the menu. Call list_products to see available items."

    order = {
        "order_id": str(uuid.uuid4())[:8],
        "customer_name": customer_name,
        "item": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "total": round(product["price"] * quantity, 2),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    _container(ORDERS_CONTAINER).upload_blob(f"{order['order_id']}.json", json.dumps(order))
    logging.info("Placed order %s", order["order_id"])
    return json.dumps({"status": "Order placed", "order": order})


@app.mcp_tool()
def list_orders() -> str:
    """List all orders that have been placed at Dominic's Bakery."""
    orders = sorted(_read_all_json(ORDERS_CONTAINER), key=lambda o: o.get("created_utc", ""))
    return json.dumps(orders)
