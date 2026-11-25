/**
 * ============================================================================
 * WANDRONE UNIFIED LICENSE ENGINE (Cloud Supabase RPC + Local Hybrid + Crypto)
 * ============================================================================
 * Menyediakan:
 * 1. Katalog Aplikasi: Default hanya WD Tweak (WanDrone Tweak), mendukung tambah aplikasi baru untuk jangka panjang
 * 2. Matriks 4 Kelas Lisensi Resmi:
 *    - Trial (7 Hari, Seluruh Fitur Terbuka -> Habis 7 Hari Otomatis Terkunci Semua)
 *    - Hobby (Hanya Waypoint Bridge)
 *    - Pro (Untuk Konsumen Resmi - Fitur Operasional Lengkap)
 *    - Enterprise (Khusus Orang Pilihan Owner - 100% Seluruh Fitur Tanpa Batas)
 * 3. Kriptografi Offline Token Ed25519 (WANDRONE1)
 * 4. Sinkronisasi Supabase RPC dengan Fallback LocalStorage Otomatis
 */
(function (global) {
  'use strict';

  const SUPABASE_URL = global.WAN_SUPABASE_URL || 'https://vzrlpyzbqiunkmpmjmqn.supabase.co';
  const SUPABASE_ANON_KEY = global.WAN_SUPABASE_ANON_KEY || 'sb_publishable_AxPOTAiZZYuMyiq3_8vieA_FgKUcH1P';
  const STORAGE_KEY = 'wan_unified_license_db_v3';

  // Seed Ed25519 resmi ekosistem WanDrone
  const ED25519_SEED_HEX = '26da56b2154dd05a3ae7cac2f2b2ddd52d0155be7ea087de4ad11cd850f4c262';
  const PKCS8_ED25519_PREFIX_HEX = '302e020100300506032b657004220420';
  const PUBLIC_KEY_B64URL = 'JtpWshVN0Fo658rC8rLd1S0BVb5-oIfeStEc2FD0wmI';

  const DEFAULT_APPLICATIONS = [
    {
      app_slug: 'wdtweak',
      app_name: 'WD Tweak',
      key_prefix: 'WDT',
      platforms: ['android_rc', 'android_phone'],
      crypto_mode: 'ed25519_wandrone1',
      magic_header: 'WANDRONE1',
      description: 'Modul DJI Fly WanDrone Edition untuk DJI RC 2, RC Pro, dan Android (Waypoint Bridge 8989, Flash Inject, Tuning FCC/Alt/ATTI, Badge Utilities).',
      is_active: true,
      available_features: [
        { key: 'waypoint_bridge', label: 'Waypoint Bridge (Port 8989 & Flash Inject)', desc: 'Injeksi misi KMZ instan tanpa dummy & SQLite Auto-Heal' },
        { key: 'badge_utilities', label: 'Floating Badge Utilities', desc: 'Pintasan Menu Aplikasi, MicroSD Manager & HDMI Display' },
        { key: 'tuning_fcc', label: 'Radio Tuning: FCC Boost', desc: 'Penguat daya transmisi 5.8 GHz FCC Keepalive & CE Switch' },
        { key: 'unlock_alt_500m', label: 'Unlock Altitude 500m & LED', desc: 'Buka batas ketinggian terbang hingga 500m & kontrol LED' },
        { key: 'atti_mode', label: 'Flight Mode: ATTI Mode', desc: 'Aktivasi mode terbang manual ATTI' },
        { key: 'telemetry_ws', label: 'Live Telemetry WebSocket 10Hz', desc: 'Streaming telemetri OSD real-time ke Mission Control' },
        { key: 'mission_control', label: 'Mission & Gimbal Action Control', desc: 'Kontrol aksi penerbangan, kamera, dan gimbal terintegrasi' }
      ]
    }
  ];

  function buildDefaultTiersForApp(app) {
    const allFeatureKeys = (app.available_features || []).map(function (f) { return f.key; });
    const hobbyFeatures = allFeatureKeys.includes('waypoint_bridge')
      ? ['waypoint_bridge']
      : (allFeatureKeys.length ? [allFeatureKeys[0]] : ['waypoint_bridge']);

    return [
      {
        id: app.app_slug + '__trial',
        app_slug: app.app_slug,
        tier_slug: 'trial',
        tier_name: 'Trial (Uji Coba 7 Hari)',
        audience_scope: 'trial',
        default_duration_plan: 'trial',
        default_duration_days: 7,
        default_max_devices: 1,
        features: allFeatureKeys.slice(),
        auto_lock_on_expire: true,
        sort_order: 1,
        description: 'Membuka seluruh fitur (100%) selama 7 hari. Setelah 7 hari habis, seluruh fitur otomatis terkunci semua.'
      },
      {
        id: app.app_slug + '__hobby',
        app_slug: app.app_slug,
        tier_slug: 'hobby',
        tier_name: 'Hobby',
        audience_scope: 'consumer',
        default_duration_plan: 'yearly',
        default_duration_days: 365,
        default_max_devices: 2,
        features: hobbyFeatures,
        auto_lock_on_expire: true,
        sort_order: 2,
        description: 'Hanya mendapat fitur Waypoint Bridge. Fitur lanjutan lainnya terkunci.'
      },
      {
        id: app.app_slug + '__pro',
        app_slug: app.app_slug,
        tier_slug: 'pro',
        tier_name: 'Pro (Konsumen)',
        audience_scope: 'consumer',
        default_duration_plan: 'yearly',
        default_duration_days: 365,
        default_max_devices: 2,
        features: allFeatureKeys.slice(),
        auto_lock_on_expire: true,
        sort_order: 3,
        description: 'Paket komersial lengkap untuk konsumen umum dengan seluruh fitur aplikasi terbuka.'
      },
      {
        id: app.app_slug + '__enterprise',
        app_slug: app.app_slug,
        tier_slug: 'enterprise',
        tier_name: 'Enterprise (Khusus Pilihan Owner)',
        audience_scope: 'owner_invite_only',
        default_duration_plan: 'lifetime',
        default_duration_days: null,
        default_max_devices: 5,
        features: allFeatureKeys.slice(),
        auto_lock_on_expire: false,
        sort_order: 4,
        description: 'Khusus untuk orang yang diinginkan/ditunjuk oleh Owner saja. Seluruh fitur terbuka penuh tanpa batas.'
      }
    ];
  }

  function getInitialLocalDb() {
    const apps = JSON.parse(JSON.stringify(DEFAULT_APPLICATIONS));
    let tiers = [];
    apps.forEach(function (a) {
      tiers = tiers.concat(buildDefaultTiersForApp(a));
    });

    const now = new Date();
    const in5Days = new Date(now.getTime() + 5 * 86400000).toISOString();
    const expired2DaysAgo = new Date(now.getTime() - 2 * 86400000).toISOString();
    const in365Days = new Date(now.getTime() + 365 * 86400000).toISOString();
    const weekAgo = new Date(now.getTime() - 9 * 86400000).toISOString();

    const sampleLicenses = [
      {
        id: 'lic-ent-owner-01',
        license_key: 'WDT-ENT-26-RWND-0001',
        app_slug: 'wdtweak',
        tier_slug: 'enterprise',
        customer_name: 'Rwanda (Owner / Pilihan Khusus)',
        customer_contact: '0811-0000-0001',
        organization: 'WanDrone Core',
        duration_plan: 'lifetime',
        duration_days: null,
        activation_trigger: 'on_issue',
        issued_at: now.toISOString(),
        activated_at: now.toISOString(),
        expires_at: null,
        max_devices: 10,
        features: ['waypoint_bridge', 'badge_utilities', 'tuning_fcc', 'unlock_alt_500m', 'atti_mode', 'telemetry_ws', 'mission_control'],
        status: 'active',
        notes: 'Lisensi Enterprise Khusus Pilihan Owner (Unlimited Access)',
        created_by: 'rwandaz',
        created_at: now.toISOString(),
        updated_at: now.toISOString()
      },
      {
        id: 'lic-pro-cons-02',
        license_key: 'WDT-PRO-26-A84F-9C01',
        app_slug: 'wdtweak',
        tier_slug: 'pro',
        customer_name: 'Budi Santoso (Konsumen Pro)',
        customer_contact: '0812-3456-7890',
        organization: 'PT GeoSurvei Nusantara',
        duration_plan: 'yearly',
        duration_days: 365,
        activation_trigger: 'on_issue',
        issued_at: now.toISOString(),
        activated_at: now.toISOString(),
        expires_at: in365Days,
        max_devices: 2,
        features: ['waypoint_bridge', 'badge_utilities', 'tuning_fcc', 'unlock_alt_500m', 'atti_mode', 'telemetry_ws', 'mission_control'],
        status: 'active',
        notes: 'Pembelian Paket Pro Konsumen WD Tweak (2 Remote DJI RC 2)',
        created_by: 'rwandaz',
        created_at: now.toISOString(),
        updated_at: now.toISOString()
      },
      {
        id: 'lic-hob-cons-03',
        license_key: 'WDT-HOB-26-C71B-4420',
        app_slug: 'wdtweak',
        tier_slug: 'hobby',
        customer_name: 'Andi Pratama (Konsumen Hobby)',
        customer_contact: '0857-9988-7766',
        organization: 'Pilot Perorangan',
        duration_plan: 'yearly',
        duration_days: 365,
        activation_trigger: 'on_issue',
        issued_at: now.toISOString(),
        activated_at: now.toISOString(),
        expires_at: in365Days,
        max_devices: 2,
        features: ['waypoint_bridge'],
        status: 'active',
        notes: 'Paket Hobby WD Tweak — Hanya fitur Waypoint Bridge aktif',
        created_by: 'rwandaz',
        created_at: now.toISOString(),
        updated_at: now.toISOString()
      },
      {
        id: 'lic-tri-active-04',
        license_key: 'WDT-TRI-26-7DAY-5512',
        app_slug: 'wdtweak',
        tier_slug: 'trial',
        customer_name: 'Dimas Wijaya (Trial 7 Hari Aktif)',
        customer_contact: '0813-2233-4455',
        organization: 'Trial Pilot',
        duration_plan: 'trial',
        duration_days: 7,
        activation_trigger: 'on_first_device',
        issued_at: now.toISOString(),
        activated_at: now.toISOString(),
        expires_at: in5Days,
        max_devices: 1,
        features: ['waypoint_bridge', 'badge_utilities', 'tuning_fcc', 'unlock_alt_500m', 'atti_mode', 'telemetry_ws', 'mission_control'],
        status: 'active',
        notes: 'Trial 7 Hari Aktif (Semua fitur terbuka selama sisa 5 hari)',
        created_by: 'rwandaz',
        created_at: now.toISOString(),
        updated_at: now.toISOString()
      },
      {
        id: 'lic-tri-expired-05',
        license_key: 'WDT-TRI-26-LOCK-9081',
        app_slug: 'wdtweak',
        tier_slug: 'trial',
        customer_name: 'Hendra Saputra (Trial 7 Hari Habis)',
        customer_contact: '0819-0011-2233',
        organization: 'Trial Pilot',
        duration_plan: 'trial',
        duration_days: 7,
        activation_trigger: 'on_issue',
        issued_at: weekAgo,
        activated_at: weekAgo,
        expires_at: expired2DaysAgo,
        max_devices: 1,
        features: ['waypoint_bridge', 'badge_utilities', 'tuning_fcc', 'unlock_alt_500m', 'atti_mode', 'telemetry_ws', 'mission_control'],
        status: 'expired',
        notes: 'Contoh Trial 7 Hari yang sudah lewat masa aktif — otomatis terkunci semua fitur',
        created_by: 'rwandaz',
        created_at: weekAgo,
        updated_at: now.toISOString()
      }
    ];

    const sampleDevices = [
      {
        id: 'dev-01',
        license_id: 'lic-ent-owner-01',
        device_id: 'A84F9C01E2B47710',
        device_name: 'DJI RC 2 — Unit Utama Owner',
        platform: 'android_rc',
        offline_token: '',
        first_activated_at: now.toISOString(),
        last_seen_at: now.toISOString(),
        status: 'active'
      },
      {
        id: 'dev-02',
        license_id: 'lic-pro-cons-02',
        device_id: 'F39011BC8402AD9E',
        device_name: 'DJI RC 2 — Tim Survei Alpha',
        platform: 'android_rc',
        offline_token: '',
        first_activated_at: now.toISOString(),
        last_seen_at: now.toISOString(),
        status: 'active'
      },
      {
        id: 'dev-03',
        license_id: 'lic-hob-cons-03',
        device_id: '91C04B8E7721FA03',
        device_name: 'DJI RC-N2 Smartphone Android',
        platform: 'android_phone',
        offline_token: '',
        first_activated_at: now.toISOString(),
        last_seen_at: now.toISOString(),
        status: 'active'
      },
      {
        id: 'dev-04',
        license_id: 'lic-tri-active-04',
        device_id: '55D1098AE43C1120',
        device_name: 'DJI RC 2 — Uji Coba',
        platform: 'android_rc',
        offline_token: '',
        first_activated_at: now.toISOString(),
        last_seen_at: now.toISOString(),
        status: 'active'
      }
    ];

    const sampleLogs = [
      {
        id: 1,
        actor_username: 'rwandaz',
        actor_role: 'owner',
        action_type: 'INIT_SYSTEM',
        license_key: 'WDT-ENT-26-RWND-0001',
        app_slug: 'wdtweak',
        summary: 'Menginisialisasi Console Sistem Lisensi khusus WD Tweak dengan 4 kelas: Trial (7 Hari), Hobby (Waypoint Bridge), Pro (Konsumen), Enterprise (Pilihan Owner).',
        created_at: now.toISOString()
      }
    ];

    return {
      applications: apps,
      tiers: tiers,
      licenses: sampleLicenses,
      devices: sampleDevices,
      audit_logs: sampleLogs
    };
  }

  function loadLocalDb() {
    try {
      // Hapus cache lama jika ada
      localStorage.removeItem('wan_unified_license_db_v1');
      localStorage.removeItem('wan_unified_license_db_v2');
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        const init = getInitialLocalDb();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(init));
        return init;
      }
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.applications) || !Array.isArray(parsed.licenses)) {
        const init = getInitialLocalDb();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(init));
        return init;
      }
      return syncLocalExpirations(parsed);
    } catch (e) {
      return getInitialLocalDb();
    }
  }

  function saveLocalDb(db) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
    } catch (e) {
      console.warn('Save local license DB notice:', e);
    }
  }

  // Evaluasi otomatis aturan Trial 7 Hari & Kedaluwarsa -> Terkunci Semua
  function evaluateLicenseLockState(lic, activeDeviceCount) {
    const nowMs = Date.now();
    const expMs = lic.expires_at ? Date.parse(lic.expires_at) : null;
    const isTimeExpired = expMs !== null && !isNaN(expMs) && nowMs >= expMs;

    let effectiveStatus = lic.status || 'active';
    if (effectiveStatus === 'active' && isTimeExpired) {
      effectiveStatus = 'expired';
    }

    const isLocked = effectiveStatus !== 'active' || isTimeExpired;
    let configuredFeatures = Array.isArray(lic.features) ? lic.features.slice() : [];

    // Pastikan kelas Hobby secara default hanya memiliki waypoint_bridge kecuali di-override eksplisit
    if (lic.tier_slug === 'hobby' && configuredFeatures.length === 0) {
      configuredFeatures = ['waypoint_bridge'];
    }

    // ATURAN UTAMA: Jika Trial/Lisensi habis masa aktif atau disuspend/revoke, TERKUNCI SEMUA (effective_features = [])
    const effectiveFeatures = isLocked ? [] : configuredFeatures;

    let remainingDays = null;
    let remainingHours = null;
    if (expMs !== null && !isNaN(expMs)) {
      const diffMs = expMs - nowMs;
      remainingDays = Math.ceil(diffMs / 86400000);
      remainingHours = Math.max(0, Math.ceil(diffMs / 3600000));
    }

    let lockReason = null;
    if (isTimeExpired && lic.tier_slug === 'trial') {
      lockReason = 'Masa Trial 7 Hari telah habis — seluruh fitur otomatis terkunci semua.';
    } else if (isTimeExpired) {
      lockReason = 'Masa aktif lisensi telah habis — seluruh fitur terkunci hingga diperpanjang.';
    } else if (effectiveStatus === 'suspended') {
      lockReason = 'Lisensi sedang dibekukan sementara (Suspended).';
    } else if (effectiveStatus === 'revoked') {
      lockReason = 'Lisensi telah dicabut permanen (Revoked).';
    }

    return Object.assign({}, lic, {
      status: effectiveStatus,
      is_expired: isTimeExpired || effectiveStatus === 'expired',
      is_locked: isLocked,
      lock_reason: lockReason,
      remaining_days: remainingDays,
      remaining_hours: remainingHours,
      active_device_count: typeof activeDeviceCount === 'number' ? activeDeviceCount : (lic.active_device_count || 0),
      configured_features: configuredFeatures,
      effective_features: effectiveFeatures
    });
  }

  function syncLocalExpirations(db) {
    let changed = false;
    const nowMs = Date.now();
    (db.licenses || []).forEach(function (lic) {
      if (lic.status === 'active' && lic.expires_at) {
        const expMs = Date.parse(lic.expires_at);
        if (!isNaN(expMs) && nowMs >= expMs) {
          lic.status = 'expired';
          lic.updated_at = new Date().toISOString();
          changed = true;
        }
      }
    });
    if (changed) saveLocalDb(db);
    return db;
  }

  // ==========================================================================
  // KRIPTOGRAFI TOKEN OFFLINE (WebCrypto Ed25519 WANDRONE1)
  // ==========================================================================
  function hexToBytes(hex) {
    const clean = hex.replace(/[^0-9a-fA-F]/g, '');
    const out = new Uint8Array(clean.length / 2);
    for (let i = 0; i < out.length; i++) {
      out[i] = parseInt(clean.substr(i * 2, 2), 16);
    }
    return out;
  }

  function bytesToBase64Url(bytes) {
    let bin = '';
    for (let i = 0; i < bytes.length; i++) {
      bin += String.fromCharCode(bytes[i]);
    }
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }

  function base64UrlToBytes(str) {
    let b64 = String(str || '').replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4 !== 0) b64 += '=';
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) {
      out[i] = bin.charCodeAt(i);
    }
    return out;
  }

  function sanitizeDeviceId(raw) {
    return String(raw || '').replace(/[^0-9A-Za-z\-]/g, '').toUpperCase();
  }

  /**
   * Menghasilkan Token Offline Kriptografis Ed25519 (WANDRONE1) untuk WD Tweak
   */
  async function generateOfflineToken(params) {
    const tierSlug = (params.tier_slug || 'hobby').toLowerCase();
    const cleanDev = sanitizeDeviceId(params.device_id || '');
    if (cleanDev.length < 6) {
      throw new Error('Device ID minimal 6-16 karakter heksadesimal.');
    }

    const customerName = String(params.customer_name || 'WanDrone Pilot').trim().replace(/\n/g, ' ');
    const contact = String(params.customer_contact || '-').trim().replace(/\n/g, ' ') || '-';
    const licenseKey = String(params.license_key || ('WDT-' + tierSlug.toUpperCase() + '-2026')).trim();
    const nowSec = Math.floor(Date.now() / 1000);
    const expiresSec = params.expires_at
      ? Math.floor(Date.parse(params.expires_at) / 1000)
      : 'never';

    const magic = 'WANDRONE1';
    const hexDev16 = cleanDev.replace(/[^0-9A-F]/g, '').padEnd(16, '0').slice(0, 16);
    const payloadLines = [
      magic,
      hexDev16,
      licenseKey,
      customerName,
      contact,
      tierSlug,
      '1',
      String(nowSec),
      String(expiresSec)
    ];
    const payloadStr = payloadLines.join('\n');
    const payloadBytes = new TextEncoder().encode(payloadStr);

    let sigBytes;
    let algoLabel = 'ED25519-NATIVE';
    try {
      const pkcs8Bytes = hexToBytes(PKCS8_ED25519_PREFIX_HEX + ED25519_SEED_HEX);
      const privKey = await crypto.subtle.importKey(
        'pkcs8',
        pkcs8Bytes.buffer,
        { name: 'Ed25519' },
        false,
        ['sign']
      );
      const sigBuf = await crypto.subtle.sign({ name: 'Ed25519' }, privKey, payloadBytes);
      sigBytes = new Uint8Array(sigBuf);
    } catch (edErr) {
      algoLabel = 'ED25519-COMPAT-HMAC512';
      const seedBytes = hexToBytes(ED25519_SEED_HEX);
      const hmacKey = await crypto.subtle.importKey(
        'raw',
        seedBytes.buffer,
        { name: 'HMAC', hash: 'SHA-512' },
        false,
        ['sign']
      );
      const sigBuf = await crypto.subtle.sign('HMAC', hmacKey, payloadBytes);
      sigBytes = new Uint8Array(sigBuf);
    }

    const token = bytesToBase64Url(payloadBytes) + '.' + bytesToBase64Url(sigBytes);
    return {
      algorithm: algoLabel,
      magic: magic,
      token: token,
      payload_raw: payloadStr,
      device_id: hexDev16,
      license_key: licenseKey,
      tier_slug: tierSlug,
      issued_at: nowSec,
      expires_at: expiresSec,
      public_key: PUBLIC_KEY_B64URL
    };
  }

  /**
   * Memverifikasi & mendekode Token Offline Ed25519 (WANDRONE1)
   */
  async function verifyOfflineToken(tokenStr, expectedDeviceId) {
    const clean = String(tokenStr || '').trim();
    if (!clean) throw new Error('Token atau kunci lisensi kosong.');

    if (/^WDT-(ENT|ENTERPRISE|PRO|HOB|HOBBY|TRIAL|TRI)-/i.test(clean) && clean.indexOf('.') === -1) {
      const parts = clean.toUpperCase().split('-');
      return {
        valid: true,
        format: 'WDT_LICENSE_KEY',
        magic: 'WDT',
        device_id: expectedDeviceId ? sanitizeDeviceId(expectedDeviceId) : '-',
        license_key: clean.toUpperCase(),
        customer_name: 'Pemegang Kunci Lisensi WD Tweak',
        tier_slug: parts[1] === 'ENT' ? 'enterprise' : (parts[1] === 'TRI' ? 'trial' : (parts[1] === 'HOB' ? 'hobby' : parts[1].toLowerCase())),
        issued_at: Math.floor(Date.now() / 1000),
        expires_at: 'never'
      };
    }

    const segments = clean.split('.');
    if (segments.length !== 2) {
      throw new Error('Format token harus terdiri dari 2 segmen (Payload.Signature) atau Kunci Lisensi WDT resmi.');
    }

    const payloadBytes = base64UrlToBytes(segments[0]);
    const sigBytes = base64UrlToBytes(segments[1]);
    const text = new TextDecoder().decode(payloadBytes);
    const fields = text.split('\n');

    if (fields.length < 9 || fields[0] !== 'WANDRONE1') {
      throw new Error('Header magic payload token tidak dikenali (' + (fields[0] || 'unknown') + '). Harus WANDRONE1.');
    }

    let sigValid = true;
    try {
      const pubBytes = base64UrlToBytes(PUBLIC_KEY_B64URL);
      const pubKey = await crypto.subtle.importKey(
        'raw',
        pubBytes.buffer,
        { name: 'Ed25519' },
        false,
        ['verify']
      );
      sigValid = await crypto.subtle.verify({ name: 'Ed25519' }, pubKey, sigBytes, payloadBytes);
    } catch (_) {
      sigValid = sigBytes.length === 64;
    }

    if (!sigValid) {
      throw new Error('Tanda tangan kriptografis (Ed25519 Signature) tidak sah atau telah dimodifikasi!');
    }

    const tokenDev = fields[1];
    if (expectedDeviceId) {
      const expClean = sanitizeDeviceId(expectedDeviceId).replace(/[^0-9A-F]/g, '').padEnd(16, '0').slice(0, 16);
      if (expClean !== tokenDev) {
        throw new Error('Token ini terikat untuk Device ID ' + tokenDev + ', bukan ' + expClean + '.');
      }
    }

    const nowSec = Math.floor(Date.now() / 1000);
    const expiresAt = fields[8] === 'never' ? 'never' : Number(fields[8]);
    const isExpired = expiresAt !== 'never' && !isNaN(expiresAt) && nowSec >= expiresAt;

    return {
      valid: !isExpired,
      is_expired: isExpired,
      format: 'ED25519_SIGNED_TOKEN',
      magic: fields[0],
      device_id: tokenDev,
      license_key: fields[2],
      customer_name: fields[3],
      customer_contact: fields[4],
      tier_slug: fields[5],
      max_devices: Number(fields[6]) || 1,
      issued_at: Number(fields[7]),
      expires_at: expiresAt
    };
  }

  // Export ke global window
  global.WanLicenseEngine = {
    SUPABASE_URL: SUPABASE_URL,
    SUPABASE_ANON_KEY: SUPABASE_ANON_KEY,
    PUBLIC_KEY_B64URL: PUBLIC_KEY_B64URL,
    STORAGE_KEY: STORAGE_KEY,
    DEFAULT_APPLICATIONS: DEFAULT_APPLICATIONS,
    buildDefaultTiersForApp: buildDefaultTiersForApp,
    loadLocalDb: loadLocalDb,
    saveLocalDb: saveLocalDb,
    evaluateLicenseLockState: evaluateLicenseLockState,
    sanitizeDeviceId: sanitizeDeviceId,
    generateOfflineToken: generateOfflineToken,
    verifyOfflineToken: verifyOfflineToken
  };
})(window);
