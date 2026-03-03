# Banner Dummy Data - Insurance Premium Financing

Use this data to create banners in the admin panel for the upcoming **Insurance Premium Financing** feature.

---

## Banner 1: Main Announcement Banner (Home Screen)

| Field | Value |
|-------|-------|
| **Title** | Premium Financing - Coming Soon! |
| **Subtitle** | Pay your insurance premiums in easy EMIs |
| **Description** | Can't afford to pay your full premium at once? Soon you'll be able to split your insurance premiums into affordable monthly installments with 0% interest for the first 3 months! |
| **Banner Type** | Coming Soon |
| **Display Position** | Home - Top (or leave empty for All Screens) |
| **Target Audience** | All Users |
| **Priority** | 95 |
| **Background Color** | #7C3AED (Purple) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | No |

---

## Banner 2: Dashboard Reminder

| Field | Value |
|-------|-------|
| **Title** | EMI for Premiums - Launching Soon! |
| **Subtitle** | Never miss a premium payment again |
| **Description** | Convert your annual premiums to monthly EMIs. Get instant approval with minimal documentation. Stay protected without financial stress! |
| **Banner Type** | Coming Soon |
| **Display Position** | Dashboard |
| **Target Audience** | Returning Users |
| **Priority** | 85 |
| **Background Color** | #059669 (Green) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | No |

---

## Banner 3: Policy List Screen

| Field | Value |
|-------|-------|
| **Title** | Struggling with Premium Payments? |
| **Subtitle** | Premium Financing coming to rescue! |
| **Description** | Soon you can finance premiums for all your policies - Health, Life, Motor & more. Flexible tenures from 3 to 12 months. |
| **Banner Type** | Coming Soon |
| **Display Position** | Policy List |
| **Target Audience** | Returning Users |
| **Priority** | 80 |
| **Background Color** | #2563EB (Blue) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | Yes |

---

## Banner 4: Premium Users Special

| Field | Value |
|-------|-------|
| **Title** | Exclusive: Priority Access to Premium Financing |
| **Subtitle** | As a valued customer, you'll get first access! |
| **Description** | Premium financing with special rates exclusively for our loyal customers. Pre-approved limits up to Rs. 5 Lakhs. Zero processing fees for early adopters! |
| **Banner Type** | Announcement |
| **Display Position** | All Screens (leave empty) |
| **Target Audience** | Premium Users (3+ policies) |
| **Priority** | 100 |
| **Background Color** | #DC2626 (Red) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | Yes |

---

## Banner 5: Full Screen Popup (High Impact)

| Field | Value |
|-------|-------|
| **Title** | Insurance Premium Financing |
| **Subtitle** | Your premiums, your pace! |
| **Description** | Big news! We're launching premium financing soon. Convert your insurance premiums into easy EMIs. Benefits: No hidden charges, Instant approval, Flexible tenure (3-12 months), All policy types supported. Be the first to know when we launch! |
| **Banner Type** | Coming Soon |
| **Display Position** | Full Screen Popup |
| **Target Audience** | All Users |
| **Priority** | 90 |
| **Background Color** | #4F46E5 (Indigo) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | Yes |

---

## Banner 6: New Users Welcome

| Field | Value |
|-------|-------|
| **Title** | New to Eazr? Premium Financing Coming Soon! |
| **Subtitle** | Affordable insurance starts here |
| **Description** | Don't let high premiums stop you from getting insured. Our upcoming premium financing feature lets you pay in small monthly installments. Upload your first policy today! |
| **Banner Type** | Informational |
| **Display Position** | Home - Bottom |
| **Target Audience** | New Users |
| **Priority** | 75 |
| **Background Color** | #0891B2 (Cyan) |
| **Text Color** | #FFFFFF (White) |
| **CTA Type** | None |
| **Is Active** | Yes |
| **Show Only Once** | No |

---

## Quick Reference - Color Codes

| Color | Hex Code | Use Case |
|-------|----------|----------|
| Purple | #7C3AED | Primary announcements |
| Indigo | #4F46E5 | Feature highlights |
| Blue | #2563EB | Informational |
| Green | #059669 | Positive/Success messages |
| Red | #DC2626 | Urgent/Important |
| Cyan | #0891B2 | Fresh/New user content |
| Orange | #EA580C | Warnings/Attention |
| Pink | #DB2777 | Special offers |

---

## Suggested Images (Optional)

You can upload images to S3 via the admin panel. Suggested image themes:

1. **EMI Calculator Visual** - Show a calculator with rupee symbol
2. **Happy Family** - Family protected with insurance shield
3. **Money/Coins Stack** - Representing savings/affordability
4. **Calendar with Checkmarks** - Monthly payment schedule
5. **Shield with Rupee** - Financial protection symbol

---

## How to Add These Banners

1. Go to **Admin Panel** > **Banners & Ads**
2. Click **"Create New Banner"** or use **"Quick Create Coming Soon"**
3. Fill in the fields from the tables above
4. Click **"Save Banner"**
5. The banner will appear in the Flutter app based on position and targeting

---

## Testing Checklist

After adding banners, verify:

- [ ] Banner appears on correct screen/position
- [ ] Target audience filtering works (new vs returning vs premium users)
- [ ] "Show Only Once" banners don't reappear after dismissal
- [ ] Priority ordering is correct (higher priority shows first)
- [ ] Colors and text are readable
- [ ] Banner analytics are being tracked (impressions/clicks)
