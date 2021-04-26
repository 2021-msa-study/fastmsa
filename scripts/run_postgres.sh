docker run --name pgdev -d --restart unless-stopped -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:9.6-alpine

