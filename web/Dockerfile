# chatbot_ra — web en modo producción.
#
# Importante: se compila con `next build` y se sirve con `next start`.
# NO usar `next dev` en producción: su runtime (webpack devtool
# eval-source-map) ejecuta cada módulo vía eval(), y una Content Security
# Policy sin 'unsafe-eval' bloquea todo el JS del chat.

# ---- deps: dependencias completas (incluye devDeps para el build) ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- builder: compila la app ----
# API_URL se lee en `next build` (Next hornea el destino de las rewrites en
# .next/routes-manifest.json); si falta, next.config cae al fallback
# localhost:8001 y el proxy /api/* apunta al propio contenedor (ECONNREFUSED).
FROM node:20-alpine AS builder
WORKDIR /app
ARG API_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV API_URL=$API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner: solo runtime de producción ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# node_modules solo con dependencias de producción (más chico y sin devDeps)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.mjs ./

EXPOSE 3000

CMD ["npm", "run", "start"]
