# Production Deployment Guide

## **Quick Deploy Options**

### **Option 1: Railway (Recommended - 5 minutes)**

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Deploy:**
   ```bash
   railway init
   railway up
   ```

4. **Get your URL:**
   ```bash
   railway domain
   ```

**Result:** You'll get a URL like `https://your-app-name.railway.app`

### **Option 2: Render (Free Tier Available)**

1. **Go to [render.com](https://render.com)**
2. **Connect your GitHub repo**
3. **Create new Web Service**
4. **Configure:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.server.app:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3

**Result:** You'll get a URL like `https://your-app-name.onrender.com`

### **Option 3: Heroku (Paid)**

1. **Install Heroku CLI:**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Login and deploy:**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

3. **Get your URL:**
   ```bash
   heroku open
   ```

**Result:** You'll get a URL like `https://your-app-name.herokuapp.com`

### **Option 4: DigitalOcean App Platform**

1. **Go to [digitalocean.com](https://digitalocean.com)**
2. **Create App Platform**
3. **Connect GitHub repo**
4. **Configure Python app**

**Result:** You'll get a URL like `https://your-app-name.ondigitalocean.app`

## **Production Environment Setup**

### **Environment Variables to Set:**

```bash
# Runtime budgets - Production settings
BUDGET_MAX_SEARCHES=200
BUDGET_MAX_FETCHES=300
BUDGET_MAX_ENRICH=150
BUDGET_MAX_LLM_TOKENS=0
CACHE_TTL_SECS=604800
PER_DOMAIN_FETCH_CAP=50
MODE=fast

# Production domain allow-list
ALLOWLIST_DOMAINS=beckershospitalreview.com,himss.org,healthit.gov,epic.com,nhs.uk,modernhealthcare.com,fiercehealthcare.com,healthcareitnews.com,healthcarefinancenews.com,healthcare-informatics.com,healthcareitconnect.com,healthcareitoutcomes.com,linkedin.com,forbes.com,inc.com,entrepreneur.com,trainingindustry.com,td.org,atd.org,hr.com,shrm.org,corporatelearning.com,businesswire.com,prnewswire.com,globenewswire.com,bloomberg.com,reuters.com,wsj.com,nytimes.com,techcrunch.com,venturebeat.com,trainingfolks.com,skillpath.com,prosolutionstraining.com,edstellar.com,tadsllc.com,pe.gatech.edu,trade.gov,educate-me.co,teambuilding.com,unboxedtechnology.com,litmos.com,saasacademyadvisors.com,trainingorchestra.com,ncwu.edu,corpedgroup.com,joshbersin.com,whatfix.com,groupmoovs.com,projectmanagementacademy.net,villanova.edu

# Production settings
PORT=8080
HOST=0.0.0.0
```

## **Testing Your Live Deployment**

Once deployed, test your endpoints:

```bash
# Health check
curl https://your-app-url.com/health

# Test healthcare segment
curl -X POST -H "Content-Type: application/json" \
  -d '{"segment": "healthcare", "targetcount": 5, "mode": "fast"}' \
  https://your-app-url.com/run

# Test corporate segment
curl -X POST -H "Content-Type: application/json" \
  -d '{"segment": "corporate", "targetcount": 5, "mode": "fast"}' \
  https://your-app-url.com/run

# Test providers segment
curl -X POST -H "Content-Type: application/json" \
  -d '{"segment": "providers", "targetcount": 5, "mode": "fast"}' \
  https://your-app-url.com/run
```

## **Recommended: Railway Deployment**

**Why Railway?**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy environment variable management
- ✅ Built-in monitoring
- ✅ Fast deployments
- ✅ No credit card required for basic usage

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will automatically detect it's a Python app
7. Set environment variables in the Railway dashboard
8. Deploy!

**Your live URL will be:** `https://your-app-name.railway.app`

## **Post-Deployment Checklist**

- [ ] Test all three segments (healthcare, corporate, providers)
- [ ] Verify CSV outputs are generated
- [ ] Check budget management is working
- [ ] Monitor logs for any errors
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring alerts

## **Production Considerations**

### **Scaling:**
- Railway: Auto-scales based on traffic
- Render: Manual scaling in dashboard
- Heroku: Add dynos as needed

### **Monitoring:**
- All platforms provide basic logs
- Consider adding Sentry for error tracking
- Set up health check monitoring

### **Security:**
- HTTPS is automatic on all platforms
- Environment variables are encrypted
- Consider adding API authentication for production use

## **Support**

If you encounter issues:
1. Check the deployment logs
2. Verify environment variables are set correctly
3. Test locally first with `uvicorn src.server.app:app --host 0.0.0.0 --port 8080`
4. Check the `/health` endpoint is responding

**Your live production URL will be ready in 5-10 minutes!**
