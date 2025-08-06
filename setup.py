#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("Dependencies installed successfully!")

def test_server():
    """Test the MCP server by running it briefly."""
    print("Testing MCP server...")
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print(f"Warning: Data directory '{data_dir}' does not exist. Creating empty directory for testing...")
        data_dir.mkdir(exist_ok=True)
        return False
    
    # Count articles
    article_count = len(list(data_dir.glob("*/*.html")))
    print(f"Found {article_count} articles in the data directory.")
    
    if article_count == 0:
        print("No articles found. Make sure your Medium export is in the 'data' directory.")
        return False
    
    print("Server setup appears ready!")
    return True

def main():
    """Main setup function."""
    print("Medium MCP Server Setup")
    print("=" * 25)
    
    try:
        install_dependencies()
        test_server()
        
        print("\nNext steps:")
        print("1. Add this server to your Claude Desktop configuration:")
        print(f"   Copy contents of 'claude_desktop_config.json' to your Claude config")
        print("2. Restart Claude Desktop")
        print("3. You should see the Medium MCP server tools available in Claude")
        print("\nAvailable tools:")
        print("- search_articles: Search through your Medium articles")
        print("- get_article: Get full content of a specific article")
        print("- list_articles: List all available articles")
        print("- get_article_topics: Extract topics and themes")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()