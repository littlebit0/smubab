/**
 * 간단한 샘플 데이터로 오늘 메뉴 반환
 * Netlify Functions 테스트용
 */
exports.handler = async (event, context) => {
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
        console.log('getTodayMenus function called');

        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];

        // 간단한 샘플 데이터
        const menus = [
            {
                date: dateStr,
                restaurant: '서울_학생식당',
                meal_type: 'lunch',
                items: [
                    { name: '잡곡밥', price: null },
                    { name: '된장찌개', price: null },
                    { name: '제육볶음', price: null },
                    { name: '계란찜', price: null },
                    { name: '배추김치', price: null }
                ]
            },
            {
                date: dateStr,
                restaurant: '서울_학생식당',
                meal_type: 'dinner',
                items: [
                    { name: '쌀밥', price: null },
                    { name: '김치찌개', price: null },
                    { name: '닭갈비', price: null },
                    { name: '샐러드', price: null },
                    { name: '깍두기', price: null }
                ]
            },
            {
                date: dateStr,
                restaurant: '천안_학생식당',
                meal_type: 'lunch',
                items: [
                    { name: '잡곡밥', price: null },
                    { name: '순두부찌개', price: null },
                    { name: '돈까스', price: null },
                    { name: '스프', price: null },
                    { name: '배추김치', price: null }
                ]
            }
        ];

        console.log(`Returning ${menus.length} sample menus`);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                date: dateStr,
                menus: menus
            })
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
