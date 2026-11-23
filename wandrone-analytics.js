/* WanDrone Web Analytics — Lightweight, Privacy-Safe Event & Pageview Tracker */
(function () {
    'use strict';

    if (window.location.protocol === 'file:') return;

    // Minimal fetchLater() polyfill (Baseline fallback using fetch keepalive / sendBeacon + visibilitychange)
    globalThis.fetchLater ??= function fetchLater(url, init = {}) {
        let timeoutHandle;
        let activated = false;

        function sendNow() {
            if (!(init.signal && init.signal.aborted)) {
                if (
                    'keepalive' in Request.prototype ||
                    init.method !== 'POST' ||
                    init.headers
                ) {
                    fetch(url, Object.assign({}, init, { keepalive: true })).catch(function () {});
                    activated = true;
                } else if (typeof navigator.sendBeacon === 'function') {
                    activated = navigator.sendBeacon(url, init.body);
                }
            }
            destroy();
        }

        function destroy() {
            document.removeEventListener('visibilitychange', sendNow);
            clearTimeout(timeoutHandle);
        }

        if (document.visibilityState === 'hidden') {
            queueMicrotask(sendNow);
        } else {
            document.addEventListener('visibilitychange', sendNow);
            if (typeof init.activateAfter === 'number' && init.activateAfter >= 0) {
                timeoutHandle = setTimeout(sendNow, init.activateAfter);
            }
        }

        if (init.signal) {
            init.signal.addEventListener('abort', destroy);
        }

        return {
            get activated() {
                return activated;
            }
        };
    };

    const SUPABASE_URL = window.WAN_SUPABASE_URL || 'https://vzrlpyzbqiunkmpmjmqn.supabase.co';
    const SUPABASE_KEY = window.WAN_SUPABASE_ANON_KEY || 'sb_publishable_AxPOTAiZZYuMyiq3_8vieA_FgKUcH1P';
    const TRACK_ENDPOINT = SUPABASE_URL + '/rest/v1/rpc/track_web_event';

    const BOT_RE = /bot|crawler|spider|headless|lighthouse|pingdom|slurp|facebookexternalhit|whatsapp|preview|curl|wget|python-requests/i;
    const RECENT_EVENTS = Object.create(null);

    function isBotVisitor() {
        try {
            if (navigator.webdriver) return true;
            if (BOT_RE.test(navigator.userAgent || '')) return true;
        } catch (_) {}
        return false;
    }

    function isStaffSession() {
        try {
            if (localStorage.getItem('wan_analytics_include_admin') === '1') return false;
            const raw = localStorage.getItem('wan_pilot_user_session');
            if (raw) {
                const u = JSON.parse(raw);
                if (u && (u.role === 'superadmin' || u.role === 'admin' || String(u.username || '').toLowerCase() === 'rwandaz')) {
                    return true;
                }
            }
            const adm = sessionStorage.getItem('wandrone_admin_user');
            if (adm) return true;
        } catch (_) {}
        return false;
    }

    function getVisitorId() {
        const KEY = 'wan_vid_v1';
        try {
            let vid = localStorage.getItem(KEY);
            if (vid && vid.length >= 8 && vid.length <= 64) return vid;
            if (window.crypto && typeof window.crypto.randomUUID === 'function') {
                vid = 'v_' + window.crypto.randomUUID().replace(/-/g, '').slice(0, 20);
            } else {
                vid = 'v_' + Math.random().toString(36).slice(2, 12) + Date.now().toString(36);
            }
            localStorage.setItem(KEY, vid);
            return vid;
        } catch (_) {
            return 'v_anon_' + Math.random().toString(36).slice(2, 10);
        }
    }

    function getPageKey() {
        const path = (window.location.pathname || '/').toLowerCase();
        if (path.indexOf('lisensi') !== -1) return 'page_lisensi';
        if (path.indexOf('tanya-jawab') !== -1) return 'page_forum';
        return 'page_home';
    }

    function getDeviceType() {
        try {
            const ua = navigator.userAgent || '';
            if (/Android|iPhone|iPad|iPod|Mobile|Opera Mini|IEMobile/i.test(ua) || window.innerWidth <= 768) {
                return 'mobile';
            }
        } catch (_) {}
        return 'desktop';
    }

    function getReferrerSource() {
        try {
            const params = new URLSearchParams(window.location.search || '');
            const utm = (params.get('utm_source') || '').trim().toLowerCase();
            if (utm) return utm.slice(0, 40);

            const ref = document.referrer || '';
            if (!ref) return 'direct';
            const u = new URL(ref);
            const host = u.hostname.toLowerCase().replace(/^www\./, '');
            const curHost = window.location.hostname.toLowerCase().replace(/^www\./, '');
            if (!host || host === curHost) return 'internal';
            if (host.indexOf('instagram.com') !== -1) return 'instagram';
            if (host.indexOf('tiktok.com') !== -1) return 'tiktok';
            if (host.indexOf('youtube.com') !== -1 || host === 'youtu.be') return 'youtube';
            if (host.indexOf('google.') !== -1) return 'google';
            if (host.indexOf('facebook.com') !== -1 || host === 'fb.com') return 'facebook';
            if (host.indexOf('whatsapp.com') !== -1 || host === 'wa.me') return 'whatsapp';
            if (host.indexOf('github.io') !== -1 || host.indexOf('github.com') !== -1) return 'github';
            return host.slice(0, 60);
        } catch (_) {
            return 'direct';
        }
    }

    function sendEvent(eventKey, meta) {
        if (!eventKey || isBotVisitor() || isStaffSession()) return;

        // 3-second debounce per event_key to avoid accidental double-clicks
        const now = Date.now();
        if (RECENT_EVENTS[eventKey] && (now - RECENT_EVENTS[eventKey]) < 3000) return;
        RECENT_EVENTS[eventKey] = now;

        const payload = {
            p_event_key: String(eventKey).slice(0, 64),
            p_page_key: getPageKey(),
            p_visitor_id: getVisitorId(),
            p_device_type: getDeviceType(),
            p_referrer: getReferrerSource(),
            p_meta: meta && typeof meta === 'object' ? meta : {}
        };

        try {
            globalThis.fetchLater(TRACK_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_KEY
                },
                body: JSON.stringify(payload),
                activateAfter: 0
            });
        } catch (_) {
            // Silently ignore quota or network errors so UX is never disrupted
        }
    }

    function resolveEventKeyFromAnchor(anchor) {
        if (!anchor) return null;
        const explicit = anchor.getAttribute('data-track');
        if (explicit) return explicit.trim();

        const href = (anchor.getAttribute('href') || '').trim();
        if (!href || href.charAt(0) === '#' || /^javascript:/i.test(href)) return null;

        const lower = href.toLowerCase();
        if (lower.indexOf('1irzfsgsevmgjv2_kuakfnvauf3xrmxwj') !== -1) return 'dl_tw_mapper';
        if (lower.indexOf('e2kpi9sfvju') !== -1) return 'watch_tutorial';
        if (lower.indexOf('12jglpbkpekanbh6q_wqsy15msnk-xupf') !== -1) return 'dl_tw_tweaks';
        if (lower.indexOf('117qs-gaumpoid0ijyeh1vbmefwa1k83q') !== -1) return 'dl_wandrone_tweaks';
        if (lower.indexOf('tw-enterprise.github.io/tw-mapper-mobile-docs') !== -1) return 'open_docs';
        if (lower.indexOf('fly.arkana.co.id/tweaker') !== -1) return 'click_license_portal';
        if (lower.indexOf('lisensi.html') !== -1) return 'click_nav_lisensi';

        if (lower.indexOf('wa.me/') !== -1) {
            if (lower.indexOf('paket%20hobby') !== -1 || lower.indexOf('paket+hobby') !== -1) return 'wa_paket_hobby';
            if (lower.indexOf('paket%20pro') !== -1 || lower.indexOf('paket+pro') !== -1) return 'wa_paket_pro';
            if (lower.indexOf('jejen') !== -1) return 'wa_jejen_lisensi';
            if (lower.indexOf('628111969111') !== -1 || lower.indexOf('upay') !== -1) return 'wa_upay_teknis';
            if (lower.indexOf('6285175009498') !== -1 || lower.indexOf('halo%20wan') !== -1) return 'wa_wan_teknis';
            if (lower.indexOf('6285199391551') !== -1 || lower.indexOf('ian') !== -1) return 'wa_ian_teknis';
            return 'wa_wan_teknis';
        }

        if (lower.indexOf('instagram.com') !== -1) return 'social_instagram';
        if (lower.indexOf('tiktok.com') !== -1) return 'social_tiktok';
        if (lower.indexOf('youtube.com/@wandroneapp') !== -1) return 'social_youtube';

        return null;
    }

    function handleInteraction(e) {
        if (e.type === 'auxclick' && e.button !== 1) return;
        const target = e.target;
        const anchor = target && target.closest ? target.closest('a[href], [data-track]') : null;
        if (!anchor) return;
        const eventKey = resolveEventKeyFromAnchor(anchor);
        if (!eventKey) return;
        const label = (anchor.getAttribute('data-track-label') || anchor.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80);
        sendEvent(eventKey, { label: label });
    }

    // Track page view once per page load (skip rapid refresh spam within 10s per page)
    function trackPageView() {
        const pageKey = getPageKey();
        const sessionKey = 'wan_pv_ts_' + pageKey;
        try {
            const last = Number(sessionStorage.getItem(sessionKey) || '0');
            if (Date.now() - last < 10000) return;
            sessionStorage.setItem(sessionKey, String(Date.now()));
        } catch (_) {}
        sendEvent(pageKey, { path: (window.location.pathname || '/').slice(0, 80) });
    }

    // Capture phase ensures tracking fires before any anti-cache navigation handler
    document.addEventListener('click', handleInteraction, true);
    document.addEventListener('auxclick', handleInteraction, true);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', trackPageView, { once: true });
    } else {
        trackPageView();
    }

    window.wanTrackEvent = sendEvent;
})();
