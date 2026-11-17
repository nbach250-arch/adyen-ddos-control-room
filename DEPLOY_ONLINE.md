# Publish the classroom control room on Render

1. Create a GitHub repository (e.g. `adyen-ddos-control-room`).
2. Upload the **contents** of this folder to the repository root (app.py, requirements.txt, render.yaml, templates/, static/), not the outer folder itself.
3. Visit Render > New > Web Service and connect that repository.
4. Choose the Free plan. Use build command `pip install -r requirements.txt` and start command `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT app:app`.
5. Deploy, then use the Render-provided HTTPS URL.

This version includes gunicorn, the production WSGI server expected by Render. Your Mac can still run `python3 app.py` locally.

**Classroom caveat:** This app keeps ONE simulation in server memory, shared among all website visitors. When one person launches an attack or resets, everyone sees that same change. It is not suitable for public deployment beyond a controlled classroom demo. An inactive free service may sleep, which resets the in-memory state. No real Adyen integration or traffic is involved.
