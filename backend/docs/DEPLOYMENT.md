# Novamind Digital Twin: Production Deployment Guide

This document provides comprehensive instructions for deploying the Novamind Digital Twin platform in a production environment with HIPAA compliance.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Build Process](#build-process)
4. [Deployment Options](#deployment-options)
5. [Security Configuration](#security-configuration)
6. [Environment Variables](#environment-variables)
7. [Performance Optimization](#performance-optimization)
8. [HIPAA Compliance](#hipaa-compliance)
9. [Monitoring & Maintenance](#monitoring--maintenance)

## Architecture Overview

Novamind Digital Twin is built using a clean architecture approach:

- **Domain Layer**: Pure business logic without framework dependencies
- **Application Layer**: State management, contexts, and hooks
- **Presentation Layer**: UI components following Atomic Design pattern
- **Infrastructure Layer**: External services, API clients, etc.

This separation ensures maintainability, testability, and scalability.

## Prerequisites

Before deploying, ensure you have:

- Node.js v18.0.0 or later
- npm v9.0.0 or later
- Access to your target hosting environment (AWS, Azure, etc.)
- SSL certificate for your domain
- Environment variables set properly

## Build Process

The application uses a sophisticated build process optimized for production:

```bash
# Clone the repository (if deploying from source)
git clone https://github.com/your-org/novamind.git
cd novamind

# Install dependencies
cd frontend
npm install --legacy-peer-deps

# Build for production
npm run build:prod
```

Alternatively, use our automated deployment script:

```bash
# Make script executable if needed
chmod +x deploy-novamind-optimized.sh

# Run the deployment script
./deploy-novamind-optimized.sh
```

The script handles:
- TypeScript fixes and validation
- Clean architecture structure verification
- Dependency installation
- Production build with optimizations
- Bundle analysis
- Security configuration
- HIPAA compliance measures

## Deployment Options

### 1. AWS S3 + CloudFront (Recommended for HIPAA)

```bash
# Deploy to S3
aws s3 sync frontend/dist/ s3://your-bucket-name/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

**CloudFront Configuration Requirements:**
- Redirect HTTP to HTTPS
- Use TLSv1.2 or later
- Configure CORS headers
- Set proper cache behaviors (no caching for API routes)

### 2. Azure Static Web Apps

```bash
# Deploy to Azure Static Web Apps
az staticwebapp create --name "novamind" --resource-group "novamind-resources" --source "frontend"
```

Configure Azure Static Web Apps with:
- Custom domains with SSL
- Authentication rules
- Route rules for SPA
- HTTP headers for security

### 3. Traditional Web Server (Apache/Nginx)

Copy the contents of the `frontend/dist` directory to your web server's document root.

**Apache Configuration:**
- Enable mod_rewrite for SPA routing
- Set proper security headers
- Configure CORS
- Enable HTTPS

**Nginx Configuration:**
- Configure for SPA routing
- Set security headers
- Enable HTTPS with strong ciphers

## Security Configuration

### Web Server Security Headers

The build process automatically generates configuration files with security headers:

- **Content-Security-Policy (CSP)**: Restricts resource loading
- **Strict-Transport-Security (HSTS)**: Forces HTTPS
- **X-Content-Type-Options**: Prevents MIME-type sniffing
- **X-Frame-Options**: Prevents clickjacking
- **X-XSS-Protection**: Helps prevent XSS attacks

### CORS Configuration

Ensure your API server has proper CORS configuration to allow requests only from your frontend domain.

## Environment Variables

The application uses environment variables for configuration. Set these in your deployment environment:

| Variable | Description | Example |
|----------|-------------|---------|
| VITE_API_MODE | API mode (real/mock) | "real" |
| VITE_API_URL | API endpoint URL | "https://api.novamind.health" |
| VITE_SESSION_TIMEOUT | Session timeout in ms | "900000" (15 min) |
| VITE_ENABLE_AUDIT_LOGGING | Enable HIPAA audit logging | "true" |
| VITE_ENABLE_PERFORMANCE_TRACKING | Enable performance tracking | "true" |
| VITE_ENABLE_MEMORY_PROFILING | Enable memory profiling | "false" |
| VITE_ENABLE_ADVANCED_VISUALIZATIONS | Enable advanced visualizations | "true" |
| VITE_ENABLE_DEMO_MODE | Enable demo mode | "false" |

## Performance Optimization

Our build is optimized for production with:

- **Code Splitting**: Separates vendor code from application code
- **Tree Shaking**: Removes unused code
- **Minification**: Reduces file sizes
- **Asset Optimization**: Optimizes images and assets
- **Caching Strategy**: Implements proper cache headers

To analyze bundle size:

```bash
# In the frontend directory
npx vite-bundle-visualizer
```

## HIPAA Compliance

The application is designed for HIPAA compliance with:

### Technical Safeguards
- **Access Control**: JWT authentication and authorization
- **Audit Controls**: Comprehensive audit logging
- **Transmission Security**: HTTPS with strong encryption
- **Integrity Controls**: Data validation and sanitization

### Administrative Safeguards
- **Session Timeout**: Automatic session expiration
- **No PHI in URLs**: Only uses POST for sensitive data
- **Secure Storage**: No PHI in localStorage or sessionStorage

To verify HIPAA compliance in your deployment:
1. Ensure HTTPS is properly configured
2. Verify security headers are present
3. Test session timeout functionality
4. Review audit logging configuration
5. Check PHI handling mechanisms

## Monitoring & Maintenance

### Monitoring
- Implement application monitoring (New Relic, Datadog, etc.)
- Set up error tracking (Sentry)
- Configure real user monitoring (RUM)
- Monitor API response times

### Updating
To update the application:
1. Pull latest changes
2. Run the deployment script
3. Verify the build succeeds
4. Deploy to production
5. Invalidate caches if necessary

### Rollback Procedure
If issues are detected:
1. Revert to previous version
2. Run the deployment script with the stable version
3. Deploy the stable build
4. Invalidate caches

---

## Quick Reference

### Key Deployment Commands

```bash
# Full deployment process
./deploy-novamind-optimized.sh

# Manual build
cd frontend && NODE_OPTIONS="--max-old-space-size=4096" npm run build:prod

# AWS deployment
aws s3 sync frontend/dist/ s3://your-bucket-name/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"

# Serve locally to verify build
cd frontend && npm run preview
```

### Post-Deployment Verification

- Verify all routes work correctly
- Check that the brain visualization loads
- Ensure theme switching works
- Verify API communication
- Check that security headers are set correctly
- Validate that the site loads quickly and efficiently

For any questions or issues, contact the Novamind DevOps team.