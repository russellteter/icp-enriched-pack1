#!/bin/bash

echo "🚀 ICP Discovery Engine - Production Deployment"
echo "================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo "📦 Deploying to Railway..."
railway up

echo "🌐 Getting your production URL..."
railway domain

echo "✅ Deployment complete!"
echo ""
echo "🎯 Your live production URL is ready!"
echo ""
echo "🌟 Modern UI Interface (Primary):"
echo "   Visit your app URL to access the clean, modern interface"
echo "   Follow the 3-step wizard: Home → Setup → Progress → Results"
echo ""
echo "📊 API Endpoints for direct testing:"
echo "   Health: curl https://your-app.railway.app/health"
echo "   Healthcare: curl -X POST -H 'Content-Type: application/json' -d '{\"segment\": \"healthcare\", \"targetcount\": 5}' https://your-app.railway.app/run"
echo "   Corporate: curl -X POST -H 'Content-Type: application/json' -d '{\"segment\": \"corporate\", \"targetcount\": 5}' https://your-app.railway.app/run"
echo "   Providers: curl -X POST -H 'Content-Type: application/json' -d '{\"segment\": \"providers\", \"targetcount\": 5}' https://your-app.railway.app/run"
echo ""
echo "🔧 Management:"
echo "   View logs: railway logs"
echo "   Open dashboard: railway open"
echo "   Modern UI provides user-friendly interface for all operations"
