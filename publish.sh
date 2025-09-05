#!/bin/bash
# Quick publish script for Shopify

echo "Publishing tournament data to Shopify..."
./go.py --skip-sync --publish

echo ""
echo "✅ Done! View your page at:"
echo "   https://8ccd49-4.myshopify.com/admin/online_store/pages"
echo ""
echo "To sync fresh data first, use: ./go.py --sync --publish"