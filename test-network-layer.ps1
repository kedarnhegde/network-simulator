# Test Network Layer Routing
# Creates a chain topology and verifies multi-hop routing works

Write-Host "Testing Network Layer Implementation" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# 1. Reset simulation
Write-Host "[1/6] Resetting simulation..." -ForegroundColor Green
Invoke-RestMethod -Method POST "$baseUrl/control/reset" | Out-Null

# 2. Create a chain topology: Node 1 <-> Node 2 <-> Node 3
# Each node only in range of adjacent nodes (not all connected)
Write-Host "[2/6] Creating 3-node chain topology..." -ForegroundColor Green
Write-Host "  Node 1 at (10, 10)" -ForegroundColor Gray
$n1 = Invoke-RestMethod -Method POST "$baseUrl/nodes" -ContentType "application/json" -Body '{"role": "sensor", "phy": "BLE", "x": 10, "y": 10}'
Write-Host "  Node 2 at (20, 10)" -ForegroundColor Gray
$n2 = Invoke-RestMethod -Method POST "$baseUrl/nodes" -ContentType "application/json" -Body '{"role": "sensor", "phy": "BLE", "x": 20, "y": 10}'
Write-Host "  Node 3 at (30, 10)" -ForegroundColor Gray
$n3 = Invoke-RestMethod -Method POST "$baseUrl/nodes" -ContentType "application/json" -Body '{"role": "broker", "phy": "BLE", "x": 30, "y": 10}'

# Note: BLE has 15m range, so nodes 10m apart are neighbors
# Node 1-3 are 20m apart, so NOT direct neighbors

# 3. Start simulation
Write-Host "[3/6] Starting simulation..." -ForegroundColor Green
Invoke-RestMethod -Method POST "$baseUrl/control/start" | Out-Null

# 4. Wait for route advertisements to build routing tables
Write-Host "[4/6] Waiting 5 seconds for route discovery..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 5. Check routing tables
Write-Host "[5/6] Checking routing tables..." -ForegroundColor Green
Write-Host ""

$tables = Invoke-RestMethod "$baseUrl/routing"

foreach ($table in $tables) {
    Write-Host "Node $($table.nodeId) routing table:" -ForegroundColor Yellow
    if ($table.routes.Count -eq 0) {
        Write-Host "  (no routes)" -ForegroundColor Gray
    } else {
        foreach ($route in $table.routes) {
            Write-Host "  -> Node $($route.dest) via next-hop $($route.nextHop) (metric: $($route.metric) hops)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

# 6. Verify multi-hop routing works
Write-Host "[6/6] Verifying multi-hop capability..." -ForegroundColor Green
$node1_table = $tables | Where-Object { $_.nodeId -eq 1 }
$route_to_3 = $node1_table.routes | Where-Object { $_.dest -eq 3 }

if ($route_to_3) {
    Write-Host "  ✓ SUCCESS: Node 1 has route to Node 3!" -ForegroundColor Green
    Write-Host "    Route: 1 -> $($route_to_3.nextHop) -> 3 (total $($route_to_3.metric) hops)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Network layer routing is working correctly!" -ForegroundColor Cyan
} else {
    Write-Host "  ✗ FAILED: Node 1 has no route to Node 3" -ForegroundColor Red
    Write-Host "    This may mean routes haven't converged yet." -ForegroundColor Yellow
    Write-Host "    Try waiting longer or check node spacing." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test complete!" -ForegroundColor Cyan
