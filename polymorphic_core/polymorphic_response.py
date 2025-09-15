#!/usr/bin/env python3
"""
polymorphic_response.py - Smart response formatting based on client type

Automatically detects what format the client wants and responds appropriately:
- WebDAV clients get WebDAV XML responses
- Browsers get HTML interfaces
- API clients get JSON data
- File managers get directory listings
"""

import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional
from fastapi import Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

class PolymorphicResponseHandler:
    """
    Handles automatic response formatting based on client requirements.
    """

    def __init__(self, service_name: str, service_capabilities: list):
        self.service_name = service_name
        self.service_capabilities = service_capabilities

    def detect_client_type(self, request: Request) -> str:
        """
        Detect what type of client is making the request.

        Returns: 'webdav', 'browser', 'api', or 'file_manager'
        """
        user_agent = request.headers.get('user-agent', '').lower()
        accept = request.headers.get('accept', '').lower()
        method = request.method.upper()

        # WebDAV detection
        if any(header in request.headers for header in ['dav', 'depth', 'destination']):
            return 'webdav'
        if method in ['PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY', 'MOVE', 'LOCK', 'UNLOCK']:
            return 'webdav'
        if 'webdav' in user_agent or 'microsoft-webdav' in user_agent:
            return 'webdav'

        # File manager detection
        if any(fm in user_agent for fm in ['files', 'finder', 'explorer', 'nautilus']):
            return 'file_manager'

        # Browser detection
        if any(browser in user_agent for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge']):
            if 'text/html' in accept and method == 'GET':
                return 'browser'

        # Default to API for everything else
        return 'api'

    def format_response(self, request: Request, data: Any) -> Response:
        """
        Format response based on detected client type.
        """
        client_type = self.detect_client_type(request)

        if client_type == 'webdav':
            return self._format_webdav_response(request, data)
        elif client_type == 'browser':
            return self._format_html_response(data)
        elif client_type == 'file_manager':
            return self._format_file_listing_response(data)
        else:  # api
            return self._format_json_response(data)

    def _format_webdav_response(self, request: Request, data: Any) -> Response:
        """
        Format WebDAV XML response for file access.
        """
        method = request.method.upper()

        if method == 'PROPFIND':
            # Return WebDAV properties
            xml_content = self._build_webdav_propfind_response(request, data)
            return Response(
                content=xml_content,
                media_type="application/xml",
                headers={
                    "DAV": "1, 2",
                    "Allow": "GET, POST, OPTIONS, HEAD, PROPFIND, PROPPATCH, MKCOL, COPY, MOVE"
                }
            )
        elif method == 'OPTIONS':
            # WebDAV capabilities
            return Response(
                content="",
                headers={
                    "DAV": "1, 2",
                    "Allow": "GET, POST, OPTIONS, HEAD, PROPFIND, PROPPATCH, MKCOL, COPY, MOVE",
                    "MS-Author-Via": "DAV"
                }
            )
        else:
            # Default WebDAV response
            return self._format_json_response(data)

    def _build_webdav_propfind_response(self, request: Request, data: Any) -> str:
        """
        Build WebDAV PROPFIND XML response.
        """
        # Create basic WebDAV multistatus response
        multistatus = ET.Element("D:multistatus")
        multistatus.set("xmlns:D", "DAV:")

        # Add the service as a "directory"
        response = ET.SubElement(multistatus, "D:response")

        # href - the resource URL
        href = ET.SubElement(response, "D:href")
        href.text = str(request.url)

        # propstat - property status
        propstat = ET.SubElement(response, "D:propstat")

        # prop - the actual properties
        prop = ET.SubElement(propstat, "D:prop")

        # Resource type - this is a collection (directory)
        resourcetype = ET.SubElement(prop, "D:resourcetype")
        ET.SubElement(resourcetype, "D:collection")

        # Display name
        displayname = ET.SubElement(prop, "D:displayname")
        displayname.text = self.service_name

        # Content type
        contenttype = ET.SubElement(prop, "D:getcontenttype")
        contenttype.text = "httpd/unix-directory"

        # Status
        status = ET.SubElement(propstat, "D:status")
        status.text = "HTTP/1.1 200 OK"

        # Add service capabilities as "files"
        for i, capability in enumerate(self.service_capabilities):
            cap_response = ET.SubElement(multistatus, "D:response")

            cap_href = ET.SubElement(cap_response, "D:href")
            cap_href.text = f"{request.url}capability_{i}.txt"

            cap_propstat = ET.SubElement(cap_response, "D:propstat")
            cap_prop = ET.SubElement(cap_propstat, "D:prop")

            # This is a file, not a collection
            cap_resourcetype = ET.SubElement(cap_prop, "D:resourcetype")

            cap_displayname = ET.SubElement(cap_prop, "D:displayname")
            cap_displayname.text = f"{capability}.txt"

            cap_contenttype = ET.SubElement(cap_prop, "D:getcontenttype")
            cap_contenttype.text = "text/plain"

            cap_status = ET.SubElement(cap_propstat, "D:status")
            cap_status.text = "HTTP/1.1 200 OK"

        # Convert to XML string
        ET.register_namespace("D", "DAV:")
        return '<?xml version="1.0" encoding="utf-8" ?>\n' + ET.tostring(multistatus, encoding='unicode')

    def _format_html_response(self, data: Any) -> HTMLResponse:
        """
        Format HTML response for browsers.
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.service_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; }}
                .service-info {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .capabilities {{ list-style: none; padding: 0; }}
                .capabilities li {{ background: #e8f4fd; margin: 8px 0; padding: 12px; border-radius: 4px; }}
                .endpoints {{ background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 8px; }}
                .endpoint {{ font-family: monospace; background: #f8f8f8; padding: 8px; margin: 4px 0; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🌐 {self.service_name}</h1>

            <div class="service-info">
                <h2>Service Information</h2>
                <p><strong>Status:</strong> ✅ Running</p>
                <p><strong>Protocol:</strong> HTTPS (SSL encrypted)</p>
                <p><strong>Access:</strong> Available via VPN and mDNS</p>
            </div>

            <h2>Capabilities</h2>
            <ul class="capabilities">
                {"".join(f"<li>• {cap}</li>" for cap in self.service_capabilities)}
            </ul>

            <div class="endpoints">
                <h2>API Endpoints</h2>
                <div class="endpoint">POST /ask - Query the service with natural language</div>
                <div class="endpoint">POST /tell - Format data for output</div>
                <div class="endpoint">POST /do - Perform actions</div>
                <div class="endpoint">GET / - This service information page</div>
            </div>

            <h2>Data Preview</h2>
            <pre style="background: #f8f8f8; padding: 20px; border-radius: 4px; overflow: auto;">
{json.dumps(data, indent=2) if isinstance(data, dict) else str(data)}
            </pre>

            <footer style="margin-top: 40px; color: #666; font-size: 0.9em;">
                <p>🔐 HTTPS-only service • 📡 mDNS discoverable • 🌐 VPN accessible</p>
            </footer>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    def _format_file_listing_response(self, data: Any) -> PlainTextResponse:
        """
        Format file-like listing for file managers.
        """
        content = f"{self.service_name}/\n"
        content += "=" * len(self.service_name) + "\n\n"

        for i, capability in enumerate(self.service_capabilities):
            content += f"capability_{i}.txt\n"

        content += f"\nservice_data.json\n"
        content += f"README.txt\n"

        return PlainTextResponse(content=content)

    def _format_json_response(self, data: Any) -> JSONResponse:
        """
        Format JSON response for API clients.
        """
        if isinstance(data, dict):
            return JSONResponse(content=data)
        else:
            return JSONResponse(content={"result": data})

def create_polymorphic_handler(service_name: str, capabilities: list) -> PolymorphicResponseHandler:
    """
    Create a polymorphic response handler for a service.
    """
    return PolymorphicResponseHandler(service_name, capabilities)