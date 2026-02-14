/**
 * 백엔드 API를 프록시하여 웹 푸시 공개키를 반환
 */
exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Content-Type': 'application/json',
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    if (event.httpMethod !== 'GET') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ success: false, message: 'Method Not Allowed' }),
        };
    }

    try {
        const apiBaseUrl =
            process.env.BACKEND_API_URL ||
            process.env.NETLIFY_BACKEND_API_URL ||
            process.env.VITE_PUSH_API_URL ||
            process.env.VITE_API_URL ||
            'https://smubab-api.onrender.com';

        const normalizedBaseUrl = apiBaseUrl.replace(/\/$/, '');
        const upstreamUrl = `${normalizedBaseUrl}/api/push/public-key`;

        const response = await fetch(upstreamUrl, {
            method: 'GET',
            headers: { Accept: 'application/json' },
        });

        const payload = await response.json();

        return {
            statusCode: response.status,
            headers,
            body: JSON.stringify(payload),
        };
    } catch (error) {
        console.error('Error in getPushPublicKey:', error);
        return {
            statusCode: 502,
            headers,
            body: JSON.stringify({ success: false, message: 'Push key proxy failed' }),
        };
    }
};
