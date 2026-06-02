FROM node:20
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

RUN apt-get update && apt-get install -y python3 python3-pip pipx curl && \
    pipx install mcpo && \
    pipx ensurepath

ENV PATH="/root/.local/bin:$PATH"

EXPOSE 8000
ENTRYPOINT ["mcpo", "--port", "8000", "--", "node", "/app/build/index.js"]
