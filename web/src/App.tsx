import { format, parseISO } from 'date-fns'
import { ko } from 'date-fns/locale'
import { useEffect, useMemo, useState } from 'react'
import { Menu, menuAPI, pushAPI } from './api'
import './App.css'
import { isPushSupported, isStandaloneMode, urlBase64ToUint8Array } from './push'

const MEAL_TYPE_NAMES: Record<string, string> = {
  breakfast: '아침',
  lunch: '점심',
  dinner: '저녁',
}

const RESTAURANT_NAMES: Record<string, string> = {
  서울_학생식당: '서울 학생식당',
  서울_교직원식당: '서울 교직원식당',
  서울_푸드코트: '서울 푸드코트',
  천안_학생식당: '천안 학생회관',
  천안_교직원식당: '천안 교직원식당',
}

const MEAL_ORDER: Record<string, number> = {
  breakfast: 0,
  lunch: 1,
  dinner: 2,
}

const formatRestaurantName = (restaurant: string) =>
  RESTAURANT_NAMES[restaurant] || restaurant.replace(/_/g, ' ')

const campusName = (restaurant: string) =>
  restaurant.startsWith('천안') ? '천안캠퍼스' : '서울캠퍼스'

const isWeekend = () => {
  const day = new Date().getDay()
  return day === 0 || day === 6
}

const sortMenus = (menus: Menu[]) =>
  [...menus].sort((a, b) => {
    const campusCompare = campusName(a.restaurant).localeCompare(campusName(b.restaurant), 'ko')
    if (campusCompare !== 0) return campusCompare
    const restaurantCompare = formatRestaurantName(a.restaurant).localeCompare(formatRestaurantName(b.restaurant), 'ko')
    if (restaurantCompare !== 0) return restaurantCompare
    return (MEAL_ORDER[a.meal_type] ?? 9) - (MEAL_ORDER[b.meal_type] ?? 9)
  })

const groupBy = <T,>(items: T[], getKey: (item: T) => string) =>
  items.reduce<Record<string, T[]>>((groups, item) => {
    const key = getKey(item)
    groups[key] ||= []
    groups[key].push(item)
    return groups
  }, {})

