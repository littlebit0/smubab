import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { useEffect, useState } from 'react'
import { Menu, menuAPI, pushAPI } from './api'
import './App.css'
import { isPushSupported, isStandaloneMode, urlBase64ToUint8Array } from './push'

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
  const [error, setError] = useState<string | null>(null)
  const [pushStatusText, setPushStatusText] = useState<string>('')
  const [showPushPrompt, setShowPushPrompt] = useState(false)
  const [isSubscribingPush, setIsSubscribingPush] = useState(false)
  const [isSendingTestPush, setIsSendingTestPush] = useState(false)

  const standalone = isStandaloneMode()
  const pushSupported = isPushSupported()

  useEffect(() => {
    loadMenus()
  }, [view])

  useEffect(() => {
    if (!pushSupported) {
      setPushStatusText('이 브라우저는 웹 푸시를 지원하지 않습니다.')
      return
    }

    if (!standalone) {
      setPushStatusText('브라우저에서도 알림을 켤 수 있습니다.')
    }

    if (!pushAPI.isConfigured()) {
      setPushStatusText('서버 푸시 설정이 아직 준비되지 않았습니다.')
      return
    }

    if (Notification.permission === 'granted') {
      setPushStatusText('메뉴 업데이트 알림이 활성화되어 있습니다.')
      setShowPushPrompt(false)
      return
    }

    if (Notification.permission === 'denied') {
      setPushStatusText('알림이 차단되어 있습니다. Safari 설정에서 허용해 주세요.')
      setShowPushPrompt(false)
      return
    }

    setPushStatusText('학식 메뉴 업데이트 알림을 켜주세요.')
    setShowPushPrompt(true)
  }, [pushSupported, standalone])

  const enablePushNotifications = async () => {
    if (!pushSupported) {
      setPushStatusText('이 브라우저는 웹 푸시를 지원하지 않습니다.')
      return
    }

    if (!standalone) {
      setPushStatusText('브라우저에서 알림 설정을 진행합니다.')
    }

    try {
      setIsSubscribingPush(true)

      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        setPushStatusText('알림 권한이 허용되지 않았습니다.')
        return
      }

      const publicKey = await pushAPI.getPublicKey()
      if (!publicKey) {
        setPushStatusText('서버 푸시 공개키가 설정되지 않았습니다.')
        return
      }

      const registration = await navigator.serviceWorker.ready
      let subscription = await registration.pushManager.getSubscription()

      if (!subscription) {
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        })
      }

      await pushAPI.subscribe(subscription.toJSON() as any)
      setPushStatusText('메뉴 업데이트 알림이 활성화되었습니다.')
      setShowPushPrompt(false)
    } catch (error) {
      console.error('Failed to enable push notifications:', error)
      setPushStatusText('알림 설정에 실패했습니다. 잠시 후 다시 시도해 주세요.')
    } finally {
      setIsSubscribingPush(false)
    }
  }

  const sendTestPushNotification = async () => {
    if (!pushSupported || Notification.permission !== 'granted') {
      setPushStatusText('테스트 알림은 알림 허용 상태에서만 가능합니다.')
      return
    }

    try {
      setIsSendingTestPush(true)
      const result = await pushAPI.sendTestPush()
      setPushStatusText(result.message)
    } catch (error: any) {
      console.error('Failed to send test push:', error)
      const message = error?.response?.data?.detail || '테스트 알림 요청에 실패했습니다.'
      setPushStatusText(message)
    } finally {
      setIsSendingTestPush(false)
    }
  }

  const loadMenus = async () => {
    try {
      setLoading(true)
      setError(null)
      if (view === 'today') {
        console.log('Fetching today menus...')
        const response = await menuAPI.getTodayMenus()
        console.log('Response received:', response)
        
        // 응답에 에러가 포함되어 있는 경우
        if (!response.success && response.error) {
          setError(response.error)
        }
        
        setMenus(response.menus || [])
      } else if (view === 'week') {
        console.log('Fetching weekly menus...')
        const response = await menuAPI.getWeeklyMenus()
        console.log('Response received:', response)
        
        // 응답에 에러가 포함되어 있는 경우
        if (!response.success && response.error) {
          setError(response.error)
        }
        
        setMenus(response.data || [])
      }
    } catch (error: any) {
      console.error('Failed to load menus:', error)
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url
      })
      
      const errorMsg = error.response?.data?.error || error.message || '알 수 없는 오류가 발생했습니다'
      setError(errorMsg)
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
              {error && (
                <p style={{fontSize: '0.85rem', color: '#e74c3c', marginTop: '0.5rem', wordBreak: 'break-word'}}>
                  오류: {error}
                </p>
              )}
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
        {pushSupported && showPushPrompt && (
          <button
            className="push-btn"
            onClick={enablePushNotifications}
            disabled={isSubscribingPush}
          >
            {isSubscribingPush ? '🔔 설정 중...' : '🔔 메뉴 업데이트 알림 켜기'}
          </button>
        )}
        {pushSupported && Notification.permission === 'granted' && (
          <button
            className="test-push-btn"
            onClick={sendTestPushNotification}
            disabled={isSendingTestPush}
          >
            {isSendingTestPush ? '⏳ 테스트 예약 중...' : '🧪 테스트 알림 (10초 후)'}
          </button>
        )}
        {pushStatusText && <p className="push-status">{pushStatusText}</p>}
        <button className="refresh-btn" onClick={loadMenus}>
          🔄 새로고침
        </button>
        <p>© 2026 SMU-Bab</p>
      </footer>
    </div>
  )
}

export default App
