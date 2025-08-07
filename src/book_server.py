#!/usr/bin/env python3

import os
import json
import glob
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Set
import re
from collections import defaultdict, Counter

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Initialize the MCP server
server = Server("medium-book-mcp-server")

# Global variables for caching
chapter_cache = {}
chapter_index = []

# List of finished chapter titles (as provided by user)
FINISHED_CHAPTERS = {
    "Tim-s-Theory-of-Trails-7f9c33b1cf7d",
    "Visualizing-the-Difference-between-Analytics---Monitoring-3cd5881cf7ab", 
    "Five-Common-Product-Fails-b42aed30e7",
    "Metric-Display-Standards-54736533c81",
    "A-Natural-Reaction-ff1ce1c1f8b6",
    "How-to-Get-Started-Designing-for-Developers-2a454c3f699b",
    "Understanding-Data-a573693cdea8",
    "How-Product-Development-Works-Best-95109dcf065d",
    "Every-designer-needs-an-ethical-framework--b64f37ec890",
    "Co-Designing-the-Digital-Machine-45ac5c0a9dc2",
    "Window-Seat-98c38b5e3a3",
    "How-Much-User-Research-Is-Enough--d18d574f3f60",
    "Slack--I-m-still-into-you--bb58e7a85165",
    "Chatting-with-Your-Computer-40962d3d651f",
    "Managing-the-High-Throughput-Design-Studio-1969645a6c12",
    "The-Analytic-Workflow-3e551e67647f",
    "Interchangeable-Parts-d2ca009eaa5b",
    "The-User-Experience-of-Language-Design-e4668ce88fad"
}

def get_data_directory() -> Path:
    """Get the path to the data directory containing Medium articles."""
    return Path(__file__).parent.parent / "data"

