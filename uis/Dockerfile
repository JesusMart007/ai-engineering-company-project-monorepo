FROM node:22-alpine

WORKDIR /app

# Each app installs its own dependencies. Sources are bind-mounted by Compose at
# runtime, so node_modules live in the image/named volumes, not on the host.
COPY talent-pipeline-tracker/package*.json ./website/
RUN cd website && npm ci

COPY backoffice/package*.json ./backoffice/
RUN cd backoffice && npm ci

COPY talent-pipeline-tracker ./website
COPY backoffice ./backoffice

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 3000 3001

CMD ["start.sh"]
