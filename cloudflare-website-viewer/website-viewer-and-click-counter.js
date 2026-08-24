export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ─────────────────────────────────────────────────────────────
    // 0. CLICK TRACKING ENDPOINT
    // ─────────────────────────────────────────────────────────────
    //
    // This endpoint is intentionally NOT protected by the Origin
    // allowlist because normal link clicks are top-level navigations
    // and may not include an Origin header.
    //
    if (url.pathname === "/click") {
      return handleClick(request, env);
    }

    // ─────────────────────────────────────────────────────────────
    // 1. CORS / ORIGIN ALLOWLIST
    // ─────────────────────────────────────────────────────────────

    const ALLOWED_ORIGINS = [
      "https://www.aroundevanston.com",
      "https://aroundevanston.com",
      "https://www.enjoyevanston.com",
      "https://enjoyevanston.com",
    ];

    const origin = request.headers.get("Origin") || "";
    const isAllowed = ALLOWED_ORIGINS.includes(origin);

    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      if (isAllowed) {
        return new Response(null, {
          status: 204,
          headers: corsHeaders(origin),
        });
      }

      return new Response("Forbidden", { status: 403 });
    }

    if (!isAllowed) {
      return new Response("Forbidden", { status: 403 });
    }

    // ─────────────────────────────────────────────────────────────
    // 2. BASIC RATE LIMITING
    // ─────────────────────────────────────────────────────────────

    const clientIP =
      request.headers.get("CF-Connecting-IP") || "unknown";

    const now = Date.now();
    const windowMs = 60_000;
    const maxRequests = 30;

    if (!globalThis.__RL) {
      globalThis.__RL = {};
    }

    const rl = globalThis.__RL;

    if (!rl[clientIP] || now - rl[clientIP].ts > windowMs) {
      rl[clientIP] = {
        ts: now,
        count: 0,
      };
    }

    rl[clientIP].count++;

    if (rl[clientIP].count > maxRequests) {
      return new Response("Too Many Requests", {
        status: 429,
        headers: corsHeaders(origin),
      });
    }

    // ─────────────────────────────────────────────────────────────
    // 3. MAILCHIMP CONFIG
    // ─────────────────────────────────────────────────────────────

    const API_KEY = env.MAILCHIMP_API_KEY;

    if (!API_KEY) {
      return new Response(
        JSON.stringify({
          error: "Server misconfiguration",
        }),
        {
          status: 500,
          headers: {
            ...corsHeaders(origin),
            "Content-Type": "application/json",
          },
        }
      );
    }

    const DC = API_KEY.split("-").pop();

    const authHeader =
      `Basic ${btoa(`anystring:${API_KEY}`)}`;

    try {
      // ───────────────────────────────────────────────────────────
      // 4. GET LATEST SENT CAMPAIGN
      // ───────────────────────────────────────────────────────────

      const campaignsRes = await fetch(
        `https://${DC}.api.mailchimp.com/3.0/campaigns?status=sent&count=1&sort_field=send_time&sort_dir=DESC`,
        {
          headers: {
            Authorization: authHeader,
          },
        }
      );

      if (!campaignsRes.ok) {
        throw new Error(
          `Mailchimp campaigns API error: ${campaignsRes.status}`
        );
      }

      const campaigns = await campaignsRes.json();
      const latest = campaigns.campaigns?.[0];

      if (!latest) {
        return new Response(
          JSON.stringify({
            error: "No sent campaigns found",
          }),
          {
            status: 404,
            headers: {
              ...corsHeaders(origin),
              "Content-Type": "application/json",
            },
          }
        );
      }

      // ───────────────────────────────────────────────────────────
      // 5. GET CAMPAIGN HTML
      // ───────────────────────────────────────────────────────────

      const contentRes = await fetch(
        `https://${DC}.api.mailchimp.com/3.0/campaigns/${latest.id}/content`,
        {
          headers: {
            Authorization: authHeader,
          },
        }
      );

      if (!contentRes.ok) {
        throw new Error(
          `Mailchimp content API error: ${contentRes.status}`
        );
      }

      const content = await contentRes.json();

      // ───────────────────────────────────────────────────────────
      // 6. REWRITE LINKS FOR CLICK TRACKING
      // ───────────────────────────────────────────────────────────

      const workerOrigin = url.origin;

      const rewrittenHtml = await rewriteLinks(
        content.html ?? "",
        workerOrigin,
        latest.id
      );

      // ───────────────────────────────────────────────────────────
      // 7. RETURN NEWSLETTER
      // ───────────────────────────────────────────────────────────

      return new Response(
        JSON.stringify({
          title: latest.settings?.subject_line ?? "",
          send_time: latest.send_time ?? "",
          archive_url: latest.archive_url ?? "",
          campaign_id: latest.id,
          html: rewrittenHtml,
        }),
        {
          status: 200,
          headers: {
            ...corsHeaders(origin),
            "Content-Type": "application/json",
          },
        }
      );
    } catch (err) {
      console.error("Newsletter error:", err);

      return new Response(
        JSON.stringify({
          error: "Failed to fetch newsletter",
        }),
        {
          status: 502,
          headers: {
            ...corsHeaders(origin),
            "Content-Type": "application/json",
          },
        }
      );
    }
  },
};


