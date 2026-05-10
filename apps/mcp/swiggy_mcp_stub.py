import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Setup logging to a file to avoid stdout pollution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("swiggy_mcp_stub.log")],
)
logger = logging.getLogger("swiggy_mcp_stub")

# --- MOCK DATA ---
MOCK_RESTAURANTS = [
    {
        "id": "res_001",
        "name": "Pizza Palace",
        "cuisine": ["Italian", "Pizza"],
        "rating": 4.5,
        "delivery_time": "25-35 mins",
        "location": "Indiranagar",
    },
    {
        "id": "res_002",
        "name": "Burger Barn",
        "cuisine": ["American", "Burgers"],
        "rating": 4.2,
        "delivery_time": "20-30 mins",
        "location": "Koramangala",
    },
    {
        "id": "res_003",
        "name": "The Tandoor Hub",
        "cuisine": ["North Indian", "Tandoor"],
        "rating": 4.7,
        "delivery_time": "40-50 mins",
        "location": "HSR Layout",
    }
]

MOCK_MENUS = {
    "res_001": [
        {"id": "p_01", "name": "Margherita Pizza", "price": 499, "description": "Classic cheese pizza"},
        {"id": "p_02", "name": "Pepperoni Feast", "price": 649, "description": "Loaded with pepperoni"},
        {"id": "p_03", "name": "Garlic Breadsticks", "price": 199, "description": "Baked fresh with garlic butter"}
    ],
    "res_002": [
        {"id": "b_01", "name": "Classic Cheeseburger", "price": 299, "description": "Juicy beef patty with cheddar"},
        {"id": "b_02", "name": "Spicy Chicken Burger", "price": 349, "description": "Fried chicken with peri-peri"},
        {"id": "b_03", "name": "Onion Rings", "price": 149, "description": "Crispy golden rings"}
    ]
}

MOCK_INSTAMART_ITEMS = [
    {"id": "im_01", "name": "Fresh Milk (1L)", "price": 60, "category": "Dairy"},
    {"id": "im_02", "name": "Bread (Brown)", "price": 45, "category": "Bakery"},
    {"id": "im_03", "name": "Coca Cola (500ml)", "price": 40, "category": "Beverages"},
    {"id": "im_04", "name": "Banana (6 units)", "price": 50, "category": "Fruits"}
]

# State for orders
orders = {}

# --- MCP SERVER SETUP ---
mcp = Server("swiggy-mcp-stub")

@mcp.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        # --- FOOD TOOLS ---
        types.Tool(
            name="food_search_restaurants",
            description="Search for restaurants on Swiggy Food by name, cuisine or location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term e.g. 'Pizza', 'Italian'"},
                    "location": {"type": "string", "description": "Location e.g. 'Indiranagar'"},
                }
            }
        ),
        types.Tool(
            name="food_get_menu",
            description="Get the full menu for a specific restaurant using its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string", "description": "The unique ID of the restaurant"}
                },
                "required": ["restaurant_id"]
            }
        ),
        types.Tool(
            name="food_place_order",
            description="Place a food order. Note: In this stub, this is a simulated transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"},
                                "quantity": {"type": "integer"}
                            }
                        }
                    },
                    "delivery_address": {"type": "string"}
                },
                "required": ["restaurant_id", "items", "delivery_address"]
            }
        ),
        types.Tool(
            name="food_track_order",
            description="Get live tracking status for a Swiggy Food order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        ),
        
        # --- INSTAMART TOOLS ---
        types.Tool(
            name="insta_search_items",
            description="Search for grocery items on Swiggy Instamart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "e.g. 'Milk', 'Eggs'"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="insta_place_order",
            description="Place a grocery order on Swiggy Instamart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"},
                                "quantity": {"type": "integer"}
                            }
                        }
                    },
                    "delivery_address": {"type": "string"}
                },
                "required": ["items", "delivery_address"]
            }
        ),

        # --- DINEOUT TOOLS ---
        types.Tool(
            name="dine_search_restaurants",
            description="Search for restaurants for dining out/reservations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "location": {"type": "string"}
                }
            }
        ),
        types.Tool(
            name="dine_book_table",
            description="Book a table at a restaurant via Swiggy Dineout.",
            inputSchema={
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string"},
                    "guests": {"type": "integer"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM"}
                },
                "required": ["restaurant_id", "guests", "date", "time"]
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    logger.info(f"Calling tool: {name} with args: {arguments}")
    
    if name == "food_search_restaurants":
        query = arguments.get("query", "").lower()
        results = [
            r for r in MOCK_RESTAURANTS 
            if query in r["name"].lower() or any(query in c.lower() for c in r["cuisine"])
        ]
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "food_get_menu":
        res_id = arguments.get("restaurant_id")
        menu = MOCK_MENUS.get(res_id, [])
        return [types.TextContent(type="text", text=json.dumps(menu, indent=2))]

    elif name == "food_place_order":
        order_id = f"SWG-FOOD-{uuid.uuid4().hex[:6].upper()}"
        orders[order_id] = {
            "status": "Accepted",
            "type": "Food",
            "details": arguments,
            "timestamp": datetime.now().isoformat()
        }
        return [types.TextContent(type="text", text=json.dumps({"success": True, "order_id": order_id, "status": "Accepted", "message": "Order placed successfully (STUB)"}, indent=2))]

    elif name == "food_track_order":
        order_id = arguments.get("order_id")
        if order_id in orders:
            # Simulate status update
            order = orders[order_id]
            time_diff = datetime.now() - datetime.fromisoformat(order["timestamp"])
            if time_diff.seconds > 120:
                order["status"] = "Delivered"
            elif time_diff.seconds > 60:
                order["status"] = "Out for Delivery"
            elif time_diff.seconds > 30:
                order["status"] = "Preparing"
            
            return [types.TextContent(type="text", text=json.dumps({"order_id": order_id, "status": order["status"]}, indent=2))]
        return [types.TextContent(type="text", text=f"Order {order_id} not found.")]

    elif name == "insta_search_items":
        query = arguments.get("query", "").lower()
        results = [i for i in MOCK_INSTAMART_ITEMS if query in i["name"].lower()]
        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "insta_place_order":
        order_id = f"SWG-INSTA-{uuid.uuid4().hex[:6].upper()}"
        orders[order_id] = {
            "status": "Picking items",
            "type": "Instamart",
            "details": arguments,
            "timestamp": datetime.now().isoformat()
        }
        return [types.TextContent(type="text", text=json.dumps({"success": True, "order_id": order_id, "message": "Instamart order placed (STUB)"}, indent=2))]

    elif name == "dine_search_restaurants":
        # Reuse food restaurants for mock
        return [types.TextContent(type="text", text=json.dumps(MOCK_RESTAURANTS, indent=2))]

    elif name == "dine_book_table":
        booking_id = f"SWG-DINE-{uuid.uuid4().hex[:6].upper()}"
        return [types.TextContent(type="text", text=json.dumps({"success": True, "booking_id": booking_id, "message": f"Table booked for {arguments['guests']} guests at {arguments['time']}"}, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
