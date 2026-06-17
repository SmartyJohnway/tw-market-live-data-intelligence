// Netlify Edge Function Proxy to bypass CORS if needed for browser direct fetch
exports.handler = async function(event, context) {
    const targetUrl = event.queryStringParameters.url;

    if (!targetUrl) {
        return {
            statusCode: 400,
            body: JSON.stringify({ error: "Missing 'url' query parameter" })
        };
    }

    try {
        const response = await fetch(targetUrl, {
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetlifyProxy/1.0"
            }
        });

        const data = await response.text();

        return {
            statusCode: response.status,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": response.headers.get("Content-Type") || "application/json"
            },
            body: data
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};
