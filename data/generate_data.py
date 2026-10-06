"""
RetailIQ - Synthetic Retail Data Generator
==========================================
Generates realistic retail datasets for the analytics pipeline.
Produces: customers, products, transactions, and store tables.

Usage:
    python data/generate_data.py
    python data/generate_data.py --rows 100000 --seed 42
"""

import argparse
import random
import csv
import os
from datetime import datetime, timedelta

# ── Configuration ────────────────────────────────────────────────────────────

SEED = 42
random.seed(SEED)

CATEGORIES = {
    "Electronics":  ["Laptop", "Smartphone", "Tablet", "Headphones", "Smartwatch", "Camera", "Speaker"],
    "Clothing":     ["T-Shirt", "Jeans", "Jacket", "Dress", "Sneakers", "Boots", "Hoodie"],
    "Home & Garden":["Coffee Maker", "Blender", "Vacuum", "Plant Pot", "Lamp", "Cushion", "Rug"],
    "Sports":       ["Yoga Mat", "Dumbbells", "Running Shoes", "Bicycle", "Tent", "Backpack", "Water Bottle"],
    "Beauty":       ["Face Serum", "Shampoo", "Lipstick", "Perfume", "Moisturiser", "Mascara", "Sunscreen"],
    "Food & Drink": ["Coffee Beans", "Protein Bar", "Olive Oil", "Herbal Tea", "Dark Chocolate", "Granola"],
}

BRANDS = {
    "Electronics":  ["TechPro", "NovaTech", "EliteGear", "PrimeTech", "VisionX"],
    "Clothing":     ["UrbanWear", "ClassicFit", "ActiveStyle", "TrendLine", "EcoThreads"],
    "Home & Garden":["HomeEssentials", "LivingCo", "GardenPro", "ComfortHome", "NatureLiving"],
    "Sports":       ["FitLife", "SportZone", "ActiveEdge", "PeakPerform", "TrailBlaze"],
    "Beauty":       ["GlowUp", "PureGlow", "LuxSkin", "NaturalBeauty", "RadiantCo"],
    "Food & Drink": ["NutriBlend", "PureOrganics", "FreshHarvest", "EcoEats", "WellnessFirst"],
}

CITIES = [
    ("Dublin", "Leinster", "Ireland"),
    ("Cork", "Munster", "Ireland"),
    ("Galway", "Connacht", "Ireland"),
    ("Limerick", "Munster", "Ireland"),
    ("Waterford", "Munster", "Ireland"),
    ("Drogheda", "Leinster", "Ireland"),
    ("Dundalk", "Leinster", "Ireland"),
    ("Sligo", "Connacht", "Ireland"),
    ("Kilkenny", "Leinster", "Ireland"),
    ("Wexford", "Leinster", "Ireland"),
]

CHANNELS = ["Online", "In-Store", "Mobile App"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Gift Card", "Cash"]

FIRST_NAMES = ["Aoife", "Cian", "Niamh", "Conor", "Siobhan", "Liam", "Aisling", "Seán",
               "Róisín", "Eoin", "Caoimhe", "Darragh", "Orla", "Ciarán", "Fiona", "Patrick",
               "Emma", "James", "Sarah", "Michael", "Laura", "David", "Karen", "John",
               "Anna", "Thomas", "Rachel", "Daniel", "Claire", "Mark"]

LAST_NAMES = ["Murphy", "Kelly", "O'Sullivan", "Walsh", "Smith", "O'Brien", "Byrne", "Ryan",
              "O'Connor", "O'Neill", "McCarthy", "Doyle", "Hughes", "Flynn", "Fitzpatrick",
              "Nolan", "Kennedy", "Lynch", "Murray", "Quinn", "Moore", "Carroll", "Collins",
              "Doherty", "O'Reilly", "Burke", "Brennan", "Gallagher", "Clarke", "Connolly"]

# ── Helper functions ──────────────────────────────────────────────────────────

def random_date(start_year=2023, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 1, 1)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")

def random_date_after(date_str, max_days=365 * 3):
    base = datetime.strptime(date_str, "%Y-%m-%d")
    return (base + timedelta(days=random.randint(0, max_days))).strftime("%Y-%m-%d")

def generate_email(first, last):
    domains = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "hotmail.com"]
    sep = random.choice([".", "_", ""])
    num = str(random.randint(1, 999)) if random.random() < 0.4 else ""
    return f"{first.lower()}{sep}{last.lower()}{num}@{random.choice(domains)}"

