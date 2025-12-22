FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Development mode
ENV NODE_ENV=development

# Start Next.js dev server
CMD ["npm", "run", "dev"]