// ======================================================================
// CLICK HANDLER
// ======================================================================

async function handleClick(request, env) {
  const url = new URL(request.url);

  const destination = url.searchParams.get("url");
  const campaign = url.searchParams.get("campaign") || "unknown";

  if (!destination) {
    return new Response("Missing destination", {
      status: 400,
    });
  }

  let destinationUrl;

  try {
    destinationUrl = new URL(destination);
  } catch {
    return new Response("Invalid destination", {
      status: 400,
    });
  }

  // Only allow normal web URLs.
  // This prevents javascript:, data:, file:, etc.
  if (
    destinationUrl.protocol !== "https:" &&
    destinationUrl.protocol !== "http:"
  ) {
    return new Response("Invalid destination", {
      status: 400,
    });
  }

  // ───────────────────────────────────────────────────────────────
  // CLICK LOGGING
  // ───────────────────────────────────────────────────────────────

  console.log(
    JSON.stringify({
      event: "newsletter_click",
      campaign,
      destination: destinationUrl.href,
      hostname: destinationUrl.hostname,
      timestamp: new Date().toISOString(),
      referrer: request.headers.get("Referer") || "",
      country:
        request.headers.get("CF-IPCountry") ||
        request.cf?.country ||
        "",
    })
  );

  // If you later add an Analytics Engine binding named ANALYTICS,
  // this will automatically start storing click data there.
  if (env.ANALYTICS) {
    env.ANALYTICS.writeDataPoint({
      blobs: [
        "newsletter_click",
        campaign,
        destinationUrl.hostname,
        destinationUrl.href,
        request.headers.get("Referer") || "",
      ],

      doubles: [1],

      indexes: [campaign],
    });
  }

  return Response.redirect(destinationUrl.href, 302);
}


// ======================================================================
// HTML LINK REWRITING
// ======================================================================

async function rewriteLinks(html, workerOrigin, campaignId) {
  const htmlResponse = new Response(html, {
    headers: {
      "Content-Type": "text/html",
    },
  });

  const rewriter = new HTMLRewriter().on(
    "a[href]",
    new LinkRewriter(workerOrigin, campaignId)
  );

  const rewrittenResponse = rewriter.transform(htmlResponse);

  return await rewrittenResponse.text();
}


class LinkRewriter {
  constructor(workerOrigin, campaignId) {
    this.workerOrigin = workerOrigin;
    this.campaignId = campaignId;
  }

  element(element) {
    const href = element.getAttribute("href");

    if (!href) {
      return;
    }

    const trimmed = href.trim();

    // Leave these alone.
    if (
      trimmed.startsWith("#") ||
      trimmed.startsWith("mailto:") ||
      trimmed.startsWith("tel:") ||
      trimmed.startsWith("sms:") ||
      trimmed.startsWith("javascript:")
    ) {
      return;
    }

    let destination;

    try {
      destination = new URL(trimmed);
    } catch {
      // Relative or malformed URL — leave unchanged.
      return;
    }

    if (
      destination.protocol !== "https:" &&
      destination.protocol !== "http:"
    ) {
      return;
    }

    // Don't accidentally wrap links that already point
    // to our click endpoint.
    if (
      destination.origin === this.workerOrigin &&
      destination.pathname === "/click"
    ) {
      return;
    }

    const trackingUrl = new URL(
      "/click",
      this.workerOrigin
    );

    trackingUrl.searchParams.set(
      "campaign",
      this.campaignId
    );

    trackingUrl.searchParams.set(
      "url",
      destination.href
    );

    element.setAttribute(
      "href",
      trackingUrl.toString()
    );
  }
}


// ======================================================================
// CORS
// ======================================================================

function corsHeaders(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
