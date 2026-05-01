/* ============================================================
   GOOGLE REVIEWS API INTEGRATION (scaffold)
   ------------------------------------------------------------
   Pulls live Google reviews from the Place Details API and
   renders them into <div id="live-reviews"></div> if present.

   Setup:
   1. Get your Place ID:
      https://developers.google.com/maps/documentation/places/web-service/place-id
      (Search "Jesse Onate Realtor Montebello" — copy the Place ID)
   2. Get a Google Maps API key with Places API enabled:
      https://console.cloud.google.com/apis/credentials
   3. Restrict the API key to:
      - HTTP referrers: jessetek.net/* (security)
      - APIs: Places API only
   4. Set both values in window.JESSE_CONFIG below in analytics.js
      or paste them inline at the top of this file.

   The API allows ~1,000 requests/month free. We cache results
   in localStorage for 24 hours so each visitor uses 0 requests
   after the first daily fetch.
   ============================================================ */

(function () {
  var cfg = window.JESSE_CONFIG || {};
  var PLACE_ID = cfg.GOOGLE_PLACE_ID || null;
  var API_KEY  = cfg.GOOGLE_PLACES_API_KEY || null;

  var container = document.getElementById('live-reviews');
  if (!container) return;

  if (!PLACE_ID || !API_KEY) {
    // Not configured yet — leave the static fallback in the DOM
    return;
  }

  var CACHE_KEY = 'jesse-google-reviews-v1';
  var CACHE_TTL = 24 * 60 * 60 * 1000; // 24h

  function render(reviews, rating, count) {
    var html = '<div class="live-reviews-header" style="text-align:center;margin-bottom:32px">';
    html += '<div style="font-size:48px;font-weight:800;color:var(--text);letter-spacing:-1.6px">' + rating.toFixed(1) + ' ★</div>';
    html += '<div style="font-size:14px;color:var(--text2)">Based on ' + count + ' Google reviews</div>';
    html += '<a href="https://search.google.com/local/writereview?placeid=' + encodeURIComponent(PLACE_ID) + '" target="_blank" rel="noopener" style="display:inline-block;margin-top:12px;font-size:13px;color:var(--blue);text-decoration:underline">Leave a review →</a>';
    html += '</div>';
    html += '<div class="live-reviews-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px">';
    reviews.slice(0, 12).forEach(function (r) {
      html += '<div style="background:#fff;border-radius:16px;padding:22px;box-shadow:var(--shadow);border:1px solid rgba(0,0,0,.04)">';
      html += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">';
      if (r.profile_photo_url) {
        html += '<img src="' + r.profile_photo_url + '" alt="" style="width:36px;height:36px;border-radius:50%" loading="lazy">';
      }
      html += '<div><div style="font-weight:600;font-size:14px">' + r.author_name + '</div>';
      html += '<div style="font-size:12px;color:var(--text3)">' + r.relative_time_description + '</div></div>';
      html += '</div>';
      html += '<div style="color:#FFD700;letter-spacing:1px;margin-bottom:8px">' + '★'.repeat(r.rating) + '</div>';
      html += '<div style="font-size:14px;color:var(--text);line-height:1.55">' + r.text + '</div>';
      html += '</div>';
    });
    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
  }

  function loadFromCache() {
    try {
      var raw = localStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (Date.now() - data.fetchedAt > CACHE_TTL) return null;
      return data;
    } catch (e) { return null; }
  }

  function saveCache(data) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(data)); } catch (e) {}
  }

  // Try cache first
  var cached = loadFromCache();
  if (cached) {
    render(cached.reviews, cached.rating, cached.count);
    return;
  }

  // Fetch from Places API
  var url = 'https://maps.googleapis.com/maps/api/place/details/json'
          + '?place_id=' + encodeURIComponent(PLACE_ID)
          + '&fields=reviews,rating,user_ratings_total'
          + '&key=' + API_KEY;

  fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (json) {
      if (!json.result) return;
      var data = {
        reviews: json.result.reviews || [],
        rating: json.result.rating || 5.0,
        count: json.result.user_ratings_total || 100,
        fetchedAt: Date.now()
      };
      saveCache(data);
      render(data.reviews, data.rating, data.count);
    })
    .catch(function (err) { console.warn('Reviews API failed', err); });
})();
