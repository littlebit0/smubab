/**
 * 간단한 샘플 데이터로 주간 메뉴 반환
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
        console.log('getWeeklyMenus function called');

        // 이번 주 월요일부터 금요일까지 날짜 생성
        const today = new Date();
        const dayOfWeek = today.getDay();
        const monday = new Date(today);
        monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));

        const menus = [];
        const restaurants = ['서울_학생식당', '천안_교직원식당', '천안_학생식당'];
        const mealTypes = ['lunch', 'dinner'];
        
        // 월요일부터 금요일까지 (5일)
        for (let i = 0; i < 5; i++) {
            const date = new Date(monday);
            date.setDate(monday.getDate() + i);
            const dateStr = date.toISOString().split('T')[0];

            restaurants.forEach(restaurant => {
                mealTypes.forEach(mealType => {
                    menus.push({
                        date: dateStr,
                        restaurant: restaurant,
                        meal_type: mealType,
                        items: [
                            { name: '잡곡밥', price: null },
                            { name: '국/찌개', price: null },
                            { name: '메인반찬', price: null },
                            { name: '부반찬', price: null },
                            { name: '김치', price: null }
                        ]
                    });
                });
            });
        }

        console.log(`Returning ${menus.length} sample weekly menus`);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                data: menus
            })
        };

    } catch (error) {
        console.error('Error in getWeeklyMenus:', error);
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: false,
                data: [],
                error: error.message
            })
        };
    }
};
