from mcp.server.fastmcp import FastMCP
import asyncio
from typing import Dict, Any, Optional

from leantool import check_lean_code

# Create an MCP server
mcp = FastMCP("LeanTool")


@mcp.tool()
async def check_lean (code: str, json_output: bool = False)-> Dict[str, Any]:
    """
    Sends code to the Lean executable and returns the results.
    
    Args:
        code: Lean code to check
        json_output: Whether to get output in JSON format
        
    Returns:
        Dictionary containing:
            - success: bool indicating if code checked successfully
            - output: string or parsed JSON containing Lean's output
            - error: string containing error message if any
    """
    return await check_lean_code (code, json_output)


if __name__ == '__main__':
    mcp.run()
