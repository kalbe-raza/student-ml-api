# Part 11 — Docker Image & Container Inspection

## `docker images`
```
IMAGE                  ID             DISK USAGE   CONTENT SIZE   EXTRA
student-ml-api:1.0.0   8981df96979c        206MB         50.9MB   U    
```

## `docker ps`
```
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS          PORTS                                         NAMES
0046ad10fb36   student-ml-api:1.0.0   "gunicorn --bind 0.0…"   25 seconds ago   Up 23 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   student-ml-api
```

## `docker logs student-ml-api`
```
[2026-09-10 16:52:58 +0000] [1] [INFO] Starting gunicorn 22.0.0
[2026-09-10 16:52:58 +0000] [1] [INFO] Listening at: http://0.0.0.0:5000 (1)
[2026-09-10 16:52:58 +0000] [1] [INFO] Using worker: sync
[2026-09-10 16:52:58 +0000] [7] [INFO] Booting worker with pid: 7
[2026-09-10 16:52:58 +0000] [8] [INFO] Booting worker with pid: 8
172.17.0.1 - - [10/Sep/2026:16:53:07 +0000] "GET /health HTTP/1.1" 200 70 "-" "curl/8.10.1"
172.17.0.1 - - [10/Sep/2026:16:53:07 +0000] "POST /predict HTTP/1.1" 200 29 "-" "curl/8.10.1"
172.17.0.1 - - [10/Sep/2026:16:53:07 +0000] "POST /predict HTTP/1.1" 400 44 "-" "curl/8.10.1"
172.17.0.1 - - [10/Sep/2026:16:53:07 +0000] "POST /predict HTTP/1.1" 400 43 "-" "curl/8.10.1"
```

## `docker inspect student-ml-api` (key fields)
```
Container ID   : 0046ad10fb36f1d824b4fe55ea9c54877e4092d826ac5d85bf6cdaf9b6385576
Image ID       : sha256:8981df96979ce778ed1e26808c6a04505392685d4b722821873b150813d6fd29
Exposed port   : 5000/tcp
Port mapping   : 5000/tcp -> 0.0.0.0:5000:::5000
Running command: ["gunicorn","--bind","0.0.0.0:5000","--workers","2","--access-logfile","-","app:app"]
Working dir    : /app
User           : appuser
```

## `docker exec -it student-ml-api sh` (executed non-interactively)
```
pwd: /app
files:
total 20
drwxr-xr-x 1 appuser appuser 4096 Sep 10 16:52 .
drwxr-xr-x 1 root    root    4096 Sep 10 16:52 ..
-rwxr-xr-x 1 appuser appuser    5 Sep 10 16:46 VERSION
-rwxr-xr-x 1 appuser appuser 1536 Sep 10 16:46 app.py
-rwxr-xr-x 1 appuser appuser   30 Sep 10 16:46 requirements.txt
VERSION file: 1.0.0
whoami: appuser
```
