import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'alp_cms.db')

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # General Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Services Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            code TEXT,
            icon TEXT,
            badge_color TEXT DEFAULT 'brand-orange',
            description TEXT,
            features TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # Projects Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            description TEXT,
            image_url TEXT,
            client_tag TEXT DEFAULT 'PT Arunika Loise Persada',
            is_featured INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Team Members / Organizational Structure Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            photo_url TEXT,
            bio TEXT,
            sort_order INTEGER DEFAULT 0,
            is_visible INTEGER DEFAULT 1
        )
    ''')

    # Migration: ensure is_visible exists in team_members
    cursor.execute("PRAGMA table_info(team_members)")
    tm_cols = [row[1] for row in cursor.fetchall()]
    if 'is_visible' not in tm_cols:
        cursor.execute("ALTER TABLE team_members ADD COLUMN is_visible INTEGER DEFAULT 1")

    # Legalities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS legalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            doc_number TEXT NOT NULL,
            issuer TEXT,
            year TEXT,
            badge_text TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # Clients / Business Partners Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subtitle TEXT,
            icon TEXT,
            color_accent TEXT,
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # Messages / Inquiries Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Seed initial data if empty
    seed_data(cursor)
    conn.commit()
    conn.close()

def seed_data(cursor):
    # 1. Admin User
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, email)
            VALUES (?, ?, ?, ?)
        ''', (
            'admin',
            generate_password_hash('admin123', method='pbkdf2:sha256'),
            'Administrator ALP',
            'admin@arunikapersada.co.id'
        ))

    # 2. Settings
    default_settings = {
        'company_name': 'PT ARUNIKA LOISE PERSADA',
        'company_short': 'ALP',
        'company_tagline': 'Civil Engineering & M&E',
        'hero_badge': 'General Contractor & Mechanical Electrical',
        'hero_title_prefix': 'Mewujudkan Karya Konstruksi yang',
        'hero_title_highlight': 'Lebih Nyata',
        'hero_description': 'PT Arunika Loise Persada (ALP) hadir sejak 2022 sebagai mitra terpercaya dalam bidang jasa konstruksi sipil, gedung, infrastruktur, serta mechanical & electrical dengan dukungan SDM berpengalaman lebih dari 20 tahun.',
        'hero_stat_1_num': '20+',
        'hero_stat_1_label': 'Tahun Pengalaman SDM',
        'hero_stat_2_num': '2022',
        'hero_stat_2_label': 'Tahun Berdiri',
        'hero_stat_3_num': '100%',
        'hero_stat_3_label': 'Komitmen Mutu',
        'about_tag': 'Tentang Kami',
        'about_heading': 'Membangun Kepercayaan Melalui Mutu dan Keandalan Nyata',
        'about_p1': 'PT Arunika Loise Persada (ALP) didirikan pada tahun 2022 sebagai perusahaan nasional yang bergerak di bidang jasa Konstruksi, Mechanical, dan Electrical. Kami berkomitmen untuk memberikan solusi konstruksi yang komprehensif, efisien, dan berstandar tinggi.',
        'about_p2': 'Didukung oleh Sumber Daya Manusia (SDM) yang sudah berpengalaman lebih dari 20 Tahun di bidangnya masing-masing, PT Arunika Loise Persada berkomitmen penuh kepada para pelanggan untuk selalu menghadirkan pelayanan jasa konstruksi terbaik dalam menciptakan karya konstruksi yang lebih nyata.',
        'about_image': 'https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=1000&q=80',
        'about_badge_year': 'Sejak 2022',
        'about_badge_title': 'Profesional & Berpengalaman',
        'vision_text': '"Menjadi perusahaan konstruksi terbaik yang berfokus pada perkembangan teknologi konstruksi, sumber daya manusia dan tata kelola perusahaan yang baik."',
        'mission_1': 'Meningkatkan Daya Saing Perusahaan di Industri Jasa Konstruksi.',
        'mission_2': 'Meningkatkan Kualitas SDM untuk menghasilkan Tenaga Kerja yang berkualitas tinggi.',
        'company_address': 'Medang Lestari Blok C-IV/A22 Pagedangan, Kabupaten Tangerang, Banten - 15334',
        'company_website': 'www.arunikapersada.co.id',
        'company_email': 'info@arunikapersada.co.id',
        'company_phone': '+62 812-9876-5432',
        'company_whatsapp': '6281298765432',
        'show_organization': '1',
        'copyright_text': '2026 PT Arunika Loise Persada. All Rights Reserved.'
    }

    for key, val in default_settings.items():
        cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))

    # 3. Services
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        services_data = [
            (
                'Civil & Construction',
                '01',
                'fa-helmet-safety',
                'brand-orange',
                'Meliputi pembangunan konstruksi sipil, perencanaan tata letak, dan design arsitektural maupun struktural.',
                json.dumps([
                    'Gedung Bertingkat & Komersial',
                    'Perumahan / Residential',
                    'Real Estate Development',
                    'Irigasi & Saluran Air',
                    'Jembatan & Infrastruktur'
                ]),
                1
            ),
            (
                'Mechanical & Electrical',
                '02',
                'fa-bolt',
                'amber-500',
                'Pengerjaan segala kebutuhan sistem kelistrikan, mekanikal, dan commissioning dengan standar industri terkini.',
                json.dumps([
                    'Instalasi Listrik & Power',
                    'Penarikan Kabel (Cable Pulling)',
                    'Pemasangan Panel Listrik',
                    'Pemasangan Genset & Backup Power',
                    'Testing & Commissioning'
                ]),
                2
            )
        ]
        cursor.executemany('''
            INSERT INTO services (title, code, icon, badge_color, description, features, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', services_data)

    # 4. Projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        projects_data = [
            (
                'Instalasi Kabel Power',
                'M&E',
                'Pemasangan jalur kabel tegangan menengah dan rendah dengan standar keselamatan tinggi.',
                'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80',
                'PT Arunika Loise Persada',
                1,
                1
            ),
            (
                'Rebar Scan Retaining Wall',
                'Civil Test',
                'Pengujian non-destruktif struktur dinding penahan tanah menggunakan teknologi pemindaian baja tulangan.',
                'https://images.unsplash.com/photo-1581094288338-2314dddb7ece?auto=format&fit=crop&w=800&q=80',
                'PT Arunika Loise Persada',
                1,
                2
            ),
            (
                'Instalasi Panel Listrik',
                'Electrical',
                'Perakitan dan pemasangan panel distribusi utama untuk gedung komersial dan industri.',
                'https://images.unsplash.com/photo-1590069261209-f8e9b8642343?auto=format&fit=crop&w=800&q=80',
                'PT Arunika Loise Persada',
                1,
                3
            ),
            (
                'Instalasi Genset',
                'Mechanical',
                'Pemasangan unit generator set lengkap dengan sistem bahan bakar dan peredam suara.',
                'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?auto=format&fit=crop&w=800&q=80',
                'PT Arunika Loise Persada',
                1,
                4
            ),
            (
                'Pekerjaan Sipil & Infrastruktur',
                'Civil Construction',
                'Pembangunan infrastruktur umum, perbaikan jalan kawasan, drainase, serta struktur beton bertulang dengan pengawasan mutu ketat.',
                'https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?auto=format&fit=crop&w=1200&q=80',
                'PT Arunika Loise Persada',
                1,
                5
            )
        ]
        cursor.executemany('''
            INSERT INTO projects (title, category, description, image_url, client_tag, is_featured, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', projects_data)

    # 5. Team Members / Struktur Organisasi
    cursor.execute("SELECT COUNT(*) FROM team_members")
    if cursor.fetchone()[0] == 0:
        team_data = [
            (
                'Direktur Utama',
                'Dewan Direksi & Kepemimpinan Utama',
                'Manajemen Eksekutif',
                'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80',
                'Memimpin visi strategis, tata kelola perusahaan, dan ekspansi kemitraan industri.',
                1
            ),
            (
                'Direktur Operasional',
                'Pengawasan Operasional & Teknis',
                'Operasional Lapangan',
                'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80',
                'Mengawasi seluruh tahapan eksekusi proyek sipil serta kelistrikan tepat mutu dan tepat waktu.',
                2
            ),
            (
                'Project Manager Civil',
                'Kepala Divisi Konstruksi Sipil',
                'Divisi Sipil',
                'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=600&q=80',
                'Berpengalaman 15+ tahun dalam supervisi gedung komersial, struktur beton, dan infrastruktur.',
                3
            ),
            (
                'Project Manager M&E',
                'Kepala Divisi Mechanical & Electrical',
                'Divisi M&E',
                'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=600&q=80',
                'Ahli dalam instalasi tegangan menengah, distribusi daya panel, genset, dan testing commissioning.',
                4
            ),
            (
                'Manager K3 & Mutu (QA/QC)',
                'Keselamatan Kerja & Pengendalian Kualitas',
                'HSE & Quality',
                'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80',
                'Menjamin standar keselamatan kerja tanpa kompromi (Zero Accident) dan kepatuhan standar mutu ISO/LPJK.',
                5
            )
        ]
        cursor.executemany('''
            INSERT INTO team_members (name, role, department, photo_url, bio, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', team_data)

    # 6. Legalities
    cursor.execute("SELECT COUNT(*) FROM legalities")
    if cursor.fetchone()[0] == 0:
        legal_data = [
            (
                'Nomor Induk Berusaha (NIB)',
                '2408220012345',
                'Kementerian Investasi / BKPM RI',
                '2022',
                'Terverifikasi OSS-RBA',
                1
            ),
            (
                'Sertifikat Standar Usaha Jasa Konstruksi',
                '0220201234567-LPJK',
                'Lembaga Pengembangan Jasa Konstruksi (LPJK)',
                '2022',
                'Klasifikasi Lengkap',
                2
            ),
            (
                'KBLI Konstruksi & Instalasi Elektrikal',
                'KBLI 41011, 43211, 42101',
                'DPMPTSP / Kementerian Teknis',
                '2022',
                'Aktif & Terdaftar',
                3
            ),
            (
                'Pengesahan Akta Pendirian Menkumham',
                'AHU-0045231.AH.01.01.TAHUN 2022',
                'Kemenkumham Republik Indonesia',
                '2022',
                'Badan Hukum PT Resmi',
                4
            ),
            (
                'NPWP Badan Usaha',
                '61.234.567.8-418.000',
                'Direktorat Jenderal Pajak (KPP Pratama Tigaraksa)',
                '2022',
                'Wajib Pajak Patuh',
                5
            )
        ]
        cursor.executemany('''
            INSERT INTO legalities (title, doc_number, issuer, year, badge_text, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', legal_data)

    # 7. Clients
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        clients_data = [
            ('JASAMARGA', 'Client Partner', 'fa-road', 'brand-orange', 1),
            ('Schneider Electric', 'Life Is On • Related Business', 'fa-bolt', 'amber-400', 2)
        ]
        cursor.executemany('''
            INSERT INTO clients (name, subtitle, icon, color_accent, sort_order)
            VALUES (?, ?, ?, ?, ?)
        ''', clients_data)

def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}
