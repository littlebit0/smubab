import { format, parseISO } from 'date-fns'
import { ko } from 'date-fns/locale'
import { useEffect, useMemo, useState } from 'react'
import { Menu, menuAPI, pushAPI } from './api'
import './App.css'
import { isPushSupported, isStandaloneMode, urlBase64ToUint8Array } from './push'

type ViewMode = 'today' | 'week'
type Campus = '서울캠퍼스' | '천안캠퍼스'
type MealKey = 'breakfast' | 'lunch'

const CAMPUS_STORAGE_KEY = 'smubab:last-campus'

const CAMPUS_OPTIONS: Campus[] = ['서울캠퍼스', '천안캠퍼스']
const MEAL_OPTIONS: MealKey[] = ['breakfast', 'lunch']

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

const RESTAURANT_ORDER: Record<string, number> = {
  서울_학생식당: 0,
  서울_교직원식당: 1,
  서울_푸드코트: 2,
  천안_학생식당: 0,
  천안_교직원식당: 1,
}

const isWeekend = () => {
  const day = new Date().getDay()
  return day === 0 || day === 6
}

const getInitialMeal = (): MealKey => {
  const now = new Date()
  const minutes = now.getHours() * 60 + now.getMinutes()
  return minutes < 10 * 60 + 30 ? 'breakfast' : 'lunch'
}

const getInitialCampus = (): Campus => {
  try {
    const savedCampus = window.localStorage.getItem(CAMPUS_STORAGE_KEY)
    if (savedCampus === '서울캠퍼스' || savedCampus === '천안캠퍼스') {
      return savedCampus
    }
  } catch {
    return '서울캠퍼스'
  }

  return '서울캠퍼스'
}

const formatRestaurantName = (restaurant: string) =>
  RESTAURANT_NAMES[restaurant] || restaurant.replace(/_/g, ' ')

const campusName = (restaurant: string): Campus =>
  restaurant.startsWith('천안') ? '천안캠퍼스' : '서울캠퍼스'

const sortMenus = (menus: Menu[]) =>
  [...menus].sort((a, b) => {
    const dateCompare = a.date.localeCompare(b.date)
    if (dateCompare !== 0) return dateCompare

    const restaurantCompare =
      (RESTAURANT_ORDER[a.restaurant] ?? 9) - (RESTAURANT_ORDER[b.restaurant] ?? 9)
    if (restaurantCompare !== 0) return restaurantCompare

    return formatRestaurantName(a.restaurant).localeCompare(formatRestaurantName(b.restaurant), 'ko')
  })

const groupBy = <T,>(items: T[], getKey: (item: T) => string) =>
  items.reduce<Record<string, T[]>>((groups, item) => {
    const key = getKey(item)
    groups[key] ||= []
    groups[key].push(item)
    return groups
  }, {})

