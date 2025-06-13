import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

async function initializeDatabase() {
    const dbPath = path.resolve(process.cwd(), 'transactions.db');
    console.log(`Initializing database at ${dbPath}`);

    const db = await open({
        filename: dbPath,
        driver: sqlite3.Database
    });

    try {
        // Drop existing table if it exists
        await db.exec('DROP TABLE IF EXISTS transactions');
        
        // Create fresh table
        await db.exec(`
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                merchant TEXT,
                amount REAL NOT NULL,
                category TEXT
            )
        `);

        // Insert some sample data
        await db.exec(`
            INSERT INTO transactions (date, type, merchant, amount, category) VALUES
            ('2024-01-01', 'Payment', 'NETFLIX', -15.99, 'Entertainment'),
            ('2024-01-02', 'Payment', 'AMAZON', -99.99, 'Shopping'),
            ('2024-01-03', 'Deposit', 'EMPLOYER', 5000.00, 'Income'),
            ('2024-01-04', 'Payment', 'GROCERY STORE', -156.78, 'Groceries'),
            ('2024-01-05', 'Payment', 'GAS STATION', -45.00, 'Transportation'),
            ('2024-01-06', 'Payment', 'SPOTIFY', -9.99, 'Entertainment')
        `);

        console.log('Database initialized successfully');
        
        // Verify data was inserted
        const count = await db.get('SELECT COUNT(*) as count FROM transactions');
        console.log(`Inserted ${count.count} transactions`);
        
        // Print schema
        const schema = await db.all("SELECT sql FROM sqlite_master WHERE type='table' AND name='transactions'");
        console.log('\nTable schema:', schema[0].sql);
        
    } catch (error) {
        console.error('Error initializing database:', error);
    } finally {
        await db.close();
    }
}

initializeDatabase().catch(console.error);