def extract_chapter_content(html_path: Path) -> Dict[str, Any]:
    """Extract content and metadata from a Medium article HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title (try multiple selectors)
        title = None
        for selector in ['h1.p-name', 'h1', 'title', '.p-name', '[data-testid="storyTitle"]']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        if not title:
            title = html_path.stem.replace('-', ' ').title()
        
        # Extract subtitle/description
        subtitle_elem = soup.select_one('.p-summary, .graf--subtitle')
        subtitle = subtitle_elem.get_text().strip() if subtitle_elem else ""
        
        # Extract main content
        content_elem = soup.select_one('.e-content, article, .postArticle-content, main')
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
        
        # Extract any meta description
        meta_desc = soup.select_one('meta[name="description"]')
        description = meta_desc.get('content') if meta_desc else subtitle
        
        # Determine chapter status
        directory_name = html_path.parent.name
        is_finished = directory_name in FINISHED_CHAPTERS
        
        # Detect if this is a comment/response (very short, starts with person's name)
        is_comment = (
            len(text_content.split()) < 200 and 
            (title.count('--') > 0 or len(title.split()) < 4)
        )
        
        # Extract design concepts from title and content
        design_concepts = extract_design_concepts(title, text_content)
        
        return {
            'title': title,
            'subtitle': subtitle,
            'content': text_content,
            'description': description,
            'path': str(html_path),
            'directory': directory_name,
            'word_count': len(text_content.split()),
            'has_images': len(list((html_path.parent / 'img').glob('*'))) > 0 if (html_path.parent / 'img').exists() else False,
            'is_finished': is_finished,
            'is_comment': is_comment,
            'status': 'finished' if is_finished else ('comment' if is_comment else 'draft'),
            'design_concepts': design_concepts
        }
    except Exception as e:
        return {
            'title': html_path.stem.replace('-', ' ').title(),
            'subtitle': '',
            'content': f"Error reading article: {e}",
            'description': "",
            'path': str(html_path),
            'directory': html_path.parent.name,
            'word_count': 0,
            'has_images': False,
            'is_finished': False,
            'is_comment': False,
            'status': 'error',
            'design_concepts': [],
            'error': str(e)
        }

def extract_design_concepts(title: str, content: str) -> List[str]:
    """Extract key design concepts from title and content."""
    concepts = []
    
    # Common software design concepts to look for
    design_terms = [
        'user experience', 'ux', 'design system', 'product strategy', 'user research',
        'analytics', 'monitoring', 'data visualization', 'interface design', 'usability',
        'product development', 'design thinking', 'systems thinking', 'workflow',
        'development process', 'design patterns', 'user interface', 'ui',
        'product management', 'design standards', 'design process', 'design methodology',
        'design tools', 'design collaboration', 'design ethics', 'design philosophy',
        'design language', 'design principles', 'design decisions', 'design leadership'
    ]
    
    text = (title + ' ' + content).lower()
    
    for term in design_terms:
        if term in text:
            concepts.append(term)
    
    # Extract concepts from title words (simple approach)
    title_words = re.findall(r'\b[A-Za-z]{4,}\b', title.lower())
    for word in title_words:
        if word not in ['with', 'from', 'your', 'this', 'that', 'will', 'have', 'been', 'they', 'them', 'their', 'common', 'much', 'best', 'high']:
            if word not in [concept.split()[-1] for concept in concepts]:  # Avoid duplicates
                concepts.append(word)
    
    return concepts[:10]  # Limit to top 10 concepts

def build_chapter_index():
    """Build an index of all chapters in the data directory."""
    global chapter_cache, chapter_index
    
    data_dir = get_data_directory()
    if not data_dir.exists():
        return
    
    chapter_index = []
    chapter_cache = {}
    
    # Find all HTML files in article directories
    for html_file in data_dir.glob("*/*.html"):
        chapter_data = extract_chapter_content(html_file)
        chapter_id = html_file.parent.name
        
        chapter_cache[chapter_id] = chapter_data
        chapter_index.append({
            'id': chapter_id,
            'title': chapter_data['title'],
            'subtitle': chapter_data['subtitle'],
            'description': chapter_data['description'],
            'word_count': chapter_data['word_count'],
            'has_images': chapter_data['has_images'],
            'status': chapter_data['status'],
            'design_concepts': chapter_data['design_concepts']
        })

def find_related_chapters_by_concepts(target_concepts: List[str], exclude_id: str = None) -> List[Dict]:
    """Find chapters with overlapping design concepts."""
    if not target_concepts:
        return []
    
    related = []
    target_set = set(concept.lower() for concept in target_concepts)
    
    for chapter_id, chapter_data in chapter_cache.items():
        if exclude_id and chapter_id == exclude_id:
            continue
            
        chapter_concepts = set(concept.lower() for concept in chapter_data['design_concepts'])
        overlap = target_set.intersection(chapter_concepts)
        
        if overlap:
            related.append({
                'id': chapter_id,
                'title': chapter_data['title'],
                'status': chapter_data['status'],
                'overlap_score': len(overlap),
                'shared_concepts': list(overlap),
                'word_count': chapter_data['word_count']
            })
    
    return sorted(related, key=lambda x: x['overlap_score'], reverse=True)

def analyze_content_overlaps(chapter_ids: List[str]) -> Dict:
    """Analyze content overlaps between specific chapters."""
    if len(chapter_ids) < 2:
        return {"error": "Need at least 2 chapters to analyze overlaps"}
    
    chapters = []
    for chapter_id in chapter_ids:
        if chapter_id in chapter_cache:
            chapters.append(chapter_cache[chapter_id])
    
    if len(chapters) < 2:
        return {"error": "Not enough valid chapters found"}
    
    # Simple word overlap analysis
    all_words = []
    chapter_words = []
    
    for chapter in chapters:
        words = set(re.findall(r'\b[a-zA-Z]{4,}\b', chapter['content'].lower()))
        chapter_words.append(words)
        all_words.extend(words)
    
    # Find common words across all chapters
    word_counts = Counter(all_words)
    common_words = [word for word, count in word_counts.items() if count >= len(chapters)]
    
    # Find pairwise overlaps
    overlaps = []
    for i, chapter1 in enumerate(chapters):
        for j, chapter2 in enumerate(chapters[i+1:], i+1):
            overlap = chapter_words[i].intersection(chapter_words[j])
            overlaps.append({
                'chapter1': chapter1['title'],
                'chapter2': chapter2['title'],
                'overlap_words': len(overlap),
                'common_themes': list(overlap)[:10]  # Top 10 overlapping words
            })
    
    return {
        'chapters_analyzed': [ch['title'] for ch in chapters],
        'common_concepts': common_words[:20],  # Top 20 common words
        'pairwise_overlaps': overlaps
    }

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools for book writing."""
    return [
        types.Tool(
            name="find_related_chapters", 
            description="Find chapters with similar themes for potential combination or reference",
            inputSchema={
                "type": "object",
                "properties": {
                    "theme": {
                        "type": "string",
                        "description": "Theme or concept to find related chapters for"
                    },
                    "chapter_id": {
                        "type": "string", 
                        "description": "Optional: ID of a chapter to find chapters similar to"
                    },
                    "include_drafts": {
                        "type": "boolean",
                        "description": "Include draft chapters in results (default: true)",
                        "default": True
                    }
                }
            }
        ),
        types.Tool(
            name="analyze_chapter_completeness",
            description="Show completion status of all chapters (finished/draft/comment)",
            inputSchema={
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["all", "finished", "draft", "comment"],
                        "description": "Filter chapters by status (default: all)",
                        "default": "all"
                    }
                }
            }
        ),
        types.Tool(
            name="get_chapter_content",
            description="Get full content of a specific chapter for editing/reference",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter_id": {
                        "type": "string",
                        "description": "The ID/directory name of the chapter"
                    }
                },
                "required": ["chapter_id"]
            }
        ),
        types.Tool(
            name="extract_design_philosophy",
            description="Extract core design concepts and philosophy themes across chapters",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific chapter IDs to analyze (if empty, analyzes all finished chapters)"
                    },
                    "concept_depth": {
                        "type": "string",
                        "enum": ["surface", "deep"],
                        "description": "Level of concept analysis (default: surface)",
                        "default": "surface"
                    }
                }
            }
        ),
        types.Tool(
            name="identify_content_overlaps",
            description="Find redundant or complementary material between chapters for merging decisions",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of chapter IDs to analyze for overlaps",
                        "minItems": 2
                    }
                },
                "required": ["chapter_ids"]
            }
        ),
        types.Tool(
            name="suggest_book_structure",
            description="Analyze potential chapter sequences and book organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_type": {
                        "type": "string", 
                        "enum": ["conceptual", "chronological", "complexity", "workflow"],
                        "description": "How to organize chapters (default: conceptual)",
                        "default": "conceptual"
                    },
                    "include_drafts": {
                        "type": "boolean",
                        "description": "Include draft chapters in structure (default: false)",
                        "default": False
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle MCP tool calls for book writing workflow."""
    
    # Ensure chapter index is built
    if not chapter_index:
        build_chapter_index()
    
    if name == "find_related_chapters":
        theme = arguments.get("theme", "")
        chapter_id = arguments.get("chapter_id")
        include_drafts = arguments.get("include_drafts", True)
        
        if chapter_id and chapter_id in chapter_cache:
            # Find chapters similar to the specified chapter
            target_concepts = chapter_cache[chapter_id]['design_concepts']
            related = find_related_chapters_by_concepts(target_concepts, exclude_id=chapter_id)
            result_text = f"Chapters related to '{chapter_cache[chapter_id]['title']}':\n\n"
        elif theme:
            # Find chapters related to theme
            related = find_related_chapters_by_concepts([theme])
            result_text = f"Chapters related to theme '{theme}':\n\n"
        else:
            return [types.TextContent(type="text", text="Error: Must provide either 'theme' or 'chapter_id'")]
        
        if not include_drafts:
            related = [r for r in related if chapter_cache[r['id']]['status'] == 'finished']
        
        for chapter in related[:10]:  # Top 10 results
            result_text += f"**{chapter['title']}** ({chapter['status']})\n"
            result_text += f"ID: {chapter['id']}\n"
            result_text += f"Shared concepts: {', '.join(chapter['shared_concepts'])}\n"
            result_text += f"Words: {chapter['word_count']}, Overlap score: {chapter['overlap_score']}\n\n"
        
        if not related:
            result_text += "No related chapters found.\n"
            
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "analyze_chapter_completeness":
        status_filter = arguments.get("status_filter", "all")
        
        chapters_by_status = defaultdict(list)
        for chapter in chapter_index:
            chapters_by_status[chapter['status']].append(chapter)
        
        result_text = "Chapter Completion Analysis:\n\n"
        
        if status_filter == "all" or status_filter == "finished":
            result_text += f"**Finished Chapters ({len(chapters_by_status['finished'])}):**\n"
            for chapter in sorted(chapters_by_status['finished'], key=lambda x: x['word_count'], reverse=True):
                result_text += f"- {chapter['title']} ({chapter['word_count']} words)\n"
            result_text += "\n"
        
        if status_filter == "all" or status_filter == "draft":
            result_text += f"**Draft Chapters ({len(chapters_by_status['draft'])}):**\n"
            for chapter in sorted(chapters_by_status['draft'], key=lambda x: x['word_count'], reverse=True):
                result_text += f"- {chapter['title']} ({chapter['word_count']} words)\n"
            result_text += "\n"
        
        if status_filter == "all" or status_filter == "comment":
            result_text += f"**Comments/Responses ({len(chapters_by_status['comment'])}):**\n"
            for chapter in chapters_by_status['comment']:
                result_text += f"- {chapter['title']} ({chapter['word_count']} words)\n"
            result_text += "\n"
        
        result_text += f"**Summary:** {len(chapters_by_status['finished'])} finished, {len(chapters_by_status['draft'])} drafts, {len(chapters_by_status['comment'])} comments\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "get_chapter_content":
        chapter_id = arguments.get("chapter_id")
        if not chapter_id:
            return [types.TextContent(type="text", text="Error: chapter_id is required")]
        
        if chapter_id not in chapter_cache:
            return [types.TextContent(type="text", text=f"Error: Chapter '{chapter_id}' not found")]
        
        chapter = chapter_cache[chapter_id]
        result_text = f"# {chapter['title']}\n\n"
        
        if chapter['subtitle']:
            result_text += f"**Subtitle:** {chapter['subtitle']}\n\n"
        
        result_text += f"**Status:** {chapter['status'].title()}\n"
        result_text += f"**Word Count:** {chapter['word_count']}\n"
        result_text += f"**Has Images:** {'Yes' if chapter['has_images'] else 'No'}\n"
        result_text += f"**Design Concepts:** {', '.join(chapter['design_concepts'])}\n"
        result_text += f"**File Path:** {chapter['path']}\n\n"
        result_text += "## Content\n\n"
        result_text += chapter['content']
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "extract_design_philosophy":
        chapter_ids = arguments.get("chapter_ids", [])
        concept_depth = arguments.get("concept_depth", "surface")
        
        if not chapter_ids:
            # Analyze all finished chapters
            chapter_ids = [ch['id'] for ch in chapter_index if ch['status'] == 'finished']
        
        all_concepts = []
        chapter_concepts = {}
        
        for chapter_id in chapter_ids:
            if chapter_id in chapter_cache:
                concepts = chapter_cache[chapter_id]['design_concepts']
                all_concepts.extend(concepts)
                chapter_concepts[chapter_id] = concepts
        
        concept_counts = Counter(all_concepts)
        top_concepts = concept_counts.most_common(20)
        
        result_text = f"Design Philosophy Analysis ({len(chapter_ids)} chapters):\n\n"
        result_text += "**Core Design Concepts:**\n"
        for concept, count in top_concepts:
            result_text += f"- **{concept.title()}**: appears in {count} chapter{'s' if count > 1 else ''}\n"
        
        result_text += f"\n**Concept Distribution Across Chapters:**\n"
        for chapter_id in chapter_ids[:10]:  # Show first 10
            if chapter_id in chapter_cache:
                title = chapter_cache[chapter_id]['title']
                concepts = chapter_concepts.get(chapter_id, [])
                result_text += f"- **{title}**: {', '.join(concepts[:5])}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "identify_content_overlaps":
        chapter_ids = arguments.get("chapter_ids", [])
        if len(chapter_ids) < 2:
            return [types.TextContent(type="text", text="Error: Need at least 2 chapter IDs")]
        
        overlap_analysis = analyze_content_overlaps(chapter_ids)
        
        if "error" in overlap_analysis:
            return [types.TextContent(type="text", text=f"Error: {overlap_analysis['error']}")]
        
        result_text = f"Content Overlap Analysis:\n\n"
        result_text += f"**Chapters Analyzed:** {', '.join(overlap_analysis['chapters_analyzed'])}\n\n"
        
        result_text += f"**Common Themes:** {', '.join(overlap_analysis['common_concepts'][:15])}\n\n"
        
        result_text += f"**Pairwise Overlaps:**\n"
        for overlap in overlap_analysis['pairwise_overlaps']:
            result_text += f"- **{overlap['chapter1']}** & **{overlap['chapter2']}**: {overlap['overlap_words']} shared terms\n"
            result_text += f"  Key themes: {', '.join(overlap['common_themes'][:5])}\n\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    elif name == "suggest_book_structure":
        organization_type = arguments.get("organization_type", "conceptual")
        include_drafts = arguments.get("include_drafts", False)
        
        # Filter chapters based on include_drafts
        if include_drafts:
            relevant_chapters = [ch for ch in chapter_index if ch['status'] in ['finished', 'draft']]
        else:
            relevant_chapters = [ch for ch in chapter_index if ch['status'] == 'finished']
        
        if organization_type == "conceptual":
            # Group by design concepts
            concept_groups = defaultdict(list)
            for chapter in relevant_chapters:
                # Use first major concept as primary grouping
                primary_concept = next((c for c in chapter['design_concepts'] if len(c.split()) > 1), 
                                     chapter['design_concepts'][0] if chapter['design_concepts'] else 'general')
                concept_groups[primary_concept].append(chapter)
        
        elif organization_type == "complexity":
            # Sort by word count (complexity proxy)
            relevant_chapters.sort(key=lambda x: x['word_count'])
        
        result_text = f"Suggested Book Structure ({organization_type} organization):\n\n"
        
        if organization_type == "conceptual":
            for i, (concept, chapters) in enumerate(concept_groups.items(), 1):
                result_text += f"## Section {i}: {concept.title()}\n"
                for chapter in sorted(chapters, key=lambda x: x['word_count'], reverse=True):
                    result_text += f"- {chapter['title']} ({chapter['word_count']} words, {chapter['status']})\n"
                result_text += "\n"
        else:
            result_text += "## Suggested Chapter Sequence:\n"
            for i, chapter in enumerate(relevant_chapters, 1):
                result_text += f"{i}. {chapter['title']} ({chapter['word_count']} words, {chapter['status']})\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    else:
        return [types.TextContent(type="text", text=f"Error: Unknown tool '{name}'")]

async def main():
    """Main entry point for the MCP server."""
    # Build the initial chapter index
    build_chapter_index()
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="medium-book-mcp-server",
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