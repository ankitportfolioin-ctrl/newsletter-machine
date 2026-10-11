# Production Deployment Guide

## 🚀 Pre-Deployment Checklist

### ✅ Required Before Deployment

1. **Environment Variables**
   - [ ] Set all required environment variables (see `.env.production`)
   - [ ] Generate strong JWT_SECRET: `openssl rand -base64 32`
   - [ ] Configure DATABASE_URL for production database
   - [ ] Set FRONTEND_URL to your production domain
   - [ ] Configure CORS_ORIGINS with your production domain

2. **Database**
   - [ ] Provision PostgreSQL database (version 14+)
   - [ ] Configure connection pooling (recommended: 20 connections)
   - [ ] Set up automated backups (daily)
   - [ ] Configure SSL/TLS for database connections
   - [ ] Test database connectivity from application server

3. **SSL/TLS Certificates**
   - [ ] Obtain SSL certificate for your domain
   - [ ] Configure HTTPS on load balancer or reverse proxy
   - [ ] Set up automatic certificate renewal (Let's Encrypt)
   - [ ] Redirect all HTTP traffic to HTTPS

4. **Domain & DNS**
   - [ ] Register production domain
   - [ ] Configure DNS records (A/CNAME)
   - [ ] Set up subdomains if needed (api.yourdomain.com)
   - [ ] Configure email records (SPF, DKIM, DMARC)

5. **Security**
   - [ ] Enable firewall rules (only allow necessary ports)
   - [ ] Set up DDoS protection (Cloudflare, AWS Shield)
   - [ ] Configure Web Application Firewall (WAF)
   - [ ] Enable security monitoring and alerts
   - [ ] Run security audit (npm audit)

6. **Monitoring & Logging**
   - [ ] Set up application monitoring (DataDog, New Relic, or similar)
   - [ ] Configure log aggregation (CloudWatch, Loggly, or similar)
   - [ ] Set up uptime monitoring (Pingdom, UptimeRobot)
   - [ ] Configure alert thresholds and notifications
   - [ ] Set up error tracking (Sentry, Rollbar)

7. **Performance**
   - [ ] Configure CDN for static assets (CloudFront, Cloudflare)
   - [ ] Enable gzip/brotli compression
   - [ ] Set up caching headers
   - [ ] Configure load balancer (if using multiple servers)
   - [ ] Run load tests to verify capacity

8. **Backup & Recovery**
   - [ ] Document backup procedures
   - [ ] Test restore procedures
   - [ ] Set up disaster recovery plan
   - [ ] Document rollback procedures

---

## 📦 Deployment Options

### Option 1: Docker + Docker Compose (Recommended for Small Scale)

**Pros:**
- Easy to set up and manage
- Consistent environments
- Built-in orchestration

**Cons:**
- Single server limitation
- Manual scaling required

**Steps:**
```bash
# 1. Clone repository
git clone <your-repo-url>
cd newsletter-machine

# 2. Configure environment
cp server/.env.production server/.env
nano server/.env  # Edit with production values

# 3. Build and start
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
docker-compose ps
curl https://yourdomain.com/health
```

### Option 2: Kubernetes (Recommended for Large Scale)

**Pros:**
- Auto-scaling
- High availability
- Advanced orchestration

**Cons:**
- Complex setup
- Higher operational overhead

**Steps:**
```bash
# 1. Build Docker images
docker build -t yourregistry/newsletter-machine-backend:latest ./server
docker build -t yourregistry/newsletter-machine-frontend:latest .

# 2. Push to registry
docker push yourregistry/newsletter-machine-backend:latest
docker push yourregistry/newsletter-machine-frontend:latest

# 3. Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### Option 3: Cloud Platform (AWS, GCP, Azure)

**Pros:**
- Managed infrastructure
- Auto-scaling
- Built-in monitoring

**Cons:**
- Vendor lock-in
- Can be expensive

**AWS Example:**
```bash
# 1. Create ECS cluster
aws ecs create-cluster --cluster-name newsletter-machine

# 2. Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster newsletter-machine \
  --service-name newsletter-machine-service \
  --task-definition newsletter-machine-task \
  --desired-count 2 \
  --load-balancers targetGroupArn=<arn>,containerName=backend,containerPort=3001
```

---

## 🔧 Server Configuration

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/newsletter-machine

upstream backend {
    server localhost:3001;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        root /var/www/newsletter-machine/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check
    location /health {
        proxy_pass http://backend/health;
    }
}
```

### Systemd Service (for non-Docker deployments)

```ini
# /etc/systemd/system/newsletter-machine.service

[Unit]
Description=Newsletter Machine Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/newsletter-machine/server
ExecStart=/usr/bin/node dist/index.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
EnvironmentFile=/var/www/newsletter-machine/server/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable newsletter-machine
sudo systemctl start newsletter-machine
sudo systemctl status newsletter-machine
```

---

## 📊 Monitoring Setup

### Application Monitoring (DataDog Example)

```javascript
// server/src/index.ts (add at top)
const dd = require('dd-trace').init({
  service: 'newsletter-machine',
  env: process.env.NODE_ENV,
  version: '1.0.0',
});
```

### Log Aggregation (Winston + CloudWatch)

```javascript
// server/src/utils/logger.ts
import winston from 'winston';
import CloudWatchTransport from 'winston-cloudwatch';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new CloudWatchTransport({
      logGroup: '/newsletter-machine/backend',
      logStream: process.env.HOSTNAME || 'backend',
      awsRegion: process.env.AWS_REGION || 'us-east-1',
    }),
  ],
});

export default logger;
```

### Health Check Monitoring

```bash
# Cron job for health checks
*/5 * * * * curl -f https://yourdomain.com/health || echo "Health check failed" | mail -s "Alert: Newsletter Machine Down" admin@yourdomain.com
```

---

## 🧪 Testing Before Launch

### 1. Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 1000 -c 50 https://yourdomain.com/health

# Expected: < 500ms response time, < 1% error rate
```

### 2. Security Testing

```bash
# Run npm audit
npm audit

# Run OWASP ZAP scan
zap-cli -p 8080 quick-scan https://yourdomain.com
```

### 3. Performance Testing

```bash
# Lighthouse audit
lighthouse https://yourdomain.com --view

# Expected: Performance > 90, Accessibility > 90, Best Practices > 90
```

### 4. User Acceptance Testing

- [ ] Test user registration and login
- [ ] Test niche creation and configuration
- [ ] Test source connection (RSS, Reddit, YouTube)
- [ ] Test content collection
- [ ] Test newsletter generation
- [ ] Test feedback submission
- [ ] Test account deletion
- [ ] Test error scenarios

---

## 🚨 Incident Response Plan

### Severity Levels

**P0 - Critical (Service Down)**
- Response time: 5 minutes
- Notification: SMS + Email + Slack
- Escalation: CTO after 15 minutes

**P1 - High (Major Feature Broken)**
- Response time: 15 minutes
- Notification: Email + Slack
- Escalation: Engineering Lead after 30 minutes

**P2 - Medium (Minor Feature Broken)**
- Response time: 1 hour
- Notification: Slack
- Escalation: Engineering Lead after 2 hours

**P3 - Low (Cosmetic Issue)**
- Response time: 4 hours
- Notification: Slack
- Escalation: Next business day

### Runbooks

#### Database Connection Failure
```bash
# 1. Check database status
sudo systemctl status postgresql

# 2. Check connection pool
curl https://yourdomain.com/health

# 3. Restart application
sudo systemctl restart newsletter-machine

# 4. Check logs
sudo journalctl -u newsletter-machine -f
```

#### High Memory Usage
```bash
# 1. Check memory usage
free -h

# 2. Check Node.js processes
ps aux | grep node

# 3. Restart if necessary
sudo systemctl restart newsletter-machine

# 4. Monitor
htop
```

#### SSL Certificate Expiry
```bash
# 1. Check certificate
sudo certbot certificates

# 2. Renew if needed
sudo certbot renew

# 3. Reload nginx
sudo systemctl reload nginx
```

---

## 📈 Post-Launch Monitoring

### First 24 Hours
- Monitor error rates every 15 minutes
- Check response times every 30 minutes
- Review logs hourly
- Monitor database connections
- Check for security alerts

### First Week
- Daily review of error logs
- Monitor user signups and engagement
- Track performance metrics
- Review user feedback
- Check backup success

### First Month
- Weekly performance review
- Monthly security audit
- User satisfaction survey
- Capacity planning review
- Cost optimization review

---

## 🔄 Rollback Procedures

### Application Rollback
```bash
# 1. Identify previous version
docker images | grep newsletter-machine

# 2. Stop current deployment
docker-compose down

# 3. Start previous version
docker-compose -f docker-compose.prod.yml up -d --scale backend=0
docker tag yourregistry/newsletter-machine-backend:v1.0.0 yourregistry/newsletter-machine-backend:latest
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl https://yourdomain.com/health
```

### Database Rollback
```bash
# 1. Stop application
sudo systemctl stop newsletter-machine

# 2. Restore from backup
pg_restore -h localhost -U newsletter_user -d newsletter_machine backup.sql

# 3. Start application
sudo systemctl start newsletter-machine

# 4. Verify
curl https://yourdomain.com/health
```

---

## 📞 Support Contacts

### Internal
- **Engineering Lead**: engineering@yourdomain.com
- **DevOps**: devops@yourdomain.com
- **On-Call**: oncall@yourdomain.com

### External
- **AWS Support**: https://console.aws.amazon.com/support
- **Domain Registrar**: [Your registrar's support]
- **SSL Provider**: [Your SSL provider's support]

---

## ✅ Launch Checklist

### Day Before Launch
- [ ] All environment variables configured
- [ ] Database backups verified
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Alert thresholds set
- [ ] Runbooks documented
- [ ] On-call schedule confirmed

### Launch Day
- [ ] Final health check passed
- [ ] DNS propagated
- [ ] SSL valid
- [ ] Monitoring active
- [ ] Team on standby
- [ ] Communication channels open

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Collect user feedback
- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Update documentation
- [ ] Schedule retrospective

---

**Good luck with your launch! 🚀**
