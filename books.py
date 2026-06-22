from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

print("=" * 60)
print("📚 BOOKS SCRAPER")
print("=" * 60)

# === USER AGENT ===
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# === PROCESS 1: CREATE DRIVER ===
print("\n🔄 Creating browser...")
driver = None
try:
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={USER_AGENT}')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # === HEADLESS MODE ===
    options.add_argument("--headless=new")
    
    # Additional options for stability
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-setuid-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Use webdriver_manager to automatically handle ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    print("✅ Browser ready in headless mode!")
    
except Exception as e:
    print(f"❌ Failed to create browser: {e}")
    print("\nTrying alternative method...")
    
    # Alternative: Try without webdriver_manager
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=options)
        print("✅ Browser ready in headless mode (alternative method)!")
    except Exception as e2:
        print(f"❌ Failed with alternative method: {e2}")
        print("\n💡 Try installing webdriver_manager:")
        print("   pip install webdriver-manager")
        exit(1)

try:
    # === PROCESS 2: LOAD PAGE ===
    try:
        print("\n📖 Loading books...")
        driver.get("http://books.toscrape.com/")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product_pod")))
        time.sleep(2)
        print("✅ Page loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load page: {e}")
        driver.quit()
        exit(1)

    # === PROCESS 3: FIND BOOKS ===
    try:
        books = driver.find_elements(By.CLASS_NAME, "product_pod")
        print(f"📚 Found {len(books)} books")
        
        if len(books) == 0:
            print("❌ No books found!")
            print("Saving page source for debugging...")
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✅ Page source saved to page_source.html")
            driver.quit()
            exit(1)
            
    except Exception as e:
        print(f"❌ Failed to find books: {e}")
        driver.quit()
        exit(1)

    # === PROCESS 4: EXTRACT DATA (PER BOOK) ===
    data = []
    failed_books = 0
    
    for index, book in enumerate(books[:20]):
        try:
            # Extract title
            try:
                title_element = book.find_element(By.TAG_NAME, "h3").find_element(By.TAG_NAME, "a")
                title = title_element.get_attribute("title")
                if not title:
                    title = title_element.text
            except Exception as e:
                title = f"Unknown_{index}"
                print(f"   ⚠️ Failed to extract title for book {index+1}: {e}")
            
            # Extract price
            try:
                price = book.find_element(By.CLASS_NAME, "price_color").text
            except Exception as e:
                price = "N/A"
                print(f"   ⚠️ Failed to extract price for '{title}': {e}")
            
            # Extract rating
            try:
                rating_element = book.find_element(By.CLASS_NAME, "star-rating")
                rating = rating_element.get_attribute("class").replace("star-rating ", "")
            except Exception as e:
                rating = "Unknown"
                print(f"   ⚠️ Failed to extract rating for '{title}': {e}")

            # Add to dataset
            data.append({
                "Title": title,
                "Price": price,
                "Rating": rating
            })
            print(f"   ✅ {title[:40]}... - {price} - {rating} stars")
            
        except Exception as e:
            failed_books += 1
            print(f"   ❌ Failed to process book {index+1}: {e}")
            continue

    print(f"\n📊 Successfully processed {len(data)} books, {failed_books} failed")

    # === PROCESS 5: SAVE TO CSV ===
    if data:
        try:
            with open('books.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Title', 'Price', 'Rating']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for book in data:
                    writer.writerow(book)
            
            print(f"\n✅ Saved {len(data)} books to books.csv")
            
            # Preview the data
            print("\n📊 Preview of scraped data:")
            print("-" * 50)
            for i, book in enumerate(data[:5], 1):
                print(f"{i}. {book['Title']} - {book['Price']} - {book['Rating']} stars")
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
    else:
        print("\n⚠️ No data to save!")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # === PROCESS 6: CLEANUP ===
    try:
        if driver:
            driver.quit()
            print("\n✅ Browser closed successfully!")
    except Exception as e:
        print(f"⚠️ Error while closing browser: {e}")
    
    print("✅ Done!")