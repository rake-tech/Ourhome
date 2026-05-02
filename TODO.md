# TODO: Integrate Google API Key for Orphanage Search & YouTube Fix

## Plan Steps

- [x] 1. Update `config.py` — add API key defaults for `YOUTUBE_API_KEY` and `GOOGLE_API_KEY`
- [x] 2. Update `ourhome_app.py` — improve YouTube fetch, add Places API orphanage search, update routes
- [x] 3. Update `templates/dashboard.html` — fix YouTube embeds, add recommended orphanages panel
- [x] 4. Update `templates/enquiry.html` — show richer orphanage cards with Places API data
- [x] 5. Test and verify

## Notes
- YouTube Data API: ✅ Working — fetches India-relevant orphan welfare videos
- Google Places API: ⚠️ `REQUEST_DENIED` — needs enabling in Google Cloud Console

