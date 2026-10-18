"""
SME Business Scenarios, Catalogs, and Domain Archetypes.
Provides localized, realistic data profiles across 9 industry sectors.
All generated entities are strictly synthetic.
"""

from __future__ import annotations

from typing import Dict, Any, List

SECTOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "grocery": {
        "name_prefixes": ["Bismillah Store", "Al-Madina General Store", "Bhai Bhai Grocery", "Ratan Store", "Green Mart", "Shwapno Partner Store"],
        "categories": ["Grains & Pulses", "Edible Oils", "Spices", "Dairy & Eggs", "Beverages", "Snacks & Confectionery", "Personal Care"],
        "margin_range": (0.08, 0.18),  # Low margin, high volume
        "cash_ratio": 0.85,
        "products": [
            ("Miniket Rice 25kg", "Grains & Pulses", 165000, 185000),
            ("Nazirshail Rice 25kg", "Grains & Pulses", 185000, 210000),
            ("Rupchanda Soybean Oil 5L", "Edible Oils", 85000, 92000),
            ("Radhuni Turmeric Powder 200g", "Spices", 7500, 9000),
            ("Aarong Liquid Milk 1L", "Dairy & Eggs", 8000, 9000),
            ("Teer Atta 2kg", "Grains & Pulses", 11000, 12500),
            ("Pran Frooto 250ml", "Beverages", 2000, 2500),
            ("Lexus Biscuit 150g", "Snacks & Confectionery", 4500, 5500),
            ("Lifebuoy Soap 100g", "Personal Care", 4500, 5500),
            ("Wheel Washing Powder 1kg", "Personal Care", 12000, 14000),
        ],
    },
    "clothing": {
        "name_prefixes": ["Apsara Fashion", "Style Zone", "Deshi Dosh Corner", "Top Ten Collection", "Aarohi Boutique", "Poshak Mela"],
        "categories": ["Panjabi", "Saree", "Shalwar Kameez", "Men's Shirts", "Denim Jeans", "Children's Wear", "Fabrics"],
        "margin_range": (0.25, 0.45),
        "cash_ratio": 0.65,
        "products": [
            ("Cotton Semi-fitted Panjabi", "Panjabi", 110000, 165000),
            ("Tangail Handloom Cotton Saree", "Saree", 150000, 240000),
            ("Linen Three-Piece", "Shalwar Kameez", 180000, 260000),
            ("Formal Oxford Cotton Shirt", "Men's Shirts", 85000, 140000),
            ("Slim Fit Stretch Denim", "Denim Jeans", 95000, 160000),
            ("Kids Party Dress", "Children's Wear", 65000, 110000),
        ],
    },
    "restaurant": {
        "name_prefixes": ["Kasturi Dine", "Dhaka Biryani House", "Cafe Bistro 24", "Hot & Spicy Fast Food", "Mayer Doa Hotel", "Chittagong Mezban"],
        "categories": ["Biryani & Rice", "Curry & Meat", "Breads & Snacks", "Desserts & Sweets", "Beverages"],
        "margin_range": (0.35, 0.55),
        "cash_ratio": 0.90,
        "products": [
            ("Special Mutton Kacchi Biryani", "Biryani & Rice", 28000, 42000),
            ("Beef Bhuna Quarter", "Curry & Meat", 16000, 25000),
            ("Chicken Roast with Polao", "Biryani & Rice", 19000, 29000),
            ("Butter Naan", "Breads & Snacks", 3000, 6000),
            ("Firni Sweet Cup", "Desserts & Sweets", 3500, 7000),
            ("Borhani 250ml", "Beverages", 4000, 8000),
        ],
    },
    "pharmacy": {
        "name_prefixes": ["Modern Pharmacy", "Care & Cure Drug House", "Popular Pharma", "Lazz Pharma Partner", "Medina Medical Hall"],
        "categories": ["Analgesics", "Antibiotics", "Gastric & Antacid", "Cardiovascular", "Vitamins & Supplements", "Surgical Supplies"],
        "margin_range": (0.12, 0.22),
        "cash_ratio": 0.88,
        "products": [
            ("Napa Extra Paracetamol 500mg Strip", "Analgesics", 2500, 3000),
            ("Seclo 20mg Omeprazole Strip", "Gastric & Antacid", 5000, 6000),
            ("Maxpro 20mg Esomeprazole Strip", "Gastric & Antacid", 6500, 8000),
            ("Zithrin 500mg Azithromycin Strip", "Antibiotics", 10500, 13000),
            ("Beximco B-50 Forte Strip", "Vitamins & Supplements", 4500, 6000),
            ("Savlon Antiseptic 100ml", "Surgical Supplies", 4200, 5200),
        ],
    },
    "electronics": {
        "name_prefixes": ["Apex Electronics", "Metro Mobile & Gadget", "Future Tech Hub", "Star Computer Shop", "Smart Vision"],
        "categories": ["Smartphones", "Accessories", "Audio", "Cables & Adapters", "Computer Parts"],
        "margin_range": (0.10, 0.25),
        "cash_ratio": 0.50,
        "products": [
            ("Fast Charging Type-C Cable 65W", "Cables & Adapters", 18000, 35000),
            ("Wireless Bluetooth Earbuds Pro", "Audio", 110000, 185000),
            ("20,000mAh Power Bank", "Accessories", 140000, 220000),
            ("Budget Smartphone 6GB/128GB", "Smartphones", 1450000, 1750000),
            ("Optical Gaming Mouse USB", "Computer Parts", 45000, 75000),
        ],
    },
    "wholesale": {
        "name_prefixes": ["Maa Traders", "Chowdhury Enterprise", "Khan & Sons Wholesale", "Eastern Distribution Ltd", "Bengal Trading House"],
        "categories": ["Dry Food Bulk", "Beverages Bulk", "Packaging Supplies", "Oil & Ghee Barrels"],
        "margin_range": (0.05, 0.12),
        "cash_ratio": 0.35,  # Mostly credit / bank transfer
        "products": [
            ("Sugar Sack 50kg Grade-A", "Dry Food Bulk", 620000, 665000),
            ("Lentils (Masoor Dal) 50kg", "Dry Food Bulk", 580000, 630000),
            ("Master Carton Juice 24-Pack", "Beverages Bulk", 42000, 48000),
            ("Corrugated Shipping Cartons (100 pcs)", "Packaging Supplies", 65000, 80000),
        ],
    },
    "manufacturing": {
        "name_prefixes": ["Sonali Plastic Products", "Bengal Footwear Workshop", "Agrani Bakery & Food", "Standard Garments Unit"],
        "categories": ["Finished Goods", "Raw Materials", "Packaging"],
        "margin_range": (0.20, 0.35),
        "cash_ratio": 0.40,
        "products": [
            ("Plastic Household Stool (Pack of 10)", "Finished Goods", 180000, 250000),
            ("Rubber Foam Sheets 50kg", "Raw Materials", 220000, 270000),
            ("Handcrafted Leather Wallet", "Finished Goods", 45000, 85000),
            ("Bread Master Crate (20 loaves)", "Finished Goods", 60000, 85000),
        ],
    },
    "service": {
        "name_prefixes": ["QuickFix Auto Care", "Sparkle Laundry Services", "Apex Digital Studio", "Cool Point AC Repair & Service"],
        "categories": ["Labor Services", "Maintenance Packages", "Parts & Consumables"],
        "margin_range": (0.45, 0.70),
        "cash_ratio": 0.75,
        "products": [
            ("Standard AC Full Servicing & Wash", "Maintenance Packages", 120000, 250000),
            ("Motorbike Engine Oil Change & Tune-up", "Labor Services", 60000, 120000),
            ("Commercial Dry Cleaning Suit", "Labor Services", 35000, 70000),
            ("Gas Refill R410A Commercial", "Parts & Consumables", 220000, 380000),
        ],
    },
    "online_seller": {
        "name_prefixes": ["CartNest Online", "Deshi Deals BD", "Urban Trendz E-Com", "Gadget Express Shop", "Kashmiri Shawl House Online"],
        "categories": ["Lifestyle & Beauty", "Gadgets", "Apparel", "Home Decor"],
        "margin_range": (0.25, 0.45),
        "cash_ratio": 0.40,  # Cash on delivery + bKash/Nagad
        "products": [
            ("Organic Argan Hair Serum 50ml", "Lifestyle & Beauty", 75000, 140000),
            ("LED Desk Lamp with Wireless Charger", "Gadgets", 125000, 220000),
            ("Linen Kurti Casual Wear", "Apparel", 85000, 155000),
            ("Aromatherapy Diffuser 300ml", "Home Decor", 95000, 175000),
        ],
    },
}

