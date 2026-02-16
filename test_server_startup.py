#!/usr/bin/env python3
"""
Simple integration test for the Peer Review MCP Server.
This test verifies the server can start and the configuration is loaded correctly.
"""

import sys
import subprocess
import signal
import time
import os

def test_server_startup():
    """Test that the server can start without errors."""
    print("🧪 Testing Peer Review MCP Server Startup")
    print("=" * 60)
    print()
    
    # Ensure PATH
    bin_path = os.path.expanduser("~/Library/Python/3.12/bin")
    env = os.environ.copy()
    if bin_path not in env["PATH"]:
        env["PATH"] = f"{bin_path}:{env['PATH']}"
    
    # Test 1: Version check
    print("1️⃣  Testing version command...")
    try:
        result = subprocess.run(
            ["peer-review-mcp", "version"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        if result.returncode == 0:
            print(f"✅ Version: {result.stdout.strip()}")
        else:
            print(f"❌ Version check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Version check failed: {e}")
        return False
    print()
    
    # Test 2: Config check
    print("2️⃣  Testing config-check command...")
    try:
        result = subprocess.run(
            ["peer-review-mcp", "config-check"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        if result.returncode == 0:
            print("✅ Configuration loaded:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print(f"❌ Config check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Config check failed: {e}")
        return False
    print()
    
    # Test 3: Server startup
    print("3️⃣  Testing server startup...")
    process = None
    try:
        # Start server in background
        process = subprocess.Popen(
            ["peer-review-mcp", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # Wait a bit for startup
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully (PID: {})".format(process.pid))
            print("   Server is running and waiting for MCP protocol messages")
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"❌ Server exited immediately")
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
    finally:
        # Clean up
        if process and process.poll() is None:
            print("\n🧹 Stopping server...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✅ Server stopped cleanly")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️  Server force-killed")
    
    print()
    print("=" * 60)
    print("✅ All basic tests passed!")
    print()
    print("📋 Server Features:")
    print("   - MCP Protocol: stdio transport")
    print("   - Available Tools:")
    print("     • analyze_pull_request - Analyze PR compliance")
    print("     • get_review_summary - Get review status")
    print("     • config_check - Verify configuration")
    print()
    print("🔌 Integration:")
    print("   The server is ready to integrate with MCP clients.")
    print("   See QUICKSTART.md for Claude Desktop configuration.")
    print()
    print("📝 Manual Testing:")
    print("   To manually test with MCP Inspector:")
    print("   1. Install: npm install -g @modelcontextprotocol/inspector")
    print("   2. Run: mcp-inspector peer-review-mcp start")
    print()
    
    return True


if __name__ == "__main__":
    success = test_server_startup()
    sys.exit(0 if success else 1)
