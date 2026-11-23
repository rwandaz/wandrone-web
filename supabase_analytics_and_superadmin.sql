-- ============================================================================
-- WANDRONE WEB: ANALITIK PENGUNJUNG & PENUNJUKAN SUPER ADMIN (OWNER-PROTECTED)
-- ============================================================================
-- Jalankan seluruh script ini SEKALI di Supabase SQL Editor (Project WanDrone).
-- Aman dijalankan ulang (idempotent).
--
-- Fitur yang diaktifkan:
--   1. Tabel public.web_analytics_events (RLS aktif, tanpa akses baca publik)
--   2. RPC public.track_web_event (write-only dengan whitelist event_key)
--   3. RPC public.admin_get_web_analytics (khusus Akun Utama & Super Admin)
--   4. RPC public.admin_clear_web_analytics (khusus Akun Utama / rwandaz)
--   5. RPC public.admin_promote_user_to_superadmin (khusus Akun Utama / rwandaz)
--   6. RPC public.admin_demote_superadmin (khusus Akun Utama / rwandaz)
--   7. Trigger proteksi tingkat database agar Akun Utama ('rwandaz') TIDAK PERNAH
--      bisa dihapus, diturunkan perannya, atau diubah username-nya oleh siapa pun.
-- ============================================================================

