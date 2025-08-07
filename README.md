# Medium MCP Server for Book Writing

Transform your Medium article archive into an intelligent writing assistant using Claude Desktop and the Model Context Protocol (MCP).

## What This Does

This MCP server gives Claude Desktop deep access to your Medium article collection, enabling sophisticated analysis and writing support for authors looking to:

- **Structure a book** from existing Medium essays
- **Find related content** across your writing to combine or reference  
- **Analyze themes and concepts** in your work
- **Identify content gaps** and writing opportunities
- **Organize chapters** by topic, complexity, or narrative flow
- **Merge multiple essay drafts** into cohesive chapters

Perfect for authors who have been writing on Medium and want to transform their distributed thoughts into a structured book.

## Features

### Core Writing Tools
- **`find_related_chapters`** - Find essays with similar themes for combination or reference
- **`analyze_chapter_completeness`** - Track which pieces are finished vs drafts vs comments
- **`get_chapter_content`** - Access full essay content for editing and review
- **`extract_design_philosophy`** - Map recurring themes across your body of work
- **`identify_content_overlaps`** - Find redundant or complementary material between essays
- **`suggest_book_structure`** - Generate potential chapter sequences and organization

### Intelligent Analysis
- Automatically categorizes essays as finished chapters, drafts, or comment responses
- Extracts key concepts and themes from your writing
- Finds content overlaps to help merge related essays
- Suggests book organization by theme, complexity, or workflow
- Tracks writing patterns and recurring ideas

## Prerequisites

1. **Medium Article Export**: You need your Medium articles in a specific directory structure with images downloaded locally
2. **Claude Desktop**: The MCP client for accessing the tools
3. **Python 3.8+**: To run the MCP server

## Getting Your Medium Data

This server requires your Medium articles in a specific format with locally downloaded images. Use the companion repository to prepare your data:

**[Medium Archive Image Downloader](https://github.com/tsheiner/medium-archive-image-downloader)**

That tool processes Medium's bulk export to:
- Download all referenced images locally
- Update HTML files to use local image paths  
- Organize articles in the required directory structure

## Installation

### 1. Clone and Setup

```bash
git clone <this-repo>
cd medium_mcp_server
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare Your Data

Place your processed Medium archive in the `data/` directory. The structure should look like:

```
data/
├── Article-Title-1-abc123/
│   ├── Article-Title-1-abc123.html
│   └── img/
│       ├── image1.jpg
│       └── image2.png
├── Article-Title-2-def456/
│   ├── Article-Title-2-def456.html
│   └── img/
└── ...
```

### 5. Configure Finished Essays

Edit `src/book_server.py` and update the `FINISHED_CHAPTERS` set with the directory names of your completed essays:

```python
FINISHED_CHAPTERS = {
    "Your-Finished-Essay-1-abc123",
    "Another-Complete-Article-def456",
    # Add your finished essay directory names here
}
```

### 6. Test the Server

```bash
python src/book_server.py
```

If successful, the server will start and show how many chapters it indexed (e.g., "Successfully indexed 46 chapters").

## Claude Desktop Integration

### 1. Find Your Claude Desktop Config

- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\\Claude\\claude_desktop_config.json`

### 2. Add the MCP Server

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "medium-book-mcp-server": {
      "command": "/path/to/your/venv/bin/python3",
      "args": ["/path/to/medium_mcp_server/src/book_server.py"],
      "env": {}
    }
  }
}
```

**Important**: Use the full path to your virtual environment's Python executable. Find it with:

```bash
# In your activated venv:
which python3
```

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop to load the new server.

## Usage Examples

Once configured, you can ask Claude questions like:

### Content Discovery
- "What themes do I write about most frequently?"
- "Show me all my essays about user experience"
- "Which of my articles are substantial enough to be book chapters?"

### Book Structure Planning  
- "Help me organize my finished essays into a logical book structure"
- "What would make good opening vs closing chapters?"
- "Group my essays by theme for potential book sections"

### Content Combination
- "I have multiple drafts about design systems - help me see how to combine them"
- "Find essays that overlap in content so I can merge them"
- "Which articles complement each other and should be sequential chapters?"

### Writing Strategy
- "What design concepts am I missing from my collection?"
- "Identify patterns in my most successful pieces"
- "What topics do I keep returning to?"

## Customization

### Adding Your Own Concepts

Edit the `extract_design_concepts()` function in `src/book_server.py` to include terminology specific to your domain:

```python
design_terms = [
    'your domain term 1',
    'your domain term 2', 
    # Add concepts relevant to your writing
]
```

### Adjusting Chapter Status

The server automatically categorizes essays, but you can fine-tune the logic in `extract_chapter_content()` based on your writing patterns.

## Troubleshooting

### Server Won't Start
- Check that your virtual environment is activated and has all dependencies
- Ensure the `data/` directory exists and contains your Medium articles
- Look at Claude Desktop's MCP logs for specific error messages

### No Articles Found
- Verify your data directory structure matches the expected format
- Check that HTML files are directly inside article directories
- Run the server manually to see indexing output

### Missing Dependencies
- Make sure you're using the virtual environment's Python in the Claude config
- Reinstall requirements with `pip install -r requirements.txt`

## Contributing

This tool is designed to be extensible. Potential enhancements:

- More sophisticated content analysis
- Export functions for book outlines
- Integration with writing tools
- Enhanced theme extraction
- Collaborative writing features

## License

MIT License - Use this to build your book!

---

## Related Projects

- [Medium Archive Image Downloader](https://github.com/tsheiner/medium-archive-image-downloader) - Prepare your Medium export for this tool
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that powers Claude integrations