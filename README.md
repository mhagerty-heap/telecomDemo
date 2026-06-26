# Nexus Mobile — Demo Telecom Site

A fictional mobile carrier website built with Node.js/Express and EJS. Designed as a realistic demo environment for analytics platforms such as Contentsquare, Heap, and Hotjar.

The site includes a full customer journey: plan browsing, device selection, checkout, account management, support, store finder, deals, and coverage pages.

---

## Tech Stack

- **Node.js / Express** — server-side rendering
- **EJS** — templating
- **Tailwind CSS** (CDN) — styling
- **express-session** — session-based auth
- **dotenv** — local environment variable loading

---

## Pages & Routes

| Route | Description |
|---|---|
| `/` | Home |
| `/plans` | Plan listing and detail |
| `/devices` | Device catalog |
| `/checkout` | Plan → device → details → confirm → success |
| `/deals` | Promotions |
| `/coverage` | Coverage map |
| `/support` | Support hub, contact, troubleshoot, outages |
| `/stores` | Store finder |
| `/account` | Dashboard, lines, devices, profile |
| `/login` | Auth |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CSQ_TAG_ID` | No | Contentsquare tag ID. If set, the CS tag loads on every page. |
| `PORT` | No | Port to run the server on. Defaults to `3000`. |

---

## Running Locally

### Prerequisites

- Node.js 18+
- npm

### Setup

```bash
git clone <your-repo-url>
cd telecom
npm install
```

Create a `.env` file in the project root:

```
CSQ_TAG_ID=your_tag_id_here
```

Start the dev server (uses nodemon on port 3001):

```bash
npm run dev
```

Or start without nodemon:

```bash
npm start
```

Visit `http://localhost:3001` (dev) or `http://localhost:3000` (start).

---

## Deploying to Vercel

1. Push the repo to GitHub
2. Import the project in [Vercel](https://vercel.com)
3. Set the following in **Settings → Environment Variables**:
   - `CSQ_TAG_ID` = your Contentsquare tag ID
4. Vercel will detect the `npm start` script automatically and deploy

> Note: `dotenv` is only used locally. On Vercel, environment variables are injected directly into the Node process — no `.env` file needed.

---

## Deploying to AWS (Elastic Beanstalk / EC2)

1. Set environment variables via the AWS console or CLI:
   - Elastic Beanstalk: **Configuration → Software → Environment Properties**
   - EC2: export them in your startup script or use AWS Secrets Manager
2. Ensure Node.js 18+ is available on the instance
3. Run `npm install && npm start`

---

## Synthetic Traffic Script

`scripts/telcoJourneyZoningFunnel.py` is a Selenium-based script that generates realistic user sessions across the site. Useful for populating analytics dashboards with diverse journey data.

### Prerequisites

```bash
pip install selenium
# chromedriver must be installed and on PATH
```

### Usage

```bash
python3 scripts/telcoJourneyZoningFunnel.py
```

See the script header for cron setup instructions.

---

## Data

Static JSON files in `/data` power the product catalog and demo users:

| File | Contents |
|---|---|
| `data/plans.json` | Mobile plan definitions |
| `data/devices.json` | Device catalog |
| `data/users.json` | Demo user accounts |
