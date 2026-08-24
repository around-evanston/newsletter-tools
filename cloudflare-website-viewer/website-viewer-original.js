export default {
  async fetch(request, env) {

    // ── 1. CORS / Origin allowlist ──────────────────────────────────────────
    const ALLOWED_ORIGINS = [
      'https://www.aroundevanston.com',
      'https://aroundevanston.com',
      'https://www.enjoyevanston.com',
      'https://enjoyevanston.com'
      // add your other domains here if needed
    ];

    const origin = request.headers.get('Origin') || '';
    const isAllowed = ALLOWED_ORIGINS.some(o => origin === o);

    // Handle preflight
    if (request.method === 'OPTIONS') {
      if (isAllowed) {
        return new Response(null, {
          status: 204,
          headers: corsHeaders(origin),
        });
      }
      return new Response('Forbidden', { status: 403 });
    }

    if (!isAllowed) {
      return new Response('Forbidden', { status: 403 });
    }

    // ── 2. Rate limiting (per IP, in-memory per Worker instance) ───────────
    // Simple token bucket: max 30 requests per minute per IP
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Date.now();
    const windowMs = 60_000;
    const maxRequests = 30;

    if (!env.__RL) env.__RL = {};
    const rl = env.__RL;
    if (!rl[clientIP] || now - rl[clientIP].ts > windowMs) {
      rl[clientIP] = { ts: now, count: 0 };
    }
    rl[clientIP].count++;
    if (rl[clientIP].count > maxRequests) {
      return new Response('Too Many Requests', { status: 429 });
    }

    // ── 3. Fetch latest Mailchimp campaign ─────────────────────────────────
    const API_KEY = env.MAILCHIMP_API_KEY;
    if (!API_KEY) {
      return new Response(JSON.stringify({ error: 'Server misconfiguration' }), {
        status: 500,
        headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
      });
    }

    const DC = API_KEY.split('-').pop(); // e.g. "us21"
    const authHeader = `Basic ${btoa(`anystring:${API_KEY}`)}`;

    try {
      // Get the single most recent sent campaign
      const campaignsRes = await fetch(
        `https://${DC}.api.mailchimp.com/3.0/campaigns?status=sent&count=1&sort_field=send_time&sort_dir=DESC`,
        { headers: { Authorization: authHeader } }
      );

      if (!campaignsRes.ok) {
        throw new Error(`Mailchimp campaigns API error: ${campaignsRes.status}`);
      }

      const campaigns = await campaignsRes.json();
      const latest = campaigns.campaigns?.[0];

      if (!latest) {
        return new Response(JSON.stringify({ error: 'No sent campaigns found' }), {
          status: 404,
          headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
        });
      }

      // Get the HTML content
      const contentRes = await fetch(
        `https://${DC}.api.mailchimp.com/3.0/campaigns/${latest.id}/content`,
        { headers: { Authorization: authHeader } }
      );

      if (!contentRes.ok) {
        throw new Error(`Mailchimp content API error: ${contentRes.status}`);
      }

      const content = await contentRes.json();

      return new Response(
        JSON.stringify({
          title: latest.settings?.subject_line ?? '',
          send_time: latest.send_time ?? '',
          archive_url: latest.archive_url ?? '',
          html: content.html ?? '',
        }),
        {
          status: 200,
          headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
        }
      );

    } catch (err) {
      return new Response(
        JSON.stringify({ error: 'Failed to fetch newsletter' }),
        {
          status: 502,
          headers: { ...corsHeaders(origin), 'Content-Type': 'application/json' },
        }
      );
    }
  },
};

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}
