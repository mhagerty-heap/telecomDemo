"""
telcoJourneyZoningFunnel.py
---------------------------
Synthetic traffic generator for Nexus Mobile (https://telecom-demo.vercel.app/).
Designed to populate Contentsquare Zoning, Journey Analysis, and Form Analytics
with realistic, behaviorally diverse session data.

Run manually:    python3 telcoJourneyZoningFunnel.py
Cron example:    */15 * * * * /path/to/scripts/venv/bin/python3 /path/to/scripts/telcoJourneyZoningFunnel.py >> /var/log/nexus_demo.log 2>&1

Requires: pip install selenium  (use venv — see README)
Requires: chromedriver installed and on PATH (or set CHROMEDRIVER_PATH below)
"""

import sys
import time
import json
import random
import datetime
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SITE_URL         = "https://telecom-demo.vercel.app"
USERS_JSON_PATH  = os.path.normpath(os.path.join(os.path.dirname(__file__), "../data/users.json"))
CHROMEDRIVER_PATH = None  # e.g. "/usr/bin/chromedriver" — leave None if chromedriver is on PATH

# Path weights — must sum to 100
PATH_WEIGHTS = {
    1: 7,    # Informed Converter       — Zoning + full checkout
    2: 3,    # Device-First Converter   — PDP → checkout
    3: 20,   # Checkout Abandoner       — Form Analytics hero
    4: 20,   # Deal/Promo Chaser        — Zoning on promo zones
    5: 50,   # Frustrated Researcher    — Journey Analysis hero
}

# Checkout form abandonment field weights (Path 3)
# Phone is the hero field — CS Form Analytics will show the spike here
ABANDON_FIELD_WEIGHTS = {
    "phone":   45,
    "address": 20,
    "email":   15,
    "zip":     12,
    "name":     8,
}

# ---------------------------------------------------------------------------
# Script run metadata
# ---------------------------------------------------------------------------

scriptRunTimestamp = datetime.datetime.now()
print(f"[INIT] ============================================================")
print(f"[INIT] scriptRunTimestamp = {scriptRunTimestamp}")
print(f"[INIT] scriptname = telcoJourneyZoningFunnel.py")

# ---------------------------------------------------------------------------
# Load user profiles
# ---------------------------------------------------------------------------

print(f"[INIT] Loading user profiles from: {USERS_JSON_PATH}")
with open(USERS_JSON_PATH, "r") as f:
    userData = json.load(f)

randomIndex = random.randint(0, len(userData) - 1)
user        = userData[randomIndex]
print(f"[INIT] userData loaded — {len(userData)} profiles available")
print(f"[INIT] selected profile index = {randomIndex}")

# Unpack profile
firstName   = user["first_name"]
lastName    = user["last_name"]
emailBase   = user["email"]
phone       = user["phone"]
address     = user["address"]
city        = user["city"]
state       = user["state"]
zip_code    = user["zip"]
coverageZip = user["coverage_zip"]
prefPlan    = user["preferred_plan"]
prefDevice  = user["preferred_device"]
userAgent   = user["user_agent"]
portIn      = user["port_in"]

# Build unique email so each CS session looks like a brand-new user
emailAppendId = random.randint(1000000000000000, 9999999999999999)
emailUsername = emailBase.split("@")[0]
emailDomain   = emailBase.split("@")[1]
email         = f"{emailUsername}+{emailAppendId}@{emailDomain}"

print(f"[INIT] firstName       = {firstName}")
print(f"[INIT] lastName        = {lastName}")
print(f"[INIT] email           = {email}")
print(f"[INIT] phone           = {phone[:4]}******")
print(f"[INIT] city            = {city}, {state}")
print(f"[INIT] zip_code        = {zip_code}")
print(f"[INIT] coverageZip     = {coverageZip}")
print(f"[INIT] preferred_plan  = {prefPlan}")
print(f"[INIT] preferred_device= {prefDevice}")
print(f"[INIT] port_in         = {portIn}")
print(f"[INIT] user_agent      = {userAgent[:72]}...")

# ---------------------------------------------------------------------------
# UTM variants — rotated by last digit of epoch time
# Index 6 is the "broken campaign" — always routes to rage+bounce path (path 6)
# ---------------------------------------------------------------------------

# Referrer URLs matching each UTM source (injected via CDP before navigation)
UTM_REFERRERS = [
    "",                             # direct — no referrer
    "https://mail.google.com/",
    "https://www.google.com/",
    "https://www.facebook.com/",
    "https://x.com/",
    "https://blog.example.com/",
    "https://www.instagram.com/",   # broken campaign source
]

timeSinceEpoch = str(time.time())
utmVariants = [
    "",
    "?utm_source=EmailList&utm_medium=email&utm_campaign=SwitchNow&utm_content=UnlimitedOffer",
    "?utm_source=Google&utm_medium=cpc&utm_campaign=Telecom5G&utm_content=BestPlans",
    "?utm_source=Facebook&utm_medium=display&utm_campaign=PhoneDeals&utm_content=iPhone16",
    "?utm_source=Twitter&utm_medium=social&utm_campaign=Coverage&utm_content=CheckYourArea",
    "?utm_source=Blog&utm_medium=referral&utm_campaign=BestCarriers2025&utm_content=NexusReview",
    "?utm_source=Instagram&utm_medium=display&utm_campaign=BrokenCampaign&utm_content=PlanSelector",
]
utmIndex    = int(timeSinceEpoch[-1]) % len(utmVariants)
startingUrl = SITE_URL + "/" + utmVariants[utmIndex]
referrerUrl = UTM_REFERRERS[utmIndex]
print(f"[INIT] utmIndex        = {utmIndex}")
print(f"[INIT] startingUrl     = {startingUrl}")
print(f"[INIT] referrerUrl     = {referrerUrl if referrerUrl else '(none — direct)'}")

# ---------------------------------------------------------------------------
# Select execution path
# UTM index 6 (BrokenCampaign) always forces path 6 — rage+bounce.
# All other UTMs use weighted random selection from paths 1-5.
# ---------------------------------------------------------------------------

PATH_NAMES = {
    1: "Informed Converter",
    2: "Device-First Converter",
    3: "Checkout Abandoner",
    4: "Deal/Promo Chaser",
    5: "Frustrated Researcher",
    6: "Rage Bounce (Broken Campaign)",
}

if utmIndex == 6:
    selectedPath = 6
    print(f"[INIT] BrokenCampaign UTM detected — forcing path 6 (Rage Bounce)")
