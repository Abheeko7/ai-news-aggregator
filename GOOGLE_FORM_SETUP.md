# Google Form Setup for Newsletter Subscribers

This guide explains how to create the Google Form, connect it to a Subscribers sheet, and sync with the AI News Aggregator.

---

## 1. Create the Google Form

**You** create the form in Google Forms. Use these exact questions to ensure the import script reads the data correctly.

### Questions to Add

| # | Question | Type | Required | Notes |
|---|----------|------|----------|-------|
| 1 | **Email** | Short answer | Yes | Validation: Response validation → Text → Email |
| 2 | **Preferred Name** | Short answer | Yes | "How would you like to be addressed in the newsletter? (e.g., John, Sarah)" |
| 3 | **Topics** | Checkboxes | Yes | Add these 4 options (exact text): |

### Checkbox Options for "Topics"

- `YouTube` – AI videos and tutorials
- `OpenAI` – OpenAI news and updates
- `Anthropic` – Anthropic/Claude news
- `Formula 1` – F1 news

**Important:** Use these exact checkbox labels so the Apps Script can map them correctly.

---

## 2. Form Response Column Order

When you create the form, Google Sheets will create a "Form Responses 1" sheet with columns in this order:

| Column A | Column B | Column C | Column D |
|----------|----------|----------|----------|
| Timestamp | Email | Preferred Name | Topics |

The **Topics** column will contain comma-separated values like `"YouTube, OpenAI"` when multiple are selected.

---

## 3. Create the Subscribers Sheet

1. In the **same** spreadsheet that receives form responses, add a new sheet.
2. Name it **Subscribers**.
3. Add this header row in row 1:

   | email | preferred_name | youtube | openai | anthropic | f1 |
   |-------|----------------|---------|--------|-----------|-----|

4. Leave row 2 and below empty. The Apps Script will fill them.

---

## 4. Add the Apps Script

1. In the spreadsheet: **Extensions → Apps Script**.
2. Replace any existing code with:

```javascript
/**
 * Syncs new form submissions into the Subscribers sheet.
 * Run on form submit (trigger) or manually.
 */
function onFormSubmit(e) {
  if (!e || !e.values) return;
  
  const sheet = SpreadsheetApp.getActiveSpreadsheet();
  const subscribersSheet = sheet.getSheetByName("Subscribers");
  if (!subscribersSheet) {
    Logger.log("Subscribers sheet not found");
    return;
  }

  // e.values: [Timestamp, Email, Preferred Name, Topics]
  const timestamp = e.values[0];
  const email = (e.values[1] || "").toString().trim();
  const preferredName = (e.values[2] || "there").toString().trim() || "there";
  const topicsStr = (e.values[3] || "").toString().toLowerCase();

  if (!email || email.indexOf("@") === -1) return;

  const youtube = topicsStr.includes("youtube");
  const openai = topicsStr.includes("openai");
  const anthropic = topicsStr.includes("anthropic");
  const f1 = topicsStr.includes("formula 1") || topicsStr.includes("formula1");

  const data = subscribersSheet.getDataRange().getValues();
  const headers = data[0];
  let found = false;

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]).trim().toLowerCase() === email.toLowerCase()) {
      subscribersSheet.getRange(i + 1, 1, i + 1, 6).setValues([
        [email, preferredName, youtube ? "true" : "false", openai ? "true" : "false", anthropic ? "true" : "false", f1 ? "true" : "false"]
      ]);
      found = true;
      break;
    }
  }

  if (!found) {
    subscribersSheet.appendRow([email, preferredName, youtube ? "true" : "false", openai ? "true" : "false", anthropic ? "true" : "false", f1 ? "true" : "false"]);
  }
}
```

3. **Save** (Ctrl/Cmd + S). Name the project if prompted (e.g. "Newsletter Subscribers Sync").

---

## 5. Set Up the Trigger

1. In Apps Script: click the **clock icon** (Triggers) in the left sidebar.
2. **Add Trigger**.
3. Configure:
   - Function: `onFormSubmit`
   - Event: **From spreadsheet**
   - Type: **On form submit**
4. Save. Approve permissions when prompted.

---

## 6. Publish the Subscribers Sheet as CSV

1. In the spreadsheet, go to the **Subscribers** sheet.
2. **File → Share → Publish to web**
3. Choose:
   - **Entire document** or **Subscribers** (the sheet)
   - Format: **Comma-separated values (.csv)**
4. Click **Publish**. Copy the URL.

The URL will look like:
```
https://docs.google.com/spreadsheets/d/SHEET_ID/export?format=csv&gid=SHEET_GID
```

---

## 7. Configure the App

1. Add to your `.env`:
   ```
   SUBSCRIBERS_CSV_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv&gid=YOUR_GID
   ```

2. On **Render**: In your web service → Environment, add:
   - Key: `SUBSCRIBERS_CSV_URL`
   - Value: the same URL

---

## 8. Flow Summary

| Step | What happens |
|------|--------------|
| 1 | User submits the Google Form |
| 2 | Response appears in Form Responses sheet |
| 3 | Apps Script runs on form submit |
| 4 | Script upserts the row into the Subscribers sheet |
| 5 | Subscribers sheet is published as CSV |
| 6 | Before each run, the pipeline imports subscribers from the CSV URL |
| 7 | Newsletter is sent to each subscriber with their preferences and preferred name |

---

## 9. Column Mapping Reference

| Form field   | Subscribers column | Import expects |
|--------------|--------------------|----------------|
| Email        | email              | Valid email    |
| Preferred Name | preferred_name   | Any string (default: "there") |
| Topics (YouTube) | youtube        | true/false     |
| Topics (OpenAI)  | openai         | true/false     |
| Topics (Anthropic) | anthropic    | true/false     |
| Topics (Formula 1) | f1            | true/false     |

---

## 10. Unsubscribe (Optional)

To support unsubscribes:

1. Add an "Unsubscribe" form (Email + confirmation) or a separate sheet for unsubscribes.
2. Extend the Apps Script or import logic to mark those emails as `active=false` in the Subscribers sheet.
3. Or manually set `active` to `false` for a subscriber in the sheet (add an `active` column if needed).

For a minimal setup, you can leave `active` out and the import will treat all rows as active.


# https://docs.google.com/forms/d/e/1FAIpQLScs1v6xzcgq5NDFkqJz2eZ3Hu7xlcnSx2pDseKafVKh-NoMHg/viewform?usp=publish-editor