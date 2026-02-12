import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { useEffect, useState } from 'react'
import { Menu, menuAPI } from './api'
import './App.css'

const MEAL_TYPE_NAMES: { [key: string]: string } = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

function App() {
  const [view, setView] = useState<'today' | 'week'>('today')
  const [loading, setLoading] = useState(true)
  const [menus, setMenus] = useState<Menu[]>([])
  const [date, setDate] = useState(new Date())
  const [selectedRestaurant, setSelectedRestaurant] = useState<string>('서울_학생식당')

  useEffect(() => {
    loadMenus()
  }, [view])

  const loadMenus = async () => {
    try {
      setLoading(true)
      if (view === 'today') {
        const response = await menuAPI.getTodayMenus()
        setMenus(response.menus || [])
      } else if (view === 'week') {
        const response = await menuAPI.getWeeklyMenus()
        setMenus(response.data || [])
      }
    } catch (error) {
      console.error('Failed to load menus:', error)
      setMenus([])
    } finally {
      setLoading(false)
    }
  }

  const groupMenusByDate = () => {
    const grouped: { [key: string]: Menu[] } = {}
    menus.forEach(menu => {
      if (!grouped[menu.date]) {
        grouped[menu.date] = []
      }
      grouped[menu.date].push(menu)
    })
    return grouped
  }

  const renderMenuItem = (item: any, index: number) => (
    <div key={index} className="menu-item">
      <span className="item-name">{item.name}</span>
      {item.price && <span className="item-price">{item.price.toLocaleString()}원</span>}
    </div>
  )

  const renderMenu = (menu: Menu, index: number) => (
    <div key={index} className="menu-card">
      <div className="menu-header">
        <span className="restaurant-name">{menu.restaurant}</span>
        <span className="meal-type">{MEAL_TYPE_NAMES[menu.meal_type] || menu.meal_type}</span>
      </div>
      <div className="menu-items">
        {menu.items.map((item, idx) => renderMenuItem(item, idx))}
      </div>
    </div>
  )

  const renderTodayView = () => {
    return (
      <div className="content">
        <div className="page-header">
          <h2>{format(date, 'yyyy년 MM월 dd일 (E)', { locale: ko })}</h2>
          <p className="subtitle">{menus.length}개의 메뉴</p>
        </div>
        <div className="menus-container">
          {menus.length > 0 ? (
            menus.map((menu, index) => renderMenu(menu, index))
          ) : (
            <div className="empty-state">
              <p>메뉴 정보를 불러올 수 없습니다</p>
              <p style={{fontSize: '0.9rem', color: '#999', marginTop: '0.5rem'}}>백엔드 API가 연결되지 않았습니다</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderWeekView = () => {
    // 선택된 식당의 메뉴만 필터링
    const filteredMenus = menus.filter(menu => menu.restaurant === selectedRestaurant)
    const grouped = groupMenusByDate()
    const dates = Object.keys(grouped).sort()
    
    // 식당별로 그룹화
    const groupedByRestaurant: { [key: string]: { [key: string]: Menu[] } } = {}
    menus.forEach(menu => {
      if (!groupedByRestaurant[menu.restaurant]) {
        groupedByRestaurant[menu.restaurant] = {}
      }
      if (!groupedByRestaurant[menu.restaurant][menu.date]) {
        groupedByRestaurant[menu.restaurant][menu.date] = []
      }
      groupedByRestaurant[menu.restaurant][menu.date].push(menu)
    })
    
    const restaurants = Object.keys(groupedByRestaurant)
    const restaurantDates = Object.keys(groupedByRestaurant[selectedRestaurant] || {}).sort()

    return (
      <div className="content">
        <div className="page-header">
          <h2>이번 주 메뉴</h2>
          <p className="subtitle">{restaurantDates.length}일 메뉴</p>
        </div>
        
        {/* 식당 선택 탭 */}
        <div className="restaurant-tabs">
          {restaurants.map(restaurant => (
            <button
              key={restaurant}
              className={`restaurant-tab ${selectedRestaurant === restaurant ? 'active' : ''}`}
              onClick={() => setSelectedRestaurant(restaurant)}
            >
              {restaurant.replace('_', ' ')}
            </button>
          ))}
        </div>
        
        <div className="week-container">
          {restaurantDates.map(dateStr => {
            const dayMenus = groupedByRestaurant[selectedRestaurant][dateStr]
            const dateObj = new Date(dateStr)
            const isToday = format(dateObj, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')

            return (
              <div key={dateStr} className={`day-card ${isToday ? 'today' : ''}`}>
                <div className="day-header">
                  <h3>{format(dateObj, 'M/d (E)', { locale: ko })}</h3>
                  {isToday && <span className="today-badge">오늘</span>}
                </div>
                <div className="day-menus">
                  {dayMenus.map((menu, index) => renderMenu(menu, index))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }



  return (
    <div className="app">
      <header className="app-header">
        <h1>🍚 SMU-Bab</h1>
        <p>상명대학교 학식</p>
      </header>

      <nav className="tab-nav">
        <button
          className={`tab ${view === 'today' ? 'active' : ''}`}
          onClick={() => setView('today')}
        >
          📅 오늘
        </button>
        <button
          className={`tab ${view === 'week' ? 'active' : ''}`}
          onClick={() => setView('week')}
        >
          📆 이번 주 (월~금)
        </button>
      </nav>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>메뉴를 불러오는 중...</p>
        </div>
      ) : (
        <>
          {view === 'today' && renderTodayView()}
          {view === 'week' && renderWeekView()}
        </>
      )}

      <footer className="app-footer">
        <button className="refresh-btn" onClick={loadMenus}>
          🔄 새로고침
        </button>
        <p>© 2026 SMU-Bab</p>
      </footer>
    </div>
  )
}

export default App
