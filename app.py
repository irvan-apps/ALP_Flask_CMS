import os
import json
import uuid
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory
)
import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'alp_secret_key_super_secure_2026')

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database tables and seed data
db.init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if file and file.filename and allowed_file(file.filename):
        orig_name = secure_filename(file.filename)
        ext = orig_name.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)
        return f"/static/uploads/{unique_name}"
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan masuk (login) terlebih dahulu.', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for templates
@app.context_processor
def inject_global_data():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    
    unread_count = 0
    if 'user_id' in session:
        cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = 0")
        unread_count = cursor.fetchone()[0]
    conn.close()
    return {
        'settings': settings,
        'unread_messages_count': unread_count,
        'current_year': datetime.now().year
    }

# ==========================================
# PUBLIC FRONTEND ROUTES
# ==========================================
@app.route('/zohoverify/verifyforzoho.html')
def zoho_verify():
    return "58200609"


@app.route('/')
def index():
    conn = db.get_db()
    cursor = conn.cursor()

    # Settings
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}

    # Services
    cursor.execute("SELECT * FROM services ORDER BY sort_order ASC, id ASC")
    services_raw = cursor.fetchall()
    services = []
    for s in services_raw:
        item = dict(s)
        try:
            item['features_list'] = json.loads(s['features']) if s['features'] else []
        except Exception:
            item['features_list'] = [f.strip() for f in (s['features'] or '').split('\n') if f.strip()]
        services.append(item)

    # Projects
    cursor.execute("SELECT * FROM projects ORDER BY sort_order ASC, id DESC")
    projects = cursor.fetchall()

    # Team Members (only visible ones for public)
    cursor.execute("SELECT * FROM team_members WHERE is_visible = 1 ORDER BY sort_order ASC, id ASC")
    team_members = cursor.fetchall()

    # Legalities
    cursor.execute("SELECT * FROM legalities ORDER BY sort_order ASC, id ASC")
    legalities = cursor.fetchall()

    # Clients
    cursor.execute("SELECT * FROM clients ORDER BY sort_order ASC, id ASC")
    clients = cursor.fetchall()

    conn.close()
    return render_template(
        'index.html',
        settings=settings,
        services=services,
        projects=projects,
        team_members=team_members,
        legalities=legalities,
        clients=clients
    )

