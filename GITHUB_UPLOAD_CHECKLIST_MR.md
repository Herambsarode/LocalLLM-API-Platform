# GitHub Upload करण्यापूर्वीची Checklist

हा **AI API Platform** project [Heramb Sarode](https://github.com/Herambsarode) आणि [Shruti Bhavsar](https://github.com/Shrutibhavsar3240) यांनी विकसित केला आहे.

## या project मधून public GitHub repository मध्ये upload करू नयेत अशा गोष्टी

खालील local/private files GitHub वर upload करू नका:

- `.env` आणि `.env.*` (`.env.example` मात्र ठेवायची)
- `ngrok.yml` — यात ngrok authtoken आहे
- `API_INFO.txt` — यात live API key आणि public tunnel URL आहे
- `ngrok.exe` — downloaded third-party binary आहे; user ने ngrok वेगळे install करावे
- `api.log`, `ngrok.log`, `logs/` आणि इतर `*.log` files
- `__pycache__/`, `*.pyc`, `.pytest_cache/`, coverage files
- `venv/` किंवा `.venv/`
- database dumps, local `*.db` files आणि IDE-specific folders

वरील entries `.gitignore` आणि Docker buildसाठी `.dockerignore` मध्ये जोडलेल्या आहेत.

## अत्यावश्यक security actions

1. `ngrok.yml` मध्ये सापडलेला authtoken ngrok dashboard मधून **revoke/rotate** करा.
2. `API_INFO.txt` मधील `sk_live_...` key application/database मधून **revoke** करून नवीन key तयार करा.
3. `.env` मधील `SECRET_KEY`, database password आणि `DEFAULT_ADMIN_PASSWORD` नवीन strong values ने बदला.
4. Production मध्ये `CORS_ORIGINS=*` वापरू नका; फक्त आवश्यक frontend domains द्या.
5. `docker-compose.yml` मधील example PostgreSQL password production deploymentपूर्वी बदला आणि secret environment variableमधून द्या.
6. Repository आधी कुठे push केली असल्यास file delete करणे पुरेसे नाही—Git history मधून secret काढा आणि key तरीही rotate करा.

## Uploadपूर्वी verify करा

PowerShell मध्ये:

```powershell
git init
git status --short
git check-ignore -v .env ngrok.yml API_INFO.txt ngrok.exe api.log ngrok.log
git ls-files
```

`git status` किंवा `git ls-files` मध्ये private files दिसत असतील तर त्यांना stage/commit करू नका. एखादी ignored file आधीच tracked असेल तर:

```powershell
git rm --cached -- .env ngrok.yml API_INFO.txt ngrok.exe api.log ngrok.log
```

हा command local file delete करत नाही; ती फक्त Git tracking मधून काढतो.

## Suggested GitHub upload commands

सध्याचा `.git` folder valid repository नसेल तर त्याचा backup/स्थिती तपासून मग नवीन repository initialize करा. Valid Git repository तयार झाल्यानंतर:

```powershell
git add .
git status
git commit -m "Initial commit: AI API Platform"
git branch -M main
git remote add origin https://github.com/<username>/<repository>.git
git push -u origin main
```

`git add .` नंतर आणि commitपूर्वी `git status` नीट तपासणे अनिवार्य आहे.

## GitHub repository description (suggested)

> A self-hosted, OpenAI-compatible API platform for LM Studio with authentication, quotas, usage tracking, monitoring, and Docker support. Developed by Heramb Sarode and Shruti Bhavsar.
