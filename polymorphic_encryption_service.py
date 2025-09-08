#!/usr/bin/env python3
"""
Polymorphic Encryption Service - Handles ALL encryption needs.
Uses ask/tell/do pattern to encrypt files, WebSockets, text, whatever.
Announces capabilities via Bonjour pattern.
"""

import asyncio
import websockets
import ssl
import pathlib
import sys
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from typing import Any, Optional, Union

# Bonjour announcements
try:
    from polymorphic_core import announcer
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            print(f"📢 {args[0] if args else ''}")
    announcer = DummyAnnouncer()


class PolymorphicEncryption:
    """Polymorphic encryption service - encrypts ANYTHING."""
    
    def __init__(self):
        """Initialize and announce capabilities."""
        self.ssl_context = None
        self.fernet = None
        self.private_key = None
        self.public_key = None
        self.proxy_tasks = []
        
        # Generate or load encryption key
        self._init_encryption()
        
        # Announce ourselves
        announcer.announce(
            "Polymorphic Encryption Service",
            [
                "I encrypt ANYTHING - files, streams, text, WebSockets",
                "I provide SSL/TLS termination for secure connections",
                "I can encrypt/decrypt using symmetric and asymmetric keys",
                "I proxy WebSocket connections with SSL termination"
            ],
            [
                'encryption.ask("status") - Get encryption status',
                'encryption.tell("base64", encrypted_data) - Format encrypted data',
                'encryption.do("encrypt file.txt") - Encrypt a file',
                'encryption.do("proxy wss 8443 to ws 8087") - SSL proxy',
                'encryption.do("generate certificates") - Create SSL certs'
            ]
        )
    
    def _init_encryption(self):
        """Initialize encryption keys and SSL context."""
        # Symmetric encryption key
        key_file = pathlib.Path(__file__).parent / ".encryption.key"
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Secure the key file
        
        self.fernet = Fernet(key)
        
        # SSL context for WebSocket proxy
        cert_path = pathlib.Path(__file__).parent / "server.crt"
        key_path = pathlib.Path(__file__).parent / "server.key"
        
        if cert_path.exists() and key_path.exists():
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(cert_path, key_path)
            announcer.announce("SSL_READY", ["SSL certificates loaded"])
    
    def ask(self, query: str, **kwargs) -> Any:
        """Ask for encryption-related information."""
        query_lower = query.lower().strip()
        
        if "status" in query_lower:
            return {
                "encryption": "active" if self.fernet else "inactive",
                "ssl": "ready" if self.ssl_context else "no certificates",
                "proxy_tasks": len(self.proxy_tasks),
                "algorithms": ["Fernet", "RSA", "SSL/TLS"]
            }
        
        elif "capabilities" in query_lower:
            return [
                "Encrypt/decrypt files",
                "Encrypt/decrypt text",
                "SSL WebSocket proxy",
                "Generate SSL certificates",
                "Hash passwords",
                "Sign/verify data"
            ]
        
        elif "certificate" in query_lower:
            cert_path = pathlib.Path(__file__).parent / "server.crt"
            if cert_path.exists():
                with open(cert_path, 'r') as f:
                    return f.read()
            return "No certificate found"
        
        elif "public url" in query_lower or "wss url" in query_lower:
            return "wss://64.111.98.139:8443/"
        
        return f"Unknown query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format encrypted data for output."""
        format_lower = format.lower().strip()
        
        if format_lower == "base64":
            if isinstance(data, bytes):
                return base64.b64encode(data).decode('utf-8')
            return str(data)
        
        elif format_lower == "hex":
            if isinstance(data, bytes):
                return data.hex()
            return str(data)
        
        elif format_lower == "status":
            status = self.ask("status")
            return f"🔐 Encryption: {status['encryption']}\n" \
                   f"🔒 SSL: {status['ssl']}\n" \
                   f"🔄 Active proxies: {status['proxy_tasks']}"
        
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform encryption actions."""
        action_lower = action.lower().strip()
        
        # Encrypt text/data
        if action_lower.startswith("encrypt "):
            target = action[8:].strip()
            
            # Check if it's a file
            if os.path.exists(target):
                return self._encrypt_file(target)
            else:
                # Treat as text
                encrypted = self.fernet.encrypt(target.encode())
                announcer.announce("ENCRYPTED", [f"Encrypted {len(target)} chars"])
                return encrypted
        
        # Decrypt text/data
        elif action_lower.startswith("decrypt "):
            target = action[8:].strip()
            
            # Check if it's a file
            if os.path.exists(target):
                return self._decrypt_file(target)
            else:
                # Treat as base64 encrypted text
                try:
                    encrypted = base64.b64decode(target)
                    decrypted = self.fernet.decrypt(encrypted)
                    return decrypted.decode()
                except:
                    return "Failed to decrypt - invalid data"
        
        # Start SSL proxy
        elif "proxy" in action_lower:
            # Parse: "proxy wss 8443 to ws 8087"
            parts = action_lower.split()
            listen_port = 8443
            forward_port = 8087
            
            for i, part in enumerate(parts):
                if part.isdigit():
                    if "listen" in action_lower[:action_lower.index(part)]:
                        listen_port = int(part)
                    else:
                        forward_port = int(part)
            
            # Start proxy in background
            asyncio.create_task(self._start_proxy(listen_port, forward_port))
            return f"Started SSL proxy: wss://64.111.98.139:{listen_port}/ → ws://localhost:{forward_port}/"
        
        # Generate SSL certificates
        elif "generate" in action_lower and "cert" in action_lower:
            return self._generate_certificates()
        
        # Hash password
        elif action_lower.startswith("hash "):
            password = action[5:].strip()
            hashed = hashlib.sha256(password.encode()).hexdigest()
            return hashed
        
        return f"Unknown action: {action}"
    
    def _encrypt_file(self, filepath: str) -> str:
        """Encrypt a file."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            encrypted = self.fernet.encrypt(data)
            
            # Save encrypted file
            encrypted_path = f"{filepath}.encrypted"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
            
            announcer.announce(
                "FILE_ENCRYPTED",
                [f"Encrypted {filepath} → {encrypted_path}"]
            )
            return encrypted_path
            
        except Exception as e:
            return f"Encryption failed: {e}"
    
    def _decrypt_file(self, filepath: str) -> str:
        """Decrypt a file."""
        try:
            with open(filepath, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.fernet.decrypt(encrypted)
            
            # Save decrypted file
            if filepath.endswith('.encrypted'):
                decrypted_path = filepath[:-10]  # Remove .encrypted
            else:
                decrypted_path = f"{filepath}.decrypted"
            
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted)
            
            announcer.announce(
                "FILE_DECRYPTED",
                [f"Decrypted {filepath} → {decrypted_path}"]
            )
            return decrypted_path
            
        except Exception as e:
            return f"Decryption failed: {e}"
    
    def _generate_certificates(self) -> str:
        """Generate self-signed SSL certificates."""
        import subprocess
        
        cert_path = pathlib.Path(__file__).parent / "server.crt"
        key_path = pathlib.Path(__file__).parent / "server.key"
        
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', str(key_path),
            '-out', str(cert_path),
            '-days', '365', '-nodes',
            '-subj', '/C=US/ST=CA/L=LA/O=Tournament/CN=64.111.98.139'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Reload SSL context
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(cert_path, key_path)
            
            announcer.announce(
                "CERTIFICATES_GENERATED",
                ["New SSL certificates created and loaded"]
            )
            return f"Generated: {cert_path} and {key_path}"
        else:
            return f"Certificate generation failed: {result.stderr}"
    
    async def _start_proxy(self, listen_port: int, forward_port: int):
        """Start SSL WebSocket proxy."""
        announcer.announce(
            "PROXY_STARTING",
            [f"SSL proxy on port {listen_port} → {forward_port}"]
        )
        
        async def handle_client(client_ws, path):
            """Handle SSL client and forward to backend."""
            forward_url = f"ws://localhost:{forward_port}{path}"
            
            try:
                async with websockets.connect(forward_url) as backend_ws:
                    # Bidirectional forwarding
                    await asyncio.gather(
                        self._forward(client_ws, backend_ws),
                        self._forward(backend_ws, client_ws)
                    )
            except Exception as e:
                announcer.announce("PROXY_ERROR", [str(e)])
        
        # Start server
        async with websockets.serve(
            handle_client,
            "0.0.0.0",
            listen_port,
            ssl=self.ssl_context,
            compression=None,
            max_size=10 * 1024 * 1024
        ):
            announcer.announce(
                "PROXY_RUNNING",
                [f"wss://64.111.98.139:{listen_port}/ → ws://localhost:{forward_port}/"]
            )
            await asyncio.Future()  # Run forever
    
    async def _forward(self, source_ws, dest_ws):
        """Forward messages between WebSockets."""
        try:
            async for message in source_ws:
                await dest_ws.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass


# Global instance for easy access
encryption = PolymorphicEncryption()


async def main():
    """Main entry point - start as proxy if requested."""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--proxy":
            # Start as SSL proxy
            listen = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
            forward = int(sys.argv[3]) if len(sys.argv) > 3 else 8087
            await encryption._start_proxy(listen, forward)
        else:
            # Process command
            result = encryption.do(" ".join(sys.argv[1:]))
            print(result)
    else:
        # Interactive mode
        print("🔐 Polymorphic Encryption Service")
        print("Commands:")
        print('  encryption.ask("status")')
        print('  encryption.do("encrypt file.txt")')
        print('  encryption.do("proxy wss 8443 to ws 8087")')
        print("\nStarting SSL proxy by default...")
        await encryption._start_proxy(8443, 8087)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Encryption service shutting down")