# MCP Servers for Waste Data Analysis

Compiled: 2026-01-15

## Overview

MCP (Model Context Protocol) is an open protocol that allows AI assistants to connect to external tools and data sources. For this project, MCP servers can enhance data exploration, querying, and workflow automation.

---

## Highly Relevant MCP Servers

### Database MCP Server
- **Package**: `@bytebase/dbhub`
- **Transport**: stdio
- **Use case**: Natural language queries against processed datasets
- **Installation**:
  ```bash
  claude mcp add --transport stdio db -- npx -y @bytebase/dbhub \
    --dsn "sqlite:///path/to/data.db"
  ```
- **Example queries**:
  - "What are the top 5 NUTS2 regions by metal waste generation?"
  - "Compare waste shipment volumes between Nordic countries"
  - "Find regions where waste generation exceeds treatment capacity"
- **Notes**: Would require converting CSV outputs to SQLite for optimal use

### Filesystem MCP Server
- **Package**: `@anthropic/mcp-server-filesystem`
- **Transport**: stdio
- **Use case**: Enhanced navigation of data directory structure
- **Installation**:
  ```bash
  claude mcp add --transport stdio fs -- npx -y @anthropic/mcp-server-filesystem \
    /path/to/mfa_project
  ```
- **Benefits**: Better file browsing across raw/interim/processed folders

### GitHub MCP Server
- **URL**: https://api.githubcopilot.com/mcp/
- **Transport**: http
- **Use case**: Issue tracking, collaboration, PR reviews
- **Installation**:
  ```bash
  claude mcp add --transport http github https://api.githubcopilot.com/mcp/
  ```
- **Example uses**:
  - Create issues for data quality problems
  - Track analysis tasks and findings
  - Collaborate on methodology decisions

---

## Potentially Useful MCP Servers

### Fetch/Web MCP Server
- **Package**: `@anthropic/mcp-server-fetch`
- **Transport**: stdio
- **Use case**: Access Eurostat API, documentation, metadata
- **Installation**:
  ```bash
  claude mcp add --transport stdio fetch -- npx -y @anthropic/mcp-server-fetch
  ```
- **Example uses**:
  - Fetch latest Eurostat dataset metadata
  - Access EU waste regulation documentation
  - Check for dataset updates

### Memory MCP Server
- **Package**: `@anthropic/mcp-server-memory`
- **Transport**: stdio
- **Use case**: Persist analysis context across sessions
- **Installation**:
  ```bash
  claude mcp add --transport stdio memory -- npx -y @anthropic/mcp-server-memory
  ```
- **Example uses**:
  - Remember key findings (e.g., "C24/C25 industries are primary metal waste generators")
  - Store methodology decisions
  - Track data quality issues discovered

---

## Configuration

### File Locations

| Scope | File | Shared? |
|-------|------|---------|
| Local | `~/.claude.json` | No |
| Project | `.mcp.json` (repo root) | Yes (via git) |
| User | `~/.claude.json` | No |

### Example `.mcp.json` for Project

```json
{
  "mcpServers": {
    "db": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub", "--dsn", "sqlite:///data/processed/mfa.db"]
    },
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

---

## Management Commands

```bash
claude mcp list              # List all configured servers
claude mcp get <name>        # Get server details
claude mcp remove <name>     # Remove a server
/mcp                         # Check status within Claude Code
```

---

## Priority Recommendation

For this waste data analysis project, the **Database MCP Server** would add the most value by enabling conversational data exploration of processed CSV files without writing pandas code for every query.

**Implementation steps**:
1. Create SQLite database from key processed CSVs
2. Configure database MCP server pointing to SQLite file
3. Query waste data through natural language

---

## References

- MCP Documentation: https://modelcontextprotocol.io/
- MCP Server Registry: https://api.anthropic.com/mcp-registry/docs
- Claude Code MCP Guide: https://docs.anthropic.com/en/docs/claude-code/mcp
