/**
 * 백엔드 API를 프록시하여 주간 메뉴를 반환
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
        const apiBaseUrl = process.env.BACKEND_API_URL || process.env.NETLIFY_BACKEND_API_URL || process.env.VITE_API_URL || 'https://smubab-api.onrender.com';

        const normalizedBaseUrl = apiBaseUrl.replace(/\/$/, '');
        const params = new URLSearchParams(event.queryStringParameters || {});
        const query = params.toString();
        const upstreamUrl = `${normalizedBaseUrl}/api/menus/week${query ? `?${query}` : ''}`;

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
        console.error('Error in getWeeklyMenus:', error);

        const today = new Date();
        const day = today.getDay();
        const monday = new Date(today);
        monday.setDate(today.getDate() - (day === 0 ? 6 : day - 1));

        const fallbackData = [];
        for (let i = 0; i < 5; i += 1) {
            const d = new Date(monday);
            d.setDate(monday.getDate() + i);
            const dateStr = d.toISOString().split('T')[0];

            fallbackData.push(
                {
                    date: dateStr,
                    restaurant: '서울_학생식당',
                    meal_type: 'breakfast',
                    items: [{ name: '조식제공X', price: null }]
                },
                {
                    date: dateStr,
                    restaurant: '서울_학생식당',
                    meal_type: 'lunch',
                    items: [{ name: '중식정보없음', price: null }]
                },
                {
                    date: dateStr,
                    restaurant: '천안_학생식당',
                    meal_type: 'breakfast',
                    items: [{ name: '조식정보없음', price: null }]
                },
                {
                    date: dateStr,
                    restaurant: '천안_학생식당',
                    meal_type: 'lunch',
                    items: [{ name: '중식정보없음', price: null }]
                },
                {
                    date: dateStr,
                    restaurant: '천안_교직원식당',
                    meal_type: 'lunch',
                    items: [{ name: '중식정보없음', price: null }]
                }
            );
        }

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                data: fallbackData,
                message: '백엔드 연결 실패로 기본 주간 메뉴를 표시합니다.'
            })
        };
    }
};
