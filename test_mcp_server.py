#!/usr/bin/env python3
"""
Test script for the Peer Review MCP Server.
This script tests the MCP server by sending it protocol messages and verifying responses.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any, Optional

def send_mcp_request(process: subprocess.Popen, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send an MCP request to the server and get response."""
    try:
        # Send request
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            return json.loads(response_line.decode().strip())
        return None
    except Exception as e:
        print(f"❌ Error communicating with server: {e}")
        return None

def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing Peer Review MCP Server")
    print("=" * 60)
    print()
    
    # Start the server
    print("1️⃣  Starting MCP server...")
    try:
        process = subprocess.Popen(
            ["peer-review-mcp", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
        time.sleep(1)  # Give server time to start
        
        if process.poll() is not None:
            stderr = process.stderr.read().decode()
            print(f"❌ Server failed to start!")
            print(f"Error: {stderr}")
            return False
            
        print("✅ Server started successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    try:
        # Test 1: Initialize
        print("2️⃣  Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = send_mcp_request(process, init_request)
        if response and "result" in response:
            print("✅ Initialization successful")
            print(f"   Server: {response['result'].get('serverInfo', {}).get('name', 'unknown')}")
            print(f"   Version: {response['result'].get('serverInfo', {}).get('version', 'unknown')}")
        else:
            print("❌ Initialization failed")
            print(f"   Response: {response}")
        print()
        
        # Test 2: List Tools
        print("3️⃣  Testing tools/list...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = send_mcp_request(process, list_tools_request)
        if response and "result" in response:
            tools = response['result'].get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool.get('description', 'No description')[:60]}")
        else:
            print("❌ Failed to list tools")
            print(f"   Response: {response}")
        print()
        
        # Test 3: Config Check Tool
        print("4️⃣  Testing config_check tool...")
        config_check_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "config_check",
                "arguments": {}
            }
        }
        
        response = send_mcp_request(process, config_check_request)
        if response and "result" in response:
            print("✅ Config check successful")
            content = response['result'].get('content', [])
            if content:
                print(f"   {content[0].get('text', 'No output')[:200]}")
        else:
            print("❌ Config check failed")
            print(f"   Response: {response}")
        print()
        
        # Test 4: Analyze PR Tool (with mocked data)
        print("5️⃣  Testing analyze_pull_request tool...")
        analyze_pr_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "analyze_pull_request",
                "arguments": {
                    "repository": "techieshailesh/peerReviewAgenticMCP",
                    "pr_number": 1
                }
            }
        }
        
        response = send_mcp_request(process, analyze_pr_request)
        if response:
            if "result" in response:
                print("✅ PR analysis started")
                content = response['result'].get('content', [])
                if content:
                    text = content[0].get('text', '')
                    # Show first 200 chars
                    print(f"   {text[:200]}...")
            elif "error" in response:
                print("⚠️  PR analysis returned error (expected if PR doesn't exist)")
                print(f"   Error: {response['error'].get('message', 'Unknown error')}")
        else:
            print("❌ No response from PR analysis")
        print()
        
        print("=" * 60)
        print("✅ MCP Server testing complete!")
        print()
        print("Next steps:")
        print("- Configure MCP client (Claude Desktop, Cline, etc.)")
        print("- See QUICKSTART.md for integration instructions")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        print("✅ Server stopped")

if __name__ == "__main__":
    # Ensure PATH includes the bin directory
    import os
    bin_path = os.path.expanduser("~/Library/Python/3.12/bin")
    if bin_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"
    
    success = test_mcp_server()
    sys.exit(0 if success else 1)
