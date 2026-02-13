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
        const apiBaseUrl = process.env.BACKEND_API_URL || process.env.NETLIFY_BACKEND_API_URL || process.env.VITE_API_URL || 'https://smubab-api.onrender.com';

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

        const dateStr = new Date().toISOString().split('T')[0];
        const fallbackMenus = [
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
        ];

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                date: dateStr,
                menus: fallbackMenus,
                message: '백엔드 연결 실패로 기본 메뉴를 표시합니다.'
            })
        };
    }
};