else:
    pathKeys     = list(PATH_WEIGHTS.keys())
    pathWeights  = list(PATH_WEIGHTS.values())
    selectedPath = random.choices(pathKeys, weights=pathWeights, k=1)[0]

print(f"[INIT] selectedPath    = {selectedPath} ({PATH_NAMES[selectedPath]})")
print(f"[INIT] ============================================================")

# ---------------------------------------------------------------------------
# Chrome setup
# ---------------------------------------------------------------------------

print(f"[BROWSER] Initialising Chrome...")
options = webdriver.ChromeOptions()

# Uncomment to run non-headless (e.g. local debugging)
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")

options.add_argument(f"user-agent={userAgent}")
options.add_argument("--incognito")
options.page_load_strategy = "eager"

if CHROMEDRIVER_PATH:
    from selenium.webdriver.chrome.service import Service
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
else:
    driver = webdriver.Chrome(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(1280, 900)
print(f"[BROWSER] Chrome launched — window size = {driver.get_window_size()}")

# Nuke any residual storage immediately on launch
driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
driver.execute_cdp_cmd("Network.clearBrowserCache", {})
print(f"[BROWSER] Cookies and cache cleared on launch")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_for(element_id, timeout=12):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )

def wait_clickable(element_id, timeout=12):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, element_id))
    )

def scroll_to(element):
    """Scroll element into view then move mouse cursor to it — generates mousemove for CS Session Replay."""
    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'})", element)
    time.sleep(random.uniform(0.4, 0.9))
    # Move mouse to element so CS records cursor position on it
    ActionChains(driver, duration=random.randint(400, 800)).move_to_element(element).perform()
    time.sleep(random.uniform(0.2, 0.5))

def mouse_drift():
    """
    Move the mouse to a random spot on the visible viewport.
    Called during long dwells and scrolls to keep mouse movement data alive
    in CS Session Replay — prevents flat/no-movement gaps in replays.
    """
    x_offset = random.randint(-300, 300)
    y_offset = random.randint(-200, 200)
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver, duration=random.randint(300, 700)).move_to_element_with_offset(
            body, x_offset, y_offset
        ).perform()
    except Exception:
        pass

def hover(element, dwell=None):
    """
    Move mouse to element and optionally dwell.
    Generates mouseover/mouseenter events CS Zoning uses for engagement scoring.
    """
    ActionChains(driver, duration=random.randint(600, 1000)).move_to_element(element).perform()
    if dwell:
        # During long dwells, drift the mouse slightly to simulate reading behaviour
        drift_count = int(dwell / 2)
        for _ in range(max(1, drift_count)):
            time.sleep(random.uniform(1.5, 2.5))
            mouse_drift()

def hover_click(element, wait_after=None):
    """Move to element, pause, click, wait. Standard interaction for all clickable elements."""
    ActionChains(driver, duration=random.randint(600, 1000)).move_to_element(element).perform()
    time.sleep(random.uniform(0.3, 0.7))
    element.click()
    time.sleep(wait_after if wait_after else random.uniform(1.5, 3.0))

def slow_scroll_page(pause_at_fraction=None):
    """
    Smooth incremental scroll down the full page.
    Moves the mouse cursor periodically during the scroll so CS Session Replay
    shows a natural reading pattern rather than a static cursor.
    pause_at_fraction: 0.0–1.0 — pauses at that % of page height for a long dwell.
    """
    total_height = driver.execute_script("return document.body.scrollHeight")
    scroll_step  = random.randint(250, 420)
    current      = 0
    paused       = False
    steps_since_drift = 0

    print(f"[SCROLL] Starting full-page scroll — page height = {total_height}px, step = {scroll_step}px")

    while current < total_height:
        current += scroll_step
        driver.execute_script(f"window.scrollTo({{top:{current},behavior:'smooth'}})")
        time.sleep(random.uniform(0.12, 0.30))
        steps_since_drift += 1

        # Move mouse every 4-6 scroll steps to simulate eyes tracking content
        if steps_since_drift >= random.randint(4, 6):
            mouse_drift()
            steps_since_drift = 0

        # Pause at the specified fraction of the page for a reading dwell
        if pause_at_fraction and not paused:
            if current >= total_height * pause_at_fraction:
                dwell_time = random.uniform(3.5, 6.5)
                print(f"[SCROLL] Pausing at {int(pause_at_fraction*100)}% of page for {dwell_time:.1f}s dwell")
                for _ in range(int(dwell_time / 1.5)):
                    time.sleep(1.5)
                    mouse_drift()
                paused = True

    time.sleep(random.uniform(0.8, 1.8))
    print(f"[SCROLL] Full-page scroll complete — scrolled to {current}px")

def cs_identify():
    driver.execute_script(
        f"if(typeof _uxa !== 'undefined') _uxa.push(['trackPageEvent','@user-identifier@{email}']);"
    )
    print(f"[CS] cs_identify sent for {email}")

def cs_custom_var(key, value):
    driver.execute_script(
        f"if(typeof _uxa !== 'undefined') _uxa.push(['setCustomVariable','{key}','{value}']);"
    )
    print(f"[CS] setCustomVariable: {key} = {value}")

def click_logo():
    """Return to homepage via nav logo click."""
    print(f"[NAV] Clicking logo to return to homepage")
    driver.execute_script("window.scrollTo({top:0,behavior:'smooth'})")
    time.sleep(random.uniform(0.8, 1.5))
    logo = wait_clickable("link-nav-logo")
    hover_click(logo, wait_after=random.uniform(3.0, 5.0))
    print(f"[NAV] Logo clicked — current URL = {driver.current_url}")

def fill_field(field_id, value, clear_first=True):
    """
    Type into a form field with realistic per-character pacing.
    Moves mouse to field first — generates mousemove + focus events for CS Form Analytics.
    """
    field = wait_clickable(field_id)
    scroll_to(field)
    ActionChains(driver, duration=700).move_to_element(field).perform()
    time.sleep(random.uniform(0.2, 0.5))
    field.click()
    if clear_first:
        field.clear()
    time.sleep(random.uniform(0.3, 0.6))
    for char in value:
        field.send_keys(char)
        time.sleep(random.uniform(0.04, 0.13))
    time.sleep(random.uniform(0.4, 0.9))
    print(f"[FORM] Filled field '{field_id}' — {len(value)} chars")

# ---------------------------------------------------------------------------
# Reusable page interactions
# ---------------------------------------------------------------------------

