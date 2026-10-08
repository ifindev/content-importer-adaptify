FROM node:22-slim AS dev

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@12.9.1 --activate

COPY . .
RUN pnpm install --frozen-lockfile

EXPOSE 3000
CMD ["pnpm", "dev"]

FROM node:22-slim AS deps

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@12.9.1 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM deps AS build

# Inlined into the browser bundle, so one image belongs to one Firebase project.
# NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL stays unset: any value makes the client
# use the emulator (lib/firebase-client.ts). Pass it only for local test images.
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL
ENV NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY \
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN \
    NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID \
    NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL=$NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL

COPY . .
RUN pnpm build

FROM node:22-slim AS prod

WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0

# Runtime env (API_URL, APP_ENV, INTERNAL_API_SECRET) comes from infra/app compose.
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
USER node

# server.js listens on $PORT (3000 if unset).
CMD ["node", "server.js"]
