# Water Quality Monitoring Application

**단일 코드베이스, 두 가지 배포 버전**

이 프로젝트는 Feature Flag 방식으로 RPI(경량)와 CPS(전체 기능) 두 가지 버전을 지원합니다.

## 📊 버전 비교

| 기능 | RPI | CPS |
|------|-----|-----|
| Dashboard | ✅ | ✅ |
| Trends Analysis | ✅ | ✅ |
| Alarms | ✅ | ✅ |
| Communications | ✅ | ✅ |
| **AI Insights** | ❌ | ✅ |
| **SCADA Alarms** | ❌ | ✅ |
| **포트** | 13000-13001 | 13100-13101 |
| **용량** | ~500MB | ~2GB |

## 🚀 빠른 시작

### RPI 버전 (경량 모니터링)

```bash
cd c:/reflex/reflex-water-app

# RPI 환경 변수 로드
cp .env.rpi .env

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
reflex run

# 접속: http://localhost:13000
```

### CPS 버전 (AI 포함 전체 기능)

```bash
cd c:/reflex/reflex-water-app

# CPS 환경 변수 로드
cp .env.cps .env

# AI 라이브러리 포함 의존성 설치
pip install -r requirements.cps.txt

# OpenAI API 키 설정 (.env 파일에서)
nano .env
# OPENAI_API_KEY=sk-your-key-here

# 앱 실행
reflex run

# 접속: http://localhost:13100
```

## 📁 프로젝트 구조

```
reflex-water-app/
├── water_app/
│   ├── water_app.py           # 메인 앱 (Feature Flag 로직)
│   ├── db.py                  # 데이터베이스 연결
│   ├── security.py            # 보안 검증
│   │
│   ├── pages/
│   │   ├── common/            # 공통 페이지 (RPI + CPS)
│   │   │   ├── dashboard.py
│   │   │   ├── trends.py
│   │   │   ├── alarms.py
│   │   │   └── communications.py
│   │   └── cps_only/          # CPS 전용
│   │       ├── ai_insights.py
│   │       └── scada_alarm_comparison.py
│   │
│   ├── states/
│   │   ├── common/            # 공통 상태
│   │   └── cps_only/          # CPS 전용 상태
│   │
│   ├── ai_engine/             # CPS 전용 AI 엔진
│   ├── components/            # UI 컴포넌트
│   ├── services/              # 비즈니스 로직
│   ├── queries/               # SQL 쿼리
│   ├── models/                # 데이터 모델
│   └── utils/                 # 유틸리티
│
├── rxconfig.py                # Reflex 설정
├── requirements.txt           # RPI 의존성
├── requirements.cps.txt       # CPS 의존성
├── .env.rpi                   # RPI 환경 변수
├── .env.cps                   # CPS 환경 변수
└── README.md
```

## 🔧 환경 변수

### VERSION_TYPE (가장 중요!)

```bash
# RPI 버전
VERSION_TYPE=RPI

# CPS 버전
VERSION_TYPE=CPS
```

이 환경 변수가 모든 기능의 on/off를 결정합니다.

### .env.rpi

```env
VERSION_TYPE=RPI
ENABLE_AI_FEATURES=false
TS_DSN=postgresql://water_user:water_password@localhost:5432/water_db
```

### .env.cps

```env
VERSION_TYPE=CPS
ENABLE_AI_FEATURES=true
OPENAI_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TS_DSN=postgresql://water_user:water_password@localhost:5432/water_db
```

## 🎯 코드 수정 가이드

### 공통 기능 수정 (RPI + CPS 모두 영향)

```bash
# 공통 페이지 수정
nano water_app/pages/common/dashboard.py

# 공통 상태 수정
nano water_app/states/common/dashboard_state.py

# 공통 서비스 수정
nano water_app/services/sensor_service.py
```

### CPS 전용 기능 수정

```bash
# AI Insights 페이지
nano water_app/pages/cps_only/ai_insights.py

# AI 엔진
nano water_app/ai_engine/rag_engine.py

# CPS 전용 상태
nano water_app/states/cps_only/ai_state.py
```

### 새로운 페이지 추가

```python
# water_app/water_app.py

# 공통 페이지 추가 (RPI + CPS)
from .pages.common.new_page import new_page
app.add_page(new_page, route="/new")

# CPS 전용 페이지 추가
if VERSION_TYPE == "CPS":
    from .pages.cps_only.ai_new import ai_new_page
    app.add_page(ai_new_page, route="/ai/new")
```

## 🧪 테스트

### RPI 버전 테스트

```bash
# 환경 설정
export VERSION_TYPE=RPI

# 앱 실행
reflex run

# 확인 사항:
# - http://localhost:13000 접속 가능
# - 4개 메뉴만 표시 (Dashboard, Trends, Alarms, Communications)
# - AI 메뉴 없음
```

### CPS 버전 테스트

```bash
# 환경 설정
export VERSION_TYPE=CPS
export OPENAI_API_KEY=sk-your-key

# 앱 실행
reflex run

# 확인 사항:
# - http://localhost:13100 접속 가능
# - 6개 메뉴 모두 표시
# - AI Insights 메뉴 동작
# - SCADA Alarms 메뉴 동작
```

### 동시 실행 테스트

```bash
# 터미널 1: RPI 실행
cd c:/reflex/reflex-water-app
export VERSION_TYPE=RPI
reflex run

# 터미널 2: CPS 실행
cd c:/reflex/reflex-water-app-cps
export VERSION_TYPE=CPS
reflex run

# RPI: http://localhost:13000
# CPS: http://localhost:13100
# 동시 접속 가능 (포트 분리)
```

## 📦 배포

### RPI 배포 (Raspberry Pi)

```bash
# 1. 코드 복사
scp -r water_app/ pi@192.168.1.100:/home/pi/water-app/

# 2. SSH 접속
ssh pi@192.168.1.100

# 3. 환경 설정
cd /home/pi/water-app
cp .env.rpi .env
pip install -r requirements.txt

# 4. 실행
reflex run --env production
```

### CPS 배포 (서버)

```bash
# 1. 코드 복사
scp -r water_app/ user@server:/opt/water-app/

# 2. SSH 접속
ssh user@server

# 3. 환경 설정
cd /opt/water-app
cp .env.cps .env
nano .env  # API 키 설정
pip install -r requirements.cps.txt

# 4. 실행
reflex run --env production
```

## 🔍 문제 해결

### Import Error: No module named 'water_app'

```bash
# 현재 디렉토리 확인
pwd
# /c/reflex/reflex-water-app 이어야 함

# PYTHONPATH 설정
export PYTHONPATH=/c/reflex/reflex-water-app:$PYTHONPATH
```

### AI 기능이 RPI에서 보임

```bash
# 환경 변수 확인
echo $VERSION_TYPE
# 반드시 "RPI" 또는 "CPS"

# .env 파일 확인
cat .env | grep VERSION_TYPE
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
netstat -ano | findstr :13000
netstat -ano | findstr :13100

# 프로세스 종료
taskkill /PID <프로세스ID> /F
```

## 📝 변경 이력

- **2025-10-01**: Feature Flag 방식으로 refactor 완료
- 단일 코드베이스로 RPI/CPS 버전 통합
- pages/states를 common/cps_only로 분리
- water_app 네이밍으로 변경 (ksys 제거)

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. VERSION_TYPE 환경 변수
2. requirements.txt vs requirements.cps.txt
3. Import 경로 (water_app.*)
4. 포트 충돌 (RPI: 13000, CPS: 13100)

---
**Created**: 2025-10-01  
**Refactored**: Feature Flag 방식 단일 코드베이스
