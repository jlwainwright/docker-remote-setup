const puppeteer = require('puppeteer');
require('dotenv').config();

async function scrapeProductDetails(page, url) {
    await page.goto(url);
    await page.waitForSelector('.product');

    return await page.evaluate(() => {
        const specs = {};
        
        // Get specifications
        const specsList = document.querySelector('.woocommerce-product-details__short-description');
        if (specsList) {
            const items = Array.from(specsList.querySelectorAll('li'));
            items.forEach(item => {
                const [key, value] = item.textContent.split(':').map(s => s.trim());
                if (key && value) specs[key] = value;
            });
        }

        // Get pricing info from text content
        const textContent = document.body.innerText;
        const basePrice = textContent.match(/R(\d+\.\d{2})/)?.[0];
        const vatIncluded = textContent.match(/\(INCL\) \/ R(\d+\.\d{2})/)?.[0];
        const rrp = textContent.match(/R(\d+\.\d{2}) \(RRP\)/)?.[0];

        return {
            title: document.querySelector('.product_title')?.textContent.trim(),
            sku: document.querySelector('.sku')?.textContent.trim(),
            basePrice,
            vatIncluded,
            rrp,
            availability: document.querySelector('.stock')?.textContent.trim(),
            specifications: specs
        };
    });
}

async function scrapeSyntechDetailed() {
    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null
    });

    try {
        const page = await browser.newPage();
        
        // Login
        await page.goto('https://www.syntech.co.za/my-account/');
        await page.waitForSelector('#username');
        await page.type('#username', process.env.USERNAME);
        await page.type('#password', process.env.PASSWORD);
        await page.click('button[value="Login"]');
        await page.waitForNavigation();

        // Get all Xiaomi product URLs
        await page.goto('https://www.syntech.co.za/brands/xiaomi-mi/');
        const productUrls = await page.evaluate(() => 
            Array.from(document.querySelectorAll('.product a'))
                .map(a => a.href)
        );

        // Scrape each product
        const products = [];
        for (const url of productUrls) {
            const product = await scrapeProductDetails(page, url);
            products.push(product);
            // Add a small delay to avoid overwhelming the server
            await new Promise(r => setTimeout(r, 1000));
        }

        // Save results
        const fs = require('fs');
        fs.writeFileSync('xiaomi-products-detailed.json', JSON.stringify(products, null, 2));

    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

scrapeSyntechDetailed();
