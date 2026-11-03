import os, sqlite3, secrets, requests
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

load_dotenv()
app = Flask(__name__)
CSRFProtect(app)
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true', MAX_CONTENT_LENGTH=1024*1024)
DB = os.getenv('DATABASE_PATH', 'applications.db')
ORG_NAME = os.getenv('ORG_NAME', 'FACTION RECRUITMENT')
ORG_SUBTITLE = os.getenv('ORG_SUBTITLE', '함께할 새로운 인재를 모집합니다.')
WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')
ADMIN_USER = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_HASH = os.getenv('ADMIN_PASSWORD_HASH', '')


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            rp_name TEXT NOT NULL, discord TEXT NOT NULL, age TEXT NOT NULL,
            playtime TEXT NOT NULL, experience TEXT NOT NULL, motivation TEXT NOT NULL,
            strengths TEXT NOT NULL, status TEXT NOT NULL DEFAULT '심사 대기', admin_note TEXT DEFAULT ''
        )''')


def notify_discord(title, description, color=0xC9A44C):
    if not WEBHOOK: return
    try:
        requests.post(WEBHOOK, json={'embeds':[{'title':title,'description':description[:4000], 'color':color, 'footer':{'text':ORG_NAME}, 'timestamp':datetime.utcnow().isoformat()}]}, timeout=5)
    except requests.RequestException:
        app.logger.exception('Discord webhook delivery failed')


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin'): return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_brand():
    return {'org_name':ORG_NAME, 'org_subtitle':ORG_SUBTITLE}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/apply', methods=['GET','POST'])
def apply():
    if request.method == 'POST':
        # Honeypot field: bots should leave this blank.
        if request.form.get('website'): abort(400)
        fields = ['rp_name','discord','age','playtime','experience','motivation','strengths']
        data = {k: request.form.get(k,'').strip() for k in fields}
        if any(not v for v in data.values()):
            flash('모든 항목을 작성해 주세요.', 'error')
            return render_template('apply.html', data=data)
        if any(len(v)>2000 for v in data.values()):
            flash('입력 내용이 너무 깁니다.', 'error')
            return render_template('apply.html', data=data)
        with db() as con:
            cur = con.execute('''INSERT INTO applications (created_at,rp_name,discord,age,playtime,experience,motivation,strengths)
                VALUES (?,?,?,?,?,?,?,?)''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *[data[k] for k in fields]))
            app_id = cur.lastrowid
        notify_discord('📩 신규 팩션 지원 접수', f"지원 번호: #{app_id}\n인게임 닉네임: {data['rp_name']}\n디스코드: {data['discord']}\n플레이 가능 시간: {data['playtime']}\n관리자 페이지에서 상세 내용을 확인해 주세요.")
        return render_template('success.html', app_id=app_id)
    return render_template('apply.html', data={})

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if not ADMIN_HASH:
            flash('.env에 ADMIN_PASSWORD_HASH를 먼저 설정해 주세요.', 'error')
        elif request.form.get('username','') == ADMIN_USER and check_password_hash(ADMIN_HASH, request.form.get('password','')):
            session.clear(); session['admin'] = True
            return redirect(url_for('dashboard'))
        else: flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
    return render_template('login.html')

@app.route('/admin/logout', methods=['POST'])
@admin_required
def logout():
    session.clear(); return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def dashboard():
    with db() as con:
        rows = con.execute('SELECT * FROM applications ORDER BY id DESC').fetchall()
    stats = {'all':len(rows), 'pending':sum(r['status']=='심사 대기' for r in rows), 'pass':sum(r['status']=='합격' for r in rows), 'fail':sum(r['status']=='불합격' for r in rows)}
    return render_template('dashboard.html', rows=rows, stats=stats)

@app.route('/admin/application/<int:app_id>')
@admin_required
def detail(app_id):
    with db() as con: row = con.execute('SELECT * FROM applications WHERE id=?',(app_id,)).fetchone()
    if not row: abort(404)
    return render_template('detail.html', row=row)

@app.route('/admin/application/<int:app_id>/update', methods=['POST'])
@admin_required
def update(app_id):
    status = request.form.get('status','')
    note = request.form.get('admin_note','').strip()[:2000]
    if status not in ('심사 대기','합격','불합격'): abort(400)
    with db() as con:
        row = con.execute('SELECT * FROM applications WHERE id=?',(app_id,)).fetchone()
        if not row: abort(404)
        con.execute('UPDATE applications SET status=?, admin_note=? WHERE id=?',(status,note,app_id))
    if status != row['status']:
        color = 0x2ECC71 if status=='합격' else (0xE74C3C if status=='불합격' else 0xC9A44C)
        notify_discord('📋 지원 심사 상태 변경', f"지원 번호: #{app_id}\n인게임 닉네임: {row['rp_name']}\n변경 상태: **{status}**", color)
    flash('지원서 정보가 저장되었습니다.', 'success')
    return redirect(url_for('detail', app_id=app_id))

@app.errorhandler(413)
def too_large(_): return '요청 크기가 너무 큽니다.', 413

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT',5000)), debug=False)
