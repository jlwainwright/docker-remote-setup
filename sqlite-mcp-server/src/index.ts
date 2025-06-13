import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import * as path from 'path';
import { z } from 'zod';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize MCP Server
const mcp = new Server(
  {
    name: "sqlite-transactions",
    version: "1.0.0",
    description: "SQLite transaction analysis server"
  },
  {
    capabilities: {
      tools: {
        "get-transaction-summary": {
          title: "Get Transaction Summary",
          description: "Get a summary of transactions within a date range",
          schema: {
            type: "object",
            properties: {
              startDate: {
                type: "string",
                description: "Start date in YYYY-MM-DD format"
              },
              endDate: {
                type: "string",
                description: "End date in YYYY-MM-DD format"
              }
            },
            required: ["startDate", "endDate"]
          }
        },
        "search-transactions": {
          title: "Search Transactions",
          description: "Search transactions by various criteria",
          schema: {
            type: "object",
            properties: {
              type: {
                type: "string",
                description: "Transaction type"
              },
              merchant: {
                type: "string",
                description: "Merchant name"
              },
              minAmount: {
                type: "number",
                description: "Minimum transaction amount"
              },
              maxAmount: {
                type: "number",
                description: "Maximum transaction amount"
              },
              category: {
                type: "string",
                description: "Transaction category"
              }
            }
          }
        },
        "get-categories": {
          title: "Get Categories",
          description: "Get a list of all transaction categories with their total amounts",
          schema: {
            type: "object",
            properties: {
              startDate: {
                type: "string",
                description: "Optional start date in YYYY-MM-DD format"
              },
              endDate: {
                type: "string",
                description: "Optional end date in YYYY-MM-DD format"
              }
            }
          }
        },
        "get-merchant-analysis": {
          title: "Get Merchant Analysis",
          description: "Get analysis of transactions by merchant",
          schema: {
            type: "object",
            properties: {
              merchant: {
                type: "string",
                description: "Merchant name to analyze"
              }
            },
            required: ["merchant"]
          }
        }
      }
    }
  }
);

// Database connection
let db: any;

// Set up database
async function setupDatabase() {
  const dbPath = process.argv[2] || './transactions.db';
  const resolvedPath = path.resolve(process.cwd(), dbPath);
  
  db = await open({
    filename: resolvedPath,
    driver: sqlite3.Database
  });

  // Verify database connection
  await db.get('SELECT COUNT(*) as count FROM transactions');
}

// Define tool call schema
const ToolCallSchema = z.object({
  method: z.literal("tools/call"),
  params: z.object({
    name: z.string(),
    params: z.record(z.unknown())
  })
});

// Handle tool calls
mcp.setRequestHandler(ToolCallSchema, async (request) => {
  const { name, params } = request.params;

  switch (name) {
    case "get-transaction-summary": {
      const query = `
        SELECT 
          COUNT(*) as total_transactions,
          SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_inflow,
          SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_outflow,
          AVG(amount) as average_amount,
          COUNT(DISTINCT type) as distinct_types
        FROM transactions 
        WHERE date BETWEEN ? AND ?`;
      
      const result = await db.get(query, [params.startDate, params.endDate]);
      return { result: { summary: result } };
    }

    case "search-transactions": {
      const conditions = [];
      const values = [];

      if (params.type) {
        conditions.push('type = ?');
        values.push(params.type);
      }
      if (params.merchant) {
        conditions.push('merchant = ?');
        values.push(params.merchant);
      }
      if (params.minAmount !== undefined) {
        conditions.push('amount >= ?');
        values.push(params.minAmount);
      }
      if (params.maxAmount !== undefined) {
        conditions.push('amount <= ?');
        values.push(params.maxAmount);
      }
      if (params.category) {
        conditions.push('category = ?');
        values.push(params.category);
      }

      const whereClause = conditions.length > 0 
        ? 'WHERE ' + conditions.join(' AND ')
        : '';

      const query = `
        SELECT * FROM transactions 
        ${whereClause}
        ORDER BY date DESC
        LIMIT 50`;

      const results = await db.all(query, values);
      return { result: { transactions: results } };
    }

    case "get-categories": {
      let whereClause = '';
      let values: any[] = [];

      if (params.startDate && params.endDate) {
        whereClause = 'WHERE date BETWEEN ? AND ?';
        values = [params.startDate, params.endDate];
      }

      const query = `
        SELECT 
          category,
          COUNT(*) as transaction_count,
          SUM(amount) as total_amount,
          AVG(amount) as average_amount
        FROM transactions
        ${whereClause}
        GROUP BY category
        ORDER BY total_amount DESC`;

      const results = await db.all(query, values);
      return { result: { categories: results } };
    }

    case "get-merchant-analysis": {
      const query = `
        SELECT 
          COUNT(*) as transaction_count,
          SUM(amount) as total_amount,
          AVG(amount) as average_amount,
          MIN(amount) as min_amount,
          MAX(amount) as max_amount,
          MIN(date) as first_transaction,
          MAX(date) as last_transaction
        FROM transactions 
        WHERE merchant = ?`;

      const result = await db.get(query, [params.merchant]);
      return { result: { analysis: result } };
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Run server
async function main() {
  try {
    await setupDatabase();
    const transport = new StdioServerTransport();
    await mcp.connect(transport);
    process.stdin.resume();
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Server failed to start:', error);
    process.exit(1);
  });
}