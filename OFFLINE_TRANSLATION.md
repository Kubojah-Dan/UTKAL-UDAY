# Offline Translation Strategy

## How It Works

### Online Mode (Teacher)
1. Teacher generates/uploads questions
2. Teacher selects languages to translate (Hindi, Tamil, Telugu, Odia)
3. Backend calls Sarvam AI API to translate
4. Translations saved in `language_variants` field in MongoDB
5. Questions synced to students with translations included

### Offline Mode (Student)
1. Student downloads questions with pre-translated content
2. Questions stored in PouchDB with `language_variants` object
3. Student changes language → Frontend reads from cached translations
4. No API calls needed - all translations already in local database

## Database Structure

```javascript
{
  "id": "q123",
  "question": "What is 2 + 2?",
  "answer": "4",
  "options": ["2", "3", "4", "5"],
  "language_variants": {
    "en": {
      "question": "What is 2 + 2?",
      "options": ["2", "3", "4", "5"],
      "hint": "Add the numbers",
      "explanation": "2 plus 2 equals 4"
    },
    "hi": {
      "question": "2 + 2 क्या है?",
      "options": ["2", "3", "4", "5"],
      "hint": "संख्याओं को जोड़ें",
      "explanation": "2 जमा 2 बराबर 4 होता है"
    },
    "ta": {
      "question": "2 + 2 என்ன?",
      "options": ["2", "3", "4", "5"],
      "hint": "எண்களைச் சேர்க்கவும்",
      "explanation": "2 கூட்டல் 2 சமம் 4"
    }
  }
}
```

## Implementation

### Backend (Already Done)
- `app/core/translation.py` - Sarvam AI integration
- `app/api/tools.py` - `/tools/approve-questions` translates before saving
- Translations stored in MongoDB `questions` collection

### Frontend (Already Done)
- `context/LanguageContext.jsx` - Language state management
- `getTranslatedContent()` - Reads from `language_variants`
- Works offline - no API calls from student side

## Workflow

### Teacher Workflow
1. Generate questions with AI
2. Select translation languages (checkboxes)
3. Click "Approve & Add to Database"
4. Backend translates to selected languages (online required)
5. Questions saved with all translations

### Student Workflow
1. Login → Questions synced to PouchDB (online required once)
2. Change language → Reads from local cache (offline works)
3. Complete quest → Saves interaction locally (offline works)
4. Sync when online → Uploads interactions to backend

## Advantages

✅ Students work 100% offline after initial sync
✅ No translation API calls from student devices
✅ Fast language switching (instant, no loading)
✅ Consistent translations (same for all students)
✅ Reduced API costs (translate once, use many times)

## Limitations

⚠️ Teacher needs internet to translate questions
⚠️ Students need internet for initial question download
⚠️ New questions require re-sync to get translations
⚠️ Translation quality depends on Sarvam AI

## Testing

### Test Translation
```bash
# Test Sarvam API directly
curl 'https://api.sarvam.ai/translate' \
  -H 'api-subscription-key: YOUR_KEY' \
  -H 'content-type: application/json' \
  --data-raw '{
    "input": "What is 2 + 2?",
    "source_language_code": "en-IN",
    "target_language_code": "hi-IN",
    "speaker_gender": "Male",
    "mode": "formal",
    "model": "mayura:v1",
    "enable_preprocessing": false
  }'
```

### Test Offline Mode
1. Generate questions with translations (online)
2. Open DevTools → Network tab → Go offline
3. Change language in student view
4. ✅ Should show translated content without network requests

## Supported Languages

Only 4 languages (as requested):
- **Hindi** (hi) - हिंदी
- **Tamil** (ta) - தமிழ்
- **Telugu** (te) - తెలుగు
- **Odia** (or) - ଓଡ଼ିଆ

## API Format

Sarvam AI requires:
- Language codes: `en-IN`, `hi-IN`, `ta-IN`, `te-IN`, `or-IN`
- Headers: `api-subscription-key` (not Bearer token)
- Model: `mayura:v1`
- Mode: `formal` (for educational content)

## Fallback Strategy

If translation fails:
1. Question saved with English only
2. Student sees English text when selecting other languages
3. No error shown to student (graceful degradation)
4. Teacher can re-translate later by editing question