def homepage_full_browse():
    """
    Full homepage browse — deliberate mouse hovers on plan cards and promo banner
    generate Zoning engagement signals. Scroll pauses at 70% for promo section.
    """
    print(f"[PAGE] homepage_full_browse() — URL = {driver.current_url}")

    # Brief read of hero section
    hero_dwell = random.uniform(1.5, 3.0)
    print(f"[PAGE] Hero section dwell — {hero_dwell:.1f}s")
    mouse_drift()
    time.sleep(hero_dwell)

    # Hover hero CTAs for Zoning signal (View Plans, Check Coverage)
    for cta_id in ["link-hero-view-plans", "link-hero-check-coverage"]:
        try:
            el = wait_for(cta_id, timeout=5)
            hover(el, dwell=random.uniform(1.0, 2.0))
            print(f"[MOUSE] Hovered hero CTA: {cta_id}")
        except Exception:
            pass

    # Scroll to plan cards section, hover each card
    print(f"[PAGE] Scrolling to plan cards section")
    plan_card_ids = [
        "link-plan-choose-basic",
        "link-plan-choose-unlimited",
        "link-plan-choose-unlimited-plus",
    ]
    for cid in plan_card_ids:
        try:
            el = driver.find_element(By.ID, cid)
            scroll_to(el)
            hover(el, dwell=random.uniform(1.5, 3.5))
            print(f"[MOUSE] Hovered plan card: {cid}")
        except Exception:
            pass

    time.sleep(random.uniform(1.0, 2.0))

    # Scroll rest of page — pause at 70% where promo banner lives
    slow_scroll_page(pause_at_fraction=0.70)

    # Explicit hover on promo banner CTA — key Zoning element
    try:
        promo = wait_for("link-promo-banner-deals", timeout=5)
        scroll_to(promo)
        hover(promo, dwell=random.uniform(3.5, 6.0))
        print(f"[MOUSE] Hovered promo banner CTA (key Zoning element)")
    except Exception:
        print(f"[WARN] Promo banner not found — skipping hover")

    time.sleep(random.uniform(1.0, 2.0))
    print(f"[PAGE] homepage_full_browse() complete")


def plans_page_browse(long_dwell=False, open_faq=False):
    """
    Browse the plans page. Hovers each plan column in comparison table.
    long_dwell=True simulates a user who can't find what they need (Path 5).
    """
    print(f"[NAV] Navigating to /plans (long_dwell={long_dwell}, open_faq={open_faq})")
    driver.get(f"{SITE_URL}/plans")
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PAGE] Plans page loaded — URL = {driver.current_url}")

    dwell = random.uniform(12.0, 20.0) if long_dwell else random.uniform(4.0, 7.0)
    print(f"[PAGE] Plans page dwell time = {dwell:.1f}s")

    # Hover each plan card's CTA — generates per-column Zoning data
    plan_ids = ["basic", "unlimited", "unlimited-plus", "prepaid"]
    for pid in plan_ids:
        try:
            el = driver.find_element(By.ID, f"link-plan-choose-{pid}")
            scroll_to(el)
            hover(el, dwell=random.uniform(1.0, 2.5))
            print(f"[MOUSE] Hovered plan column: {pid}")
        except Exception:
            print(f"[WARN] Plan card not found: link-plan-choose-{pid}")

    # Scroll to comparison table — key Zoning zone
    print(f"[PAGE] Dwelling on comparison table for {dwell:.1f}s")
    slow_scroll_page(pause_at_fraction=0.55)
    time.sleep(dwell * 0.4)   # remaining dwell after scroll
    mouse_drift()
    time.sleep(dwell * 0.3)
    mouse_drift()
    time.sleep(dwell * 0.3)

    if open_faq:
        faq_index = random.randint(0, 4)
        try:
            faq_btn = wait_clickable(f"btn-faq-{faq_index}", timeout=5)
            scroll_to(faq_btn)
            hover_click(faq_btn, wait_after=random.uniform(3.0, 5.0))
            print(f"[INTERACT] Opened FAQ accordion index={faq_index}")
        except Exception:
            print(f"[WARN] FAQ button btn-faq-{faq_index} not found")

    print(f"[PAGE] plans_page_browse() complete")


def device_listing_browse():
    """Browse device listing — hover 2-3 cards, scroll to generate engagement."""
    print(f"[NAV] Navigating to /devices")
    driver.get(f"{SITE_URL}/devices")
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PAGE] Device listing loaded — URL = {driver.current_url}")

    slow_scroll_page(pause_at_fraction=0.40)

    device_ids = ["iphone-16-pro", "galaxy-s25-ultra", "pixel-9-pro", "iphone-16", "galaxy-a55"]
    hovered    = random.sample(device_ids, k=random.randint(2, 3))
    print(f"[PAGE] Will hover device cards: {hovered}")
    for did in hovered:
        try:
            card = driver.find_element(By.ID, f"link-device-view-{did}")
            scroll_to(card)
            hover(card, dwell=random.uniform(1.5, 3.0))
            print(f"[MOUSE] Hovered device card: {did}")
        except Exception:
            print(f"[WARN] Device card not found: link-device-view-{did}")

    time.sleep(random.uniform(1.0, 2.0))
    print(f"[PAGE] device_listing_browse() complete")


def device_pdp_browse(device_id="iphone-16-pro"):
    """
    Browse a device PDP. Swaps a color swatch, opens specs accordion,
    and dwells on price/CTA box — all key Zoning zones for device pages.
    """
    print(f"[NAV] Navigating to /devices/{device_id}")
    driver.get(f"{SITE_URL}/devices/{device_id}")
    time.sleep(random.uniform(3.0, 5.0))
    print(f"[PAGE] Device PDP loaded — URL = {driver.current_url}")

    # Scroll through the PDP first pass
    slow_scroll_page(pause_at_fraction=0.35)

    # Color swatch swap — generates click event on Zoning zone
    try:
        color_btn = wait_clickable("btn-color-1", timeout=5)
        scroll_to(color_btn)
        hover_click(color_btn, wait_after=random.uniform(1.0, 2.0))
        print(f"[INTERACT] Swapped color swatch (btn-color-1)")
    except Exception:
        print(f"[WARN] Color swatch btn-color-1 not found")

    # Specs accordion toggle
    try:
        specs_btn = wait_clickable("btn-specs-toggle", timeout=5)
        scroll_to(specs_btn)
        hover_click(specs_btn, wait_after=random.uniform(2.0, 4.0))
        print(f"[INTERACT] Opened specs accordion")
    except Exception:
        print(f"[WARN] Specs toggle btn-specs-toggle not found")

    # Scroll back up to price/CTA box — long hover generates Zoning dwell signal
    try:
        cta = wait_for("link-device-add-with-plan", timeout=5)
        scroll_to(cta)
        dwell = random.uniform(4.0, 7.0)
        print(f"[MOUSE] Dwelling on device CTA box for {dwell:.1f}s (key Zoning zone)")
        hover(cta, dwell=dwell)
    except Exception:
        print(f"[WARN] Device CTA link-device-add-with-plan not found")

    print(f"[PAGE] device_pdp_browse() complete")


