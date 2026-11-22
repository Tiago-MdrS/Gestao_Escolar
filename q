warning: in the working copy of 'backend/app/main.py', LF will be replaced by CRLF the next time Git touches it
[1mdiff --git a/backend/app/database.py b/backend/app/database.py[m
[1mindex 1ecd878..17ec92c 100644[m
[1m--- a/backend/app/database.py[m
[1m+++ b/backend/app/database.py[m
[36m@@ -5,7 +5,7 @@[m [mfrom app.core.config import settings[m
 [m
 engine = create_engine([m
     settings.DATABASE_URL,[m
[31m-    echo=True,[m
[32m+[m[32m    echo=settings.SQL_ECHO,[m
     pool_pre_ping=True[m
 )[m
 [m
[1mdiff --git a/backend/app/main.py b/backend/app/main.py[m
[1mindex 8b0720f..5b7f18a 100644[m
[1m--- a/backend/app/main.py[m
[1m+++ b/backend/app/main.py[m
[36m@@ -1,4 +1,5 @@[m
[31m-﻿from fastapi import FastAPI, HTTPException[m
[32m+[m[32m﻿[m
[32m+[m[32mfrom fastapi import FastAPI, HTTPException, Request[m
 from sqlalchemy import text[m
 [m
 from app.core.config import settings[m
[36m@@ -34,6 +35,22 @@[m [mapp = FastAPI([m
     version="1.0.0"[m
 )[m
 [m
[32m+[m
[32m+[m[32m@app.middleware("http")[m
[32m+[m[32masync def remover_prefixo_api(request: Request, call_next):[m
[32m+[m[32m    path = request.scope["path"][m
[32m+[m
[32m+[m[32m    if path == "/api" or path.startswith("/api/"):[m
[32m+[m[32m        novo_path = path[4:] or "/"[m
[32m+[m[32m        request.scope["path"] = novo_path[m
[32m+[m
[32m+[m[32m        raw_path = request.scope.get("raw_path")[m
[32m+[m[32m        if raw_path and raw_path.startswith(b"/api"):[m
[32m+[m[32m            request.scope["raw_path"] = raw_path[4:] or b"/"[m
[32m+[m
[32m+[m[32m    return await call_next(request)[m
[32m+[m
[32m+[m
 app.include_router(auth.router)[m
 app.include_router(usuarios.router)[m
 [m
