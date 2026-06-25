"""
generate_users.py
-----------------
Generates 10,000 synthetic user profiles for the Nexus Mobile demo Selenium script.
Output: ../data/users.json

Run once (or whenever you need a fresh dataset):
    python3 generate_users.py

Requires: pip install faker
"""

import json
import random
import os
from faker import Faker

fake = Faker("en_US")

# ---------------------------------------------------------------------------
# Weighted distribution tables
# ---------------------------------------------------------------------------

PLAN_WEIGHTS = [
    ("unlimited",       0.40),
    ("unlimited-plus",  0.25),
    ("basic",           0.20),
    ("prepaid",         0.15),
]

DEVICE_WEIGHTS = [
    ("iphone-16-pro",       0.35),
    ("galaxy-s25-ultra",    0.20),
    ("pixel-9-pro",         0.15),
    ("iphone-16",           0.10),
    ("galaxy-a55",          0.08),
    ("moto-g-power-5g",     0.07),
    ("nexus-hotspot-pro",   0.05),
]

# ZIP first digits and the coverage outcome they produce (from coverage.ejs logic)
# Used to give variety to coverage page sessions
ZIP_FIRST_DIGITS = {
    "1": "4G LTE",           # default coverage
    "2": "5G Extended",
    "3": "Extended LTE",
    "4": "5G Extended",
    "5": "4G LTE",
    "6": "5G Ultra",
    "7": "5G Extended",
    "8": "5G Ultra",
    "9": "Limited Coverage",  # warning result
    "0": "4G LTE",
}

# 20 curated UA strings — realistic browser distribution
# ~45% Chrome/Windows, ~25% Chrome/Mac, ~20% Safari/Mac, ~10% Chrome/Android
USER_AGENTS = [
    # Chrome on Windows (9 entries ~45%)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome on Mac (5 entries ~25%)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Safari on Mac (4 entries ~20%)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # Chrome on Android (2 entries ~10%)
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

# US states for shipping forms
US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
]

# Phone brands associated with preferred devices (for realistic metadata)
DEVICE_TO_BRAND = {
    "iphone-16-pro":    "Apple",
    "iphone-16":        "Apple",
    "galaxy-s25-ultra": "Samsung",
    "galaxy-a55":       "Samsung",
    "pixel-9-pro":      "Google",
    "moto-g-power-5g":  "Motorola",
    "nexus-hotspot-pro": "Nexus",
}


def weighted_choice(weight_table):
    """Pick a value from [(value, weight), ...] table."""
    values, weights = zip(*weight_table)
    return random.choices(values, weights=weights, k=1)[0]


def generate_zip(preferred_coverage=None):
    """
    Generate a realistic 5-digit US ZIP.
    Optionally bias the first digit toward a specific coverage outcome.
    """
    first = str(random.randint(1, 9))
    rest = "".join([str(random.randint(0, 9)) for _ in range(4)])
    return first + rest


def make_email(first, last):
    """
    Build a base email. The Selenium script will append a unique +id suffix
    at runtime so each CS session looks like a fresh user.
    """
    formats = [
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()}{last.lower()}",
        f"{first.lower()}{last.lower()[0]}",
        f"{first.lower()[0]}{last.lower()}",
        f"{last.lower()}{first.lower()[0]}",
    ]
    username = random.choice(formats)
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "protonmail.com"]
    return f"{username}@{random.choice(domains)}"


def generate_profile(index):
    first = fake.first_name()
    last = fake.last_name()
    preferred_plan = weighted_choice(PLAN_WEIGHTS)
    preferred_device = weighted_choice(DEVICE_WEIGHTS)
    zip_code = generate_zip()
    ua_index = index % len(USER_AGENTS)

    # Lines count — weighted toward 1-2 lines
    lines_interested = random.choices([1, 2, 3, 4, 5], weights=[40, 35, 15, 7, 3], k=1)[0]

    return {
        "id":                   index,
        "first_name":           first,
        "last_name":            last,
        "email":                make_email(first, last),
        "phone":                fake.numerify("##########"),        # 10 digits, no formatting
        "address":              fake.street_address(),
        "city":                 fake.city(),
        "state":                random.choice(US_STATES),
        "zip":                  zip_code,
        "preferred_plan":       preferred_plan,
        "preferred_device":     preferred_device,
        "preferred_brand":      DEVICE_TO_BRAND.get(preferred_device, "Any"),
        "lines_interested":     lines_interested,
        "coverage_zip":         generate_zip(),                     # separate ZIP for coverage page check
        "user_agent":           USER_AGENTS[ua_index],
        "current_carrier":      random.choice(["Verizon", "AT&T", "T-Mobile", "Sprint", "Boost", "Cricket", "None"]),
        "months_with_carrier":  random.randint(1, 84),              # 1 month to 7 years
        "monthly_spend":        random.choice([25, 35, 45, 55, 65, 75, 85, 95, 110, 130, 150]),
        "port_in":              random.choices([True, False], weights=[60, 40], k=1)[0],
    }


def main():
    print("Generating 10,000 user profiles...")
    profiles = [generate_profile(i) for i in range(10000)]

    output_path = os.path.join(os.path.dirname(__file__), "../data/users.json")
    output_path = os.path.normpath(output_path)

    with open(output_path, "w") as f:
        json.dump(profiles, f, indent=2)

    print(f"Done. Written to: {output_path}")
    print(f"Total profiles: {len(profiles)}")

    # Quick distribution summary
    plan_counts = {}
    device_counts = {}
    for p in profiles:
        plan_counts[p["preferred_plan"]] = plan_counts.get(p["preferred_plan"], 0) + 1
        device_counts[p["preferred_device"]] = device_counts.get(p["preferred_device"], 0) + 1

    print("\nPlan distribution:")
    for k, v in sorted(plan_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({v/100:.1f}%)")

    print("\nDevice distribution:")
    for k, v in sorted(device_counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v} ({v/100:.1f}%)")


if __name__ == "__main__":
    main()
