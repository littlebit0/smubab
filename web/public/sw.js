self.addEventListener('push', (event) => {
    if (!event.data) return;

    let payload = {};
    try {
        payload = event.data.json();
    } catch {
        payload = { title: 'SMU-Bab', body: event.data.text() };
    }

    const title = payload.title || 'SMU-Bab';
    const options = {
        body: payload.body || '메뉴 업데이트를 확인해보세요.',
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        data: {
            url: payload.url || '/',
        },
        tag: payload.tag || 'smubab-update',
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = event.notification?.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            for (const client of windowClients) {
                if ('focus' in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
            return undefined;
        })
    );
});