EXPENSE_CATEGORIES = [
    ("rent", 0.35),
    ("utilities", 0.15),
    ("salary", 0.30),
    ("supplies", 0.08),
    ("marketing", 0.05),
    ("maintenance", 0.04),
    ("other", 0.03),
]

CUSTOMER_NAMES = [
    "Rahim Ahmed", "Karim Ullah", "Fatema Begum", "Tania Sultana", "Mohammad Hossain",
    "Abdul Malek", "Nasima Akter", "Kamal Uddin", "Arifur Rahman", "Shamima Yasmin",
    "Sohail Rana", "Rehana Parvin", "Mustafa Kamal", "Salma Khatun", "Biplob Barua",
    "Anwar Parvez", "Farhana Islam", "Ziaur Rahman", "Rashed Khan", "Monira Sultana",
    "Habibur Rahman", "Shirin Akhter", "Mahbub Alam", "Rokeya Begum", "Nazmul Huda"
]

SUPPLIER_NAMES = [
    "Pran Agro Distributorship", "Square Consumer Products Depo", "Akij Food & Beverage Hub",
    "Meghna Group Distribution", "ACI Logistics Agency", "Bashundhara Paper & Tissue Supply",
    "Unilever BD Distributor", "Beximco Pharma Depot", "Square Pharmaceuticals Center",
    "Incepta Distribution Unit", "City Group Mills Supplier", "Globe Enterprise Agency"
]