-- 1. TABEL ANALITIK WEB
CREATE TABLE IF NOT EXISTS public.web_analytics_events (
    id BIGSERIAL PRIMARY KEY,
    event_key TEXT NOT NULL,
    page_key TEXT NOT NULL DEFAULT 'page_home',
    visitor_id TEXT NOT NULL,
    device_type TEXT NOT NULL DEFAULT 'desktop',
    referrer TEXT NOT NULL DEFAULT 'direct',
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_web_analytics_created_at ON public.web_analytics_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_analytics_event_key ON public.web_analytics_events (event_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_analytics_visitor_id ON public.web_analytics_events (visitor_id, created_at DESC);

ALTER TABLE public.web_analytics_events ENABLE ROW LEVEL SECURITY;

-- Pastikan publik (anon/authenticated) TIDAK bisa membaca atau mengubah tabel secara langsung
REVOKE ALL ON TABLE public.web_analytics_events FROM anon, authenticated;

-- 2. HELPER VERIFIKASI KREDENSIAL & PERAN ADMIN (MENGGUNAKAN user_login EXISTING)
CREATE OR REPLACE FUNCTION public._wan_verify_admin_role(
    p_admin_user TEXT,
    p_admin_pass TEXT
) RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_res JSONB;
    v_role TEXT;
BEGIN
    IF p_admin_user IS NULL OR trim(p_admin_user) = '' OR p_admin_pass IS NULL OR p_admin_pass = '' THEN
        RAISE EXCEPTION 'Kredensial administrator tidak lengkap.';
    END IF;

    BEGIN
        SELECT to_jsonb(public.user_login(trim(p_admin_user), p_admin_pass)) INTO v_res;
    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Autentikasi gagal: username atau kata sandi tidak valid.';
    END;

    IF v_res IS NULL THEN
        RAISE EXCEPTION 'Autentikasi gagal: akun tidak ditemukan.';
    END IF;

    IF v_res ? 'user_login' AND jsonb_typeof(v_res->'user_login') = 'object' THEN
        v_res := v_res->'user_login';
    END IF;

    IF LOWER(trim(p_admin_user)) = 'rwandaz' THEN
        RETURN 'owner';
    END IF;

    v_role := LOWER(COALESCE(v_res->>'role', 'user'));
    RETURN v_role;
END;
$$;

REVOKE ALL ON FUNCTION public._wan_verify_admin_role(TEXT, TEXT) FROM PUBLIC, anon, authenticated;

-- 3. RPC WRITE-ONLY UNTUK MENCATAT KUNJUNGAN & KLIK PENGUNJUNG
CREATE OR REPLACE FUNCTION public.track_web_event(
    p_event_key TEXT,
    p_page_key TEXT DEFAULT 'page_home',
    p_visitor_id TEXT DEFAULT 'anon',
    p_device_type TEXT DEFAULT 'desktop',
    p_referrer TEXT DEFAULT 'direct',
    p_meta JSONB DEFAULT '{}'::jsonb
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_event TEXT := LOWER(trim(COALESCE(p_event_key, '')));
    v_page TEXT := LOWER(trim(COALESCE(p_page_key, 'page_home')));
    v_visitor TEXT := LEFT(trim(COALESCE(p_visitor_id, 'anon')), 64);
    v_device TEXT := CASE WHEN LOWER(COALESCE(p_device_type, '')) = 'mobile' THEN 'mobile' ELSE 'desktop' END;
    v_ref TEXT := LEFT(LOWER(trim(COALESCE(p_referrer, 'direct'))), 60);
    v_meta JSONB := CASE WHEN jsonb_typeof(COALESCE(p_meta, '{}'::jsonb)) = 'object' THEN COALESCE(p_meta, '{}'::jsonb) ELSE '{}'::jsonb END;
BEGIN
    -- Whitelist ketat event_key agar tidak bisa disalahgunakan untuk injeksi data sampah
    IF v_event NOT IN (
        'page_home', 'page_lisensi', 'page_forum',
        'dl_tw_mapper', 'watch_tutorial', 'dl_tw_tweaks', 'dl_wandrone_tweaks', 'open_docs',
        'click_nav_lisensi', 'click_license_portal', 'wa_paket_hobby', 'wa_paket_pro',
        'wa_jejen_lisensi', 'wa_ian_teknis', 'wa_upay_teknis', 'wa_wan_teknis',
        'social_instagram', 'social_tiktok', 'social_youtube'
    ) THEN
        RETURN jsonb_build_object('success', false, 'ignored', true);
    END IF;

    IF v_page NOT IN ('page_home', 'page_lisensi', 'page_forum') THEN
        v_page := 'page_home';
    END IF;

    IF v_visitor = '' THEN
        v_visitor := 'anon';
    END IF;

    IF v_ref = '' THEN
        v_ref := 'direct';
    END IF;

    INSERT INTO public.web_analytics_events (event_key, page_key, visitor_id, device_type, referrer, meta)
    VALUES (v_event, v_page, v_visitor, v_device, v_ref, v_meta);

    RETURN jsonb_build_object('success', true);
END;
$$;

GRANT EXECUTE ON FUNCTION public.track_web_event(TEXT, TEXT, TEXT, TEXT, TEXT, JSONB) TO anon, authenticated;

-- 4. RPC BACA STATISTIK WEB (KHUSUS AKUN UTAMA & SUPER ADMIN YANG DITUNJUK)
CREATE OR REPLACE FUNCTION public.admin_get_web_analytics(
    admin_user TEXT,
    admin_pass TEXT,
    p_days INTEGER DEFAULT 30
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_since TIMESTAMPTZ;
    v_summary JSONB;
    v_events JSONB;
    v_daily JSONB;
    v_referrers JSONB;
    v_recent JSONB;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin') THEN
        RAISE EXCEPTION 'Akses Ditolak: Statistik Web hanya dapat diakses oleh Akun Utama dan Super Admin.';
    END IF;

    IF COALESCE(p_days, 30) <= 0 THEN
        v_since := '1970-01-01 00:00:00+00'::timestamptz;
    ELSIF p_days = 1 THEN
        v_since := date_trunc('day', NOW() AT TIME ZONE 'Asia/Jakarta') AT TIME ZONE 'Asia/Jakarta';
    ELSE
        v_since := NOW() - make_interval(days => p_days);
    END IF;

    -- Ringkasan KPI Utama
    SELECT jsonb_build_object(
        'unique_visitors', COALESCE(COUNT(DISTINCT visitor_id), 0),
        'total_page_views', COALESCE(COUNT(*) FILTER (WHERE event_key IN ('page_home', 'page_lisensi', 'page_forum')), 0),
        'home_views', COALESCE(COUNT(*) FILTER (WHERE event_key = 'page_home'), 0),
        'home_unique', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE event_key = 'page_home'), 0),
        'lisensi_views', COALESCE(COUNT(*) FILTER (WHERE event_key = 'page_lisensi'), 0),
        'lisensi_unique', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE event_key = 'page_lisensi'), 0),
        'forum_views', COALESCE(COUNT(*) FILTER (WHERE event_key = 'page_forum'), 0),
        'forum_unique', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE event_key = 'page_forum'), 0),
        'total_trial_clicks', COALESCE(COUNT(*) FILTER (WHERE event_key IN ('dl_tw_mapper', 'watch_tutorial', 'dl_tw_tweaks', 'dl_wandrone_tweaks', 'open_docs')), 0),
        'trial_unique', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE event_key IN ('dl_tw_mapper', 'watch_tutorial', 'dl_tw_tweaks', 'dl_wandrone_tweaks', 'open_docs')), 0),
        'total_license_clicks', COALESCE(COUNT(*) FILTER (WHERE event_key IN ('click_nav_lisensi', 'click_license_portal', 'wa_paket_hobby', 'wa_paket_pro')), 0),
        'total_contact_clicks', COALESCE(COUNT(*) FILTER (WHERE event_key IN ('wa_jejen_lisensi', 'wa_ian_teknis', 'wa_upay_teknis', 'wa_wan_teknis', 'wa_paket_hobby', 'wa_paket_pro')), 0),
        'contact_unique', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE event_key IN ('wa_jejen_lisensi', 'wa_ian_teknis', 'wa_upay_teknis', 'wa_wan_teknis', 'wa_paket_hobby', 'wa_paket_pro')), 0),
        'mobile_visitors', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE device_type = 'mobile'), 0),
        'desktop_visitors', COALESCE(COUNT(DISTINCT visitor_id) FILTER (WHERE device_type = 'desktop'), 0)
    )
    INTO v_summary
    FROM public.web_analytics_events
    WHERE created_at >= v_since;

    -- Breakdown per event_key
    SELECT COALESCE(jsonb_object_agg(
        event_key,
        jsonb_build_object(
            'total', total_cnt,
            'unique', unique_cnt
        )
    ), '{}'::jsonb)
    INTO v_events
    FROM (
        SELECT
            event_key,
            COUNT(*) AS total_cnt,
            COUNT(DISTINCT visitor_id) AS unique_cnt
        FROM public.web_analytics_events
        WHERE created_at >= v_since
        GROUP BY event_key
    ) s;

    -- Tren Harian (WIB / Asia/Jakarta)
    SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
            'day', to_char(day_bucket, 'YYYY-MM-DD'),
            'visitors', visitors_cnt,
            'page_views', pv_cnt,
            'trial_clicks', trial_cnt,
            'contact_clicks', contact_cnt
        ) ORDER BY day_bucket ASC
    ), '[]'::jsonb)
    INTO v_daily
    FROM (
        SELECT
            date_trunc('day', created_at AT TIME ZONE 'Asia/Jakarta')::date AS day_bucket,
            COUNT(DISTINCT visitor_id) AS visitors_cnt,
            COUNT(*) FILTER (WHERE event_key IN ('page_home', 'page_lisensi', 'page_forum')) AS pv_cnt,
            COUNT(*) FILTER (WHERE event_key IN ('dl_tw_mapper', 'watch_tutorial', 'dl_tw_tweaks', 'dl_wandrone_tweaks', 'open_docs')) AS trial_cnt,
            COUNT(*) FILTER (WHERE event_key IN ('wa_jejen_lisensi', 'wa_ian_teknis', 'wa_upay_teknis', 'wa_wan_teknis', 'wa_paket_hobby', 'wa_paket_pro')) AS contact_cnt
        FROM public.web_analytics_events
        WHERE created_at >= v_since
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT 31
    ) d;

    -- Top Sumber Trafik (Referrer eksternal / direct)
    SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
            'source', referrer,
            'visitors', visitors_cnt,
            'views', views_cnt
        ) ORDER BY visitors_cnt DESC, views_cnt DESC
    ), '[]'::jsonb)
    INTO v_referrers
    FROM (
        SELECT
            referrer,
            COUNT(DISTINCT visitor_id) AS visitors_cnt,
            COUNT(*) AS views_cnt
        FROM public.web_analytics_events
        WHERE created_at >= v_since
          AND event_key IN ('page_home', 'page_lisensi', 'page_forum')
          AND referrer <> 'internal'
        GROUP BY referrer
        ORDER BY visitors_cnt DESC, views_cnt DESC
        LIMIT 10
    ) r;

    -- 20 Aktivitas Klik Terbaru (tanpa data pribadi)
    SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
            'event_key', event_key,
            'page_key', page_key,
            'device_type', device_type,
            'referrer', referrer,
            'visitor_tag', RIGHT(visitor_id, 6),
            'created_at', created_at
        ) ORDER BY created_at DESC
    ), '[]'::jsonb)
    INTO v_recent
    FROM (
        SELECT event_key, page_key, device_type, referrer, visitor_id, created_at
        FROM public.web_analytics_events
        WHERE created_at >= v_since
        ORDER BY created_at DESC
        LIMIT 20
    ) rec;

    RETURN jsonb_build_object(
        'success', true,
        'days', p_days,
        'summary', v_summary,
        'events', v_events,
        'daily_trend', v_daily,
        'referrers', v_referrers,
        'recent', v_recent
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_get_web_analytics(TEXT, TEXT, INTEGER) TO anon, authenticated;

-- 5. RPC BERSIHKAN DATA ANALITIK LAMA (AKUN UTAMA & SUPER ADMIN)
CREATE OR REPLACE FUNCTION public.admin_clear_web_analytics(
    admin_user TEXT,
    admin_pass TEXT,
    p_keep_days INTEGER DEFAULT 90
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_deleted INTEGER := 0;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin') THEN
        RAISE EXCEPTION 'Akses Ditolak: Hanya Akun Utama dan Super Admin yang berhak membersihkan data statistik lama.';
    END IF;

    DELETE FROM public.web_analytics_events
    WHERE created_at < NOW() - make_interval(days => GREATEST(COALESCE(p_keep_days, 90), 7));

    GET DIAGNOSTICS v_deleted = ROW_COUNT;

    RETURN jsonb_build_object(
        'success', true,
        'deleted_count', v_deleted,
        'message', format('%s catatan statistik lebih lama dari %s hari telah dibersihkan.', v_deleted, GREATEST(COALESCE(p_keep_days, 90), 7))
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_clear_web_analytics(TEXT, TEXT, INTEGER) TO anon, authenticated;

-- 6. RPC TUNJUK PENGGUNA / ADMIN MENJADI SUPER ADMIN (KHUSUS AKUN UTAMA rwandaz)
CREATE OR REPLACE FUNCTION public.admin_promote_user_to_superadmin(
    admin_user TEXT,
    admin_pass TEXT,
    target_user_id BIGINT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_target_username TEXT;
    v_promote_res JSONB;
    v_admin_tbl TEXT;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role <> 'owner' THEN
        RAISE EXCEPTION 'Akses Ditolak: Hanya Akun Utama (rwandaz) yang dapat menunjuk Super Admin.';
    END IF;

    -- Ambil username target dari forum_users
    IF to_regclass('public.forum_users') IS NOT NULL THEN
        EXECUTE 'SELECT username FROM public.forum_users WHERE id = $1 LIMIT 1'
        INTO v_target_username
        USING target_user_id;
    END IF;

    IF v_target_username IS NULL THEN
        RAISE EXCEPTION 'Pengguna target tidak ditemukan.';
    END IF;

    IF LOWER(v_target_username) = 'rwandaz' THEN
        RETURN jsonb_build_object('success', true, 'message', 'Akun Utama sudah memiliki hak akses penuh.');
    END IF;

    -- Pastikan akun target sudah memiliki entri admin lewat fungsi eksisting (jika belum)
    BEGIN
        SELECT to_jsonb(public.admin_promote_user_to_admin(admin_user, admin_pass, target_user_id, NULL))
        INTO v_promote_res;
    EXCEPTION WHEN OTHERS THEN
        -- Jika sudah menjadi admin sebelumnya, lanjutkan ke peningkatan peran superadmin
        NULL;
    END;

    -- Tingkatkan role menjadi 'superadmin' di forum_users
    IF to_regclass('public.forum_users') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'forum_users' AND column_name = 'role'
        ) THEN
            EXECUTE 'UPDATE public.forum_users SET role = ''superadmin'' WHERE LOWER(username) = LOWER($1)'
            USING v_target_username;
        END IF;
    END IF;

    -- Tingkatkan role menjadi 'superadmin' di tabel admin eksisting (admin_users / forum_admins / admins)
    FOREACH v_admin_tbl IN ARRAY ARRAY['admin_users', 'forum_admins', 'admins'] LOOP
        IF to_regclass('public.' || v_admin_tbl) IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = v_admin_tbl AND column_name = 'role'
            ) THEN
                EXECUTE format('UPDATE public.%I SET role = ''superadmin'' WHERE LOWER(username) = LOWER($1)', v_admin_tbl)
                USING v_target_username;
            END IF;
        END IF;
    END LOOP;

    -- Catat ke audit log jika tabel system_logs tersedia
    IF to_regclass('public.system_logs') IS NOT NULL THEN
        BEGIN
            EXECUTE 'INSERT INTO public.system_logs (actor_username, actor_role, action_type, action_name, target_identifier, description)
                     VALUES ($1, ''superadmin'', ''KELOLA_PENGGUNA'', ''Tunjuk Super Admin'', $2, $3)'
            USING trim(admin_user), '@' || v_target_username,
                  format('Akun Utama menunjuk @%s sebagai Super Admin dengan akses penuh (Akun Utama tetap terlindungi).', v_target_username);
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'username', v_target_username,
        'role', 'superadmin',
        'message', format('Akun @%s berhasil ditunjuk sebagai Super Admin. Akun Utama tetap terlindungi penuh.', v_target_username)
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_promote_user_to_superadmin(TEXT, TEXT, BIGINT) TO anon, authenticated;

-- 7. RPC CABUT STATUS SUPER ADMIN (KHUSUS AKUN UTAMA rwandaz)
CREATE OR REPLACE FUNCTION public.admin_demote_superadmin(
    admin_user TEXT,
    admin_pass TEXT,
    target_username TEXT,
    downgrade_to_role TEXT DEFAULT 'admin'
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_target TEXT := trim(COALESCE(target_username, ''));
    v_new_role TEXT := CASE WHEN LOWER(COALESCE(downgrade_to_role, 'admin')) = 'user' THEN 'user' ELSE 'admin' END;
    v_admin_tbl TEXT;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role <> 'owner' THEN
        RAISE EXCEPTION 'Akses Ditolak: Hanya Akun Utama (rwandaz) yang dapat mencabut status Super Admin.';
    END IF;

    IF v_target = '' THEN
        RAISE EXCEPTION 'Username target tidak valid.';
    END IF;

    IF LOWER(v_target) = 'rwandaz' THEN
        RAISE EXCEPTION 'Akun Utama (rwandaz) dilindungi dan tidak dapat diturunkan perannya.';
    END IF;

    IF v_new_role = 'user' THEN
        -- Cabut seluruh akses admin termasuk superadmin
        IF to_regclass('public.forum_users') IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'forum_users' AND column_name = 'role'
            ) THEN
                EXECUTE 'UPDATE public.forum_users SET role = ''user'' WHERE LOWER(username) = LOWER($1)'
                USING v_target;
            END IF;
        END IF;

        FOREACH v_admin_tbl IN ARRAY ARRAY['admin_users', 'forum_admins', 'admins'] LOOP
            IF to_regclass('public.' || v_admin_tbl) IS NOT NULL THEN
                EXECUTE format('DELETE FROM public.%I WHERE LOWER(username) = LOWER($1)', v_admin_tbl)
                USING v_target;
            END IF;
        END LOOP;
    ELSE
        -- Turunkan dari Super Admin menjadi Admin Moderasi biasa
        IF to_regclass('public.forum_users') IS NOT NULL THEN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'forum_users' AND column_name = 'role'
            ) THEN
                EXECUTE 'UPDATE public.forum_users SET role = ''admin'' WHERE LOWER(username) = LOWER($1)'
                USING v_target;
            END IF;
        END IF;

        FOREACH v_admin_tbl IN ARRAY ARRAY['admin_users', 'forum_admins', 'admins'] LOOP
            IF to_regclass('public.' || v_admin_tbl) IS NOT NULL THEN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = v_admin_tbl AND column_name = 'role'
                ) THEN
                    EXECUTE format('UPDATE public.%I SET role = ''admin'' WHERE LOWER(username) = LOWER($1)', v_admin_tbl)
                    USING v_target;
                END IF;
            END IF;
        END LOOP;
    END IF;

    -- Catat ke audit log jika tersedia
    IF to_regclass('public.system_logs') IS NOT NULL THEN
        BEGIN
            EXECUTE 'INSERT INTO public.system_logs (actor_username, actor_role, action_type, action_name, target_identifier, description)
                     VALUES ($1, ''superadmin'', ''KELOLA_PENGGUNA'', ''Cabut Super Admin'', $2, $3)'
            USING trim(admin_user), '@' || v_target,
                  format('Akun Utama mencabut status Super Admin @%s (peran baru: %s).', v_target, v_new_role);
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'username', v_target,
        'role', v_new_role,
        'message', CASE
            WHEN v_new_role = 'admin' THEN format('Status Super Admin @%s telah dicabut dan diturunkan menjadi Admin Moderasi.', v_target)
            ELSE format('Seluruh akses Super Admin & Admin untuk @%s telah dicabut (kembali menjadi Pilot).', v_target)
        END
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_demote_superadmin(TEXT, TEXT, TEXT, TEXT) TO anon, authenticated;

