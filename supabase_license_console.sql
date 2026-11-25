-- ============================================================================
-- WANDRONE UNIFIED LICENSE CONSOLE: MULTI-APP, 4-TIER, DURATION & DEVICE SLOTS
-- ============================================================================
-- Jalankan script ini di Supabase SQL Editor (Project WanDrone).
-- Aman dijalankan berulang kali (100% Idempotent).
--
-- Mencakup:
--   1. public.license_applications (Katalog Multi-Aplikasi: WD Tweak, TW-Mapper, dll.)
--   2. public.license_tiers (4 Kelas Resmi: Trial 7 Hari, Hobby, Pro Konsumen, Enterprise Pilihan Owner)
--   3. public.licenses (Lisensi Pelanggan: Aplikasi, Kelas, Jangka Waktu, Max Device, Fitur)
--   4. public.license_devices (Manajemen Slot Perangkat Aktif & Token Offline)
--   5. public.license_audit_logs (Log Audit Penerbitan & Perubahan Lisensi)
--   6. RPC Admin & RPC Publik Cek/Aktivasi Mandiri (dengan Auto-Lock saat Trial/Masa Aktif Habis)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. TABEL MASTER APLIKASI (MULTI-APPLICATION REGISTRY)
CREATE TABLE IF NOT EXISTS public.license_applications (
    app_slug TEXT PRIMARY KEY,
    app_name TEXT NOT NULL,
    key_prefix TEXT NOT NULL DEFAULT 'WDT',
    platforms TEXT[] NOT NULL DEFAULT ARRAY['android_rc', 'android_phone'],
    crypto_mode TEXT NOT NULL DEFAULT 'ed25519_wandrone1',
    available_features JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. TABEL MASTER KELAS LISENSI PER APLIKASI (TIER & ENTITLEMENT MATRIX)
CREATE TABLE IF NOT EXISTS public.license_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_slug TEXT NOT NULL REFERENCES public.license_applications(app_slug) ON DELETE CASCADE,
    tier_slug TEXT NOT NULL,
    tier_name TEXT NOT NULL,
    audience_scope TEXT NOT NULL DEFAULT 'consumer', -- 'trial' | 'consumer' | 'owner_invite_only'
    default_duration_plan TEXT NOT NULL DEFAULT 'yearly', -- 'trial_7d' | 'monthly' | 'quarterly' | 'yearly' | 'lifetime'
    default_duration_days INTEGER, -- 7 untuk trial, 30, 90, 365, atau NULL untuk lifetime
    default_max_devices INTEGER NOT NULL DEFAULT 2,
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    auto_lock_on_expire BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (app_slug, tier_slug)
);

-- 3. TABEL DATA LISENSI PELANGGAN
CREATE TABLE IF NOT EXISTS public.licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key TEXT NOT NULL UNIQUE,
    app_slug TEXT NOT NULL REFERENCES public.license_applications(app_slug) ON DELETE RESTRICT,
    tier_slug TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_contact TEXT NOT NULL DEFAULT '-',
    organization TEXT NOT NULL DEFAULT '-',
    duration_plan TEXT NOT NULL DEFAULT 'yearly', -- 'trial' | 'monthly' | 'quarterly' | 'yearly' | 'lifetime' | 'custom'
    duration_days INTEGER, -- 7 untuk trial, dst. NULL jika lifetime
    activation_trigger TEXT NOT NULL DEFAULT 'on_issue', -- 'on_issue' | 'on_first_device'
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- NULL jika lifetime (permanen)
    max_devices INTEGER NOT NULL DEFAULT 2,
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active', -- 'active' | 'pending' | 'expired' | 'suspended' | 'revoked'
    notes TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT 'rwandaz',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_licenses_app_tier ON public.licenses (app_slug, tier_slug);
CREATE INDEX IF NOT EXISTS idx_licenses_status ON public.licenses (status, expires_at);
CREATE INDEX IF NOT EXISTS idx_licenses_customer ON public.licenses (customer_name, customer_contact);

-- 4. TABEL SLOT PERANGKAT TERDAFTAR (DEVICE BINDINGS)
CREATE TABLE IF NOT EXISTS public.license_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID NOT NULL REFERENCES public.licenses(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL DEFAULT 'DJI RC / Android Device',
    platform TEXT NOT NULL DEFAULT 'android_rc',
    offline_token TEXT NOT NULL DEFAULT '',
    first_activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active', -- 'active' | 'released'
    UNIQUE (license_id, device_id)
);

CREATE INDEX IF NOT EXISTS idx_license_devices_lookup ON public.license_devices (device_id, status);
CREATE INDEX IF NOT EXISTS idx_license_devices_license ON public.license_devices (license_id, status);

-- 5. TABEL LOG AUDIT LISENSI
CREATE TABLE IF NOT EXISTS public.license_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_username TEXT NOT NULL,
    actor_role TEXT NOT NULL DEFAULT 'superadmin',
    action_type TEXT NOT NULL,
    license_key TEXT,
    app_slug TEXT,
    summary TEXT NOT NULL,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_license_audit_created ON public.license_audit_logs (created_at DESC);

