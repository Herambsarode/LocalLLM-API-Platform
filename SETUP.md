# AI API Platform — Complete Setup Guide

हा project **Heramb Sarode** आणि **Shruti Bhavsar** यांनी विकसित केला आहे. या guideमध्ये local API, PostgreSQL, LM Studio आणि ngrok tunnel setup दिला आहे.

## 1. आवश्यक software

- Python 3.12 किंवा नवीन
- PostgreSQL 16+
- LM Studio आणि एक downloaded/loaded local model
- Git
- ngrok account आणि ngrok Agent CLI
- Redis (optional)

Install verify करण्यासाठी:

```powershell
python --version
git --version
ngrok version
```

## 2. Project clone करा

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

## 3. Python environment तयार करा

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PowerShell activation block झाल्यास current terminalसाठी:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## 4. Environment configuration

```powershell
Copy-Item .env.example .env
```

`.env` मध्ये किमान खालील values बदला:

```env
SECRET_KEY=YOUR_RANDOM_SECRET_OF_AT_LEAST_64_CHARACTERS
DATABASE_URL=postgresql+asyncpg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/ai_api
DATABASE_SYNC_URL=postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/ai_api
LM_STUDIO_BASE_URL=http://localhost:1234/v1
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=CHOOSE_A_STRONG_PASSWORD
CORS_ORIGINS=http://localhost:8000
```

Random secret तयार करण्यासाठी:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`.env` GitHubवर commit करू नका. Repositoryमध्ये फक्त `.env.example` ठेवायची आहे.

## 5. PostgreSQL database

PostgreSQLमध्ये `ai_api` database तयार करा आणि `.env` मधील username/password त्याच्याशी जुळवा. नंतर migration चालवा:

```powershell
alembic upgrade head
```

Docker वापरत असल्यास:

```powershell
docker compose up -d db redis
```

## 6. LM Studio setup

1. LM Studio install करा.
2. आवश्यक GGUF model download/load करा.
3. Local Server सुरू करा; default address `http://localhost:1234` आहे.
4. हे endpoint verify करा:

```powershell
Invoke-RestMethod http://127.0.0.1:1234/v1/models
```

## 7. API सुरू करा

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

दुसऱ्या PowerShell windowमध्ये health check करा:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Useful local URLs:

- Dashboard: `http://127.0.0.1:8000/dashboard`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## 8. ngrok install करा

Windowsसाठी ngrok Agent CLI [official ngrok download page](https://ngrok.com/download/windows) किंवा Microsoft Storeमधून install करा. Install झाल्यावर:

```powershell
ngrok version
```

## 9. ngrok authtoken set करा

1. [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) मध्ये account तयार/login करा.
2. Dashboardमधील **Your Authtoken** copy करा.
3. खालील commandमध्ये placeholderच्या जागी token द्या:

```powershell
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

या commandमुळे token ngrokच्या user-level configमध्ये save होतो. Windowsमध्ये default config साधारण `%LocalAppData%\ngrok\ngrok.yml` येथे असतो.

महत्त्वाचे:

- Authtoken command output, screenshot, README किंवा project fileमध्ये paste करू नका.
- Projectमध्ये token असलेली `ngrok.yml` commit करू नका.
- Token चुकून GitHubवर गेला तर ngrok dashboardमधून लगेच revoke/rotate करा.
- ngrok authtoken आणि या applicationचा `sk_live_...` API key वेगवेगळे credentials आहेत.

## 10. Public ngrok tunnel सुरू करा

API आधी port `8000` वर चालू असणे आवश्यक आहे. नवीन PowerShell windowमध्ये:

```powershell
ngrok http 8000
```

ngrok consoleमध्ये `https://...ngrok-free.app` किंवा accountला assign झालेला public URL दिसेल. तो browserमध्ये उघडा:

```text
https://YOUR_NGROK_DOMAIN/health
https://YOUR_NGROK_DOMAIN/docs
```

Free/random URL ngrok restart केल्यावर बदलू शकतो. Reserved/static domain वापरायचा असल्यास ngrok dashboardमधून domain तयार करा आणि dashboardने दिलेला exact start command वापरा.

ngrok local inspection UI:

```text
http://127.0.0.1:4040
```

## 11. Application API key

Applicationचा `sk_live_...` API key admin/API workflowमधून generate होतो. तो ngrok authtoken नाही. Client example:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://YOUR_NGROK_DOMAIN/v1",
    api_key="sk_live_your_generated_api_key",
)
```

Real application API key source code, HTML, documentation किंवा GitHubमध्ये hardcode करू नका.

## 12. Common ngrok errors

### `ERR_NGROK_8012`

ngrok चालू आहे, पण port `8000` वर API उपलब्ध नाही. आधी verify करा:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

API बंद असल्यास Uvicorn पुन्हा सुरू करा.

### `ERR_NGROK_3200`

ngrok endpoint offline आहे. Tunnel पुन्हा सुरू करा:

```powershell
ngrok http 8000
```

### ngrok authentication error

Authtoken पुन्हा configure करा:

```powershell
ngrok config add-authtoken YOUR_NEW_NGROK_AUTHTOKEN
```

## 13. GitHub uploadपूर्वी final check

```powershell
git status
git check-ignore -v .env ngrok.yml API_INFO.txt ngrok.exe
git grep -n "sk_live_"
```

`git grep` मध्ये फक्त placeholder/example key दिसली पाहिजे; real key दिसता कामा नये.

Official ngrok references:

- [Download ngrok for Windows](https://ngrok.com/download/windows)
- [ngrok CLI documentation](https://ngrok.com/docs/agent/cli)
- [Share localhost quickstart](https://ngrok.com/docs/guides/share-localhost/quickstart)