-- 8. TRIGGER PROTEKSI TINGKAT DATABASE UNTUK AKUN UTAMA ('rwandaz')
-- Menjamin Akun Utama TIDAK PERNAH bisa dihapus, diubah username-nya,
-- atau diturunkan perannya dari 'superadmin' oleh RPC mana pun.
CREATE OR REPLACE FUNCTION public._wan_protect_owner_account()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_json JSONB := to_jsonb(OLD);
    v_new_json JSONB;
    v_old_user TEXT := LOWER(COALESCE(v_old_json->>'username', ''));
    v_new_user TEXT;
    v_new_role TEXT;
BEGIN
    IF v_old_user = 'rwandaz' THEN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Proteksi Akun Utama: Akun rwandaz tidak dapat dihapus dari sistem.';
        END IF;

        IF TG_OP = 'UPDATE' THEN
            v_new_json := to_jsonb(NEW);
            v_new_user := LOWER(COALESCE(v_new_json->>'username', ''));
            IF v_new_user <> 'rwandaz' THEN
                RAISE EXCEPTION 'Proteksi Akun Utama: Username akun utama tidak dapat diubah.';
            END IF;

            IF v_new_json ? 'role' THEN
                v_new_role := LOWER(COALESCE(v_new_json->>'role', ''));
                IF v_new_role <> 'superadmin' THEN
                    RAISE EXCEPTION 'Proteksi Akun Utama: Hak akses akun utama tidak dapat diturunkan.';
                END IF;
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    v_tbl TEXT;
BEGIN
    FOREACH v_tbl IN ARRAY ARRAY['forum_users', 'admin_users', 'forum_admins', 'admins'] LOOP
        IF to_regclass('public.' || v_tbl) IS NOT NULL THEN
            EXECUTE format('DROP TRIGGER IF EXISTS trg_wan_protect_owner_%I ON public.%I', v_tbl, v_tbl);
            EXECUTE format(
                'CREATE TRIGGER trg_wan_protect_owner_%I
                 BEFORE UPDATE OR DELETE ON public.%I
                 FOR EACH ROW
                 EXECUTE FUNCTION public._wan_protect_owner_account()',
                v_tbl, v_tbl
            );
        END IF;
    END LOOP;
END;
$$;
