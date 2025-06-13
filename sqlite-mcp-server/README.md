# SQLite Transaction Analysis MCP Server

A Model Context Protocol (MCP) server for analyzing bank transactions stored in a SQLite database.

## Features

- Transaction summary and analysis
- Category-based analysis
- Merchant analysis
- Flexible transaction search
- Read-only access for security

## Installation

1. Ensure you have Node.js installed
2. Clone this repository
3. Install dependencies:
```bash
npm install
```

## Setting up the Database

1. Initialize the database:
```bash
npx ts-node src/init-db.ts
```

This will create a sample database with test transactions.

## Starting the Server

```bash
npx ts-node src/sqlite-server.ts transactions.db
```

## Integration with Claude for Desktop

Add the following configuration to your Claude for Desktop configuration file (typically at `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "sqlite-transactions": {
      "command": "npx",
      "args": ["ts-node", "src/sqlite-server.ts", "transactions.db"],
      "cwd": "/Users/jacques/DevFolder/sqlite-mcp-server"
    }
  }
}
```

## Available Tools

1. `get_transaction_summary`: Get a summary of transactions within a date range
2. `search_transactions`: Search transactions by various criteria
3. `get_categories`: Get transaction categories with summary statistics
4. `get_merchant_analysis`: Analyze transactions for a specific merchant

## Security

- Read-only access by default
- SQL injection prevention
- Input validation
- Error handling

## Development

Build TypeScript:
```bash
npm run build
```

Run in development mode:
```bash
npm run dev transactions.db
```

## License

MIT