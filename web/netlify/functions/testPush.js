/**
 * 백엔드 API를 프록시하여 테스트 푸시 발송
 */
exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json',
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    if (event.httpMethod !== 'POST') {
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
        const upstreamUrl = `${normalizedBaseUrl}/api/push/test`;

        const response = await fetch(upstreamUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: event.body || '{}',
        });

        const payload = await response.json();

        return {
            statusCode: response.status,
            headers,
            body: JSON.stringify(payload),
        };
    } catch (error) {
        console.error('Error in testPush:', error);
        return {
            statusCode: 502,
            headers,
            body: JSON.stringify({ success: false, message: 'Push test proxy failed' }),
        };
    }
};
