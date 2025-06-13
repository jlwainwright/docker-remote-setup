const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Main function to parse statement
function parseStatement(text) {
  const lines = text.split('\n');
  const transactions = [];
  let inTransactions = false;
  
  // Extract account info with error handling
  const accountMatch = text.match(/Account (?:No|Number)\s*[:.]?\s*(\d+)/i);
  const accountNumber = accountMatch ? accountMatch[1] : 'UNKNOWN';
  
  const statementMatch = text.match(/Statement (?:No|Number)\s*[:.]?\s*(\d+)/i);
  const statementNumber = statementMatch ? statementMatch[1] : 'UNKNOWN';
  
  const periodMatch = text.match(/(?:Statement )?Period\s*[:.]?\s*(.*?)\s*(?:to|until|-)\s*(.*?)(?:\n|$)/i);
  const period = periodMatch ? periodMatch : ['', 'UNKNOWN', 'UNKNOWN'];
  
  // Parse transactions
  for (const line of lines) {
    // Look for transaction section header
    if (line.includes('Transactions in RAND (ZAR)') || line.includes('Date') && line.includes('Description') && line.includes('Amount')) {
      inTransactions = true;
      continue;
    }
    
    // Skip empty lines and section headers
    if (inTransactions && line.trim() && !line.includes('Page') && !line.includes('Delivery Method') && !line.includes('Turnover for Statement Period') && !line.match(/^\s*Closing Balance/)) {
      // Match FNB transaction lines (date, description, amount)
    const transactionRegex = /^(\d{1,2} \w{3})\s+(.*?)\s+(-?\d{1,3}(?:,\d{3})*\.\d{2})\s*(Cr|Dr)?$/i;

    if (transactionRegex.test(line)) {
      const match = line.match(transactionRegex);
      if (match) {
        const [_, date, description, amount, type] = match;
        const isCredit = type === 'Cr';
        const transactionAmount = parseFloat(amount.replace(/,/g, ''));

        transactions.push({
          date: date.trim(),
          description: description.trim(),
          amount: isCredit ? Math.abs(transactionAmount) : -Math.abs(transactionAmount),
          type: isCredit ? 'credit' : 'debit'
        });
      }
    }
  }

    return {
    accountNumber,
    statementNumber,
    periodFrom: period[1].trim(),
    periodTo: period[2].trim(),
    openingBalance: parseFloat((text.match(/Opening Balance(.*?)(?:Cr|$)/i) || ['', '0'])[1].replace(/,/g, '').trim()),
    closingBalance: parseFloat((text.match(/Closing Balance(.*?)(?:Cr|$)/i) || ['', '0'])[1].replace(/,/g, '').trim()),
    transactions,
    summary: {
      totalCredits: transactions.filter(t => t.type === 'credit').reduce((sum, t) => sum + t.amount, 0),
      totalDebits: transactions.filter(t => t.type === 'debit').reduce((sum, t) => sum + t.amount, 0),
      transactionCount: transactions.length
    }
  };
}

// Process all PDF text files in directory
function processStatements() {
  try {
    const files = fs.readdirSync(__dirname).filter(f => f.endsWith('.pdf'));
    const results = [];
    
    for (const file of files) {
      try {
        console.log(`Processing ${file}...`);
        const textFile = `${file}.txt`;
        execSync(`pdftotext "${path.join(__dirname, file)}" "${path.join(__dirname, textFile)}"`);
        const text = fs.readFileSync(path.join(__dirname, textFile), 'utf8');
        
        // Save text for debugging
        fs.writeFileSync(`${file}.debug.txt`, text);
        
        const statement = parseStatement(text);
        results.push(statement);
        console.log(`Successfully processed ${file}`);
      } catch (err) {
        console.error(`Error processing ${file}:`, err.message);
      }
    }
    
    fs.writeFileSync('statements.json', JSON.stringify(results, null, 2));
    console.log(`Processed ${files.length} statements. Results saved to statements.json`);
    
    // Print summary
    results.forEach((result, i) => {
      console.log(`\nStatement ${i+1}:`);
      console.log(`Account: ${result.accountNumber}`);
      console.log(`Period: ${result.periodFrom} to ${result.periodTo}`);
      console.log(`Transactions: ${result.transactions.length}`);
    });
    
  } catch (err) {
    console.error('Fatal error:', err);
    process.exit(1);
  }
}

processStatements();
