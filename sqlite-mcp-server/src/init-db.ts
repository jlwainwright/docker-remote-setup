import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import * as fs from 'fs';
import * as path from 'path';

async function initializeDatabase() {
    const dbPath = path.resolve(process.cwd(), 'transactions.db');
    console.log(`Initializing database at: ${dbPath}`);

    try {
        // Remove existing database if it exists
        if (fs.existsSync(dbPath)) {
            console.log('Removing existing database...');
            fs.unlinkSync(dbPath);
        }

        // Create or open the database
        const db = await open({
            filename: dbPath,
            driver: sqlite3.Database
        });

        // Read and execute schema
        const schema = await fs.promises.readFile(path.join(__dirname, 'schema.sql'), 'utf-8');
        await db.exec(schema);
        console.log('Schema created successfully');

        // Sample data
        const sampleTransactions = [
            {
                id: '09c8db25f6711da82417b73cbc8d3451',
                date: '2024-12-18 00:00:00',
                transaction_date: '2024-12-18 00:00:00',
                amount: 150.0,
                type: 'Payment',
                merchant: 'NETFLIX',
                account: null,
                card: null,
                reference: '1234',
                full_description: 'Payment: NETFLIX - R150.00 (Acc: 1234)',
                category: 'Entertainment'
            },
            {
                id: '864bf49d6f4176d7f8f9d6f1238ecbf0',
                date: '2024-12-18 00:00:00',
                transaction_date: '2024-12-18 00:00:00',
                amount: 500.0,
                type: 'Transfer',
                merchant: null,
                account: 'JOHN DOE',
                card: null,
                reference: '1234',
                full_description: 'Transfer: JOHN DOE - R500.00 (Acc: 1234)',
                category: 'Transfer'
            },
            {
                id: '6d0e5ce1c45d10ba2b3fb0cfa1ce7438',
                date: '2024-12-18 00:00:00',
                transaction_date: '2024-12-18 00:00:00',
                amount: 75.5,
                type: 'Card Purchase',
                merchant: 'WOOLWORTHS',
                account: null,
                card: '5678',
                reference: '5678',
                full_description: 'Card Purchase: WOOLWORTHS - R75.50 (Card: 5678)',
                category: 'Groceries'
            }
        ];

        // Insert sample data
        const stmt = await db.prepare(`
            INSERT INTO transactions (
                id, date, transaction_date, amount, type, merchant, 
                account, card, reference, full_description, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `);

        console.log('Inserting sample transactions...');
        for (const transaction of sampleTransactions) {
            await stmt.run(
                transaction.id,
                transaction.date,
                transaction.transaction_date,
                transaction.amount,
                transaction.type,
                transaction.merchant,
                transaction.account,
                transaction.card,
                transaction.reference,
                transaction.full_description,
                transaction.category
            );
        }

        await stmt.finalize();
        await db.close();
        
        // Verify file permissions
        await fs.promises.chmod(dbPath, 0o644);
        
        console.log('Database initialized successfully');
        console.log(`Database file created at: ${dbPath}`);
        console.log('You can now start the server with:');
        console.log('npx ts-node src/sqlite-server.ts');
        
    } catch (error) {
        console.error('Failed to initialize database:', error);
        process.exit(1);
    }
}

initializeDatabase().catch(console.error);