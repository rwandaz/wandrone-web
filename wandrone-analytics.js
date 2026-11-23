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
            if (localStorage.getItem('wan_analytics_exclude_admin') !== '1') return false;
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

    const LOCAL_EVENTS_KEY = 'wan_local_analytics_events_v1';

    function saveLocalEvent(rec) {
        try {
            const raw = localStorage.getItem(LOCAL_EVENTS_KEY);
            const list = raw ? JSON.parse(raw) : [];
            const arr = Array.isArray(list) ? list : [];
            arr.push(rec);
            if (arr.length > 1500) {
                arr.splice(0, arr.length - 1500);
            }
            localStorage.setItem(LOCAL_EVENTS_KEY, JSON.stringify(arr));
        } catch (_) {}
    }

    function buildLocalAnalyticsData(days) {
        const dNum = Number.isFinite(Number(days)) ? Number(days) : 30;
        let sinceMs = 0;
        if (dNum === 1) {
            const now = new Date();
            sinceMs = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
        } else if (dNum > 1) {
            sinceMs = Date.now() - (dNum * 86400000);
        }

        let list = [];
        try {
            const raw = localStorage.getItem(LOCAL_EVENTS_KEY);
            list = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(list)) list = [];
        } catch (_) {
            list = [];
        }

        const filtered = list.filter(function (item) {
            if (!item || !item.event_key) return false;
            const ts = Date.parse(item.created_at || '') || 0;
            return ts >= sinceMs;
        });

        const PAGE_KEYS = { page_home: 1, page_lisensi: 1, page_forum: 1 };
        const TRIAL_KEYS = { dl_tw_mapper: 1, watch_tutorial: 1, dl_tw_tweaks: 1, dl_wandrone_tweaks: 1, open_docs: 1 };
        const LICENSE_KEYS = { click_nav_lisensi: 1, click_license_portal: 1, wa_paket_hobby: 1, wa_paket_pro: 1 };
        const CONTACT_KEYS = { wa_jejen_lisensi: 1, wa_ian_teknis: 1, wa_upay_teknis: 1, wa_wan_teknis: 1, wa_paket_hobby: 1, wa_paket_pro: 1 };

        const allVisitors = new Set();
        const homeVis = new Set();
        const lisVis = new Set();
        const forumVis = new Set();
        const trialVis = new Set();
        const contactVis = new Set();
        const mobileVis = new Set();
        const desktopVis = new Set();

        let totalPageViews = 0;
        let homeViews = 0;
        let lisensiViews = 0;
        let forumViews = 0;
        let totalTrialClicks = 0;
        let totalLicenseClicks = 0;
        let totalContactClicks = 0;

        const eventsAgg = Object.create(null);
        const dailyMap = Object.create(null);
        const refMap = Object.create(null);

        filtered.forEach(function (ev) {
            const k = ev.event_key;
            const vid = ev.visitor_id || 'anon';
            const dev = ev.device_type === 'mobile' ? 'mobile' : 'desktop';
            const ref = ev.referrer || 'direct';
            const day = String(ev.created_at || new Date().toISOString()).slice(0, 10);

            allVisitors.add(vid);
            if (dev === 'mobile') mobileVis.add(vid);
            else desktopVis.add(vid);

            if (!eventsAgg[k]) eventsAgg[k] = { total: 0, visitors: new Set() };
            eventsAgg[k].total += 1;
            eventsAgg[k].visitors.add(vid);

            if (!dailyMap[day]) {
                dailyMap[day] = { visitors: new Set(), page_views: 0, trial_clicks: 0, contact_clicks: 0 };
            }
            dailyMap[day].visitors.add(vid);

            if (PAGE_KEYS[k]) {
                totalPageViews += 1;
                dailyMap[day].page_views += 1;
                if (k === 'page_home') { homeViews += 1; homeVis.add(vid); }
                if (k === 'page_lisensi') { lisensiViews += 1; lisVis.add(vid); }
                if (k === 'page_forum') { forumViews += 1; forumVis.add(vid); }

                if (ref !== 'internal') {
                    if (!refMap[ref]) refMap[ref] = { visitors: new Set(), views: 0 };
                    refMap[ref].visitors.add(vid);
                    refMap[ref].views += 1;
                }
            }

            if (TRIAL_KEYS[k]) {
                totalTrialClicks += 1;
                trialVis.add(vid);
                dailyMap[day].trial_clicks += 1;
            }
            if (LICENSE_KEYS[k]) {
                totalLicenseClicks += 1;
            }
            if (CONTACT_KEYS[k]) {
                totalContactClicks += 1;
                contactVis.add(vid);
                dailyMap[day].contact_clicks += 1;
            }
        });

        const eventsOut = {};
        Object.keys(eventsAgg).forEach(function (k) {
            eventsOut[k] = {
                total: eventsAgg[k].total,
                unique: eventsAgg[k].visitors.size
            };
        });

        const dailyTrend = Object.keys(dailyMap).sort().slice(-31).map(function (day) {
            return {
                day: day,
                visitors: dailyMap[day].visitors.size,
                page_views: dailyMap[day].page_views,
                trial_clicks: dailyMap[day].trial_clicks,
                contact_clicks: dailyMap[day].contact_clicks
            };
        });

        const referrers = Object.keys(refMap).map(function (r) {
            return {
                source: r,
                visitors: refMap[r].visitors.size,
                views: refMap[r].views
            };
        }).sort(function (a, b) {
            return (b.visitors - a.visitors) || (b.views - a.views);
        }).slice(0, 10);

        const recent = filtered.slice(-20).reverse().map(function (ev) {
            return {
                event_key: ev.event_key,
                page_key: ev.page_key || 'page_home',
                device_type: ev.device_type || 'desktop',
                referrer: ev.referrer || 'direct',
                visitor_tag: String(ev.visitor_id || 'anon').slice(-6),
                created_at: ev.created_at
            };
        });

        return {
            success: true,
            days: dNum,
            summary: {
                unique_visitors: allVisitors.size,
                total_page_views: totalPageViews,
                home_views: homeViews,
                home_unique: homeVis.size,
                lisensi_views: lisensiViews,
                lisensi_unique: lisVis.size,
                forum_views: forumViews,
                forum_unique: forumVis.size,
                total_trial_clicks: totalTrialClicks,
                trial_unique: trialVis.size,
                total_license_clicks: totalLicenseClicks,
                total_contact_clicks: totalContactClicks,
                contact_unique: contactVis.size,
                mobile_visitors: mobileVis.size,
                desktop_visitors: desktopVis.size
            },
            events: eventsOut,
            daily_trend: dailyTrend,
            referrers: referrers,
            recent: recent
        };
    }

    function clearLocalAnalyticsData(keepDays) {
        const kd = Math.max(Number(keepDays) || 90, 0);
        if (kd <= 0) {
            try { localStorage.removeItem(LOCAL_EVENTS_KEY); } catch (_) {}
            return 0;
        }
        const cutoff = Date.now() - (kd * 86400000);
        try {
            const raw = localStorage.getItem(LOCAL_EVENTS_KEY);
            const list = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(list)) return 0;
            const kept = list.filter(function (item) {
                const ts = Date.parse((item && item.created_at) || '') || 0;
                return ts >= cutoff;
            });
            const removed = list.length - kept.length;
            localStorage.setItem(LOCAL_EVENTS_KEY, JSON.stringify(kept));
            return removed;
        } catch (_) {
            return 0;
        }
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

        const cleanEventKey = String(eventKey).slice(0, 64);
        const pageKey = getPageKey();
        const visitorId = getVisitorId();
        const deviceType = getDeviceType();
        const referrer = getReferrerSource();
        const cleanMeta = meta && typeof meta === 'object' ? meta : {};

        saveLocalEvent({
            event_key: cleanEventKey,
            page_key: pageKey,
            visitor_id: visitorId,
            device_type: deviceType,
            referrer: referrer,
            meta: cleanMeta,
            created_at: new Date().toISOString()
        });

        const payload = {
            p_event_key: cleanEventKey,
            p_page_key: pageKey,
            p_visitor_id: visitorId,
            p_device_type: deviceType,
            p_referrer: referrer,
            p_meta: cleanMeta
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
        if (target && target.closest && target.closest('#admin-modal')) return;
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
    window.wanBuildLocalAnalyticsData = buildLocalAnalyticsData;
    window.wanClearLocalAnalyticsData = clearLocalAnalyticsData;
})();
