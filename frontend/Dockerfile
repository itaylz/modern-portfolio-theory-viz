# Use Node to build the assets
FROM node:18-slim
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Start the React development server
# (For a real production app we'd use Nginx, but 'npm start' is fine for a portfolio demo)
EXPOSE 3000
CMD ["npm", "start"]