def checkout_step1_plan(plan_id=None):
    """Navigate to checkout step 1 and select a plan."""
    pid = plan_id or prefPlan
    print(f"[CHECKOUT] Step 1 — navigating to /checkout/plan?planId={pid}")
    driver.get(f"{SITE_URL}/checkout/plan?planId={pid}")
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[CHECKOUT] Step 1 loaded — URL = {driver.current_url}")

    try:
        plan_card = wait_clickable(f"card-{pid}")
        scroll_to(plan_card)
        hover_click(plan_card, wait_after=random.uniform(1.5, 3.0))
        print(f"[CHECKOUT] Step 1 — plan card selected: {pid}")
    except Exception:
        print(f"[WARN] Plan card card-{pid} not found — continuing with default selection")

    submit = wait_clickable("btn-checkout-plan-continue")
    scroll_to(submit)
    hover_click(submit, wait_after=random.uniform(2.0, 4.0))
    print(f"[CHECKOUT] Step 1 complete — clicked Continue — URL = {driver.current_url}")


def checkout_step2_device(device_id=None, skip=False):
    """Select a device (or skip with BYOD)."""
    print(f"[CHECKOUT] Step 2 — device selection (skip/BYOD={skip})")
    time.sleep(random.uniform(1.5, 3.0))
    print(f"[CHECKOUT] Step 2 loaded — URL = {driver.current_url}")

    if skip:
        byod = wait_for("card-byod", timeout=8)
        scroll_to(byod)
        hover(byod, dwell=random.uniform(1.0, 2.0))
        submit = wait_clickable("btn-checkout-device-continue")
        scroll_to(submit)
        hover_click(submit, wait_after=random.uniform(2.0, 3.5))
        print(f"[CHECKOUT] Step 2 — BYOD selected, continuing")
    else:
        did = device_id or prefDevice
        try:
            card = wait_clickable(f"card-{did}", timeout=5)
            scroll_to(card)
            hover_click(card, wait_after=random.uniform(1.5, 3.0))
            print(f"[CHECKOUT] Step 2 — device card selected: {did}")
        except Exception:
            print(f"[WARN] Device card card-{did} not found — defaulting to BYOD")
        submit = wait_clickable("btn-checkout-device-continue")
        scroll_to(submit)
        hover_click(submit, wait_after=random.uniform(2.0, 3.5))

    print(f"[CHECKOUT] Step 2 complete — URL = {driver.current_url}")


def checkout_step3_full(abandon_at=None):
    """
    Fill checkout details form.
    abandon_at = None      → complete the entire form
    abandon_at = "phone"   → fills name+email, types phone, then hesitates and exits (hero drop-off)
    abandon_at = "address" → fills through phone, stops at address
    abandon_at = "email"   → fills name only, stops before email
    abandon_at = "zip"     → fills through state, stops before zip
    abandon_at = "name"    → types first name only, exits immediately
    Returns True if form was submitted, False if abandoned.
    """
    time.sleep(random.uniform(1.5, 3.0))
    print(f"[CHECKOUT] Step 3 — details form loaded — URL = {driver.current_url}")
    print(f"[CHECKOUT] Step 3 — abandon_at = {abandon_at if abandon_at else 'None (full completion)'}")

    # --- firstName (always filled) ---
    if abandon_at == "name":
        fill_field("firstName", firstName)
        print(f"[CHECKOUT] Step 3 — pausing after firstName, then abandoning")
        time.sleep(random.uniform(4.0, 7.0))
        mouse_drift()
        print(f"[CHECKOUT] Step 3 — ABANDONED at: name")
        return False

    fill_field("firstName", firstName)
    fill_field("lastName", lastName)

    # --- email ---
    if abandon_at == "email":
        print(f"[CHECKOUT] Step 3 — pausing before email field, then abandoning")
        email_field = wait_for("email")
        scroll_to(email_field)
        hover(email_field, dwell=random.uniform(1.5, 3.0))
        time.sleep(random.uniform(4.0, 8.0))
        mouse_drift()
        print(f"[CHECKOUT] Step 3 — ABANDONED at: email")
        return False

    fill_field("email", email)
    fill_field("phone", phone[:10])

    # --- phone (hero abandonment) ---
    if abandon_at == "phone":
        phone_field = wait_for("phone")
        scroll_to(phone_field)
        print(f"[CHECKOUT] Step 3 — phone field hesitation (key Form Analytics drop-off point)")
        # Move mouse to and from the phone field repeatedly to simulate re-reading
        for _ in range(random.randint(2, 4)):
            ActionChains(driver, duration=random.randint(500, 900)).move_to_element(phone_field).perform()
            time.sleep(random.uniform(1.5, 2.5))
            mouse_drift()
        total_hesitation = random.uniform(7.0, 12.0)
        print(f"[CHECKOUT] Step 3 — dwelling on phone field for {total_hesitation:.1f}s before abandoning")
        time.sleep(total_hesitation)
        print(f"[CHECKOUT] Step 3 — ABANDONED at: phone (hesitation complete)")
        return False

    fill_field("address", address)
    fill_field("city", city)
    fill_field("state", state[:2].upper())

    # --- zip ---
    if abandon_at == "zip":
        zip_field = wait_for("zip")
        scroll_to(zip_field)
        hover(zip_field, dwell=random.uniform(1.5, 2.5))
        print(f"[CHECKOUT] Step 3 — pausing before zip field, then abandoning")
        time.sleep(random.uniform(4.0, 7.0))
        mouse_drift()
        print(f"[CHECKOUT] Step 3 — ABANDONED at: zip")
        return False

    fill_field("zip", zip_code)

    # Submit form
    submit = wait_clickable("btn-checkout-details-continue")
    scroll_to(submit)
    hover_click(submit, wait_after=random.uniform(2.0, 4.0))
    print(f"[CHECKOUT] Step 3 complete — form submitted — URL = {driver.current_url}")
    return True


