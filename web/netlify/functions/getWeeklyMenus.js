const axios = require('axios');
const cheerio = require('cheerio');

/**
 * 서울캠퍼스 메뉴 크롤링
 */
async function crawlSeoulCampus(targetDate) {
    const menus = [];
    const url = 'https://www.smu.ac.kr/kor/life/restaurantView.do';

    try {
        const response = await axios.get(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout: 20000
        });

        const $ = cheerio.load(response.data);
        const tables = $('table');

        if (tables.length < 2) {
            console.log('Seoul: 식단표 테이블을 찾을 수 없습니다');
            return menus;
        }

        // 두 번째 테이블이 실제 식단표
        const menuTable = tables.eq(1);
        const rows = menuTable.find('tr');

        if (rows.length < 2) {
            console.log('Seoul: 테이블 행이 부족합니다');
            return menus;
        }

        // 첫 번째 행: 날짜 헤더
        const headerRow = rows.eq(0);
        const headerCells = headerRow.find('th, td');

        // 두 번째 행: 메뉴 내용
        const menuRow = rows.eq(1);
        const menuCells = menuRow.find('th, td');

        // 식당 종류 확인
        let restaurant = '서울_학생식당';
        const restaurantLabel = menuCells.eq(0).text().trim();
        if (restaurantLabel.includes('교직원') || restaurantLabel.includes('교수')) {
            restaurant = '서울_교직원식당';
        }

        // 날짜와 메뉴 매칭
        const minLength = Math.min(headerCells.length, menuCells.length);
        for (let i = 1; i < minLength; i++) {
            const dateText = headerCells.eq(i).text().trim();
            const menuText = menuCells.eq(i).text().trim();

            if (!menuText) continue;

            // 날짜 파싱 (예: "월(02.09)")
            const dateMatch = dateText.match(/\((\d{2})\.(\d{2})\)/);
            if (dateMatch) {
                const month = parseInt(dateMatch[1]);
                const day = parseInt(dateMatch[2]);

                // 연도 추론
                let year = targetDate.getFullYear();
                if (month === 12 && targetDate.getMonth() === 0) {
                    year = targetDate.getFullYear() - 1;
                } else if (month === 1 && targetDate.getMonth() === 11) {
                    year = targetDate.getFullYear() + 1;
                }

                const menuDate = new Date(year, month - 1, day);
                const dateStr = formatDate(menuDate);

                // 메뉴 아이템 파싱
                const items = parseMenuText(menuText);

                if (items.length > 0) {
                    menus.push({
                        date: dateStr,
                        restaurant: restaurant,
                        meal_type: 'lunch',
                        items: items
                    });
                }
            }
        }

        // 조식 샘플 추가 (월~금)
        const monday = getMonday(targetDate);
        for (let i = 0; i < 5; i++) {
            const breakfastDate = new Date(monday);
            breakfastDate.setDate(monday.getDate() + i);

            menus.push({
                date: formatDate(breakfastDate),
                restaurant: '서울_학생식당',
                meal_type: 'breakfast',
                items: [
                    { name: '토스트', price: null },
                    { name: '시리얼', price: null },
                    { name: '우유', price: null },
                    { name: '과일', price: null }
                ]
            });
        }

        console.log(`Seoul: ${menus.length} menus crawled`);

    } catch (error) {
        console.error('Error crawling Seoul campus:', error.message);
    }

    return menus;
}

/**
 * 천안캠퍼스 샘플 메뉴 생성
 */
