#!/usr/bin/env python3
"""
Script to generate mock data for the Jira Performance Dashboard.
Run this script to populate the database with sample data.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mock_data import generate_mock_data


async def main():
    """Generate mock data for development."""
    print("🚀 Generating mock data for Jira Performance Dashboard...")
    
    try:
        await generate_mock_data()
        print("✅ Mock data generated successfully!")
        print("📊 Generated data includes:")
        print("   - 3 projects")
        print("   - 5 users")
        print("   - 90 days of ticket history")
        print("   - Random commits and productivity data")
        print("\n🌐 You can now access the dashboard at http://localhost:3000")
        
    except Exception as e:
        print(f"❌ Error generating mock data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())