@app.route('/contact', methods=['POST'])
def contact_submit():
    # Handle AJAX or standard POST
    nama = request.form.get('nama', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    pesan = request.form.get('pesan', '').strip()

    if not nama or not email or not pesan:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'status': 'error', 'message': 'Mohon isi semua kolom yang diperlukan.'}), 400
        flash('Mohon lengkapi formulir kontak.', 'error')
        return redirect(url_for('index', _anchor='kontak'))

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (name, email, phone, message)
        VALUES (?, ?, ?, ?)
    ''', (nama, email, phone, pesan))
    conn.commit()
    conn.close()

    success_msg = f"Terima kasih {nama}, pesan Anda telah berhasil dikirimkan kepada Tim PT Arunika Loise Persada. Kami akan segera menghubungi Anda."

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'status': 'success', 'message': success_msg})

    flash(success_msg, 'success')
    return redirect(url_for('index', _anchor='kontak'))

# ==========================================
# ADMIN AUTH ROUTES
# ==========================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_name'] = user['name'] or user['username']
            flash(f"Selamat datang kembali, {session['user_name']}!", 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('Username atau kata sandi tidak sesuai.', 'error')

    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Anda telah keluar dari dashboard CMS.', 'info')
    return redirect(url_for('admin_login'))

# ==========================================
# ADMIN DASHBOARD & SETTINGS
# ==========================================

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = db.get_db()
    cursor = conn.cursor()

    stats = {
        'services': cursor.execute("SELECT COUNT(*) FROM services").fetchone()[0],
        'projects': cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
        'team': cursor.execute("SELECT COUNT(*) FROM team_members").fetchone()[0],
        'legalities': cursor.execute("SELECT COUNT(*) FROM legalities").fetchone()[0],
        'clients': cursor.execute("SELECT COUNT(*) FROM clients").fetchone()[0],
        'messages_total': cursor.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'messages_unread': cursor.execute("SELECT COUNT(*) FROM messages WHERE is_read = 0").fetchone()[0],
    }

    cursor.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 5")
    recent_messages = cursor.fetchall()

    cursor.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 4")
    recent_projects = cursor.fetchall()

    conn.close()
    return render_template('admin/dashboard.html', stats=stats, recent_messages=recent_messages, recent_projects=recent_projects)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    conn = db.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Handle about image upload if provided
        uploaded_image = save_uploaded_file(request.files.get('about_image_file'))
        
        for key in request.form:
            val = request.form.get(key)
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))

        if uploaded_image:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('about_image', uploaded_image))

        conn.commit()
        conn.close()
        flash('Pengaturan website berhasil diperbarui.', 'success')
        return redirect(url_for('admin_settings'))

    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return render_template('admin/settings.html', settings=settings)

# ==========================================
# ADMIN SERVICES CRUD
# ==========================================

@app.route('/admin/services')
@login_required
def admin_services():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services ORDER BY sort_order ASC, id ASC")
    services = cursor.fetchall()
    conn.close()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/new', methods=['GET', 'POST'])
@login_required
def admin_service_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        code = request.form.get('code', '').strip()
        icon = request.form.get('icon', 'fa-helmet-safety').strip()
        badge_color = request.form.get('badge_color', 'brand-orange').strip()
        description = request.form.get('description', '').strip()
        sort_order = int(request.form.get('sort_order', 0) or 0)
        
        features_raw = request.form.get('features', '').strip()
        features_list = [f.strip() for f in features_raw.split('\n') if f.strip()]
        features_json = json.dumps(features_list)

        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO services (title, code, icon, badge_color, description, features, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, code, icon, badge_color, description, features_json, sort_order))
        conn.commit()
        conn.close()

        flash(f'Layanan "{title}" berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_services'))

    return render_template('admin/service_form.html', service=None, features_text='')

@app.route('/admin/services/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_service_edit(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE id = ?", (id,))
    service = cursor.fetchone()

    if not service:
        conn.close()
        flash('Layanan tidak ditemukan.', 'error')
        return redirect(url_for('admin_services'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        code = request.form.get('code', '').strip()
        icon = request.form.get('icon', '').strip()
        badge_color = request.form.get('badge_color', 'brand-orange').strip()
        description = request.form.get('description', '').strip()
        sort_order = int(request.form.get('sort_order', 0) or 0)
        
        features_raw = request.form.get('features', '').strip()
        features_list = [f.strip() for f in features_raw.split('\n') if f.strip()]
        features_json = json.dumps(features_list)

        cursor.execute('''
            UPDATE services
            SET title = ?, code = ?, icon = ?, badge_color = ?, description = ?, features = ?, sort_order = ?
            WHERE id = ?
        ''', (title, code, icon, badge_color, description, features_json, sort_order, id))
        conn.commit()
        conn.close()

        flash(f'Layanan "{title}" berhasil diperbarui!', 'success')
        return redirect(url_for('admin_services'))

    features_text = ""
    if service['features']:
        try:
            features_text = "\n".join(json.loads(service['features']))
        except Exception:
            features_text = service['features']

    conn.close()
    return render_template('admin/service_form.html', service=service, features_text=features_text)

@app.route('/admin/services/delete/<int:id>', methods=['POST'])
@login_required
def admin_service_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Layanan berhasil dihapus.', 'success')
    return redirect(url_for('admin_services'))

# ==========================================
# ADMIN PROJECTS CRUD
# ==========================================

@app.route('/admin/projects')
@login_required
def admin_projects():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY sort_order ASC, id DESC")
    projects = cursor.fetchall()
    conn.close()
    return render_template('admin/projects.html', projects=projects)

@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        client_tag = request.form.get('client_tag', 'PT Arunika Loise Persada').strip()
        image_url = request.form.get('image_url', '').strip()
        sort_order = int(request.form.get('sort_order', 0) or 0)
        is_featured = 1 if request.form.get('is_featured') else 0

        # Check for uploaded file
        uploaded_file = save_uploaded_file(request.files.get('image_file'))
        if uploaded_file:
            image_url = uploaded_file

        if not image_url:
            image_url = 'https://images.unsplash.com/photo-1541888946425-d0fbb18f764a?auto=format&fit=crop&w=800&q=80'

        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (title, category, description, image_url, client_tag, is_featured, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, description, image_url, client_tag, is_featured, sort_order))
        conn.commit()
        conn.close()

        flash(f'Proyek "{title}" berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_projects'))

    return render_template('admin/project_form.html', project=None)

@app.route('/admin/projects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_project_edit(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (id,))
    project = cursor.fetchone()

    if not project:
        conn.close()
        flash('Proyek tidak ditemukan.', 'error')
        return redirect(url_for('admin_projects'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        client_tag = request.form.get('client_tag', 'PT Arunika Loise Persada').strip()
        image_url = request.form.get('image_url', '').strip()
        sort_order = int(request.form.get('sort_order', 0) or 0)
        is_featured = 1 if request.form.get('is_featured') else 0

        uploaded_file = save_uploaded_file(request.files.get('image_file'))
        if uploaded_file:
            image_url = uploaded_file
        elif not image_url:
            image_url = project['image_url']

        cursor.execute('''
            UPDATE projects
            SET title = ?, category = ?, description = ?, image_url = ?, client_tag = ?, is_featured = ?, sort_order = ?
            WHERE id = ?
        ''', (title, category, description, image_url, client_tag, is_featured, sort_order, id))
        conn.commit()
        conn.close()

        flash(f'Proyek "{title}" berhasil diperbarui!', 'success')
        return redirect(url_for('admin_projects'))

    conn.close()
    return render_template('admin/project_form.html', project=project)

@app.route('/admin/projects/delete/<int:id>', methods=['POST'])
@login_required
def admin_project_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Proyek berhasil dihapus.', 'success')
    return redirect(url_for('admin_projects'))

# ==========================================
# ADMIN STRUKTUR ORGANISASI / TEAM CRUD
# ==========================================

@app.route('/admin/organization')
@login_required
def admin_organization():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_members ORDER BY sort_order ASC, id ASC")
    members = cursor.fetchall()
    cursor.execute("SELECT value FROM settings WHERE key = 'show_organization'")
    row = cursor.fetchone()
    show_org = row['value'] if row else '1'
    conn.close()
    return render_template('admin/organization.html', members=members, show_organization=show_org)

@app.route('/admin/organization/toggle-section', methods=['POST'])
@login_required
def admin_organization_toggle_section():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'show_organization'")
    row = cursor.fetchone()
    current_val = row['value'] if row else '1'
    new_val = '0' if current_val == '1' else '1'
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('show_organization', ?)", (new_val,))
    conn.commit()
    conn.close()
    status_text = "Ditampilkan (Unhide)" if new_val == '1' else "Disembunyikan (Hide)"
    flash(f"Bagian Tenaga Ahli / Struktur Organisasi di Landing Page sekarang: {status_text}", "success")
    return redirect(url_for('admin_organization'))

@app.route('/admin/organization/toggle-visibility/<int:id>', methods=['POST'])
@login_required
def admin_organization_toggle_visibility(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, is_visible FROM team_members WHERE id = ?", (id,))
    member = cursor.fetchone()
    if member:
        new_vis = 0 if member['is_visible'] == 1 else 1
        cursor.execute("UPDATE team_members SET is_visible = ? WHERE id = ?", (new_vis, id))
        conn.commit()
        status_text = "Ditampilkan di landing page" if new_vis == 1 else "Disembunyikan dari landing page"
        flash(f'Status Tenaga Ahli "{member["name"]}" diubah menjadi: {status_text}.', 'success')
    conn.close()
    return redirect(url_for('admin_organization'))

@app.route('/admin/organization/new', methods=['POST'])
@login_required
def admin_organization_new():
    name = request.form.get('name', '').strip()
    role = request.form.get('role', '').strip()
    department = request.form.get('department', '').strip()
    bio = request.form.get('bio', '').strip()
    photo_url = request.form.get('photo_url', '').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)
    is_visible = 1 if request.form.get('is_visible') else 0

    uploaded_file = save_uploaded_file(request.files.get('photo_file'))
    if uploaded_file:
        photo_url = uploaded_file
    elif not photo_url:
        photo_url = 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80'

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO team_members (name, role, department, photo_url, bio, sort_order, is_visible)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, role, department, photo_url, bio, sort_order, is_visible))
    conn.commit()
    conn.close()

    flash(f'Anggota struktur "{name}" berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_organization'))

@app.route('/admin/organization/edit/<int:id>', methods=['POST'])
@login_required
def admin_organization_edit(id):
    name = request.form.get('name', '').strip()
    role = request.form.get('role', '').strip()
    department = request.form.get('department', '').strip()
    bio = request.form.get('bio', '').strip()
    photo_url = request.form.get('photo_url', '').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)
    is_visible = 1 if request.form.get('is_visible') else 0

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM team_members WHERE id = ?", (id,))
    member = cursor.fetchone()

    if not member:
        conn.close()
        flash('Data anggota tidak ditemukan.', 'error')
        return redirect(url_for('admin_organization'))

    uploaded_file = save_uploaded_file(request.files.get('photo_file'))
    if uploaded_file:
        photo_url = uploaded_file
    elif not photo_url:
        photo_url = member['photo_url']

    cursor.execute('''
        UPDATE team_members
        SET name = ?, role = ?, department = ?, photo_url = ?, bio = ?, sort_order = ?, is_visible = ?
        WHERE id = ?
    ''', (name, role, department, photo_url, bio, sort_order, is_visible, id))
    conn.commit()
    conn.close()

    flash(f'Data "{name}" berhasil diperbarui!', 'success')
    return redirect(url_for('admin_organization'))

@app.route('/admin/organization/delete/<int:id>', methods=['POST'])
@login_required
def admin_organization_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM team_members WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Data anggota struktur berhasil dihapus.', 'success')
    return redirect(url_for('admin_organization'))

# ==========================================
# ADMIN LEGALITAS CRUD
# ==========================================

@app.route('/admin/legality')
@login_required
def admin_legality():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM legalities ORDER BY sort_order ASC, id ASC")
    legalities = cursor.fetchall()
    conn.close()
    return render_template('admin/legality.html', legalities=legalities)

@app.route('/admin/legality/new', methods=['POST'])
@login_required
def admin_legality_new():
    title = request.form.get('title', '').strip()
    doc_number = request.form.get('doc_number', '').strip()
    issuer = request.form.get('issuer', '').strip()
    year = request.form.get('year', '').strip()
    badge_text = request.form.get('badge_text', 'Terverifikasi').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO legalities (title, doc_number, issuer, year, badge_text, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, doc_number, issuer, year, badge_text, sort_order))
    conn.commit()
    conn.close()

    flash(f'Legalitas "{title}" berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_legality'))

@app.route('/admin/legality/edit/<int:id>', methods=['POST'])
@login_required
def admin_legality_edit(id):
    title = request.form.get('title', '').strip()
    doc_number = request.form.get('doc_number', '').strip()
    issuer = request.form.get('issuer', '').strip()
    year = request.form.get('year', '').strip()
    badge_text = request.form.get('badge_text', '').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE legalities
        SET title = ?, doc_number = ?, issuer = ?, year = ?, badge_text = ?, sort_order = ?
        WHERE id = ?
    ''', (title, doc_number, issuer, year, badge_text, sort_order, id))
    conn.commit()
    conn.close()

    flash(f'Legalitas "{title}" berhasil diperbarui!', 'success')
    return redirect(url_for('admin_legality'))