-- AKTIFKAN RLS & KUNCI AKSES TABEL LANGSUNG (HANYA LEWAT RPC RESMI)
ALTER TABLE public.license_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_tiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_audit_logs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.license_applications FROM anon, authenticated;
REVOKE ALL ON TABLE public.license_tiers FROM anon, authenticated;
REVOKE ALL ON TABLE public.licenses FROM anon, authenticated;
REVOKE ALL ON TABLE public.license_devices FROM anon, authenticated;
REVOKE ALL ON TABLE public.license_audit_logs FROM anon, authenticated;

-- ============================================================================
-- SEED KATALOG APLIKASI (HANYA WD TWEAK) & 4 KELAS LISENSI RESMI
-- ============================================================================

INSERT INTO public.license_applications (app_slug, app_name, key_prefix, platforms, crypto_mode, available_features, description, is_active)
VALUES
(
    'wdtweak',
    'WD Tweak',
    'WDT',
    ARRAY['android_rc', 'android_phone'],
    'ed25519_wandrone1',
    '[
        {"key": "waypoint_bridge", "label": "Waypoint Bridge (Port 8989 & Flash Inject)", "desc": "Injeksi misi KMZ instan tanpa dummy & SQLite Auto-Heal"},
        {"key": "badge_utilities", "label": "Floating Badge Utilities", "desc": "Pintasan Menu Aplikasi, MicroSD Manager & HDMI Display"},
        {"key": "tuning_fcc", "label": "Radio Tuning: FCC Boost", "desc": "Peningkatan daya pancar sinyal 5.8 GHz FCC Keepalive"},
        {"key": "unlock_alt_500m", "label": "Unlock Altitude 500m & LED", "desc": "Buka batas ketinggian terbang hingga 500 meter & kontrol LED"},
        {"key": "atti_mode", "label": "Flight Mode: ATTI Mode", "desc": "Opsi aktivasi mode terbang manual ATTI"},
        {"key": "telemetry_ws", "label": "Live Telemetry WebSocket 10Hz", "desc": "Streaming data OSD telemetri real-time ke GCS"},
        {"key": "mission_control", "label": "Mission & Gimbal Action Control", "desc": "Kendali kamera, gimbal, dan eksekusi misi jarak jauh"}
    ]'::jsonb,
    'Modul resmi DJI Fly WanDrone Edition untuk DJI RC 2, RC Pro, dan Android.',
    TRUE
)
ON CONFLICT (app_slug) DO UPDATE SET
    app_name = EXCLUDED.app_name,
    key_prefix = EXCLUDED.key_prefix,
    available_features = EXCLUDED.available_features,
    description = EXCLUDED.description,
    updated_at = NOW();

-- SEED 4 KELAS LISENSI UNTUK WD TWEAK (SESUAI ATURAN: TRIAL 7 HARI, HOBBY=WAYPOINT BRIDGE, PRO=KONSUMEN, ENTERPRISE=PILIHAN OWNER)
INSERT INTO public.license_tiers (app_slug, tier_slug, tier_name, audience_scope, default_duration_plan, default_duration_days, default_max_devices, features, auto_lock_on_expire, description, sort_order)
VALUES
(
    'wdtweak',
    'trial',
    'Trial (Uji Coba 7 Hari)',
    'trial',
    'trial',
    7,
    1,
    '["waypoint_bridge", "badge_utilities", "tuning_fcc", "unlock_alt_500m", "atti_mode", "telemetry_ws", "mission_control"]'::jsonb,
    TRUE,
    'Membuka seluruh fitur selama 7 hari. Setelah 7 hari habis, seluruh fitur otomatis terkunci semua.',
    1
),
(
    'wdtweak',
    'hobby',
    'Hobby',
    'consumer',
    'yearly',
    365,
    2,
    '["waypoint_bridge"]'::jsonb,
    TRUE,
    'Khusus fitur Waypoint Bridge (Port 8989 & Flash Inject KMZ). Fitur tuning dan utilitas lanjutan terkunci.',
    2
),
(
    'wdtweak',
    'pro',
    'Pro (Konsumen Resmi)',
    'consumer',
    'yearly',
    365,
    2,
    '["waypoint_bridge", "badge_utilities", "tuning_fcc", "unlock_alt_500m", "atti_mode", "telemetry_ws", "mission_control"]'::jsonb,
    TRUE,
    'Paket lengkap untuk konsumen/pembeli resmi dengan seluruh fitur operasional terbuka penuh.',
    3
),
(
    'wdtweak',
    'enterprise',
    'Enterprise (Khusus Pilihan Owner)',
    'owner_invite_only',
    'lifetime',
    NULL,
    5,
    '["waypoint_bridge", "badge_utilities", "tuning_fcc", "unlock_alt_500m", "atti_mode", "telemetry_ws", "mission_control"]'::jsonb,
    FALSE,
    'Lisensi VIP / Internal khusus untuk orang yang ditunjuk langsung oleh Owner. Seluruh fitur terbuka penuh tanpa batas.',
    4
)
ON CONFLICT (app_slug, tier_slug) DO UPDATE SET
    tier_name = EXCLUDED.tier_name,
    audience_scope = EXCLUDED.audience_scope,
    default_duration_plan = EXCLUDED.default_duration_plan,
    default_duration_days = EXCLUDED.default_duration_days,
    default_max_devices = EXCLUDED.default_max_devices,
    features = EXCLUDED.features,
    auto_lock_on_expire = EXCLUDED.auto_lock_on_expire,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