function App() {
  const [view, setView] = useState<'today' | 'week'>(() => isWeekend() ? 'week' : 'today')
  const [loading, setLoading] = useState(true)
  const [menus, setMenus] = useState<Menu[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pushStatusText, setPushStatusText] = useState<string>('')
  const [showPushPrompt, setShowPushPrompt] = useState(false)
  const [isSubscribingPush, setIsSubscribingPush] = useState(false)
  const [isSendingTestPush, setIsSendingTestPush] = useState(false)

  const standalone = isStandaloneMode()
  const pushSupported = isPushSupported()

  const sortedMenus = useMemo(() => sortMenus(menus), [menus])
  const restaurantCount = useMemo(
    () => new Set(menus.map(menu => menu.restaurant)).size,
    [menus]
  )
  const itemCount = useMemo(
    () => menus.reduce((total, menu) => total + menu.items.length, 0),
    [menus]
  )

  useEffect(() => {
    loadMenus()
  }, [view])

  useEffect(() => {
    if (!pushSupported) {
      setPushStatusText('이 브라우저는 푸시 알림을 지원하지 않습니다.')
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
      setPushStatusText('메뉴 업데이트 알림이 켜져 있습니다.')
      setShowPushPrompt(false)
      return
    }

    if (Notification.permission === 'denied') {
      setPushStatusText('알림이 차단되어 있습니다. 브라우저 설정에서 허용해 주세요.')
      setShowPushPrompt(false)
      return
    }

    setPushStatusText('학식 메뉴 업데이트 알림을 켤 수 있습니다.')
    setShowPushPrompt(true)
  }, [pushSupported, standalone])

  const enablePushNotifications = async () => {
    if (!pushSupported) {
      setPushStatusText('이 브라우저는 푸시 알림을 지원하지 않습니다.')
      return
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
      setPushStatusText('메뉴 업데이트 알림이 켜졌습니다.')
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
        const response = await menuAPI.getTodayMenus()
        setError(response.success ? null : response.error || response.message || '메뉴 정보를 확인하는 중입니다.')
        setMenus(response.menus || [])
        return
      }

      const response = await menuAPI.getWeeklyMenus()
      setError(response.success ? null : response.error || response.message || '주간 메뉴 정보를 확인하는 중입니다.')
      setMenus(response.data || [])
    } catch (error: any) {
      console.error('Failed to load menus:', error)
      const errorMsg = error.response?.data?.error || error.message || '알 수 없는 오류가 발생했습니다.'
      setError(errorMsg)
      setMenus([])
    } finally {
      setLoading(false)
    }
  }

  const renderMenuItem = (item: Menu['items'][number], index: number) => (
    <li key={`${item.name}-${index}`} className="menu-item">
      <span className="item-dot" aria-hidden="true"></span>
      <span className="item-name">{item.name}</span>
      {item.price != null && <span className="item-price">{item.price.toLocaleString()}원</span>}
    </li>
  )

  const renderMenu = (menu: Menu, compact = false) => (
    <article key={`${menu.date}-${menu.restaurant}-${menu.meal_type}`} className={`menu-card meal-${menu.meal_type} ${compact ? 'compact' : ''}`}>
      <div className="menu-header">
        <div>
          <span className="campus-label">{campusName(menu.restaurant)}</span>
          <h3 className="restaurant-name">{formatRestaurantName(menu.restaurant)}</h3>
        </div>
        <span className="meal-type">{MEAL_TYPE_NAMES[menu.meal_type] || menu.meal_type}</span>
      </div>
      <ul className="menu-items">
        {menu.items.map((item, idx) => renderMenuItem(item, idx))}
      </ul>
    </article>
  )

  const renderStatusBanner = () => (
    error ? (
      <div className="status-banner" role="status">
        <strong>연결 상태 확인 필요</strong>
        <span>{error}</span>
      </div>
    ) : null
  )

  const renderTodayView = () => {
    const campusGroups = groupBy(sortedMenus, menu => campusName(menu.restaurant))
    const campuses = ['서울캠퍼스', '천안캠퍼스'].filter(campus => campusGroups[campus]?.length)

    return (
      <section className="content" aria-labelledby="today-title">
        <div className="page-header">
          <div>
            <p className="eyebrow">오늘의 식단</p>
            <h2 id="today-title">{format(new Date(), 'yyyy년 MM월 dd일 (E)', { locale: ko })}</h2>
            <p className="page-subtitle">캠퍼스별 식당과 끼니를 한 화면에서 확인하세요.</p>
          </div>
          <div className="metric-row" aria-label="메뉴 요약">
            <div className="metric">
              <strong>{restaurantCount}</strong>
              <span>식당</span>
            </div>
            <div className="metric">
              <strong>{menus.length}</strong>
              <span>식단</span>
            </div>
          </div>
        </div>

        {renderStatusBanner()}

        {campuses.length > 0 ? (
          <div className="campus-layout">
            {campuses.map(campus => (
              <section key={campus} className="campus-section">
                <div className="section-title-row">
                  <h3>{campus}</h3>
                  <span>{campusGroups[campus].length}개 식단</span>
                </div>
                <div className="menus-container">
                  {campusGroups[campus].map(menu => renderMenu(menu))}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <strong>메뉴 정보를 불러올 수 없습니다</strong>
            <span>잠시 후 새로고침해 주세요.</span>
          </div>
        )}
      </section>
    )
  }

  const renderWeekView = () => {
    const byDate = groupBy(sortedMenus, menu => menu.date)
    const dates = Object.keys(byDate).sort()

    return (
      <section className="content wide" aria-labelledby="week-title">
        <div className="page-header">
          <div>
            <p className="eyebrow">이번 주 식단표</p>
            <h2 id="week-title">날짜별 전체 메뉴</h2>
            <p className="page-subtitle">식당을 오가지 않고 월요일부터 금요일까지 바로 비교할 수 있습니다.</p>
          </div>
          <div className="metric-row" aria-label="주간 메뉴 요약">
            <div className="metric">
              <strong>{dates.length}</strong>
              <span>일</span>
            </div>
            <div className="metric">
              <strong>{itemCount}</strong>
              <span>항목</span>
            </div>
          </div>
        </div>

        {renderStatusBanner()}

        {dates.length > 0 ? (
          <div className="week-grid">
            {dates.map(dateStr => {
              const dateObj = parseISO(dateStr)
              const isToday = format(dateObj, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')

              return (
                <section key={dateStr} className={`week-day ${isToday ? 'today' : ''}`}>
                  <div className="day-header">
                    <div>
                      <span>{format(dateObj, 'E요일', { locale: ko })}</span>
                      <h3>{format(dateObj, 'M월 d일', { locale: ko })}</h3>
                    </div>
                    {isToday && <span className="today-badge">오늘</span>}
                  </div>
                  <div className="day-menus">
                    {byDate[dateStr].map(menu => renderMenu(menu, true))}
                  </div>
                </section>
              )
            })}
          </div>
        ) : (
          <div className="empty-state">
            <strong>이번 주 메뉴를 찾지 못했습니다</strong>
            <span>백엔드 연결과 배포 환경 변수를 확인해 주세요.</span>
          </div>
        )}
      </section>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="brand-block">
            <span className="brand-mark">SMU</span>
            <h1>SMU-Bab</h1>
            <p>상명대학교 학식</p>
          </div>
          <button className="header-refresh" onClick={loadMenus} disabled={loading}>
            새로고침
          </button>
        </div>
      </header>

      <nav className="tab-nav" aria-label="메뉴 보기">
        <button
          className={`tab ${view === 'today' ? 'active' : ''}`}
          onClick={() => setView('today')}
          aria-pressed={view === 'today'}
        >
          오늘
        </button>
        <button
          className={`tab ${view === 'week' ? 'active' : ''}`}
          onClick={() => setView('week')}
          aria-pressed={view === 'week'}
        >
          이번 주
        </button>
      </nav>

      <main className="app-main">
        {loading ? (
          <div className="loading">
            <div className="spinner" aria-hidden="true"></div>
            <p>메뉴를 불러오는 중...</p>
          </div>
        ) : (
          <>
            {view === 'today' && renderTodayView()}
            {view === 'week' && renderWeekView()}
          </>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-actions">
          {pushSupported && showPushPrompt && (
            <button
              className="push-btn"
              onClick={enablePushNotifications}
              disabled={isSubscribingPush}
            >
              {isSubscribingPush ? '설정 중...' : '알림 켜기'}
            </button>
          )}
          {pushSupported && Notification.permission === 'granted' && (
            <button
              className="test-push-btn"
              onClick={sendTestPushNotification}
              disabled={isSendingTestPush}
            >
              {isSendingTestPush ? '테스트 예약 중...' : '테스트 알림'}
            </button>
          )}
          <button className="refresh-btn" onClick={loadMenus} disabled={loading}>
            새로고침
          </button>
        </div>
        {pushStatusText && <p className="push-status">{pushStatusText}</p>}
        <p className="copyright">2026 SMU-Bab</p>
      </footer>
    </div>
  )
}

export default App
