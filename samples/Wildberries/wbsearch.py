import requests
import json
import os
import csv
import time
from tabulate import tabulate

def fetch_products(query, max_page):
    """Fetch products from the API and save to JSON."""
    json_path = './all.json'
    if os.path.exists(json_path):
        os.remove(json_path)

    all_products = []
    for page in range(1, max_page + 1):
        url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?dest=-1257786&page={page}&query={query}&resultset=catalog&spp=27"
        print(f"Fetching page {page}/{max_page}...")

        for attempt in range(3):
            try:
                response = requests.get(url, timeout=10)
                print(f"Status: {response.status_code}")

                if response.status_code != 200:
                    print(f"Error: Status code {response.status_code}")
                    time.sleep(0.1 * (attempt + 1))
                    continue

                data = response.json()
                if not isinstance(data, dict):
                    print("Error: Invalid JSON response")
                    break

                products = data.get('data', {}).get('products', [])
                if not products:
                    print("No more products found")
                    break

                all_products.extend(products)
                print(f"Added {len(products)} products (Total: {len(all_products)})")

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({'products': all_products}, f, ensure_ascii=False)
                break

            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(0.1 * (attempt + 1))
                if attempt == 2:
                    print("Max retries reached, skipping page")

    return all_products

def save_results(products):
    """Save products to text and CSV files with tabulated output."""
    if not products:
        print("No products to save!")
        return

    # Prepare data for output
    table = [['Index', 'ID', 'Name', 'Feedbacks']]
    text_lines = []
    for idx, item in enumerate(products):
        name = item.get('name', 'N/A')
        product_id = item.get('id', 'N/A')
        feedbacks = item.get('feedbacks', 0)
        table.append([idx, product_id, name, feedbacks])
        text_lines.append(f"Product(index={idx}, id={product_id}, name={name}, feedbacks={feedbacks})")

    # Print tabulated output
    print("\n" + "="*60 + "\nProduct List\n" + "="*60)
    print(tabulate(table, headers='firstrow', tablefmt='grid', stralign='left'))

    # Save to text file
    with open('./all.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text_lines))
    print("\nSaved to all.txt")

    # Save to CSV
    with open('./all.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(table)
    print("Saved to all.csv")

def main():
    """Main function to handle product search and output."""
    # Prompt user for search query
    query = input("Enter the product name to search for (e.g., плакаты): ").strip()
    if not query:
        print("Error: Search query cannot be empty!")
        return

    max_page = 62  # Default max pages, can be adjusted if needed

    try:
        products = fetch_products(query, max_page)
        save_results(products)
        print(f"\nTotal products found: {len(products)}")
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == '__main__':
    main()