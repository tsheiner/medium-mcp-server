# Medium MCP Server Development Plan

## Project Goal
Build a local MCP server that helps author structure a software design wisdom book by providing Claude with intelligent access to Medium article archive. The server treats each Medium essay as a potential book chapter and helps with combining drafts, identifying themes, and structuring the overall narrative flow.

## Current Status
- ✅ Medium bulk export completed
- ✅ Script processed to download images and update HTML paths
- ✅ Archive organized in `export/article-name/` directories with `article.html` + `img/` folders
- 🎯 **Next**: Build MCP server to index and serve this content

## Technical Stack
- **Language**: Python (selected for rapid development and rich text processing libraries)
- **MCP Protocol**: Uses Claude's Model Context Protocol for local tool integration
- **Storage**: Local filesystem (the processed Medium archive)
- **Deployment**: Local server, no hosting required

## Archive Structure
```
export/
├── article-1-title/
│   ├── article.html (with local image refs)
│   └── img/
│       ├── image1.jpg
│       └── image2.png
├── article-2-title/
│   ├── article.html
│   └── img/
│       └── banner.jpg
└── article-n-title/
    ├── article.html
    └── img/
```

## Development Process

### Phase 1: MCP Server Foundation
1. **Setup MCP server boilerplate**
   - Install MCP SDK
   - Create basic server structure
   - Configure Claude Desktop integration

### Phase 2: Content Processing
2. **Parse Medium archive**
   - Read HTML files from `export/*/article.html`
   - Extract metadata (title, date, tags, content)
   - Build searchable index
   - Handle image references

### Phase 3: MCP Tools Implementation
3. **Core search tools**
   - `search_articles(query)` - keyword/theme search
   - `get_article(id)` - retrieve full content
   - `list_topics()` - show all themes/tags
   - `find_similar(article_id)` - content similarity

### Phase 4: Advanced Features
4. **Content analysis tools**
   - Writing style analysis
   - Theme extraction
   - Topic clustering
   - Content gap identification

## Planned MCP Tools (Book-Chapter Paradigm)

| Tool Name | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `find_related_chapters` | Find essays around a theme to potentially combine | theme/concept | clustered related essays |
| `analyze_chapter_completeness` | Detect which essays are finished vs drafts | none/essay ID | completion status analysis |
| `extract_design_concepts` | Map design philosophy themes across essays | essay set | core concept taxonomy |
| `identify_content_overlaps` | Find redundant/complementary material for merging | essay IDs | overlap analysis |
| `suggest_chapter_sequence` | Analyze how essays could flow as book chapters | theme/concept | suggested chapter ordering |
| `get_chapter_content` | Get full essay content for editing/combining | chapter ID | complete essay with metadata |

## Key Context for Next Session

### User Profile
- **Technical comfort level**: Sufficient for MCP development with AI guidance
- **Publishing frequency**: Infrequent (bulk export approach works well)
- **Archive status**: Already processed with images downloaded locally
- **Primary goal**: Brainstorming tool for extending existing Medium themes

### Technical Context
- **Archive location**: `data/` directory with subdirs for each article
- **File structure**: `article-name/article.html` + `article-name/img/`
- **Images**: Already downloaded and HTML updated with local paths
- **Integration target**: Claude Desktop via MCP connection

### Background
The user has a script that enhanced Medium's bulk export by downloading all referenced images and updating HTML files to use local paths. This solves Medium's limitation of not including images in their official export.

## Next Immediate Steps

1. **Environment Setup**
   - Choose Python vs TypeScript for MCP server
   - Install MCP development dependencies
   - Verify Claude Desktop installation

2. **Basic Server Creation**
   - Create MCP server boilerplate
   - Implement basic connection to Claude Desktop
   - Test server registration and ping

3. **Content Parsing**
   - Build HTML parser for Medium export files
   - Extract article metadata and content
   - Create article indexing system

4. **Core Tool Implementation**
   - Implement `list_articles` tool first
   - Add `search_articles` functionality
   - Test integration with Claude

5. **Advanced Features**
   - Add content similarity analysis
   - Implement theme extraction
   - Build writing style analysis tools

## Questions for Next Session

- Programming language preference (Python/TypeScript)?
- Any specific search/analysis features to prioritize?
- Claude Desktop already installed for MCP connection?
- Preferred development environment/IDE?
- Any particular content themes or patterns you want to focus on first?

## Success Criteria

The MCP server will be successful when:
- Claude can search across all Medium articles instantly
- Article content and images are accessible for reference
- Writing themes and patterns can be analyzed
- New content ideas can be generated based on existing work
- The system works reliably for brainstorming sessions

## Resources Needed

- Medium export archive (✅ Complete)
- MCP SDK documentation
- HTML parsing library
- Text search/indexing capabilities
- Claude Desktop with MCP configuration