# ── Generators ────────────────────────────────────────────────────────────────

def generate_customers(n):
    rows = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        city, province, country = random.choice(CITIES)
        signup = random_date(2020, 2024)
        rows.append({
            "customer_id":   i,
            "first_name":    first,
            "last_name":     last,
            "email":         generate_email(first, last),
            "city":          city,
            "province":      province,
            "country":       country,
            "signup_date":   signup,
            "loyalty_tier":  random.choice(["Bronze", "Silver", "Gold", "Platinum"]),
            "age_group":     random.choice(["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]),
        })
    return rows

def generate_products(n=500):
    rows = []
    pid = 1
    for category, items in CATEGORIES.items():
        brands = BRANDS[category]
        per_cat = n // len(CATEGORIES)
        for _ in range(per_cat):
            brand   = random.choice(brands)
            product = random.choice(items)
            name    = f"{brand} {product} {'Pro' if random.random() > 0.6 else ''} {random.randint(1,5)}".strip()
            cost    = round(random.uniform(5, 800), 2)
            price   = round(cost * random.uniform(1.2, 2.5), 2)
            rows.append({
                "product_id":   pid,
                "product_name": name,
                "category":     category,
                "brand":        brand,
                "cost_price":   cost,
                "sale_price":   price,
                "stock_level":  random.randint(0, 500),
                "is_active":    random.choice([1, 1, 1, 0]),   # ~75% active
                "launch_date":  random_date(2019, 2024),
            })
            pid += 1
    return rows

def generate_stores():
    rows = []
    for i, (city, province, country) in enumerate(CITIES, start=1):
        rows.append({
            "store_id":      i,
            "store_name":    f"{city} Flagship" if i <= 3 else f"{city} Store",
            "city":          city,
            "province":      province,
            "country":       country,
            "store_type":    random.choice(["Flagship", "Standard", "Express"]),
            "opened_date":   random_date(2010, 2022),
            "sq_footage":    random.randint(2000, 15000),
            "staff_count":   random.randint(5, 80),
        })
    return rows

def generate_transactions(customers, products, stores, n):
    product_ids  = [p["product_id"]  for p in products if p["is_active"]]
    customer_ids = [c["customer_id"] for c in customers]
    store_ids    = [s["store_id"]    for s in stores]
    price_map    = {p["product_id"]: p["sale_price"] for p in products}

    rows = []
    for i in range(1, n + 1):
        pid   = random.choice(product_ids)
        qty   = random.randint(1, 5)
        price = price_map[pid]
        disc  = round(random.uniform(0, 0.3), 2) if random.random() < 0.25 else 0.0
        channel = random.choice(CHANNELS)
        rows.append({
            "transaction_id":  i,
            "customer_id":     random.choice(customer_ids),
            "product_id":      pid,
            "store_id":        random.choice(store_ids) if channel == "In-Store" else None,
            "transaction_date":random_date(2023, 2026),
            "channel":         channel,
            "quantity":        qty,
            "unit_price":      price,
            "discount_pct":    disc,
            "revenue":         round(price * qty * (1 - disc), 2),
            "payment_method":  random.choice(PAYMENT_METHODS),
            "is_returned":     1 if random.random() < 0.05 else 0,
        })
    return rows

def write_csv(rows, path):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓  {path}  ({len(rows):,} rows)")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate RetailIQ sample data")
    parser.add_argument("--customers",    type=int, default=5000,  help="Number of customers")
    parser.add_argument("--transactions", type=int, default=50000, help="Number of transactions")
    parser.add_argument("--seed",         type=int, default=42,    help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)
    out = "data/raw"

    print("\nRetailIQ Data Generator")
    print("=" * 40)

    customers    = generate_customers(args.customers)
    products     = generate_products(500)
    stores       = generate_stores()
    transactions = generate_transactions(customers, products, stores, args.transactions)

    write_csv(customers,    f"{out}/customers.csv")
    write_csv(products,     f"{out}/products.csv")
    write_csv(stores,       f"{out}/stores.csv")
    write_csv(transactions, f"{out}/transactions.csv")

    print(f"\nDone! Generated {args.transactions:,} transactions across {args.customers:,} customers.")

if __name__ == "__main__":
    main()