function App() {
  const [view, setView] = useState<ViewMode>(() => isWeekend() ? 'week' : 'today')
  const [selectedCampus, setSelectedCampus] = useState<Campus>(getInitialCampus)
  const [selectedMeal, setSelectedMeal] = useState<MealKey>(getInitialMeal)
  const [loading, setLoading] = useState(true)
  const [menus, setMenus] = useState<Menu[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pushStatusText, setPushStatusText] = useState<string>('')
  const [showPushPrompt, setShowPushPrompt] = useState(false)
  const [isSubscribingPush, setIsSubscribingPush] = useState(false)
  const [isSendingTestPush, setIsSendingTestPush] = useState(false)

  const standalone = isStandaloneMode()
  const pushSupported = isPushSupported()

  const visibleMenus = useMemo(() => {
    return sortMenus(
      menus.filter(menu =>
        campusName(menu.restaurant) === selectedCampus &&
        menu.meal_type === selectedMeal
      )
    )
  }, [menus, selectedCampus, selectedMeal])

  const visibleItemCount = useMemo(
    () => visibleMenus.reduce((total, menu) => total + menu.items.length, 0),
    [visibleMenus]
  )

  useEffect(() => {
    loadMenus()
  }, [view])

  useEffect(() => {
    try {
      window.localStorage.setItem(CAMPUS_STORAGE_KEY, selectedCampus)
    } catch {
      // localStorage can be unavailable in restricted browser modes.
    }
  }, [selectedCampus])

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

  const renderSelectorButton = <T extends string>(
    value: T,
    activeValue: T,
    onClick: (value: T) => void,
    label: string,
    className = 'selector-button'
  ) => (
    <button
      key={value}
      className={`${className} ${activeValue === value ? 'active' : ''}`}
      onClick={() => onClick(value)}
      aria-pressed={activeValue === value}
    >
      {label}
    </button>
  )

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
          <span className="campus-label">{selectedCampus}</span>
          <h3 className="restaurant-name">{formatRestaurantName(menu.restaurant)}</h3>
        </div>
        <span className="meal-type">{MEAL_TYPE_NAMES[menu.meal_type] || menu.meal_type}</span>
      </div>
      <ul className="menu-items">
        {menu.items.length > 0 ? (
          menu.items.map((item, idx) => renderMenuItem(item, idx))
        ) : (
          <li className="menu-item empty-menu-item">
            <span className="item-dot" aria-hidden="true"></span>
            <span className="item-name">등록된 메뉴가 없습니다.</span>
          </li>
        )}
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

  const renderControls = () => (
    <section className="selector-panel" aria-label="캠퍼스와 끼니 선택">
      <div className="selector-group campus-switch">
        {CAMPUS_OPTIONS.map(campus =>
          renderSelectorButton<Campus>(
            campus,
            selectedCampus,
            value => setSelectedCampus(value),
            campus
          )
        )}
      </div>
      <div className="selector-group meal-switch">
        {MEAL_OPTIONS.map(meal =>
          renderSelectorButton<MealKey>(
            meal,
            selectedMeal,
            value => setSelectedMeal(value),
            MEAL_TYPE_NAMES[meal],
            'meal-button'
          )
        )}
      </div>
    </section>
  )

  const renderTodayView = () => (
    <section className="content" aria-labelledby="today-title">
      <div className="page-header">
        <div>
          <p className="eyebrow">오늘의 식단</p>
          <h2 id="today-title">{selectedCampus} · {MEAL_TYPE_NAMES[selectedMeal]}</h2>
          <p className="page-subtitle">{format(new Date(), 'yyyy년 MM월 dd일 (E)', { locale: ko })}</p>
        </div>
        <div className="metric-row" aria-label="선택 메뉴 요약">
          <div className="metric">
            <strong>{visibleMenus.length}</strong>
            <span>식단</span>
          </div>
          <div className="metric">
            <strong>{visibleItemCount}</strong>
            <span>항목</span>
          </div>
        </div>
      </div>

      {renderControls()}
      {renderStatusBanner()}

      {visibleMenus.length > 0 ? (
        <div className="focused-menu-layout">
          {visibleMenus.map(menu => renderMenu(menu))}
        </div>
      ) : (
        <div className="empty-state">
          <strong>{selectedCampus} {MEAL_TYPE_NAMES[selectedMeal]} 메뉴가 없습니다</strong>
          <span>다른 끼니를 선택하거나 잠시 후 새로고침해 주세요.</span>
        </div>
      )}
    </section>
  )

  const renderWeekView = () => {
    const byDate = groupBy(visibleMenus, menu => menu.date)
    const dates = Object.keys(byDate).sort()

    return (
      <section className="content wide" aria-labelledby="week-title">
        <div className="page-header">
          <div>
            <p className="eyebrow">이번 주 식단표</p>
            <h2 id="week-title">{selectedCampus} · {MEAL_TYPE_NAMES[selectedMeal]}</h2>
            <p className="page-subtitle">선택한 캠퍼스와 끼니만 날짜별로 보여줍니다.</p>
          </div>
          <div className="metric-row" aria-label="주간 선택 메뉴 요약">
            <div className="metric">
              <strong>{dates.length}</strong>
              <span>일</span>
            </div>
            <div className="metric">
              <strong>{visibleItemCount}</strong>
              <span>항목</span>
            </div>
          </div>
        </div>

        {renderControls()}
        {renderStatusBanner()}

        {dates.length > 0 ? (
          <div className="week-grid focused-week-grid">
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
            <strong>{selectedCampus} {MEAL_TYPE_NAMES[selectedMeal]} 주간 메뉴가 없습니다</strong>
            <span>다른 끼니를 선택하거나 잠시 후 새로고침해 주세요.</span>
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
            <p>{selectedCampus} {MEAL_TYPE_NAMES[selectedMeal]}</p>
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
