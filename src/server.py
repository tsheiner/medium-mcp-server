#!/usr/bin/env python3

import os
import json
import glob
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Initialize the MCP server
server = Server("medium-mcp-server")

# Global variables for caching
article_cache = {}
article_index = []

def get_data_directory() -> Path:
    """Get the path to the data directory containing Medium articles."""
    return Path(__file__).parent.parent / "data"

def extract_article_content(html_path: Path) -> Dict[str, Any]:
    """Extract content and metadata from a Medium article HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title (try multiple selectors)
        title = None
        for selector in ['h1', 'title', '.p-name', '[data-testid="storyTitle"]']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        if not title:
            title = html_path.stem.replace('-', ' ').title()
        
        # Extract main content
        content_elem = soup.select_one('article, .postArticle-content, .e-content, main')
        if content_elem:
            # Remove script and style elements
            for script in content_elem(["script", "style"]):
                script.decompose()
            text_content = content_elem.get_text()
        else:
            # Fallback: get all text
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text()
        
        # Clean up text
        text_content = re.sub(r'\n\s*\n', '\n\n', text_content.strip())
        
        # Extract any meta description or summary
        meta_desc = soup.select_one('meta[name="description"]')
        description = meta_desc.get('content') if meta_desc else ""
        
        return {
            'title': title,
            'content': text_content,
            'description': description,
            'path': str(html_path),
            'directory': html_path.parent.name,
            'word_count': len(text_content.split()),
            'has_images': len(list((html_path.parent / 'img').glob('*'))) > 0 if (html_path.parent / 'img').exists() else False
        }
    except Exception as e:
        return {
            'title': html_path.stem.replace('-', ' ').title(),
            'content': f"Error reading article: {e}",
            'description': "",
            'path': str(html_path),
            'directory': html_path.parent.name,
            'word_count': 0,
            'has_images': False,
            'error': str(e)
        }

def build_article_index():
    """Build an index of all articles in the data directory."""
    global article_cache, article_index
    
    data_dir = get_data_directory()
    if not data_dir.exists():
        return
    
    article_index = []
    article_cache = {}
    
    # Find all HTML files in article directories
    for html_file in data_dir.glob("*/*.html"):
        article_data = extract_article_content(html_file)
        article_id = html_file.parent.name
        
        article_cache[article_id] = article_data
        article_index.append({
            'id': article_id,
            'title': article_data['title'],
            'description': article_data['description'],
            'word_count': article_data['word_count'],
            'has_images': article_data['has_images']
        })

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="search_articles",
            description="Search through Medium articles by keyword or theme",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for article content"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_article",
            description="Get the full content of a specific Medium article",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "The ID/directory name of the article"
                    }
                },
                "required": ["article_id"]
            }
        ),
        types.Tool(
            name="list_articles",
            description="List all available Medium articles with basic metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        types.Tool(
            name="get_article_topics",
            description="Extract key topics and themes from articles",
            inputSchema={
                "type": "object", 
                "properties": {
                    "article_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of article IDs to analyze (if empty, analyzes all articles)"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle MCP tool calls."""
    
    # Ensure article index is built
    if not article_index:
        build_article_index()
    
    if name == "search_articles":
        query = arguments.get("query", "").lower()
        limit = arguments.get("limit", 10)
        
        matching_articles = []
        for article_id, article_data in article_cache.items():
            # Simple text search
            content_lower = article_data['content'].lower()
            title_lower = article_data['title'].lower()
            
            if query in content_lower or query in title_lower:
                matching_articles.append({
                    'id': article_id,
                    'title': article_data['title'],
                    'description': article_data['description'],
                    'relevance': content_lower.count(query) + title_lower.count(query) * 2
                })
        
        # Sort by relevance
        matching_articles.sort(key=lambda x: x['relevance'], reverse=True)
        results = matching_articles[:limit]
        
        result_text = f"Found {len(results)} articles matching '{query}':\n\n"
        for article in results:
            result_text += f"**{article['title']}** (ID: {article['id']})\n"
            if article['description']:
                result_text += f"Description: {article['description']}\n"
            result_text += f"Relevance score: {article['relevance']}\n\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "get_article":
        article_id = arguments.get("article_id")
        if not article_id:
            return [types.TextContent(type="text", text="Error: article_id is required")]
        
        if article_id not in article_cache:
            return [types.TextContent(type="text", text=f"Error: Article '{article_id}' not found")]
        
        article = article_cache[article_id]
        result_text = f"# {article['title']}\n\n"
        if article['description']:
            result_text += f"**Description:** {article['description']}\n\n"
        
        result_text += f"**Word Count:** {article['word_count']}\n"
        result_text += f"**Has Images:** {'Yes' if article['has_images'] else 'No'}\n"
        result_text += f"**File Path:** {article['path']}\n\n"
        result_text += "## Content\n\n"
        result_text += article['content']
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "list_articles":
        limit = arguments.get("limit", 20)
        articles = article_index[:limit]
        
        result_text = f"Available Medium Articles ({len(articles)} of {len(article_index)} total):\n\n"
        for article in articles:
            result_text += f"**{article['title']}** (ID: {article['id']})\n"
            if article['description']:
                result_text += f"Description: {article['description']}\n"
            result_text += f"Words: {article['word_count']}, Images: {'Yes' if article['has_images'] else 'No'}\n\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "get_article_topics":
        article_ids = arguments.get("article_ids", [])
        if not article_ids:
            article_ids = list(article_cache.keys())
        
        # Simple keyword extraction from titles
        topics = {}
        for article_id in article_ids:
            if article_id in article_cache:
                article = article_cache[article_id]
                # Extract keywords from title (simple approach)
                words = re.findall(r'\b[A-Za-z]{4,}\b', article['title'].lower())
                for word in words:
                    if word not in ['with', 'from', 'your', 'this', 'that', 'will', 'have', 'been', 'they', 'them', 'their']:
                        topics[word] = topics.get(word, 0) + 1
        
        # Sort topics by frequency
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:20]
        
        result_text = f"Key topics from {len(article_ids)} articles:\n\n"
        for topic, count in sorted_topics:
            result_text += f"- **{topic.title()}**: appears in {count} article{'s' if count > 1 else ''}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    else:
        return [types.TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

async def main():
    """Main entry point for the MCP server."""
    # Build the initial article index
    build_article_index()
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="medium-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