def checkout_step4_confirm():
    """Review confirm page and place order."""
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[CHECKOUT] Step 4 — confirm page loaded — URL = {driver.current_url}")

    # Scroll through summary — user reads the order details
    slow_scroll_page(pause_at_fraction=0.5)

    cs_identify()
    cs_custom_var("checkout_stage", "confirm")

    place_btn = wait_clickable("btn-checkout-place-order")
    scroll_to(place_btn)
    dwell = random.uniform(2.0, 4.0)
    print(f"[CHECKOUT] Step 4 — hovering Place Order button for {dwell:.1f}s before clicking")
    hover(place_btn, dwell=dwell)
    hover_click(place_btn, wait_after=random.uniform(4.0, 7.0))
    print(f"[CHECKOUT] Step 4 — Place Order clicked — URL = {driver.current_url}")


def verify_success():
    print(f"[CHECKOUT] Waiting for success page...")
    try:
        WebDriverWait(driver, 15).until(
            lambda d: "/checkout/success" in d.current_url
        )
        print(f"[CHECKOUT] SUCCESS — success page confirmed — URL = {driver.current_url}")
        cs_identify()
        cs_custom_var("conversion", "true")
        cs_custom_var("preferred_plan", prefPlan)
        cs_custom_var("preferred_device", prefDevice)
        return True
    except Exception:
        print(f"[WARN] Success page not detected — current URL = {driver.current_url}")
        return False


# ===========================================================================
# PATH IMPLEMENTATIONS
# ===========================================================================

def path1_informed_converter():
    """
    Researches thoroughly before committing. Full checkout conversion.
    Homepage → Plans page (comparison dwell) → Plan detail → Checkout steps 1-4.
    CS value: Zoning on homepage plan cards + promo banner. Clean funnel for Journey baseline.
    """
    print(f"\n[PATH1] ========== Informed Converter ==========")
    driver.get(startingUrl)
    time.sleep(random.uniform(3.0, 5.0))
    print(f"[PATH1] Homepage loaded — URL = {driver.current_url}")
    cs_identify()

    homepage_full_browse()

    plans_page_browse(long_dwell=False, open_faq=True)

    print(f"[PATH1] Navigating to plan detail page: /plans/{prefPlan}")
    driver.get(f"{SITE_URL}/plans/{prefPlan}")
    time.sleep(random.uniform(4.0, 7.0))
    print(f"[PATH1] Plan detail loaded — URL = {driver.current_url}")

    try:
        hero_cta = wait_for("link-plan-detail-hero-cta", timeout=5)
        scroll_to(hero_cta)
        dwell = random.uniform(2.5, 4.5)
        print(f"[PATH1] Hovering plan detail hero CTA for {dwell:.1f}s")
        hover(hero_cta, dwell=dwell)
    except Exception:
        print(f"[WARN] Plan detail hero CTA not found")

    checkout_step1_plan()
    checkout_step2_device(device_id=prefDevice)
    completed = checkout_step3_full(abandon_at=None)
    if completed:
        checkout_step4_confirm()
        verify_success()
        time.sleep(random.uniform(2.0, 4.0))

    print(f"[PATH1] ========== Path 1 complete ==========\n")


def path2_device_first_converter():
    """
    Device browsing leads to checkout via PDP CTA.
    Homepage → Devices listing → Device PDP → Checkout (plan → device pre-selected → details → confirm).
    CS value: Zoning on device page zones (color swatch, specs, CTA). Alternative funnel entry in Journey.
    """
    print(f"\n[PATH2] ========== Device-First Converter ==========")
    driver.get(startingUrl)
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH2] Homepage loaded — URL = {driver.current_url}")
    cs_identify()

    homepage_full_browse()
    device_listing_browse()
    device_pdp_browse(device_id=prefDevice)

    print(f"[PATH2] Clicking 'Get This Device + Plan' CTA")
    cta = wait_clickable("link-device-add-with-plan")
    hover_click(cta, wait_after=random.uniform(2.0, 4.0))
    print(f"[PATH2] CTA clicked — URL = {driver.current_url}")

    checkout_step1_plan()

    # Device step — prefDevice was passed via query param, should be pre-selected
    print(f"[PATH2] Step 2 — device should be pre-selected ({prefDevice}), continuing")
    time.sleep(random.uniform(1.5, 3.0))
    print(f"[PATH2] Step 2 loaded — URL = {driver.current_url}")
    submit = wait_clickable("btn-checkout-device-continue")
    scroll_to(submit)
    hover_click(submit, wait_after=random.uniform(2.0, 3.5))
    print(f"[PATH2] Step 2 complete — URL = {driver.current_url}")

    completed = checkout_step3_full(abandon_at=None)
    if completed:
        checkout_step4_confirm()
        verify_success()
        time.sleep(random.uniform(2.0, 4.0))

    print(f"[PATH2] ========== Path 2 complete ==========\n")


def path3_checkout_abandoner():
    """
    Reaches checkout details form but abandons mid-fill.
    Phone field is the hero abandonment point (45% of runs).
    CS value: Form Analytics — clear drop-off spike at phone field.
    """
    print(f"\n[PATH3] ========== Checkout Abandoner ==========")

    fields   = list(ABANDON_FIELD_WEIGHTS.keys())
    weights  = list(ABANDON_FIELD_WEIGHTS.values())
    abandon_at = random.choices(fields, weights=weights, k=1)[0]
    print(f"[PATH3] Abandonment target field = {abandon_at} (weight: {ABANDON_FIELD_WEIGHTS[abandon_at]}%)")

    driver.get(startingUrl)
    time.sleep(random.uniform(2.0, 5.0))
    print(f"[PATH3] Homepage loaded — URL = {driver.current_url}")
    cs_identify()

    # Brief homepage read — click View Plans hero CTA
    time.sleep(random.uniform(1.5, 3.0))
    try:
        view_plans = wait_clickable("link-hero-view-plans")
        scroll_to(view_plans)
        hover_click(view_plans, wait_after=random.uniform(3.0, 5.0))
        print(f"[PATH3] Clicked hero 'View Plans' CTA — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] Hero CTA not found — navigating directly to /plans")
        driver.get(f"{SITE_URL}/plans")
        time.sleep(random.uniform(3.0, 5.0))

    # Plans page — find preferred plan and click choose
    try:
        choose = wait_clickable(f"link-plan-choose-{prefPlan}")
        scroll_to(choose)
        hover(choose, dwell=random.uniform(1.5, 3.0))
        hover_click(choose, wait_after=random.uniform(2.0, 4.0))
        print(f"[PATH3] Clicked 'Choose {prefPlan}' — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] Plan choose link not found — navigating directly to checkout")
        driver.get(f"{SITE_URL}/checkout/plan?planId={prefPlan}")
        time.sleep(random.uniform(2.0, 4.0))

    # Checkout step 1 — continue with selected plan
    print(f"[PATH3] Checkout step 1 — URL = {driver.current_url}")
    submit = wait_clickable("btn-checkout-plan-continue")
    scroll_to(submit)
    hover_click(submit, wait_after=random.uniform(2.0, 3.5))
    print(f"[PATH3] Step 1 submitted — URL = {driver.current_url}")

    # Checkout step 2 — BYOD skip
    checkout_step2_device(skip=True)

    # Checkout step 3 — fill form then abandon at target field
    cs_custom_var("checkout_stage", "details")
    checkout_step3_full(abandon_at=abandon_at)

    # Post-abandonment — go back to homepage via logo (shows up in Journey Sankey)
    time.sleep(random.uniform(1.5, 3.0))
    click_logo()
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH3] Returned to homepage post-abandonment — URL = {driver.current_url}")
    print(f"[PATH3] ========== Path 3 complete ==========\n")


