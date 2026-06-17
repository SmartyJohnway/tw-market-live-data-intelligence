// Netlify Edge Function Proxy to bypass CORS if needed for browser direct fetch
exports.handler = async function(event, context) {
    const targetUrl = event.queryStringParameters.url;

    if (!targetUrl) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: "Missing 'url' query parameter" })
        };
    }

    // ALLOWLIST for security
    const allowedHosts = [
        "openapi.twse.com.tw",
        "www.tpex.org.tw",
        "query1.finance.yahoo.com",
        "query2.finance.yahoo.com",
        "mis.twse.com.tw"
    ];

    try {
        const urlObj = new URL(targetUrl);
        if (!allowedHosts.includes(urlObj.hostname)) {
            return {
                statusCode: 403,
                body: JSON.stringify({ error: "Host not allowed by proxy." })
            };
        }
    } catch (e) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: "Invalid URL format." })
        };
    }

    // Only allow GET requests
    if (event.httpMethod !== "GET") {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: "Method not allowed. Only GET is supported." })
        };
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => {
        controller.abort();
    }, 10000); // 10 seconds timeout

    try {
        const response = await fetch(targetUrl, {
            method: "GET",
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetlifyProxy/1.0"
            },
            signal: controller.signal
        });

        clearTimeout(timeout);

        // Simple size cap (e.g. 5MB). In a real Edge Function you might stream it, but for a basic check:
        const data = await response.text();
        if (data.length > 5 * 1024 * 1024) {
            return {
                statusCode: 413,
                body: JSON.stringify({ error: "Response too large." })
            };
        }

        return {
            statusCode: response.status,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": response.headers.get("Content-Type") || "application/json"
            },
            body: data
        };
    } catch (error) {
        clearTimeout(timeout);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.name === 'AbortError' ? "Request timed out" : error.message })
        };
    }
};
