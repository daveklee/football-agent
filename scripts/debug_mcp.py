import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    print("🚀 Starting MCP Server Debugger...")
    
    # Path to MCP server script
    mcp_script = os.path.abspath("fantasy-football-mcp-public/fantasy_football_multi_league.py")
    python_exe = sys.executable
    
    print(f"Server Script: {mcp_script}")
    print(f"Python Exe: {python_exe}")
    
    # Server parameters
    server_params = StdioServerParameters(
        command=python_exe,
        args=[mcp_script],
        env={**os.environ} # Pass current environment with secrets
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("✅ Connected to stdio channels")
            
            async with ClientSession(read, write) as session:
                print("✅ Initialized ClientSession")
                
                await session.initialize()
                print("✅ Session initialized")
                
                # List tools
                print("🔍 Listing tools...")
                response = await session.list_tools()
                
                print(f"✅ Found {len(response.tools)} tools:")
                for tool in response.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n✅ MCP Server is responding correctly!")
                return True

    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
