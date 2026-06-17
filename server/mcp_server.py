import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent
from mcp.server.stdio import stdio_server
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from probe_twse_openapi import probe as probe_twse
from probe_tpex_openapi import probe as probe_tpex
from probe_yahoo import probe as probe_yahoo
from probe_twse_mis import probe as probe_mis
from probe_finmind import probe as probe_finmind

app = Server("tw-market-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the AI agent."""
    return [
        Tool(
            name="probe_twse_openapi",
            description="Probe the TWSE OpenAPI for daily close quotes.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="probe_tpex_openapi",
            description="Probe the TPEx OpenAPI for daily close quotes.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="probe_yahoo_finance",
            description="Probe Yahoo Finance for multiple TW market data assets.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="probe_twse_mis",
            description="Probe TWSE MIS for realtime info across multiple assets.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="probe_finmind",
            description="Probe FinMind API for Taiwan stock data across multiple assets.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution requests."""
    yahoo_symbols = ["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]
    mis_symbols = ["tse_2330.tw", "tse_1435.tw", "tse_0050.tw", "tse_00929.tw", "tse_t00.tw", "otc_o00.tw"]
    finmind_datasets = [
        ("TaiwanStockPrice", "2330"),
        ("TaiwanStockPrice", "1435"),
        ("TaiwanStockPrice", "0050"),
        ("TaiwanStockPrice", "00929"),
        ("TaiwanStockPrice", "TAIEX"),
        ("TaiwanFutureDaily", "TX"),
    ]
    try:
        if name == "probe_twse_openapi":
            result = probe_twse()
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "probe_tpex_openapi":
            result = probe_tpex()
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "probe_yahoo_finance":
            result = probe_yahoo(symbols=yahoo_symbols)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "probe_twse_mis":
            result = probe_mis(symbols=mis_symbols)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        elif name == "probe_finmind":
            result = probe_finmind(datasets=finmind_datasets)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
