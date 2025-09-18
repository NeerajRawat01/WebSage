# Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy the frontend code
COPY . .

# Build the Next.js app
RUN yarn build

# Expose Next.js default port
EXPOSE 3000

# Run Next.js in production mode
CMD ["yarn", "start", "-H", "0.0.0.0"]
