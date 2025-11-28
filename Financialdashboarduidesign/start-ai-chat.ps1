# Quick Start Script for AI Chat
# Run this from PowerShell to start all required services

Write-Host "🚀 Starting Stockify AI Chat Services..." -ForegroundColor Cyan
Write-Host ""

# Check if ports are already in use
Write-Host "Checking ports..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "⚠️  Port 8000 already in use (Backend may already be running)" -ForegroundColor Yellow
}
if ($port8001) {
    Write-Host "⚠️  Port 8001 already in use (MCP Server may already be running)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting services in separate windows..." -ForegroundColor Green

# Start Backend API (Port 8000)
Write-Host "1️⃣  Starting Backend API on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd d:\sentimetrix\backend; Write-Host 'Backend API Server' -ForegroundColor Green; python server.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# Start MCP Server (Port 8001)
Write-Host "2️⃣  Starting MCP+RAG Server on port 8001..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd d:\sentimetrix\mcp; `$env:MCP_SERVER_PORT='8001'; `$env:MCP_API_KEY='stockify-mcp-2025'; Write-Host 'MCP+RAG Server' -ForegroundColor Green; python run_server.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "3️⃣  Starting Frontend Dev Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd d:\sentimetrix\Financialdashboarduidesign; Write-Host 'Frontend Dev Server' -ForegroundColor Green; npm run dev" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service Status:" -ForegroundColor Yellow
Write-Host "   Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "   MCP Server:   http://localhost:8001" -ForegroundColor White
Write-Host "   Frontend:     http://localhost:5173 (check terminal for actual port)" -ForegroundColor White
Write-Host ""
Write-Host "🤖 Try these queries in the AI Chat:" -ForegroundColor Cyan
Write-Host "   - Why did HDFC Bank move up this month?" -ForegroundColor Gray
Write-Host "   - Explain TCS price change" -ForegroundColor Gray
Write-Host "   - What happened to Reliance?" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to open health checks..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

# Health checks
Write-Host ""
Write-Host "Running health checks..." -ForegroundColor Cyan

try {
    $backend = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Backend API: Running" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API: Not responding" -ForegroundColor Red
}

try {
    $mcp = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ MCP Server is healthy" -ForegroundColor Green
    Write-Host "   Vector DB: $($mcp.components.vector_db.total_embeddings) embeddings, $($mcp.components.vector_db.unique_symbols) symbols" -ForegroundColor Gray
} catch {
    Write-Host "❌ MCP Server check failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "📚 Documentation: AI_CHAT_INTEGRATION.md" -ForegroundColor Cyan
Write-Host ""
