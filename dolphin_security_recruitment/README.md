# 돌핀 보안국 FiveM 팩션 지원 시스템

블랙 + 골드 디자인의 공개 지원 홈페이지입니다. Flask, SQLite, Discord Webhook으로 구성되어 있습니다.

## 포함 기능
- 누구나 접속 가능한 지원서 제출 페이지
- 관리자 로그인 및 지원자 목록/상세 확인
- 심사 대기 / 합격 / 불합격 상태 관리
- 신규 지원 및 심사 상태 변경 시 디스코드 웹훅 알림
- CSRF 보호, 입력 길이 제한, 봇 방지 허니팟 필드
- Render 배포용 `render.yaml` 포함

## 가장 쉬운 배포 방법: GitHub + Render

### 1. GitHub 저장소 만들기
1. https://github.com 에 로그인합니다.
2. 오른쪽 위 `+` → `New repository`를 누릅니다.
3. Repository name에 `dolphin-security-recruitment`를 입력합니다.
4. 가능하면 `Private`를 선택하고 `Create repository`를 누릅니다.
5. 이 프로젝트 압축을 푼 폴더 안의 파일과 폴더(`app.py`, `render.yaml`, `requirements.txt`, `templates`, `static` 등)를 저장소 최상위에 업로드합니다. ZIP 파일 자체를 업로드하는 것이 아닙니다.
6. `.env` 파일이나 비밀번호/웹훅 URL은 절대 업로드하지 않습니다. `.gitignore`가 `.env`를 제외하도록 설정되어 있습니다.

### 2. 관리자 비밀번호 해시 만들기
Windows에서 프로젝트 폴더를 연 뒤 주소 표시줄에 `cmd`를 입력해 Enter를 누릅니다. 다음을 실행합니다.

```bash
python -m pip install -r requirements.txt
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('여기에_사용할_비밀번호'))"
```

출력된 긴 문자열을 복사해 둡니다. 이 문자열은 Render의 `ADMIN_PASSWORD_HASH` 값으로 사용합니다. 원래 비밀번호를 GitHub나 채팅에 올리지 마세요.

### 3. Render에 배포하기
1. https://render.com 에 가입/로그인하고 GitHub 계정을 연결합니다.
2. Dashboard에서 `New` → `Blueprint`를 선택합니다.
3. 방금 만든 GitHub 저장소를 연결하고 브랜치 `main`을 선택합니다.
4. Render가 저장소 최상위의 `render.yaml`을 읽습니다. 서비스 이름은 `dolphin-security-recruitment`로 설정해도 됩니다.
5. 환경변수 입력 화면에서 `ADMIN_PASSWORD_HASH`에 2단계에서 만든 해시를 붙여넣습니다.
6. `DISCORD_WEBHOOK_URL`에는 디스코드 채널 웹후크 URL을 입력합니다. 지금 연결하지 않을 경우 비워 두고 나중에 Render 서비스의 Environment에서 추가해도 됩니다.
7. Blueprint를 적용해 배포합니다. `render.yaml`은 Starter 유료 웹 서비스와 `/var/data` 영구 디스크를 사용합니다. 결제/요금 안내를 확인하고 진행하세요.
8. 배포가 완료되면 Render가 제공하는 `https://...onrender.com` 주소를 엽니다.

### 4. 디스코드 웹후크 만들기
1. 디스코드 서버에서 알림을 받을 채널의 설정을 엽니다.
2. `연동` → `웹후크` → `새 웹후크`를 선택합니다.
3. 웹후크 URL을 복사합니다.
4. Render Dashboard → 해당 서비스 → `Environment`에서 `DISCORD_WEBHOOK_URL`을 추가/수정하고 저장 후 재배포합니다.
5. 웹후크 URL은 비밀번호처럼 취급합니다. 외부에 공개되면 누구나 해당 채널에 메시지를 보낼 수 있으므로 유출 시 디스코드에서 웹후크를 재생성하세요.

### 5. 관리자 페이지
- 지원자 페이지: `https://배포주소/`
- 지원서 작성: `https://배포주소/apply`
- 관리자 로그인: `https://배포주소/admin/login`
- 아이디는 Render의 `ADMIN_USERNAME` (기본값 `admin`)입니다.
- 비밀번호는 해시를 만들 때 입력한 원래 비밀번호입니다.

## 중요: 데이터 보관 및 비용
- Render 기본 파일시스템은 임시 저장소입니다. 이 프로젝트는 SQLite DB를 `/var/data/applications.db`에 저장하고 Render 영구 디스크를 연결하도록 설정했습니다.
- Render 영구 디스크는 유료 웹 서비스에서 사용할 수 있습니다. 현재 Blueprint는 `plan: starter`로 설정되어 있으므로 배포 전에 Render 요금 화면에서 실제 금액을 확인하세요. 무료 플랜으로 바꾸고 디스크를 제거하면 지원서 데이터가 재배포/재시작 때 사라질 수 있습니다.
- 디스크가 연결된 서비스는 한 인스턴스에서만 실행해야 합니다.
- 관리자 비밀번호는 강력하고 고유한 값으로 사용하고, `.env` 및 웹훅 URL을 공개 저장소에 올리지 마세요.

## 로컬 테스트
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows CMD: .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python app.py
```
브라우저에서 `http://127.0.0.1:5000`에 접속합니다. 로컬 `.env` 파일은 `.env.example`을 복사해 만들고 값을 설정합니다.
