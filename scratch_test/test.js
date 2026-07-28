import puppeteer from 'puppeteer';
import fs from 'fs';

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  
  const logStream = fs.createWriteStream('browser_logs.txt', { flags: 'w' });
  
  page.on('console', msg => {
    const text = msg.text();
    console.log(text);
    logStream.write(text + '\n');
  });

  console.log("Navigating to dashboard to set localStorage...");
  await page.goto('http://localhost:5173');
  await page.evaluate(() => localStorage.setItem('user_role', 'employee'));
  
  console.log("Reloading page (Simulating a page refresh)...");
  await page.goto('http://localhost:5173');
  
  console.log("Waiting 3 seconds for initial load and background fetch...");
  await new Promise(r => setTimeout(r, 3000));
  
  console.log("Triggering 'Unpin' (or toggle pin) on the first article...");
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const pinButtons = buttons.filter(b => b.title === 'Unpin Article' || b.title === 'Pin Article');
    if (pinButtons.length > 0) {
      pinButtons[0].click();
    } else {
      console.log("[TEST] No pin/unpin buttons found!");
    }
  });
  
  console.log("Waiting 2 seconds for state to settle after unpin...");
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("Closing browser...");
  await browser.close();
  logStream.end();
})();
