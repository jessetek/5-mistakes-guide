# Next Phase — Operator Action Items

This document covers the CRO improvements that need YOUR action (account creation, partnerships, content production) — not code. The code-side changes are already shipped. Pair this with what's already deployed for max conversion lift.

Last updated: 2026-05-05

---

## 1. Microsoft Clarity — weekly review checklist

Clarity is already installed (project `wke2elyrvc` at https://clarity.microsoft.com/projects/view/wke2elyrvc). It's silently capturing every visitor session, every click, every scroll. **You're not using it. That's the biggest free win on the table.**

### 30-min weekly review (every Monday morning)

1. **Open the dashboard:** https://clarity.microsoft.com/projects/view/wke2elyrvc
2. **Filter by last 7 days, all devices.**
3. **Check the Heatmaps tab for these 5 pages:**
   - `/` (home)
   - `/zoom` (book call)
   - `/valuation` (home value)
   - `/guide` (PDF download)
   - `/rates` (SMS subscribe)
4. **Look for:**
   - **Click maps:** Are people clicking your CTAs, or trying to click non-clickable elements (images, headings)?
   - **Scroll maps:** Where do most users stop? If 70% never see your form, the form is too low.
   - **Dead clicks:** Users tapping something expecting it to work. Indicates UI confusion.
   - **Rage clicks:** Users tapping repeatedly out of frustration. Indicates broken UX.
5. **Watch 3-5 random session recordings.** What confuses people? Where do they get stuck?
6. **Write down 1-3 issues to fix this week.** Even one fix per week compounds.

### Common red flags to watch for

- **Scroll depth on `/` < 30%:** Hero isn't compelling, fix the headline or photo
- **Dead clicks on the rotating glitch word:** Users think it's clickable — make it actually link to something
- **Rage clicks anywhere:** Broken interaction, immediate fix
- **Quick-back rate > 40%** on a page: Page is failing the visitor's expectation. Look at where they came from (referrer) and what they were promised vs what they saw

---

## 2. LeadConnector — SMS keyword opt-in setup

Right now the only way into the SMS list is the `/rates` form. Add a keyword path so people can text **JESSE** to (562) 609-4200 from anywhere — your IG bio, business card, ad copy, signage.

### Setup steps in LeadConnector

1. **Log in:** https://app.leadconnectorhq.com
2. **Navigate:** Marketing → SMS → Keyword Triggers
3. **Create 4 keywords:**

| Keyword | What it does |
|---|---|
| `JESSE` | General opt-in, sends "Welcome — what brings you here? Reply BUY, SELL, RATES, or GUIDE." |
| `BUY` | Sends 5-Mistakes guide PDF link + tags as "buyer" |
| `SELL` | Sends valuation form link + tags as "seller" |
| `RATES` | Adds to weekly rate text list, confirms next Thursday delivery |
| `GUIDE` | Sends 5-Mistakes guide PDF link |

4. **TCPA-compliant auto-reply for each:** "Reply STOP to opt out. Msg & data rates may apply. ~4-5 msgs/mo."
5. **Test each keyword from your own phone.**
6. **Add to:**
   - Your Instagram bio: "Text JESSE to 562-609-4200"
   - Your `/about` page (I can wire this up — say the word)
   - Your business cards (next print run)
   - Email signature

Why it works: 70%+ of SoCal buyers respond to text faster than form fills. Some people will never fill a web form but will text. This widens your funnel.

---

## 3. Email nurture sequence — copy & timing

For the buyer-quiz email opt-in (which is now wired up site-side), here's the 5-email sequence to set up in LeadConnector.

### Workflow trigger

In LeadConnector → Workflows → Create new → Trigger: "Form Submitted" + filter `source = buyer-quiz`

### Email 1 — Day 0 (immediately on quiz submit)

**Subject:** Your buyer readiness PDF is here — plus the 5-Mistakes guide
**Body:**

> Hey [firstName],
>
> Your buyer readiness score and 30-day action plan are attached as a PDF. So is the 5-Mistakes guide I promised.
>
> The action plan is personalized to your score and gaps. It's the same plan I'd build for you on a 1:1 call — just delivered in writing first so you can read at your own pace.
>
> If something jumps out and you want to talk through it, my calendar is here: https://jessetek.net/zoom
>
> Otherwise, you'll hear from me one more time this week with the next thing.
>
> — Jesse
> 562-609-4200 · DRE #02133131

### Email 2 — Day 2

**Subject:** [firstName] — the #1 thing your score tells me
**Body:** (Personalize to the band: "Stretch Buyer," "Ready Buyer," "Almost There," "Strategist," "Patient Pre-Buyer")

> Hey [firstName],
>
> Looked at your quiz answers more carefully. The thing that stands out to me most is [BAND-SPECIFIC INSIGHT — e.g. "your timeline is more aggressive than your savings supports right now, but that's actually fixable in 90 days"].
>
> If I were you, my next move would be:
>
> [BAND-SPECIFIC ACTION — e.g. "talk to a lender about pre-approval before doing anything else, because the pre-approval letter dictates everything downstream"].
>
> I have 3 lender contacts I trust who specialize in first-time buyers in Downey/LA/OC. None pay me referral fees — these are just the ones who actually deliver. Want me to introduce you?
>
> — Jesse

### Email 3 — Day 5

**Subject:** A real client in your situation (you'll like this)
**Body:**

> Hey [firstName],
>
> Wanted to share a quick story. Last quarter I worked with [client first name + similar buyer profile to recipient — e.g. "Carlos, also a stretch buyer with a similar timeline"]. He was sure he was 6 months from being able to buy. Turned out he was already qualified — just nobody had told him.
>
> Closed in Pico Rivera at $635K, 3.5% down, FHA loan. Total cash to close: $11K (lower than he expected).
>
> Read the full story: [Link to relevant case study, or a specific anecdote]
>
> The pattern I see most often is people underestimate their own readiness. The math is simpler than you think.
>
> — Jesse

### Email 4 — Day 9

**Subject:** Quick question for you
**Body:**

> Hey [firstName],
>
> Quick one — when you took the quiz, what was the actual reason you wanted to know your buyer readiness?
>
> - Buying in the next 90 days?
> - Just exploring whether it's possible at all?
> - Frustrated with renting and want to see what's realistic?
> - Something else?
>
> Whatever it is, I want to make sure my follow-ups are useful, not noise.
>
> Just reply to this email — I read every one personally.
>
> — Jesse

### Email 5 — Day 14

**Subject:** Last check-in (then I'll get out of your inbox)
**Body:**

> Hey [firstName],
>
> Last note from me on this thread.
>
> If you're ready to talk through your situation — even if you're 6+ months away from buying — my 15-min call is free, no pitch, no pressure: https://jessetek.net/zoom
>
> If you're not ready or just here to learn, I get it. I'll keep you on my weekly rate text list (Thursdays at 11:30am, useful market intel) but I won't keep emailing about the quiz.
>
> Whenever you're ready, you have my number.
>
> — Jesse
> 562-609-4200

### Tracking

Tag every recipient who:
- Books a call → "quiz-converted"
- Replies to email 4 → "quiz-engaged"
- Doesn't open 3 in a row → "quiz-cold" (move to monthly newsletter only)

---

## 4. Meta retargeting funnel

You have Meta Pixel installed (ID `269951940252971`). It's been collecting audience data since activation. Time to use it.

### Setup in Meta Ads Manager

1. **Go to:** https://business.facebook.com/adsmanager
2. **Audiences → Create audience → Custom audience → Website**
3. **Build these 4 audiences:**

| Audience name | Definition | Why |
|---|---|---|
| `JT-Homepage Visitors` | Visited `/` in last 30 days, didn't visit `/zoom` | These got interested but didn't book |
| `JT-Valuation Abandoners` | Visited `/valuation`, didn't submit form | Hot leads who hesitated to share address |
| `JT-Guide Downloaders` | Submitted `/guide` form | Already in your list — upsell to call |
| `JT-Buyers` | Visited `/buyer` OR `/buyer-quiz` | Buyer-intent audience |

4. **Build a 1% lookalike** of your "Closed Clients" custom audience (upload a CSV of past client emails).

### Campaign structure

**Campaign 1: Homepage retargeting** → "JT-Homepage Visitors"
- Ad: 15-second video of you at a kitchen table with a client
- Headline: "100+ SoCal families closed. Want a 15-min call?"
- CTA: Book Now → /zoom
- Budget: $10/day to start

**Campaign 2: Valuation recovery** → "JT-Valuation Abandoners"
- Ad: Static image of a real CMA report (numbers visible, address blurred)
- Headline: "Don't have your address yet? Grab the 5-Mistakes guide instead"
- CTA: Learn More → /guide
- Budget: $5/day

**Campaign 3: Guide-downloader upsell** → "JT-Guide Downloaders"
- Ad: Carousel of 3 client wins
- Headline: "Read the guide. Now talk to a real realtor about your situation."
- CTA: Book Now → /zoom
- Budget: $10/day

**Campaign 4: Lookalike acquisition** → "Lookalike of Closed Clients"
- Ad: Same as Campaign 1
- Headline: "Bilingual SoCal realtor. 100+ families. 5.0 stars."
- CTA: Get Quote → /valuation OR Book Now → /zoom
- Budget: $20/day, scale up if CPL is good

### Expected outcome

Industry CTR for retargeted real estate: 0.5-1.5% (vs 0.06% cold). Conversion rate on retargeted clicks: 4-8x higher. Expect $30-$80 cost per lead, much lower than cold traffic.

### Important: don't run for 14+ days without checking. CPL drifts up fast if frequency caps aren't set.

---

## 5. Google Local Services Ads (LSA)

LSA puts you at the very top of Google search above all paid ads, with a green "Google Screened" badge. Most realtors don't run LSA because it requires verification. **That's why you should.**

### Application steps

1. **Go to:** https://ads.google.com/local-services-ads
2. **Select:** Real estate agent
3. **Service area:** Downey + 25-mile radius (covers your full LA/OC service area)
4. **Required documents** (have these ready):
   - California real estate license (DRE #02133131)
   - $1M general liability insurance certificate
   - 3 client references (Google will call them)
   - Background check consent (Google runs this automatically — clean record required)
5. **Budget:** Start at $30/day. You only pay per qualified lead, not per click. Expected $40-$80 per lead.
6. **Hours:** Set to your actual response hours (the 5-min response promise depends on this).

### Expected timeline

- Application: 1 hour
- Verification: 2-4 weeks
- First lead: usually within a week of going live
- Steady state: 3-8 leads/week at $30-50/lead

### Why it dominates

- Pay-per-lead, not pay-per-click (much better unit economics)
- Top-of-page placement above standard ads
- "Google Screened" badge = instant trust
- Phone-call leads only — no cold email or form fills, real interest

---

## 6. Listings syndication checklist

Each of these is a free or low-cost backlink + lead source + SEO trust signal. Do them all.

### Tier 1 — High impact (do these first)

| Service | Action | Time |
|---|---|---|
| **Google Business Profile** | Verify or claim. Add hours, services, photos, weekly post. https://business.google.com | 30 min + 5 min/week |
| **Realtor.com agent profile** | Free profile claim. Add headshot, bio, listings, reviews. | 20 min |
| **Zillow Premier Agent** | Free profile (paid lead version optional later). Critical for buyer search. | 20 min |
| **Yelp Business** | Free claim. Most realtors don't bother — works in your favor. | 15 min |
| **Better Business Bureau** | Free non-accredited listing. $500/yr to upgrade with badge — worth it. | 10 min |

### Tier 2 — Solid backlinks (do this month)

| Service | Action |
|---|---|
| **Redfin Partner Agent** | Apply at redfin.com/partner-agent. Sends you Redfin's overflow leads. |
| **HomeLight** | Free directory listing. They match consumers to top-rated agents. |
| **Trulia** | Owned by Zillow, separate listing. Claim and update. |
| **NextDoor Pro** | Free business profile in your neighborhood. Hyperlocal trust signal. |
| **Bilingual real estate directories** | LatinosEnRealEstate.com, NAHREP.org member directory |

### Tier 3 — Long-tail (when you have time)

- **Yelp local guide listings** for Downey realtors
- **Reddit r/RealEstate, r/FirstTimeHomeBuyer** — answer questions, signature link
- **Quora** — answer SoCal real estate questions, link to relevant insights post
- **Local SoCal Facebook groups** — first-time buyer groups for Downey/Whittier

---

## 7. Lender partnership talking points

A lender embed on `/buyer` and `/calculator` adds value AND captures a key lifecycle moment. Here's the pitch.

### Who to contact

Look for **bilingual loan officers** at these institutions (in priority order):

1. **Local credit unions** — Kinecta, SchoolsFirst, Wescom. Often have first-time buyer programs.
2. **Major banks with bilingual LOs** — Chase, Wells Fargo, BofA Hispanic Banking
3. **Independent mortgage brokers** — usually best rates and most attentive

### The partnership pitch (5-min phone call)

> "Hey [LO name], I'm Jesse Oñate, bilingual realtor in Downey, 100+ closings. I send roughly 40-60 buyer leads/year and right now I'm looking for ONE lender to be my go-to for my first-time buyers — bilingual, fast pre-approvals, doesn't ghost. In exchange I'd embed your pre-approval form on my site (jessetek.net/buyer and /calculator) and refer my first-time buyers to you exclusively. No referral fee structure — just a working partnership. Worth a 30-min meeting?"

### What to negotiate

- **48-hour pre-approval turnaround** for your referrals (must be in writing)
- **Their pre-approval form** embedded on your `/buyer` page
- **Co-branded landing page** (lender-financing-options.html) — costs them nothing, dominates SEO
- **Educational webinars** quarterly — joint content marketing
- **No ITIN restrictions** — important for Hispanic buyers without SSN

### What you do NOT do

- Take referral fees (illegal in most states under RESPA — unless you have a properly disclosed Marketing Service Agreement)
- Promise specific rates
- Give them direct contact info for your leads without permission

---

## 8. Trustpilot / Birdeye verified reviews

Diversifies trust signals beyond Google. Important for ad copy ("4.9 on Trustpilot" can be stronger than another Google badge).

### Trustpilot setup

1. **Sign up:** https://business.trustpilot.com
2. **Free tier:** Get verified, collect reviews, display badge
3. **Plan time:** 1 hour to set up + 30 days to collect first 20+ reviews
4. **Review collection:** Use their auto-invite tool. Send to last 50 closed clients. Expected 30-40% response rate.
5. **Embed:** Add their widget to `/reviews` page (I can wire it up once you have the embed code)

### Birdeye alternative

Birdeye consolidates Google + Yelp + Facebook reviews into one widget. Paid — starts at $299/mo. Worth it if you want to streamline the multi-platform review workflow. Their widget is what's currently embedded on `/reviews` (`reputationhub.site` — looks like a Birdeye/Jtek setup).

---

## 9. Video hero asset (when ready)

The audit recommended a 15-second video hero on `/`. To make this happen:

### What to film

A single 15-second loop showing:
- 0-3s: You at a kitchen table with a client family, talking
- 3-7s: Quick walkthrough of a property you sold (interior)
- 7-12s: Handing keys to a client at the front door (the classic shot)
- 12-15s: You on the phone, looking professional, smiling

### Production specs

- 1920×1080, 30fps minimum
- MP4, H.264 codec
- < 2MB file size (compress aggressively — 480p downscaled is fine)
- WebM secondary version for browsers that support it
- Silent (autoplaying audio is a conversion killer + browser-blocked anyway)
- Loop seamlessly (last frame matches first)

### Cost

- Self-shot on iPhone 15+ with a tripod and natural light: $0
- Local SoCal videographer for half-day shoot: $400-$800
- Post-production (color, cut, compress): another $200 if outsourced

### Implementation

When the video is ready, drop it at `public/img/hero-loop.mp4` and `public/img/hero-loop.webm`. I'll wire up the `<video>` tag with proper poster fallback to the existing photo.

---

## 10. Programmatic SEO — additional landing pages

Currently you have 47 city pages. Three additional templates × 47 cities = 141 new long-tail SEO pages.

### Template 1: "Best Bilingual Realtor in [City]"

Targets: bilingual searchers in each city. Highest intent.
URL pattern: `/best-bilingual-realtor-{city-slug}`
Content: 600 words, mentions specific city neighborhoods, Spanish-speaking value prop, your bilingual specialty, embedded reviews.

### Template 2: "Sell Your [City] Home for $X+ Over Asking"

Targets: sellers researching pricing strategy.
URL pattern: `/sell-{city-slug}-over-asking`
Content: 600 words, the Maria-Whittier case study story applied to that city, median over-asking data, your strategy, valuation CTA.

### Template 3: "First-Time Buyer in [City] — 2026 Guide"

Targets: first-time buyer queries with city modifiers.
URL pattern: `/first-time-buyer-{city-slug}-2026`
Content: 600 words, specific city median price, programs (CalHFA), schools, neighborhoods to target by budget, buyer quiz CTA.

### To generate

Tell me when you want these built. I can generate all 141 in a batch from a Python template (similar to how the existing 47 city pages were built). Estimate: 2-3 hours of my time + a content review pass. Output: 141 new pages, all properly canonicalized, in sitemap, internally linked from `/service-areas`.

### Expected SEO impact

Long-tail keywords like "best bilingual realtor downey" or "sell my whittier home over asking" have low competition but real search volume. Most realtors don't target these. Expected: 5-15 additional organic leads/month within 6 months of indexing.

---

## Priority order if you can only do 3 things

1. **Activate weekly Clarity reviews.** 30 min/week, free, immediately actionable insights.
2. **Apply for Google Local Services Ads.** 1-hour setup, top-of-page Google placement, pay-per-lead.
3. **Set up the SMS keyword (`JESSE`) in LeadConnector.** 15 min, widens funnel by 30%+.

Everything else compounds on top of these three.