@app.route('/admin/legality/delete/<int:id>', methods=['POST'])
@login_required
def admin_legality_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM legalities WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Dokumen legalitas berhasil dihapus.', 'success')
    return redirect(url_for('admin_legality'))

# ==========================================
# ADMIN CLIENTS CRUD
# ==========================================

@app.route('/admin/clients')
@login_required
def admin_clients():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY sort_order ASC, id ASC")
    clients = cursor.fetchall()
    conn.close()
    return render_template('admin/clients.html', clients=clients)

@app.route('/admin/clients/new', methods=['POST'])
@login_required
def admin_client_new():
    name = request.form.get('name', '').strip()
    subtitle = request.form.get('subtitle', '').strip()
    icon = request.form.get('icon', 'fa-building').strip()
    color_accent = request.form.get('color_accent', 'brand-orange').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clients (name, subtitle, icon, color_accent, sort_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, subtitle, icon, color_accent, sort_order))
    conn.commit()
    conn.close()

    flash(f'Mitra / Klien "{name}" berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_clients'))

@app.route('/admin/clients/edit/<int:id>', methods=['POST'])
@login_required
def admin_client_edit(id):
    name = request.form.get('name', '').strip()
    subtitle = request.form.get('subtitle', '').strip()
    icon = request.form.get('icon', 'fa-building').strip()
    color_accent = request.form.get('color_accent', 'brand-orange').strip()
    sort_order = int(request.form.get('sort_order', 0) or 0)

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clients
        SET name = ?, subtitle = ?, icon = ?, color_accent = ?, sort_order = ?
        WHERE id = ?
    ''', (name, subtitle, icon, color_accent, sort_order, id))
    conn.commit()
    conn.close()

    flash(f'Mitra / Klien "{name}" berhasil diperbarui!', 'success')
    return redirect(url_for('admin_clients'))

@app.route('/admin/clients/delete/<int:id>', methods=['POST'])
@login_required
def admin_client_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Mitra / Klien berhasil dihapus.', 'success')
    return redirect(url_for('admin_clients'))

# ==========================================
# ADMIN INBOX / MESSAGES
# ==========================================

@app.route('/admin/messages')
@login_required
def admin_messages():
    filter_read = request.args.get('filter')
    conn = db.get_db()
    cursor = conn.cursor()

    if filter_read == 'unread':
        cursor.execute("SELECT * FROM messages WHERE is_read = 0 ORDER BY id DESC")
    elif filter_read == 'read':
        cursor.execute("SELECT * FROM messages WHERE is_read = 1 ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM messages ORDER BY id DESC")

    messages = cursor.fetchall()
    conn.close()
    return render_template('admin/messages.html', messages=messages, current_filter=filter_read)

@app.route('/admin/messages/read/<int:id>')
@login_required
def admin_message_mark_read(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Pesan ditandai sebagai telah dibaca.', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/unread/<int:id>')
@login_required
def admin_message_mark_unread(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET is_read = 0 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Pesan ditandai sebagai belum dibaca.', 'info')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/delete/<int:id>', methods=['POST'])
@login_required
def admin_message_delete(id):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Pesan berhasil dihapus.', 'success')
    return redirect(url_for('admin_messages'))

# ==========================================
# ADMIN PROFILE & PASSWORD CHANGE
# ==========================================

@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic profile update
        cursor.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user['id']))
        session['user_name'] = name

        # Password update if requested
        if new_password:
            if not check_password_hash(user['password_hash'], current_password):
                conn.close()
                flash('Kata sandi saat ini salah.', 'error')
                return redirect(url_for('admin_profile'))

            if new_password != confirm_password:
                conn.close()
                flash('Konfirmasi kata sandi baru tidak cocok.', 'error')
                return redirect(url_for('admin_profile'))

            if len(new_password) < 6:
                conn.close()
                flash('Kata sandi baru minimal 6 karakter.', 'error')
                return redirect(url_for('admin_profile'))

            new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
            flash('Kata sandi Anda berhasil diperbarui!', 'success')

        conn.commit()
        conn.close()
        flash('Profil administrator berhasil diperbarui.', 'success')
        return redirect(url_for('admin_profile'))

    conn.close()
    return render_template('admin/profile.html', user=user)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"[*] PT Arunika Loise Persada CMS running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
