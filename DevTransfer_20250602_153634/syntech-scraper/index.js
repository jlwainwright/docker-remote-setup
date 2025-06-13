const puppeteer = require('puppeteer');
require('dotenv').config();

async function scrapeSyntech() {
    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null
    });

    try {
        const page = await browser.newPage();

        // Go to login page with longer timeout
        await page.goto('https://www.syntech.co.za/my-account/', { waitUntil: 'networkidle2', timeout: 60000 });
        await page.screenshot({ path: 'login-page.png' });

        // Wait for login form and fill credentials
        await page.waitForSelector('#username', { timeout: 60000 });
        await page.type('#username', process.env.USERNAME);
        await page.type('#password', process.env.PASSWORD);

        // Click login button and wait for navigation
        await Promise.all([
            page.click('button[value="Login"]'),
            page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 60000 })
        ]);
        await page.screenshot({ path: 'after-login.png' });

        // Check if login was successful by waiting for an element that should be present after login
        try {
            await page.waitForSelector('.woocommerce-MyAccount-navigation', { timeout: 10000 }); // Example selector, may need adjustment
            console.log('Login successful.');
        } catch (error) {
            console.error('Login failed or timed out.');
            return; // Stop execution if login fails
        }

        // Navigate to Xiaomi products with longer timeout
        await page.goto('https://www.syntech.co.za/brands/xiaomi-mi/', { 
            waitUntil: 'networkidle2', 
            timeout: 60000 
        });
        
        // Wait for dynamic content to load
        await page.waitForTimeout(5000); // Wait 5 seconds for dynamic content
        
        // Take screenshot for debugging
        await page.screenshot({ path: 'products-page.png' });

        // Log the current URL to verify redirection
        console.log('Current URL:', await page.url());

        // Try multiple selectors for products with different approaches
        const selectorsToTry = [
            '.products li', // Common WooCommerce structure
            '.product',
            '.product-item',
            '.woocommerce-loop-product',
            '.product-grid-item',
            '[data-widget_type="wc-products.default"]', // ElementOR widget
            '.woocommerce ul.products',
            '.porto-products' // Porto theme specific
        ];

        let products = [];
        let foundSelector = null;

        for (const selector of selectorsToTry) {
            try {
                // First check if element exists
                const elementExists = await page.evaluate((sel) => !!document.querySelector(sel), selector);
                if (elementExists) {
                    console.log(`Found matching selector: ${selector}`);
                    foundSelector = selector;
                    break;
                }
                console.log(`Selector ${selector} not found, trying next...`);
            } catch (error) {
                console.log(`Error checking selector ${selector}:`, error.message);
            }
        }

        if (!foundSelector) {
            // Get more detailed page structure for debugging
            const pageStructure = await page.evaluate(() => {
                const getElementInfo = (element, depth = 0) => {
                    if (depth > 3) return null; // Limit depth to avoid huge output
                    
                    return {
                        tag: element.tagName,
                        id: element.id,
                        classes: element.className,
                        text: element.textContent?.trim().substring(0, 100),
                        children: Array.from(element.children)
                            .map(child => getElementInfo(child, depth + 1))
                            .filter(Boolean)
                    };
                };
                
                return getElementInfo(document.body);
            });

            // Log the structure to a file for analysis
            const fs = require('fs');
            fs.writeFileSync('page-structure.json', JSON.stringify(pageStructure, null, 2));
            
            console.error('Could not find any product elements. Page structure saved to page-structure.json');
            throw new Error('Could not find any product elements on the page');
        }

        // Extract product information
        products = await page.evaluate((selector) => {
            return Array.from(document.querySelectorAll(selector)).map(product => {
                const allText = product.innerText;

                const basePrice = allText.match(/R(\d+\.\d{2})/)?.[0] || 'N/A';
                const vatIncluded = allText.match(/\(INCL\) \/ R(\d+\.\d{2})/)?.[0] || 'N/A';
                const rrp = allText.match(/R(\d+\.\d{2}) \(RRP\)/)?.[0] || 'N/A';

                return {
                    title: product.querySelector('.woocommerce-loop-product__title')?.textContent.trim() ||
                        product.querySelector('.product-title')?.textContent.trim() ||
                        'Unknown',
                    sku: product.querySelector('.sku')?.textContent.trim() || 'N/A',
                    basePrice,
                    vatIncluded,
                    rrp,
                    availability: product.querySelector('.stock')?.textContent.trim() || 'Unknown'
                };
            });
        }, foundSelector);

        // Save results
        const fs = require('fs');
        fs.writeFileSync('xiaomi-products.json', JSON.stringify(products, null, 2));
        console.log('Successfully scraped', products.length, 'products');

    } catch (error) {
        console.error('Scraping error:', error);
        // Save error details
        const fs = require('fs');
        fs.writeFileSync('scraping-error.log', error.stack);
    } finally {
        await browser.close();
    }
}

scrapeSyntech();