def path4_promo_chaser():
    """
    Attracted by promotional content. Engages heavily with deals but doesn't convert.
    Homepage → Deals page → Devices listing → exit.
    CS value: Zoning on homepage promo banner vs hero CTA. Deals page engagement heatmap.
    """
    print(f"\n[PATH4] ========== Deal/Promo Chaser ==========")
    driver.get(startingUrl)
    time.sleep(random.uniform(3.0, 5.0))
    print(f"[PATH4] Homepage loaded — URL = {driver.current_url}")
    cs_identify()

    time.sleep(random.uniform(1.5, 3.0))

    # Scroll to promo banner section — pause there
    print(f"[PATH4] Scrolling to promo banner section")
    slow_scroll_page(pause_at_fraction=0.65)

    # Long hover on promo CTA — key Zoning element vs. hero CTA
    try:
        promo = wait_for("link-promo-banner-deals", timeout=5)
        scroll_to(promo)
        dwell = random.uniform(4.5, 7.0)
        print(f"[PATH4] Hovering promo banner for {dwell:.1f}s (key Zoning comparison element)")
        hover(promo, dwell=dwell)
        hover_click(promo, wait_after=random.uniform(3.0, 5.0))
        print(f"[PATH4] Clicked promo banner — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] Promo banner not found — navigating directly to /deals")
        driver.get(f"{SITE_URL}/deals")
        time.sleep(random.uniform(3.0, 5.0))

    # Deals page — hover multiple deal cards
    print(f"[PATH4] Deals page loaded — URL = {driver.current_url}")
    time.sleep(random.uniform(2.0, 4.0))
    slow_scroll_page(pause_at_fraction=0.50)

    hover_count = random.randint(2, 4)
    print(f"[PATH4] Will hover {hover_count} deal card CTAs")
    for i in range(hover_count):
        try:
            el = driver.find_element(By.ID, f"btn-deal-cta-{i}")
            scroll_to(el)
            dwell = random.uniform(2.0, 4.5)
            hover(el, dwell=dwell)
            print(f"[MOUSE] Hovered deal CTA btn-deal-cta-{i} for {dwell:.1f}s")
        except Exception:
            print(f"[WARN] Deal CTA btn-deal-cta-{i} not found")

    # Click one deal CTA
    try:
        first_cta = driver.find_element(By.ID, "btn-deal-cta-0")
        hover_click(first_cta, wait_after=random.uniform(2.0, 4.0))
        print(f"[PATH4] Clicked btn-deal-cta-0 — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] btn-deal-cta-0 not found — skipping click")

    # Navigate to devices via nav — browsing but not buying
    time.sleep(random.uniform(1.5, 3.0))
    try:
        nav_devices = wait_clickable("link-nav-devices")
        hover_click(nav_devices, wait_after=random.uniform(3.0, 5.0))
        print(f"[PATH4] Clicked nav Devices link — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] Nav devices link not found — navigating directly")
        driver.get(f"{SITE_URL}/devices")
        time.sleep(random.uniform(3.0, 5.0))

    slow_scroll_page(pause_at_fraction=0.60)
    time.sleep(random.uniform(1.0, 2.5))
    print(f"[PATH4] Exiting without conversion — URL = {driver.current_url}")
    print(f"[PATH4] ========== Path 4 complete ==========\n")


