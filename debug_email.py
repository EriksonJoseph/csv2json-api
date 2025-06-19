#!/usr/bin/env python3
"""
Email Debug Script for Docker Container
Run this script inside the container to debug email connectivity issues
"""

import asyncio
import socket
import smtplib
import os
import sys
from datetime import datetime

async def test_email_connectivity():
    """Test email connectivity from container environment"""
    
    print("🔧 Email Connectivity Debug Script")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Get SMTP settings from environment
    smtp_config = {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "use_tls": os.getenv("SMTP_USE_TLS", "True").lower() == "true",
        "from_email": os.getenv("SMTP_FROM_EMAIL", "")
    }
    
    print("📧 SMTP Configuration:")
    for key, value in smtp_config.items():
        if key == "password":
            print(f"  {key}: {'***' if value else 'NOT SET'}")
        else:
            print(f"  {key}: {value}")
    print()
    
    tests = []
    
    # Test 1: DNS Resolution
    print("🔍 Test 1: DNS Resolution")
    try:
        ip = socket.gethostbyname(smtp_config["host"])
        print(f"  ✅ {smtp_config['host']} resolves to {ip}")
        tests.append(("DNS Resolution", True, f"Resolves to {ip}"))
    except Exception as e:
        print(f"  ❌ DNS Resolution failed: {e}")
        tests.append(("DNS Resolution", False, str(e)))
    print()
    
    # Test 2: Network Connectivity
    print("🔍 Test 2: Network Connectivity")
    try:
        sock = socket.create_connection((smtp_config["host"], smtp_config["port"]), timeout=10)
        sock.close()
        print(f"  ✅ Can connect to {smtp_config['host']}:{smtp_config['port']}")
        tests.append(("Network Connectivity", True, "Connection successful"))
    except Exception as e:
        print(f"  ❌ Network connection failed: {e}")
        tests.append(("Network Connectivity", False, str(e)))
    print()
    
    # Test 3: SMTP Connection
    print("🔍 Test 3: SMTP Connection")
    try:
        server = smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30)
        response = server.noop()
        server.quit()
        print(f"  ✅ SMTP server responds: {response}")
        tests.append(("SMTP Connection", True, f"Server responds: {response}"))
    except Exception as e:
        print(f"  ❌ SMTP connection failed: {e}")
        tests.append(("SMTP Connection", False, str(e)))
    print()
    
    # Test 4: TLS Support
    if smtp_config["use_tls"]:
        print("🔍 Test 4: TLS Support")
        try:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30)
            server.starttls()
            server.quit()
            print(f"  ✅ TLS connection successful")
            tests.append(("TLS Support", True, "TLS handshake successful"))
        except Exception as e:
            print(f"  ❌ TLS connection failed: {e}")
            tests.append(("TLS Support", False, str(e)))
        print()
    
    # Test 5: Authentication
    if smtp_config["username"] and smtp_config["password"]:
        print("🔍 Test 5: SMTP Authentication")
        try:
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30)
            if smtp_config["use_tls"]:
                server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.quit()
            print(f"  ✅ Authentication successful")
            tests.append(("Authentication", True, "Login successful"))
        except Exception as e:
            print(f"  ❌ Authentication failed: {e}")
            tests.append(("Authentication", False, str(e)))
        print()
    else:
        print("🔍 Test 5: SMTP Authentication")
        print("  ⚠️  Username or password not configured")
        tests.append(("Authentication", False, "Credentials not configured"))
        print()
    
    # Test 6: Internet Connectivity
    print("🔍 Test 6: General Internet Connectivity")
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=5)
        sock.close()
        print(f"  ✅ Can reach Google DNS (8.8.8.8:53)")
        tests.append(("Internet Connectivity", True, "Can reach external servers"))
    except Exception as e:
        print(f"  ❌ Internet connectivity failed: {e}")
        tests.append(("Internet Connectivity", False, str(e)))
    print()
    
    # Summary
    print("📊 Test Summary:")
    print("=" * 50)
    passed = sum(1 for _, success, _ in tests if success)
    total = len(tests)
    
    for test_name, success, message in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name} - {message}")
    
    print()
    print(f"📈 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email should work from this container.")
    else:
        print("⚠️  Some tests failed. Check the errors above for troubleshooting.")
        
        # Common issues and solutions
        print()
        print("🔧 Common Issues and Solutions:")
        print("-" * 40)
        
        failed_tests = [name for name, success, _ in tests if not success]
        
        if "DNS Resolution" in failed_tests:
            print("• DNS Resolution Failed:")
            print("  - Check if the container has proper DNS configuration")
            print("  - Try using IP address instead of hostname")
            print("  - Check Docker network settings")
        
        if "Network Connectivity" in failed_tests:
            print("• Network Connectivity Failed:")
            print("  - Container might not have internet access")
            print("  - Check Docker network configuration")
            print("  - Verify firewall settings")
            print("  - Ensure the SMTP port is not blocked")
        
        if "Authentication" in failed_tests:
            print("• Authentication Failed:")
            print("  - Check if username/password are correct")
            print("  - For Gmail: Use App Password instead of regular password")
            print("  - Verify 2FA settings if enabled")
        
        if "TLS Support" in failed_tests:
            print("• TLS Failed:")
            print("  - Check if the SMTP server supports TLS")
            print("  - Try disabling TLS (set SMTP_USE_TLS=False)")
            print("  - Check SSL/TLS certificate validity")

if __name__ == "__main__":
    asyncio.run(test_email_connectivity())