function getCheonanSampleMenus(targetDate) {
    const menus = [];
    const monday = getMonday(targetDate);

    // 월~금 5일간 메뉴 생성
    for (let i = 0; i < 5; i++) {
        const menuDate = new Date(monday);
        menuDate.setDate(monday.getDate() + i);
        const dateStr = formatDate(menuDate);

        // 교직원 식당 - 조식
        menus.push({
            date: dateStr,
            restaurant: '천안_교직원식당',
            meal_type: 'breakfast',
            items: [
                { name: '토스트', price: null },
                { name: '계란후라이', price: null },
                { name: '우유', price: null },
                { name: '과일', price: null }
            ]
        });

        // 교직원 식당 - 중식
        menus.push({
            date: dateStr,
            restaurant: '천안_교직원식당',
            meal_type: 'lunch',
            items: [
                { name: '쌀밥', price: null },
                { name: '된장찌개', price: null },
                { name: '불고기', price: null },
                { name: '나물무침', price: null },
                { name: '김치', price: null }
            ]
        });

        // 학생 식당 - 조식
        menus.push({
            date: dateStr,
            restaurant: '천안_학생식당',
            meal_type: 'breakfast',
            items: [
                { name: '토스트', price: null },
                { name: '시리얼', price: null },
                { name: '우유', price: null },
                { name: '요거트', price: null }
            ]
        });

        // 학생 식당 - 중식
        menus.push({
            date: dateStr,
            restaurant: '천안_학생식당',
            meal_type: 'lunch',
            items: [
                { name: '잡곡밥', price: null },
                { name: '김치찌개', price: null },
                { name: '돈까스', price: null },
                { name: '샐러드', price: null },
                { name: '배추김치', price: null }
            ]
        });
    }

    console.log(`Cheonan: ${menus.length} sample menus generated`);
    return menus;
}

/**
 * 메뉴 텍스트 파싱 (서울캠 형식: "잡곡밥경상도식소고기무국돈육메추리알장조림")
 */
function parseMenuText(text) {
    const items = [];

    if (!text || text.trim() === '') {
        return items;
    }

    // 줄바꿈이 있으면 라인별로 처리
    if (text.includes('\n')) {
        const lines = text.trim().split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed && trimmed.length > 1) {
                items.push({ name: trimmed, price: null });
            }
        }
    } else {
        // 키워드로 분리
        const keywords = ['밥', '국', '찌개', '탕', '찜', '조림', '볶음', '무침', '구이', '전',
            '튀김', '회', '샐러드', '스프', '파스타', '스테이크', '덮밥', '면'];

        let tempText = text;
        for (const keyword of keywords) {
            tempText = tempText.split(keyword).join(`${keyword}|`);
        }

        const parts = tempText.split('|').filter(p => p.trim());

        for (const part of parts) {
            const trimmed = part.trim();
            if (trimmed.length > 1) {
                items.push({ name: trimmed, price: null });
            }
        }
    }

    // 최소 1개 아이템 보장
    if (items.length === 0 && text.length > 0) {
        items.push({ name: text.substring(0, 50), price: null });
    }

    return items;
}

/**
 * 해당 주의 월요일 구하기
 */
function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
}

/**
 * 날짜 포맷팅 (yyyy-MM-dd)
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Netlify Function Handler
 */
exports.handler = async (event, context) => {
    // CORS 헤더
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Content-Type': 'application/json'
    };

    // OPTIONS preflight 요청 처리
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    try {
        const targetDate = new Date();

        console.log(`Crawling weekly menus for ${formatDate(targetDate)}`);

        // 서울캠퍼스 크롤링
        const seoulMenus = await crawlSeoulCampus(targetDate);

        // 천안캠퍼스 샘플 데이터
        const cheonanMenus = getCheonanSampleMenus(targetDate);

        // 합치기
        const allMenus = [...seoulMenus, ...cheonanMenus];

        // 월~금만 필터링
        const monday = getMonday(targetDate);
        const friday = new Date(monday);
        friday.setDate(monday.getDate() + 4);

        const mondayStr = formatDate(monday);
        const fridayStr = formatDate(friday);

        const filteredMenus = allMenus.filter(menu =>
            menu.date >= mondayStr && menu.date <= fridayStr
        );

        console.log(`Total ${filteredMenus.length} menus for the week`);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                data: filteredMenus
            })
        };

    } catch (error) {
        console.error('Error in getWeeklyMenus:', error);

        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({
                success: false,
                error: error.message
            })
        };
    }
};
