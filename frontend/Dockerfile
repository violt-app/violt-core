FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json* ./

# Update npm to the latest version
RUN npm install -g npm@latest

# Install dependencies
RUN npm ci --legacy-peer-deps


# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set API URL for production build
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Add fallback URL for external access
ARG NEXT_PUBLIC_EXTERNAL_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_EXTERNAL_API_URL=${NEXT_PUBLIC_EXTERNAL_API_URL}

# Build the Next.js application
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create a non-root user to run the application (Alpine specific)
RUN addgroup --system --gid 1001 nodejs && \
	adduser --system --uid 1001 nextjs

# Copy necessary files from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set proper permissions
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose the application port
EXPOSE 3000

# Create entrypoint script for platform-specific initialization
# USER root
# RUN echo '#!/bin/sh\n\
#     # Check if we need to update API URL at runtime\n\
#     if [ -n "$NEXT_PUBLIC_API_URL" ]; then\n\
#     echo "Using API URL: $NEXT_PUBLIC_API_URL"\n\
#     fi\n\
#     \n\
#     # Run the application\n\
#     exec node server.js\n\
#     ' > /frontend/entrypoint.sh && chmod +x /frontend/entrypoint.sh
# USER nextjs

# # Set the command to run the application using the entrypoint script
# ENTRYPOINT ["/frontend/entrypoint.sh"]
CMD ["node", "server.js"]