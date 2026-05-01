# Valuation Page Automation Setup

Two pieces:
1. **Code (already deployed)** — `/api/valuation` pushes form submissions to your Jtek/LeadConnector account with auto-tags
2. **LeadConnector workflow (you set up once)** — fires on those tags to auto-text the seller and notify you

---

## What the form sends to LeadConnector

When someone submits the valuation form, a contact is created (or upserted if they already exist) with:

**Standard fields:**
- `firstName` / `lastName` (split from "name" field)
- `phone` OR `email` (auto-detected — if the contact field has `@`, it's email; otherwise phone)
- `address1` (the property address — note: this is the seller's home, not their mailing address)
- `source`: `Free Home Valuation Request`

**Custom fields** (visible in contact detail):
- `property_address` — the address they entered
- `bedrooms` — 1, 2, 3, 4, or 5+
- `sell_timeline` — Just curious / 3-6 months / 1-3 months / ASAP

**Tags** (always added):
- `valuation-request`
- `seller`

**Tags by timeline** (one of):
- `lead-hot` + `timeline-asap`
- `lead-hot` + `timeline-1-3-months`
- `lead-warm` + `timeline-3-6-months`
- `lead-nurture` + `timeline-curious`

---

## LeadConnector Workflow #1 — Auto-text the seller

This sends an instant text confirmation when a valuation request comes in. Builds trust, sets a 24h expectation, prevents the seller from second-guessing.

**Setup:**

1. Log into Jtek/LeadConnector → **Automation** → **Workflows** → **+ Create Workflow** → **Start from scratch**
2. **Trigger:** "Contact Tag" → tag is `valuation-request`
3. **Add filter:** "Has Phone" (so we only text people who gave a phone, not email-only)
4. **Add action:** "Send SMS"
   - From: your business number
   - Message:
     ```
     Hey {{contact.first_name}} — Jesse here. Got your valuation request for {{contact.custom_field.property_address}}. I'll text you within 24h with real comps + a value range. — Jesse Oñate, Realtor
     ```
5. **Wait step:** 1 minute (gives you time to be notified before the seller might reply)
6. **Save & Publish**

**Variant for email-only leads:** create a second workflow with the same trigger + filter "Has Email" instead, action: "Send Email" with the same copy.

---

## LeadConnector Workflow #2 — Notify Jesse instantly

So you know within 30 seconds that a hot lead just came in.

**Setup:**

1. New Workflow → **Trigger:** "Contact Tag" is `valuation-request`
2. **Add action:** "Send Internal Notification" (or "Send SMS to Internal User")
   - To: your personal cell
   - Message:
     ```
     🏠 NEW VALUATION
     Name: {{contact.first_name}} {{contact.last_name}}
     Address: {{contact.custom_field.property_address}}
     Timeline: {{contact.custom_field.sell_timeline}}
     Bedrooms: {{contact.custom_field.bedrooms}}
     Phone: {{contact.phone}}
     Email: {{contact.email}}
     ```
3. **Add action:** "Create Task" — assigned to you, due date today, title `CMA: {{contact.first_name}} – {{contact.custom_field.property_address}}`
4. **Save & Publish**

---

## LeadConnector Workflow #3 (optional) — Hot-lead escalation

If the seller picked **ASAP** or **1-3 months**, they're a serious lead. Push them to a separate pipeline / tag them for priority follow-up.

**Setup:**

1. New Workflow → **Trigger:** "Contact Tag" is `lead-hot`
2. **Add action:** "Move to Pipeline" → your seller pipeline → stage: "Hot · Needs CMA Today"
3. **Add action:** "Send Internal SMS" — `🔥 HOT VALUATION LEAD: {{contact.first_name}} wants to sell within 3 months at {{contact.custom_field.property_address}}`
4. **Save & Publish**

---

## Test it

After setting up the workflows:

1. Go to https://jessetek.net/valuation
2. Submit the form with **your own** phone/email, address `123 Test Ave, Downey, CA`, timeline `ASAP`
3. Within 1-2 minutes you should:
   - Get the seller-facing auto-text/email on your contact info
   - Get the internal notification on your cell
   - See the new contact in LeadConnector with all 4 tags applied
   - See the contact in your seller pipeline at "Hot" stage

If anything's missing, check:
- Workflow is **Published** (not just saved as draft)
- Trigger filters match exactly (tag must be exactly `valuation-request`, no typos)
- Tag was added to the test contact (visible in their contact detail)

---

## Future: turn this into a nurture sequence

Once your CMA delivery is rolling, consider adding to Workflow #1:

- **Wait 24 hours** → "If contact has tag `cma-sent` STOP, else send a follow-up text" (`Hey {{first}}, did you get my CMA email? Reply HERE if not.`)
- **Wait 7 days** → "If contact has not booked a call → send valuation FAQ email"
- **Wait 30 days** → "Move to long-term nurture pipeline"

This gets built once and runs forever.
