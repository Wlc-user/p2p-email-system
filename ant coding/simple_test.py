#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to verify basic functionality
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project path
sys.path.append(str(Path(__file__).parent))

def test_modules():
    """Test module imports"""
    print("[+] Testing module imports...")

    try:
        from server.protocols import Message, MessageType, Mail, MailAddress, MailStatus
        from server.storage_manager import StorageManager
        from server.security import SecurityManager
        from server.mail_handler import MailHandler
        from server.server_manager import ServerManager
        from client.main import MailClient

        print("[+] All modules imported successfully")
        return True
    except Exception as e:
        print(f"[-] Module import failed: {e}")
        return False

def test_storage():
    """Test storage manager"""
    print("\n[+] Testing storage manager...")

    try:
        temp_dir = tempfile.mkdtemp()

        config = {
            'encryption_key': 'test-key-1234567890',
            'jwt_secret': 'test-secret-1234567890',
            'salt_length': 16
        }

        storage_manager = StorageManager(temp_dir)

        # Test user creation
        user_data = storage_manager.create_user(
            username="testuser",
            domain="test.com",
            password="testpass",
            email="test@test.com"
        )

        assert user_data is not None
        assert user_data["username"] == "testuser"

        # Test user authentication
        auth_user = storage_manager.authenticate_user(
            username="testuser",
            domain="test.com",
            password="testpass"
        )

        assert auth_user is not None

        # Cleanup
        shutil.rmtree(temp_dir)

        print("[+] Storage manager test passed")
        return True
    except Exception as e:
        print(f"[-] Storage manager test failed: {e}")
        return False

def test_security():
    """Test security manager"""
    print("\n[+] Testing security manager...")

    try:
        config = {
            'encryption_key': 'test-key-1234567890',
            'jwt_secret': 'test-secret-1234567890',
            'salt_length': 16
        }

        security_manager = SecurityManager(config)

        # Test password hashing
        password = "TestPass123!"
        hashed = security_manager.hash_password(password)
        verified = security_manager.verify_password(password, hashed)
        assert verified == True

        # Test token management
        token = security_manager.generate_token("testuser", "test.com")
        assert security_manager.verify_token(token) == True

        print("[+] Security manager test passed")
        return True
    except Exception as e:
        print(f"[-] Security manager test failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Simple Test - Smart Secure Email System")
    print("=" * 60)

    results = []

    # Test 1: Module imports
    results.append(("Module Imports", test_modules()))

    # Test 2: Storage manager
    results.append(("Storage Manager", test_storage()))

    # Test 3: Security manager
    results.append(("Security Manager", test_security()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[+] PASSED" if result else "[-] FAILED"
        print(f"{name:30} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[!] All tests passed!")
        return 0
    else:
        print("\n[!] Some tests failed!")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[-] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
