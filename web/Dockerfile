FROM node:22-slim AS dev

WORKDIR /app
RUN corepack enable && corepack prepare pnpm@12.9.1 --activate

COPY . .
RUN pnpm install --frozen-lockfile

EXPOSE 3000
CMD ["pnpm", "dev"]

# TODO(Phase 5): FROM node:22-slim AS prod
#   pnpm install --prod --frozen-lockfile, pnpm build, pnpm start
