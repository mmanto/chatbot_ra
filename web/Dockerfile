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
FROM node:20-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
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