def path5_frustrated_researcher():
    """
    Can't find what they need — loops between homepage and plans 3 times,
    checks coverage, then escalates to support troubleshooter.
    CS value: Journey Sankey shows plans→home→plans→plans loop.
    Three visits to plans page signals high intent + friction.
    Support escalation at the end is the key Journey endpoint.
    """
    print(f"\n[PATH5] ========== Frustrated Researcher ==========")
    driver.get(startingUrl)
    time.sleep(random.uniform(4.0, 6.0))
    print(f"[PATH5] Homepage loaded — URL = {driver.current_url}")
    cs_identify()

    # Homepage — slow scroll, no CTA clicks
    print(f"[PATH5] Homepage — slow browse, no clicks")
    slow_scroll_page(pause_at_fraction=None)
    time.sleep(random.uniform(2.0, 4.0))

    # Plans visit 1 — long dwell, no FAQ
    print(f"[PATH5] Plans visit 1 of 3 — long dwell, no FAQ")
    plans_page_browse(long_dwell=True, open_faq=False)
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH5] Plans visit 1 complete")

    # Back to homepage via browser back button — this is the key Journey loop signal
    print(f"[PATH5] Pressing browser back button → homepage")
    driver.back()
    time.sleep(random.uniform(3.0, 5.0))
    print(f"[PATH5] Back to homepage — URL = {driver.current_url}")
    mouse_drift()
    time.sleep(random.uniform(1.0, 2.5))

    # Plans visit 2 — long dwell, open FAQs (user is looking for an answer)
    print(f"[PATH5] Plans visit 2 of 3 — long dwell, opening FAQs")
    plans_page_browse(long_dwell=True, open_faq=True)
    faq_index_2 = random.randint(0, 4)
    try:
        faq2 = wait_clickable(f"btn-faq-{faq_index_2}", timeout=5)
        scroll_to(faq2)
        hover_click(faq2, wait_after=random.uniform(4.0, 7.0))
        print(f"[PATH5] Opened second FAQ accordion: btn-faq-{faq_index_2}")
    except Exception:
        print(f"[WARN] btn-faq-{faq_index_2} not found")
    print(f"[PATH5] Plans visit 2 complete")

    # Coverage page — checks ZIP, reads result, clicks nothing
    print(f"[PATH5] Navigating to /coverage — checking ZIP {coverageZip}")
    driver.get(f"{SITE_URL}/coverage")
    time.sleep(random.uniform(3.0, 5.0))
    print(f"[PATH5] Coverage page loaded — URL = {driver.current_url}")
    try:
        zip_input = wait_clickable("zip-input")
        scroll_to(zip_input)
        hover_click(zip_input, wait_after=random.uniform(0.8, 1.5))
        fill_field("zip-input", coverageZip, clear_first=True)
        check_btn = wait_clickable("btn-coverage-check")
        scroll_to(check_btn)
        hover_click(check_btn, wait_after=random.uniform(2.0, 3.5))
        print(f"[PATH5] Coverage check submitted — ZIP = {coverageZip}")
        time.sleep(random.uniform(3.0, 5.0))
        mouse_drift()
        print(f"[PATH5] Coverage result read — no CTA clicked")
    except Exception as e:
        print(f"[WARN] Coverage ZIP check failed: {e}")

    # Plans visit 3 — third visit is the key Journey loop signal
    print(f"[PATH5] Plans visit 3 of 3 — short dwell, no FAQ (user giving up)")
    plans_page_browse(long_dwell=False, open_faq=False)
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH5] Plans visit 3 complete")

    # Support troubleshooter — selects issue, steps through wizard, escalates
    print(f"[PATH5] Navigating to /support/troubleshoot")
    driver.get(f"{SITE_URL}/support/troubleshoot")
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH5] Troubleshoot page loaded — URL = {driver.current_url}")

    issue_choices  = ["network", "billing", "calls", "data"]
    selected_issue = random.choice(issue_choices)
    print(f"[PATH5] Selecting troubleshoot issue: {selected_issue}")
    try:
        issue_btn = wait_clickable(f"btn-troubleshoot-issue-{selected_issue}")
        scroll_to(issue_btn)
        hover_click(issue_btn, wait_after=random.uniform(2.0, 4.0))
        print(f"[PATH5] Issue button clicked: btn-troubleshoot-issue-{selected_issue}")
    except Exception:
        print(f"[WARN] Issue button btn-troubleshoot-issue-{selected_issue} not found")

    try:
        next_btn = wait_clickable("btn-troubleshoot-next", timeout=5)
        scroll_to(next_btn)
        hover_click(next_btn, wait_after=random.uniform(2.0, 4.0))
        print(f"[PATH5] Clicked Next — advanced to step 2")
    except Exception:
        print(f"[WARN] btn-troubleshoot-next not found")

    try:
        resolve_no = wait_clickable("btn-troubleshoot-resolve-no", timeout=5)
        scroll_to(resolve_no)
        hover_click(resolve_no, wait_after=random.uniform(2.0, 4.0))
        print(f"[PATH5] Clicked 'No, not resolved' — issue unresolved")
    except Exception:
        print(f"[WARN] btn-troubleshoot-resolve-no not found")

    # Escalate to contact support — this is the frustration Journey endpoint
    try:
        contact_link = wait_for("link-troubleshoot-contact", timeout=5)
        scroll_to(contact_link)
        dwell = random.uniform(2.5, 4.5)
        print(f"[PATH5] Hovering contact support escalation link for {dwell:.1f}s")
        hover(contact_link, dwell=dwell)
        hover_click(contact_link, wait_after=random.uniform(3.0, 5.0))
        print(f"[PATH5] Escalated to contact support — URL = {driver.current_url}")
    except Exception:
        print(f"[WARN] link-troubleshoot-contact not found — could not escalate")

    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH5] Exiting without conversion — URL = {driver.current_url}")
    print(f"[PATH5] ========== Path 5 complete ==========\n")