-- ============================================================================
-- HELPER INTERNAL: SINKRONISASI KEDALUWARSA OTOMATIS (AUTO-LOCK EXPIRED TRIALS)
-- ============================================================================
CREATE OR REPLACE FUNCTION public._wan_sync_expired_licenses()
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE public.licenses
    SET status = 'expired',
        updated_at = NOW()
    WHERE status = 'active'
      AND expires_at IS NOT NULL
      AND expires_at <= NOW();
END;
$$;

-- ============================================================================
-- RPC 1: AMBIL SELURUH DATA CONSOLE LISENSI (ADMIN / SUPERADMIN / OWNER)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.admin_get_license_console_data(
    admin_user TEXT,
    admin_pass TEXT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_apps JSONB;
    v_tiers JSONB;
    v_licenses JSONB;
    v_devices JSONB;
    v_logs JSONB;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin', 'admin') THEN
        RAISE EXCEPTION 'Akses ditolak: Anda tidak memiliki izin membuka Console Sistem Lisensi.';
    END IF;

    PERFORM public._wan_sync_expired_licenses();

    SELECT COALESCE(jsonb_agg(to_jsonb(a) ORDER BY a.created_at ASC), '[]'::jsonb)
    INTO v_apps
    FROM public.license_applications a;

    SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY t.app_slug ASC, t.sort_order ASC), '[]'::jsonb)
    INTO v_tiers
    FROM public.license_tiers t;

    SELECT COALESCE(jsonb_agg(
        to_jsonb(l) || jsonb_build_object(
            'active_device_count', (
                SELECT COUNT(*)::int FROM public.license_devices d
                WHERE d.license_id = l.id AND d.status = 'active'
            ),
            'is_locked', (
                l.status <> 'active' OR (l.expires_at IS NOT NULL AND l.expires_at <= NOW())
            ),
            'effective_features', CASE
                WHEN l.status <> 'active' OR (l.expires_at IS NOT NULL AND l.expires_at <= NOW()) THEN '[]'::jsonb
                ELSE l.features
            END
        )
        ORDER BY l.created_at DESC
    ), '[]'::jsonb)
    INTO v_licenses
    FROM public.licenses l;

    SELECT COALESCE(jsonb_agg(
        to_jsonb(d) || jsonb_build_object(
            'license_key', l.license_key,
            'app_slug', l.app_slug,
            'tier_slug', l.tier_slug,
            'customer_name', l.customer_name
        )
        ORDER BY d.last_seen_at DESC
    ), '[]'::jsonb)
    INTO v_devices
    FROM public.license_devices d
    JOIN public.licenses l ON l.id = d.license_id;

    SELECT COALESCE(jsonb_agg(to_jsonb(lg) ORDER BY lg.created_at DESC), '[]'::jsonb)
    INTO v_logs
    FROM (
        SELECT * FROM public.license_audit_logs
        ORDER BY created_at DESC
        LIMIT 100
    ) lg;

    RETURN jsonb_build_object(
        'success', true,
        'actor_role', v_role,
        'applications', v_apps,
        'tiers', v_tiers,
        'licenses', v_licenses,
        'devices', v_devices,
        'audit_logs', v_logs
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_get_license_console_data(TEXT, TEXT) TO anon, authenticated;

-- ============================================================================
-- RPC 2: TERBITKAN ATAU EDIT LISENSI (PER APLIKASI, KELAS, DURASI, DEVICE)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.admin_upsert_license(
    admin_user TEXT,
    admin_pass TEXT,
    p_payload JSONB
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_id UUID;
    v_is_new BOOLEAN := FALSE;
    v_app_slug TEXT;
    v_tier_slug TEXT;
    v_prefix TEXT;
    v_key TEXT;
    v_customer_name TEXT;
    v_customer_contact TEXT;
    v_organization TEXT;
    v_duration_plan TEXT;
    v_duration_days INTEGER;
    v_activation_trigger TEXT;
    v_expires_at TIMESTAMPTZ;
    v_max_devices INTEGER;
    v_features JSONB;
    v_status TEXT;
    v_notes TEXT;
    v_device_id TEXT;
    v_device_name TEXT;
    v_offline_token TEXT;
    v_lic RECORD;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin', 'admin') THEN
        RAISE EXCEPTION 'Akses ditolak: Hanya Administrator yang dapat mengelola lisensi.';
    END IF;

    v_app_slug := LOWER(trim(COALESCE(p_payload->>'app_slug', 'wdtweak')));
    v_tier_slug := LOWER(trim(COALESCE(p_payload->>'tier_slug', 'hobby')));

    -- Proteksi Kelas Enterprise: Khusus pilihan Owner / Super Admin
    IF v_tier_slug = 'enterprise' AND v_role NOT IN ('owner', 'superadmin') THEN
        RAISE EXCEPTION 'Kelas Enterprise khusus untuk orang pilihan Owner / Super Admin.';
    END IF;

    SELECT key_prefix INTO v_prefix FROM public.license_applications WHERE app_slug = v_app_slug;
    IF v_prefix IS NULL THEN
        v_prefix := 'WDT';
    END IF;

    v_customer_name := trim(COALESCE(p_payload->>'customer_name', ''));
    IF v_customer_name = '' THEN
        RAISE EXCEPTION 'Nama pemilik/penerima lisensi wajib diisi.';
    END IF;

    v_customer_contact := trim(COALESCE(p_payload->>'customer_contact', '-'));
    v_organization := trim(COALESCE(p_payload->>'organization', '-'));
    v_duration_plan := LOWER(trim(COALESCE(p_payload->>'duration_plan', 'yearly')));
    v_activation_trigger := LOWER(trim(COALESCE(p_payload->>'activation_trigger', 'on_issue')));
    v_max_devices := GREATEST(COALESCE((p_payload->>'max_devices')::int, 1), 1);
    v_status := LOWER(trim(COALESCE(p_payload->>'status', 'active')));
    v_notes := trim(COALESCE(p_payload->>'notes', ''));

    -- Hitung durasi hari & tanggal expired
    IF v_tier_slug = 'trial' OR v_duration_plan = 'trial' THEN
        v_duration_plan := 'trial';
        v_duration_days := COALESCE((p_payload->>'duration_days')::int, 7);
    ELSIF v_duration_plan = 'lifetime' THEN
        v_duration_days := NULL;
    ELSIF v_duration_plan = 'monthly' THEN
        v_duration_days := COALESCE((p_payload->>'duration_days')::int, 30);
    ELSIF v_duration_plan = 'quarterly' THEN
        v_duration_days := COALESCE((p_payload->>'duration_days')::int, 90);
    ELSIF v_duration_plan = 'yearly' THEN
        v_duration_days := COALESCE((p_payload->>'duration_days')::int, 365);
    ELSE
        v_duration_days := COALESCE((p_payload->>'duration_days')::int, 365);
    END IF;

    IF v_duration_plan = 'lifetime' THEN
        v_expires_at := NULL;
    ELSIF p_payload ? 'custom_expires_at' AND COALESCE(p_payload->>'custom_expires_at', '') <> '' THEN
        v_expires_at := (p_payload->>'custom_expires_at')::timestamptz;
    ELSIF v_activation_trigger = 'on_first_device' THEN
        -- Akan dihitung saat device pertama kali aktivasi
        v_expires_at := NULL;
    ELSE
        v_expires_at := NOW() + make_interval(days => COALESCE(v_duration_days, 7));
    END IF;

    -- Tentukan fitur berdasarkan kelas atau override payload
    IF p_payload ? 'features' AND jsonb_typeof(p_payload->'features') = 'array' THEN
        v_features := p_payload->'features';
    ELSE
        SELECT features INTO v_features
        FROM public.license_tiers
        WHERE app_slug = v_app_slug AND tier_slug = v_tier_slug;
        IF v_features IS NULL THEN
            IF v_tier_slug = 'hobby' THEN
                v_features := '["waypoint_bridge"]'::jsonb;
            ELSE
                v_features := '["waypoint_bridge", "badge_utilities", "tuning_fcc", "unlock_alt_500m", "atti_mode", "telemetry_ws", "mission_control"]'::jsonb;
            END IF;
        END IF;
    END IF;

    IF COALESCE(p_payload->>'id', '') <> '' THEN
        v_id := (p_payload->>'id')::uuid;
    END IF;

    IF v_id IS NOT NULL AND EXISTS (SELECT 1 FROM public.licenses WHERE id = v_id) THEN
        UPDATE public.licenses
        SET app_slug = v_app_slug,
            tier_slug = v_tier_slug,
            customer_name = v_customer_name,
            customer_contact = v_customer_contact,
            organization = v_organization,
            duration_plan = v_duration_plan,
            duration_days = v_duration_days,
            activation_trigger = v_activation_trigger,
            expires_at = v_expires_at,
            max_devices = v_max_devices,
            features = v_features,
            status = v_status,
            notes = v_notes,
            updated_at = NOW()
        WHERE id = v_id
        RETURNING * INTO v_lic;
    ELSE
        v_is_new := TRUE;
        v_key := UPPER(trim(COALESCE(p_payload->>'license_key', '')));
        IF v_key = '' THEN
            v_key := v_prefix || '-' || UPPER(LEFT(v_tier_slug, 3)) || '-' ||
                     TO_CHAR(NOW(), 'YY') || '-' ||
                     UPPER(SUBSTRING(encode(gen_random_bytes(4), 'hex') FROM 1 FOR 4)) || '-' ||
                     UPPER(SUBSTRING(encode(gen_random_bytes(4), 'hex') FROM 1 FOR 4));
        END IF;

        INSERT INTO public.licenses (
            license_key, app_slug, tier_slug, customer_name, customer_contact,
            organization, duration_plan, duration_days, activation_trigger,
            issued_at, activated_at, expires_at, max_devices, features, status, notes, created_by
        ) VALUES (
            v_key, v_app_slug, v_tier_slug, v_customer_name, v_customer_contact,
            v_organization, v_duration_plan, v_duration_days, v_activation_trigger,
            NOW(),
            CASE WHEN v_activation_trigger = 'on_issue' THEN NOW() ELSE NULL END,
            v_expires_at, v_max_devices, v_features, v_status, v_notes, trim(admin_user)
        )
        RETURNING * INTO v_lic;
    END IF;

    -- Jika disertakan Device ID awal saat penerbitan, langsung daftarkan ke slot perangkat
    v_device_id := UPPER(REGEXP_REPLACE(COALESCE(p_payload->>'initial_device_id', ''), '[^0-9A-Za-z\-]', '', 'g'));
    v_device_name := trim(COALESCE(p_payload->>'initial_device_name', 'DJI RC / Perangkat Utama'));
    v_offline_token := trim(COALESCE(p_payload->>'initial_offline_token', ''));

    IF LENGTH(v_device_id) >= 6 THEN
        INSERT INTO public.license_devices (license_id, device_id, device_name, offline_token, status)
        VALUES (v_lic.id, v_device_id, CASE WHEN v_device_name = '' THEN 'DJI RC / Perangkat Utama' ELSE v_device_name END, v_offline_token, 'active')
        ON CONFLICT (license_id, device_id) DO UPDATE SET
            device_name = EXCLUDED.device_name,
            offline_token = CASE WHEN EXCLUDED.offline_token <> '' THEN EXCLUDED.offline_token ELSE public.license_devices.offline_token END,
            status = 'active',
            last_seen_at = NOW();

        IF v_lic.activated_at IS NULL THEN
            UPDATE public.licenses
            SET activated_at = NOW(),
                expires_at = CASE
                    WHEN duration_plan = 'lifetime' THEN NULL
                    WHEN expires_at IS NULL AND duration_days IS NOT NULL THEN NOW() + make_interval(days => duration_days)
                    ELSE expires_at
                END
            WHERE id = v_lic.id
            RETURNING * INTO v_lic;
        END IF;
    END IF;

    INSERT INTO public.license_audit_logs (actor_username, actor_role, action_type, license_key, app_slug, summary, meta)
    VALUES (
        trim(admin_user),
        v_role,
        CASE WHEN v_is_new THEN 'ISSUE_LICENSE' ELSE 'UPDATE_LICENSE' END,
        v_lic.license_key,
        v_lic.app_slug,
        CASE WHEN v_is_new
            THEN format('Menerbitkan lisensi %s (%s) untuk %s [%s device]', v_lic.app_slug, UPPER(v_lic.tier_slug), v_lic.customer_name, v_lic.max_devices)
            ELSE format('Memperbarui lisensi %s (%s) milik %s', v_lic.license_key, UPPER(v_lic.tier_slug), v_lic.customer_name)
        END,
        jsonb_build_object('tier', v_lic.tier_slug, 'duration_plan', v_lic.duration_plan, 'max_devices', v_lic.max_devices, 'status', v_lic.status)
    );

    RETURN jsonb_build_object('success', true, 'license', to_jsonb(v_lic));
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_upsert_license(TEXT, TEXT, JSONB) TO anon, authenticated;

-- ============================================================================
-- RPC 3: AKSI CEPAT MANAJEMEN LISENSI & SLOT DEVICE (RESET, EXTEND, SUSPEND, DLL.)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.admin_manage_license_action(
    admin_user TEXT,
    admin_pass TEXT,
    p_action TEXT,
    p_license_id UUID,
    p_meta JSONB DEFAULT '{}'::jsonb
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_lic RECORD;
    v_days INTEGER;
    v_dev_id TEXT;
    v_summary TEXT;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin', 'admin') THEN
        RAISE EXCEPTION 'Akses ditolak.';
    END IF;

    SELECT * INTO v_lic FROM public.licenses WHERE id = p_license_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Data lisensi tidak ditemukan.';
    END IF;

    IF p_action = 'extend_days' THEN
        v_days := COALESCE((p_meta->>'days')::int, 30);
        UPDATE public.licenses
        SET expires_at = GREATEST(COALESCE(expires_at, NOW()), NOW()) + make_interval(days => v_days),
            status = 'active',
            updated_at = NOW()
        WHERE id = p_license_id
        RETURNING * INTO v_lic;
        v_summary := format('Memperpanjang masa aktif %s selama +%s hari', v_lic.license_key, v_days);

    ELSIF p_action = 'set_lifetime' THEN
        UPDATE public.licenses
        SET duration_plan = 'lifetime',
            duration_days = NULL,
            expires_at = NULL,
            status = 'active',
            updated_at = NOW()
        WHERE id = p_license_id
        RETURNING * INTO v_lic;
        v_summary := format('Mengubah jangka waktu %s menjadi Lifetime (Permanen)', v_lic.license_key);

    ELSIF p_action = 'set_status' THEN
        UPDATE public.licenses
        SET status = LOWER(trim(COALESCE(p_meta->>'status', 'active'))),
            updated_at = NOW()
        WHERE id = p_license_id
        RETURNING * INTO v_lic;
        v_summary := format('Mengubah status lisensi %s menjadi %s', v_lic.license_key, UPPER(v_lic.status));

    ELSIF p_action = 'unbind_device' THEN
        v_dev_id := trim(COALESCE(p_meta->>'device_id', ''));
        DELETE FROM public.license_devices
        WHERE license_id = p_license_id AND device_id = v_dev_id;
        v_summary := format('Melepas perangkat %s dari slot lisensi %s', v_dev_id, v_lic.license_key);

    ELSIF p_action = 'reset_all_devices' THEN
        DELETE FROM public.license_devices
        WHERE license_id = p_license_id;
        v_summary := format('Mereset seluruh slot perangkat pada lisensi %s', v_lic.license_key);

    ELSIF p_action = 'bind_device' THEN
        v_dev_id := UPPER(REGEXP_REPLACE(COALESCE(p_meta->>'device_id', ''), '[^0-9A-Za-z\-]', '', 'g'));
        IF LENGTH(v_dev_id) < 6 THEN
            RAISE EXCEPTION 'Device ID tidak valid.';
        END IF;
        INSERT INTO public.license_devices (license_id, device_id, device_name, offline_token, status)
        VALUES (
            p_license_id,
            v_dev_id,
            COALESCE(NULLIF(trim(p_meta->>'device_name'), ''), 'DJI RC / Perangkat Terdaftar'),
            COALESCE(p_meta->>'offline_token', ''),
            'active'
        )
        ON CONFLICT (license_id, device_id) DO UPDATE SET
            device_name = EXCLUDED.device_name,
            offline_token = CASE WHEN EXCLUDED.offline_token <> '' THEN EXCLUDED.offline_token ELSE public.license_devices.offline_token END,
            status = 'active',
            last_seen_at = NOW();
        v_summary := format('Mendaftarkan perangkat %s ke lisensi %s', v_dev_id, v_lic.license_key);

    ELSIF p_action = 'delete_license' THEN
        IF v_role NOT IN ('owner', 'superadmin') THEN
            RAISE EXCEPTION 'Hanya Owner / Super Admin yang dapat menghapus record lisensi secara permanen.';
        END IF;
        DELETE FROM public.licenses WHERE id = p_license_id;
        v_summary := format('Menghapus permanen lisensi %s (%s)', v_lic.license_key, v_lic.customer_name);

    ELSE
        RAISE EXCEPTION 'Aksi tidak dikenali: %', p_action;
    END IF;

    INSERT INTO public.license_audit_logs (actor_username, actor_role, action_type, license_key, app_slug, summary, meta)
    VALUES (trim(admin_user), v_role, UPPER(p_action), v_lic.license_key, v_lic.app_slug, v_summary, COALESCE(p_meta, '{}'::jsonb));

    RETURN jsonb_build_object('success', true, 'summary', v_summary, 'license', to_jsonb(v_lic));
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_manage_license_action(TEXT, TEXT, TEXT, UUID, JSONB) TO anon, authenticated;

-- ============================================================================
-- RPC 4: PENGATURAN JANGKA PANJANG (TAMBAH/EDIT APLIKASI & KELAS LISENSI)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.admin_upsert_app_or_tier(
    admin_user TEXT,
    admin_pass TEXT,
    p_kind TEXT,
    p_payload JSONB
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_role TEXT;
    v_app_slug TEXT;
    v_tier_slug TEXT;
BEGIN
    v_role := public._wan_verify_admin_role(admin_user, admin_pass);
    IF v_role NOT IN ('owner', 'superadmin') THEN
        RAISE EXCEPTION 'Hanya Owner / Super Admin yang dapat mengubah struktur Katalog Aplikasi & Kelas Lisensi.';
    END IF;

    IF p_kind = 'application' THEN
        v_app_slug := LOWER(REGEXP_REPLACE(COALESCE(p_payload->>'app_slug', ''), '[^a-z0-9_\-]', '', 'g'));
        IF v_app_slug = '' THEN
            RAISE EXCEPTION 'Kode slug aplikasi wajib diisi.';
        END IF;

        INSERT INTO public.license_applications (
            app_slug, app_name, key_prefix, platforms, crypto_mode, available_features, description, is_active, updated_at
        ) VALUES (
            v_app_slug,
            trim(COALESCE(p_payload->>'app_name', v_app_slug)),
            UPPER(trim(COALESCE(p_payload->>'key_prefix', 'WAN'))),
            ARRAY['android_rc', 'android_phone', 'windows'],
            COALESCE(p_payload->>'crypto_mode', 'ed25519_wandrone1'),
            COALESCE(p_payload->'available_features', '[]'::jsonb),
            COALESCE(p_payload->>'description', ''),
            COALESCE((p_payload->>'is_active')::boolean, TRUE),
            NOW()
        )
        ON CONFLICT (app_slug) DO UPDATE SET
            app_name = EXCLUDED.app_name,
            key_prefix = EXCLUDED.key_prefix,
            crypto_mode = EXCLUDED.crypto_mode,
            available_features = EXCLUDED.available_features,
            description = EXCLUDED.description,
            is_active = EXCLUDED.is_active,
            updated_at = NOW();

        INSERT INTO public.license_audit_logs (actor_username, actor_role, action_type, app_slug, summary)
        VALUES (trim(admin_user), v_role, 'CONFIG_APPLICATION', v_app_slug, format('Memperbarui konfigurasi aplikasi %s', v_app_slug));

    ELSIF p_kind = 'tier' THEN
        v_app_slug := LOWER(trim(COALESCE(p_payload->>'app_slug', 'wdtweak')));
        v_tier_slug := LOWER(REGEXP_REPLACE(COALESCE(p_payload->>'tier_slug', ''), '[^a-z0-9_\-]', '', 'g'));
        IF v_tier_slug = '' THEN
            RAISE EXCEPTION 'Kode kelas lisensi wajib diisi.';
        END IF;

        INSERT INTO public.license_tiers (
            app_slug, tier_slug, tier_name, audience_scope, default_duration_plan,
            default_duration_days, default_max_devices, features, auto_lock_on_expire, description, updated_at
        ) VALUES (
            v_app_slug,
            v_tier_slug,
            trim(COALESCE(p_payload->>'tier_name', v_tier_slug)),
            COALESCE(p_payload->>'audience_scope', 'consumer'),
            COALESCE(p_payload->>'default_duration_plan', 'yearly'),
            (p_payload->>'default_duration_days')::int,
            GREATEST(COALESCE((p_payload->>'default_max_devices')::int, 2), 1),
            COALESCE(p_payload->'features', '[]'::jsonb),
            COALESCE((p_payload->>'auto_lock_on_expire')::boolean, TRUE),
            COALESCE(p_payload->>'description', ''),
            NOW()
        )
        ON CONFLICT (app_slug, tier_slug) DO UPDATE SET
            tier_name = EXCLUDED.tier_name,
            audience_scope = EXCLUDED.audience_scope,
            default_duration_plan = EXCLUDED.default_duration_plan,
            default_duration_days = EXCLUDED.default_duration_days,
            default_max_devices = EXCLUDED.default_max_devices,
            features = EXCLUDED.features,
            auto_lock_on_expire = EXCLUDED.auto_lock_on_expire,
            description = EXCLUDED.description,
            updated_at = NOW();

        INSERT INTO public.license_audit_logs (actor_username, actor_role, action_type, app_slug, summary)
        VALUES (trim(admin_user), v_role, 'CONFIG_TIER', v_app_slug, format('Memperbarui kelas lisensi %s pada aplikasi %s', UPPER(v_tier_slug), v_app_slug));
    END IF;

    RETURN jsonb_build_object('success', true);
END;
$$;

GRANT EXECUTE ON FUNCTION public.admin_upsert_app_or_tier(TEXT, TEXT, TEXT, JSONB) TO anon, authenticated;

-- ============================================================================
-- RPC 5: PORTAL CEK & AKTIVASI MANDIRI PEMBELI (lisensi.html & REST CLIENT)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.public_check_or_activate_license(
    p_query TEXT,
    p_device_id TEXT DEFAULT NULL,
    p_device_name TEXT DEFAULT NULL,
    p_action TEXT DEFAULT 'check'
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_clean_q TEXT := UPPER(trim(COALESCE(p_query, '')));
    v_clean_dev TEXT := UPPER(REGEXP_REPLACE(COALESCE(p_device_id, ''), '[^0-9A-Za-z\-]', '', 'g'));
    v_lic RECORD;
    v_app RECORD;
    v_active_count INTEGER;
    v_is_expired BOOLEAN;
    v_is_locked BOOLEAN;
    v_devices JSONB;
    v_msg TEXT := 'Lisensi ditemukan.';
BEGIN
    IF v_clean_q = '' THEN
        RAISE EXCEPTION 'Masukkan Kunci Lisensi atau Device ID terlebih dahulu.';
    END IF;

    PERFORM public._wan_sync_expired_licenses();

    -- Cari berdasarkan License Key atau berdasarkan Device ID yang terdaftar
    SELECT l.* INTO v_lic
    FROM public.licenses l
    WHERE UPPER(l.license_key) = v_clean_q
       OR EXISTS (
           SELECT 1 FROM public.license_devices d
           WHERE d.license_id = l.id
             AND UPPER(d.device_id) = v_clean_q
             AND d.status = 'active'
       )
    ORDER BY l.created_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'found', false,
            'message', 'Kunci Lisensi atau Device ID tidak ditemukan. Pastikan penulisan sudah benar atau hubungi narahubung resmi.'
        );
    END IF;

    -- Jika p_action = 'activate' dan menyertakan p_device_id
    IF LOWER(COALESCE(p_action, 'check')) = 'activate' AND LENGTH(v_clean_dev) >= 6 THEN
        IF v_lic.status IN ('suspended', 'revoked') THEN
            RAISE EXCEPTION 'Lisensi ini sedang dibekukan atau telah dicabut. Hubungi administrator.';
        END IF;

        IF v_lic.expires_at IS NOT NULL AND v_lic.expires_at <= NOW() THEN
            RAISE EXCEPTION 'Masa berlaku lisensi ini telah habis (Kedaluwarsa). Silakan lakukan perpanjangan.';
        END IF;

        -- Hitung slot aktif selain device ini
        SELECT COUNT(*)::int INTO v_active_count
        FROM public.license_devices
        WHERE license_id = v_lic.id
          AND status = 'active'
          AND UPPER(device_id) <> v_clean_dev;

        IF v_active_count >= v_lic.max_devices THEN
            RAISE EXCEPTION 'Slot perangkat sudah penuh (%/% perangkat aktif). Hubungi admin untuk mereset slot perangkat lama.', v_active_count, v_lic.max_devices;
        END IF;

        INSERT INTO public.license_devices (license_id, device_id, device_name, status)
        VALUES (
            v_lic.id,
            v_clean_dev,
            COALESCE(NULLIF(trim(p_device_name), ''), 'DJI RC / Perangkat Pengguna'),
            'active'
        )
        ON CONFLICT (license_id, device_id) DO UPDATE SET
            device_name = COALESCE(NULLIF(trim(p_device_name), ''), public.license_devices.device_name),
            status = 'active',
            last_seen_at = NOW();

        -- Jika trigger 'on_first_device' dan baru pertama kali diaktifkan, mulai hitung mundur durasi sekarang!
        IF v_lic.activated_at IS NULL THEN
            UPDATE public.licenses
            SET activated_at = NOW(),
                status = 'active',
                expires_at = CASE
                    WHEN duration_plan = 'lifetime' THEN NULL
                    WHEN expires_at IS NULL AND duration_days IS NOT NULL THEN NOW() + make_interval(days => duration_days)
                    ELSE expires_at
                END,
                updated_at = NOW()
            WHERE id = v_lic.id
            RETURNING * INTO v_lic;
        END IF;

        v_msg := format('Perangkat %s berhasil diaktifkan pada slot lisensi %s.', v_clean_dev, v_lic.license_key);
    END IF;

    SELECT * INTO v_app FROM public.license_applications WHERE app_slug = v_lic.app_slug;

    v_is_expired := (v_lic.status = 'expired') OR (v_lic.expires_at IS NOT NULL AND v_lic.expires_at <= NOW());
    v_is_locked := v_is_expired OR (v_lic.status <> 'active');

    SELECT COUNT(*)::int INTO v_active_count
    FROM public.license_devices
    WHERE license_id = v_lic.id AND status = 'active';

    SELECT COALESCE(jsonb_agg(jsonb_build_object(
        'device_id', d.device_id,
        'device_name', d.device_name,
        'first_activated_at', d.first_activated_at,
        'last_seen_at', d.last_seen_at,
        'offline_token', d.offline_token
    ) ORDER BY d.first_activated_at ASC), '[]'::jsonb)
    INTO v_devices
    FROM public.license_devices d
    WHERE d.license_id = v_lic.id AND d.status = 'active';

    RETURN jsonb_build_object(
        'found', true,
        'message', v_msg,
        'license_key', v_lic.license_key,
        'app_slug', v_lic.app_slug,
        'app_name', COALESCE(v_app.app_name, v_lic.app_slug),
        'tier_slug', v_lic.tier_slug,
        'customer_name', v_lic.customer_name,
        'duration_plan', v_lic.duration_plan,
        'duration_days', v_lic.duration_days,
        'issued_at', v_lic.issued_at,
        'activated_at', v_lic.activated_at,
        'expires_at', v_lic.expires_at,
        'status', CASE WHEN v_is_expired THEN 'expired' ELSE v_lic.status END,
        'is_expired', v_is_expired,
        'is_locked', v_is_locked,
        'lock_reason', CASE
            WHEN v_is_expired AND v_lic.tier_slug = 'trial' THEN 'Masa uji coba Trial 7 Hari telah berakhir. Seluruh fitur kini terkunci.'
            WHEN v_is_expired THEN 'Masa berlaku lisensi telah kedaluwarsa. Seluruh fitur dikunci hingga diperpanjang.'
            WHEN v_lic.status = 'suspended' THEN 'Lisensi dibekukan sementara oleh administrator.'
            WHEN v_lic.status = 'revoked' THEN 'Lisensi telah dicabut.'
            ELSE NULL
        END,
        'max_devices', v_lic.max_devices,
        'active_device_count', v_active_count,
        'effective_features', CASE WHEN v_is_locked THEN '[]'::jsonb ELSE v_lic.features END,
        'configured_features', v_lic.features,
        'devices', v_devices
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.public_check_or_activate_license(TEXT, TEXT, TEXT, TEXT) TO anon, authenticated;
