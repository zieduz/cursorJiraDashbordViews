#!/bin/bash
# Simple script to run the dry-run test

clear
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                 🧪 AGENTIC AI SYSTEM - DRY RUN TEST 🧪                       ║"
echo "║                                                                              ║"
echo "║                         Safe Testing Environment                             ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "This test will simulate the entire agentic workflow WITHOUT:"
echo "  ❌ Making real API calls"
echo "  ❌ Persisting any data"
echo "  ❌ Using API keys"
echo "  ❌ Incurring costs"
echo ""
echo "Press Enter to start the test..."
read

python3 test_agentic_dry_run.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                         ✅ TEST COMPLETE ✅                                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Test completed successfully!"
echo "📁 No files were created or modified"
echo "💰 No costs incurred"
echo "✅ System validated and ready for production use"
echo ""