def path6_rage_bounce():
    """
    Broken campaign path. User arrives from Instagram BrokenCampaign UTM.
    A JS error is injected simulating a broken plan selector, clicks on plan
    CTAs are disabled, user rage clicks then hard-bounces with no navigation.

    CS demo story:
      - Error Analysis:   JS error on checkout.init.js correlated with rage sessions
      - Zoning:           rage click concentration on plan card CTAs
      - Session Replay:   watch user try and fail to select a plan
      - Journey:          100% single-page bounce from this UTM campaign
    """
    print(f"\n[PATH6] ========== Rage Bounce (Broken Campaign) ==========")
    print(f"[PATH6] UTM: BrokenCampaign — injecting JS error and disabling plan clicks")

    # --- Inject a realistic-looking JS error into the browser console ---
    # This surfaces in CS Error Analysis tied to the rage sessions from this campaign.
    # The error references generic filenames — not site-specific.
    driver.execute_script("""
        window.addEventListener('load', function() {
            setTimeout(function() {
                try {
                    var planModule = undefined;
                    planModule.init({ planId: null });
                } catch(e) {
                    var err = new Error("Uncaught TypeError: Cannot read properties of undefined (reading 'init') — checkout.init.js:47");
                    err.stack = "TypeError: Cannot read properties of undefined (reading 'init')\\n    at initPlanSelector (checkout.init.js:47:18)\\n    at onDOMReady (app.bundle.js:112:5)";
                    console.error(err);
                    window.__injectedPlanError = err.message;
                }
            }, 800);
        });
    """)
    print(f"[PATH6] JS error injected — will appear in CS Error Analysis")

    # --- Disable clicks on plan CTA links so the user's clicks do nothing ---
    # Targets all plan choose links and the hero get-started CTA.
    driver.execute_script("""
        function disablePlanClicks() {
            var selectors = [
                'a[id^="link-plan-choose"]',
                'a[id^="link-compare-choose"]',
                '#link-nav-get-started',
                '#link-hero-view-plans'
            ];
            selectors.forEach(function(sel) {
                document.querySelectorAll(sel).forEach(function(el) {
                    el.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                    }, true);
                    el.style.cursor = 'pointer';  // still looks clickable
                });
            });
        }
        if (document.readyState === 'complete') {
            disablePlanClicks();
        } else {
            window.addEventListener('load', disablePlanClicks);
        }
    """)
    print(f"[PATH6] Plan click handlers disabled — CTAs are now dead")

    # Brief read of homepage — user lands and starts scanning
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[PATH6] User reading homepage — URL = {driver.current_url}")
    mouse_drift()
    time.sleep(random.uniform(1.0, 2.5))

    # Scroll down to the plan cards section
    print(f"[PATH6] Scrolling to plan cards section")
    slow_scroll_page(pause_at_fraction=0.45)

    # Target the featured (Unlimited) plan CTA — most prominent, most likely rage target
    rage_target_id = "link-plan-choose-unlimited"
    try:
        rage_el = wait_for(rage_target_id, timeout=8)
        scroll_to(rage_el)
        print(f"[PATH6] Located rage target: {rage_target_id}")
    except Exception:
        print(f"[WARN] Rage target {rage_target_id} not found — aborting rage sequence")
        return

    # --- Rage click sequence ---
    # Starts with normal click cadence, speeds up as frustration grows,
    # with small mouse micro-movements between clicks (classic rage pattern).
    print(f"[PATH6] Starting rage click sequence on {rage_target_id}")
    actions = ActionChains(driver, duration=400)

    # First click — normal, user thinks it just missed
    actions.move_to_element(rage_el).perform()
    time.sleep(random.uniform(1.2, 2.0))
    rage_el.click()
    print(f"[PATH6] Rage click 1 — normal speed")
    time.sleep(random.uniform(1.0, 1.8))

    # Second click — slight impatience
    actions.move_to_element_with_offset(rage_el, 2, 1).perform()
    rage_el.click()
    print(f"[PATH6] Rage click 2 — slight impatience")
    time.sleep(random.uniform(0.6, 1.0))

    # Clicks 3-8 — rapid frustrated clicking with micro mouse movements
    rage_count = random.randint(5, 7)
    print(f"[PATH6] Entering rapid rage phase — {rage_count} more clicks")
    for i in range(rage_count):
        x_jitter = random.randint(-4, 4)
        y_jitter = random.randint(-3, 3)
        ActionChains(driver, duration=random.randint(80, 180)).move_to_element_with_offset(
            rage_el, x_jitter, y_jitter
        ).perform()
        rage_el.click()
        print(f"[PATH6] Rage click {i + 3} — rapid (jitter x={x_jitter}, y={y_jitter})")
        time.sleep(random.uniform(0.08, 0.25))

    # Post-rage pause — user stares at the screen, confused
    stare_time = random.uniform(3.0, 5.5)
    print(f"[PATH6] Post-rage pause — staring at screen for {stare_time:.1f}s")
    mouse_drift()
    time.sleep(stare_time)

    # Hard bounce — no navigation, just quit
    # Session ends on the homepage with zero pageviews beyond entry
    print(f"[PATH6] Hard bounce — no navigation — exiting from {driver.current_url}")
    print(f"[PATH6] ========== Path 6 complete ==========\n")


# ===========================================================================
# DEBUG OVERRIDES
# Uncomment one line to force a specific path during local testing.
# Comment all out before deploying to cron.
# ===========================================================================
# selectedPath = 1   # Informed Converter
# selectedPath = 2   # Device-First Converter
# selectedPath = 3   # Checkout Abandoner
# selectedPath = 4   # Deal/Promo Chaser
# selectedPath = 5   # Frustrated Researcher
# selectedPath = 6   # Rage Bounce (Broken Campaign) — also set utmIndex = 6 above

# ===========================================================================
# MAIN
# ===========================================================================

try:
    # Inject referrer header via CDP before first navigation so CS/Heap see it correctly
    driver.execute_cdp_cmd("Network.enable", {})
    if referrerUrl:
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": {"Referer": referrerUrl}})
        print(f"[MAIN] Referrer injected via CDP: {referrerUrl}")
    else:
        print(f"[MAIN] No referrer set (direct traffic)")

    print(f"\n[MAIN] Loading starting URL: {startingUrl}")
    driver.get(startingUrl)
    time.sleep(random.uniform(2.0, 4.0))
    print(f"[MAIN] Page loaded — URL = {driver.current_url}")

    # Verify referrer was received by the page
    page_referrer = driver.execute_script("return document.referrer;")
    print(f"[MAIN] document.referrer = '{page_referrer}'")

    # Verify CS _uxa library is present
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("if(typeof _uxa==='object'){return true;}")
        )
        print(f"[MAIN] _uxa CS Library confirmed present")
    except Exception:
        print(f"[WARN] _uxa not detected — CS tag may not be installed on this environment")

    # Tag every session from this script so SCs can filter synthetic traffic in CS and Heap
    SCRIPT_NAME = "telcoJourneyZoningFunnel"
    driver.execute_script(
        f"if(typeof _uxa !== 'undefined') _uxa.push(['setCustomVariable','script_name','{SCRIPT_NAME}']);"
    )
    driver.execute_script(
        f"if(typeof heap !== 'undefined') heap.track('Selenium Script Session', {{'script_name': '{SCRIPT_NAME}', 'path': '{selectedPath}', 'path_name': '{PATH_NAMES[selectedPath]}'}});"
    )
    print(f"[MAIN] CS dynamic variable set: script_name = {SCRIPT_NAME}")
    print(f"[MAIN] Heap event fired: 'Selenium Script Session' — script_name={SCRIPT_NAME}, path={selectedPath}, path_name={PATH_NAMES[selectedPath]}")

    print(f"[MAIN] Executing path {selectedPath}: {PATH_NAMES[selectedPath]}")

    if selectedPath == 1:
        path1_informed_converter()
    elif selectedPath == 2:
        path2_device_first_converter()
    elif selectedPath == 3:
        path3_checkout_abandoner()
    elif selectedPath == 4:
        path4_promo_chaser()
    elif selectedPath == 5:
        path5_frustrated_researcher()
    elif selectedPath == 6:
        path6_rage_bounce()

except Exception as e:
    print(f"[ERROR] Unhandled exception: {e}")
    import traceback
    traceback.print_exc()

finally:
    print(f"\n[CLEANUP] Clearing storage and closing browser")
    try:
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        print(f"[CLEANUP] localStorage and sessionStorage cleared")
    except Exception:
        pass
    driver.delete_all_cookies()
    print(f"[CLEANUP] Cookies deleted")
    driver.quit()
    print(f"[CLEANUP] Browser closed — script complete")
