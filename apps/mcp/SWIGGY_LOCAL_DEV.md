# Swiggy MCP Local Development Guide

This guide helps you "wire Swiggy MCP to local" so you can build your integration and record the demo video required for Swiggy production access.

## 1. Prerequisites
Ensure you have the MCP SDK installed in your environment:
```bash
pip install mcp
```

## 2. Running the Stub Server
The stub server (`swiggy_mcp_stub.py`) uses `stdio` to communicate. You don't run it directly in your terminal to interact with it; instead, you configure an MCP client (like Claude Desktop) to launch it.

However, you can test if it starts without errors by running:
```bash
python d:/sentimatix/apps/mcp/swiggy_mcp_stub.py
```
*(It will wait for input, which is normal for stdio servers. Press Ctrl+C to stop.)*

## 3. Configure Claude Desktop
To use these tools in Claude Desktop, add the following to your `claude_desktop_config.json`:

**Windows Path:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "swiggy-stub": {
      "command": "python",
      "args": [
        "d:/sentimatix/apps/mcp/swiggy_mcp_stub.py"
      ],
      "env": {}
    }
  }
}
```

## 4. Tools Available
Once configured, you can ask Claude to:
- "Search for Pizza in Bangalore on Swiggy"
- "Show me the menu for Pizza Palace"
- "Order a Margherita Pizza to 123 Main St"
- "Check my order status"
- "Search for Milk on Instamart"
- "Book a table for 2 at Burger Barn for tonight"

## 5. Tips for your Production Access Video
Swiggy looks for:
- **End-to-End Flow**: Show searching, selecting, and "placing" an order.
- **Error Handling**: The stub handles basic cases, but you can record how your agent handles "No restaurants found" or "Item out of stock".
- **User Confirmation**: Ensure your agent asks "Would you like me to place this order for ₹499?" before calling the `place_order` tool.

When ready, record your screen using Loom or Zoom and include the link in your application at [swiggy.com/access](https://swiggy.com/access).
