/**
 * 백엔드 API를 프록시하여 오늘 메뉴를 반환
 */
exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Content-Type': 'application/json'
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    try {
        const apiBaseUrl = process.env.BACKEND_API_URL || process.env.VITE_API_URL;

        if (!apiBaseUrl) {
            throw new Error('BACKEND_API_URL 또는 VITE_API_URL 환경 변수가 설정되지 않았습니다.');
        }

        const normalizedBaseUrl = apiBaseUrl.replace(/\/$/, '');
        const upstreamUrl = `${normalizedBaseUrl}/api/menus/today`;

        const response = await fetch(upstreamUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`백엔드 응답 오류: ${response.status} ${response.statusText}`);
        }

        const payload = await response.json();

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify(payload)
        };
    } catch (error) {
        console.error('Error in getTodayMenus:', error);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: false,
                date: new Date().toISOString().split('T')[0],
                menus: [],
                error: error.message
            })
        };
    }
};
