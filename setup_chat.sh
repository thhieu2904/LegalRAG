#!/usr/bin/env bash
# Setup script for Chat Page with Multi-turn Clarification

echo "🚀 Setting up LegalRAG Chat Page with Multi-turn Clarification"
echo "============================================================"

cd frontend

echo "📦 Installing dependencies..."
npm install react-router-dom@^6.28.1

echo "✅ Dependencies installed!"

echo ""
echo "🎯 SETUP COMPLETE!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && conda activate LegalRAG_v1 && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "🎉 Features implemented:"
echo "✅ Full-screen chat interface"  
echo "✅ Multi-turn clarification (Giai đoạn 1→2→3→4)"
echo "✅ Proper API integration with /api/v2/clarify"
echo "✅ Question suggestions after collection selection"
echo "✅ Responsive design for desktop"
echo "✅ Dark mode support"
echo "✅ Real-time typing indicators"
echo ""
echo "🔧 Backend Multi-turn Flow:"
echo "  1. Ambiguous query → Collection selection"
echo "  2. Collection selected → Question suggestions" 
echo "  3. Question selected → Final answer"
echo ""
echo "🚀 Ready to test!"
