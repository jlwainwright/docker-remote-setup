import { Server, ServerOptions } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import * as path from 'path';
import { z } from 'zod';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface SQLiteServerConfig {
    databasePath: string;
    readOnly?: boolean;
}

// Define Zod schemas for our requests
const ToolCallRequestSchema = z.object({
    method: z.literal("tools/call"),
    params: z.object({
        name: z.string(),
        params: z.record(z.unknown())
    })
});

type ToolCallRequest = z.infer<typeof ToolCallRequestSchema>;

class SQLiteServer {
    private server: Server;
    private db: any;
    private config: SQLiteServerConfig;

    constructor(config: SQLiteServerConfig) {
        this.config = {
            readOnly: false,
            ...config
        };

        const serverInfo = {
            name: "sqlite-transactions",
            version: "1.0.0",
            description: "SQLite transaction analysis server"
        };

        const serverOptions: ServerOptions = {
            capabilities: {
                tools: {
                    GetTransactionSummary: {
                        title: "Get Transaction Summary",
                        description: "Get a summary of transactions within a date range",
                        inputSchema: {
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
                        },
                        examples: [
                            {
                                name: "January Summary",
                                params: {
                                    startDate: "2024-01-01",
                                    endDate: "2024-01-31"
                                }
                            }
                        ]
                    },
                    SearchTransactions: {
                        title: "Search Transactions",
                        description: "Search transactions by various criteria",
                        inputSchema: {
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
                        },
                        examples: [
                            {
                                name: "Search Netflix",
                                params: {
                                    merchant: "NETFLIX"
                                }
                            }
                        ]
                    },
                    GetCategories: {
                        title: "Get Categories",
                        description: "Get a list of all transaction categories with their total amounts",
                        inputSchema: {
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
                        },
                        examples: [
                            {
                                name: "All Categories",
                                params: {}
                            }
                        ]
                    },
                    GetMerchantAnalysis: {
                        title: "Get Merchant Analysis",
                        description: "Get analysis of transactions by merchant",
                        inputSchema: {
                            type: "object",
                            properties: {
                                merchant: {
                                    type: "string",
                                    description: "Merchant name to analyze"
                                }
                            },
                            required: ["merchant"]
                        },
                        examples: [
                            {
                                name: "Analyze Netflix",
                                params: {
                                    merchant: "NETFLIX"
                                }
                            }
                        ]
                    }
                }
            }
        };

        this.server = new Server(serverInfo, serverOptions);
        this.setupHandlers();
    }

    private setupHandlers() {
        // Handle tool calls
        this.server.setRequestHandler(ToolCallRequestSchema, async (request: ToolCallRequest) => {
            const { name, params } = request.params;

            switch (name) {
                case "GetTransactionSummary": {
                    const query = `
                        SELECT 
                            COUNT(*) as total_transactions,
                            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_inflow,
                            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_outflow,
                            AVG(amount) as average_amount,
                            COUNT(DISTINCT type) as distinct_types
                        FROM transactions 
                        WHERE date BETWEEN ? AND ?
                    `;
                    
                    const result = await this.db.get(query, [params.startDate, params.endDate]);
                    return { 
                        result: { summary: result }
                    };
                }

                case "SearchTransactions": {
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
                        LIMIT 50
                    `;

                    const results = await this.db.all(query, values);
                    return { 
                        result: { transactions: results }
                    };
                }

                case "GetCategories": {
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
                        ORDER BY total_amount DESC
                    `;

                    const results = await this.db.all(query, values);
                    return { 
                        result: { categories: results }
                    };
                }

                case "GetMerchantAnalysis": {
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
                        WHERE merchant = ?
                    `;

                    const result = await this.db.get(query, [params.merchant]);
                    return { 
                        result: { analysis: result }
                    };
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        });
    }

    private async setupDatabase() {
        try {
            const resolvedPath = path.resolve(process.cwd(), this.config.databasePath);
            
            this.db = await open({
                filename: resolvedPath,
                driver: sqlite3.Database,
                mode: this.config.readOnly ? sqlite3.OPEN_READONLY : sqlite3.OPEN_READWRITE
            });

            await this.db.get('SELECT COUNT(*) as count FROM transactions');
            
        } catch (err) {
            const error = err as Error;
            if (error.message?.includes('no such table')) {
                throw new Error('Database exists but schema is not initialized. Please run init-db.ts first.');
            } else if ('code' in error && error.code === 'SQLITE_CANTOPEN') {
                throw new Error('Could not open database file. Please check if the file exists and has correct permissions.');
            }
            throw error;
        }
    }

    public async start() {
        try {
            await this.setupDatabase();
            const transport = new StdioServerTransport();
            await this.server.connect(transport);
            process.stdin.resume();
        } catch (error) {
            process.stderr.write(`Error starting server: ${error}\n`);
            process.exit(1);
        }
    }

    private async shutdown() {
        try {
            if (this.db) {
                await this.db.close();
            }
            process.exit(0);
        } catch (error) {
            process.stderr.write(`Error during shutdown: ${error}\n`);
            process.exit(1);
        }
    }
}

export default SQLiteServer;