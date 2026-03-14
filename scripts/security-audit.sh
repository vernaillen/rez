#!/bin/bash
# Nightly security audit for harmonics-clawd VPS
# Reports findings — does NOT auto-fix anything

echo "🔒 SECURITY AUDIT — $(date '+%A %d %B %Y, %H:%M UTC')"
echo "   Host: $(hostname) | $(uname -s) $(uname -r)"
echo ""

ISSUES=0

# 1. UFW Firewall
echo "1️⃣ FIREWALL (ufw)"
UFW=$(sudo ufw status 2>/dev/null || ufw status 2>/dev/null || echo "")
if echo "$UFW" | grep -q "Status: active"; then
    echo "   ✅ UFW is active"
    echo "$UFW" | grep -v "^Status" | grep -v "^$" | sed 's/^/   /'
elif [ -f /etc/ufw/ufw.conf ] && grep -q "ENABLED=yes" /etc/ufw/ufw.conf 2>/dev/null; then
    echo "   ✅ UFW is active (verified via config)"
    echo "   (no sudo — can't show detailed rules)"
else
    echo "   ❌ UFW is NOT active (or can't verify without sudo)"
    ISSUES=$((ISSUES+1))
fi
echo ""

# 2. Fail2ban
echo "2️⃣ FAIL2BAN"
if systemctl is-active --quiet fail2ban 2>/dev/null; then
    BANNED=$(sudo fail2ban-client status sshd 2>/dev/null | grep "Currently banned" | awk '{print $NF}' || echo "?")
    TOTAL=$(sudo fail2ban-client status sshd 2>/dev/null | grep "Total banned" | awk '{print $NF}' || echo "?")
    echo "   ✅ Fail2ban active — Currently banned: ${BANNED:-0} | Total banned: ${TOTAL:-0}"
else
    echo "   ❌ Fail2ban is NOT running"
    ISSUES=$((ISSUES+1))
fi
echo ""

# 3. SSH Config
echo "3️⃣ SSH CONFIG"
SSHD_CONFIG="/etc/ssh/sshd_config"
PASS_AUTH=$(grep -i "^PasswordAuthentication" $SSHD_CONFIG 2>/dev/null | awk '{print $2}')
ROOT_LOGIN=$(grep -i "^PermitRootLogin" $SSHD_CONFIG 2>/dev/null | awk '{print $2}')
# Check includes too
if [ -z "$PASS_AUTH" ]; then
    PASS_AUTH=$(grep -ri "^PasswordAuthentication" /etc/ssh/sshd_config.d/ 2>/dev/null | head -1 | awk '{print $2}')
fi
if [ "$PASS_AUTH" = "no" ]; then
    echo "   ✅ Password authentication: disabled"
else
    echo "   ⚠️ Password authentication: ${PASS_AUTH:-not explicitly set}"
    ISSUES=$((ISSUES+1))
fi
if [ "$ROOT_LOGIN" = "no" ] || [ "$ROOT_LOGIN" = "prohibit-password" ]; then
    echo "   ✅ Root login: ${ROOT_LOGIN}"
else
    echo "   ⚠️ Root login: ${ROOT_LOGIN:-not explicitly set}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# 4. Open Ports
echo "4️⃣ OPEN PORTS"
echo "   Listening on 0.0.0.0 / [::]:"
ss -tlnp 2>/dev/null | grep -E "0\.0\.0\.0|:::" | awk '{print "   " $4 " — " $6}' | sed 's/users:(("/  /;s/".*//'
UNEXPECTED=$(ss -tlnp 2>/dev/null | grep -E "0\.0\.0\.0|:::" | grep -v -E ":(22|80|443|18789|8178) " | grep -v "127\." | grep -v "::1")
if [ -n "$UNEXPECTED" ]; then
    echo "   ⚠️ Potentially unexpected ports found (review above)"
    ISSUES=$((ISSUES+1))
else
    echo "   ✅ No unexpected open ports"
fi
echo ""

# 5. Docker Containers
echo "5️⃣ DOCKER CONTAINERS"
if command -v docker &>/dev/null; then
    CONTAINERS=$(docker ps --format "{{.Names}} — {{.Image}} ({{.Status}})" 2>/dev/null)
    if [ -n "$CONTAINERS" ]; then
        echo "$CONTAINERS" | sed 's/^/   /'
        COUNT=$(docker ps -q 2>/dev/null | wc -l)
        echo "   ℹ️ $COUNT container(s) running — review if expected"
    else
        echo "   ✅ No running containers"
    fi
else
    echo "   ℹ️ Docker not installed"
fi
echo ""

# 6. Disk Usage
echo "6️⃣ DISK USAGE"
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
DISK_AVAIL=$(df -h / | tail -1 | awk '{print $4}')
if [ "$DISK_PCT" -lt 80 ]; then
    echo "   ✅ Disk usage: ${DISK_PCT}% (${DISK_AVAIL} free)"
else
    echo "   ❌ Disk usage: ${DISK_PCT}% — above 80% threshold! (${DISK_AVAIL} free)"
    ISSUES=$((ISSUES+1))
fi
echo ""

# 7. Failed Login Attempts (last 24h)
echo "7️⃣ FAILED LOGINS (last 24h)"
FAILED=$(journalctl _SYSTEMD_UNIT=sshd.service --since "24 hours ago" 2>/dev/null | grep -c "Failed password" 2>/dev/null || true)
FAILED=${FAILED:-0}; FAILED=$(echo "$FAILED" | tr -d '\n' | awk '{print $1+0}')
INVALID=$(journalctl _SYSTEMD_UNIT=sshd.service --since "24 hours ago" 2>/dev/null | grep -c "Invalid user" 2>/dev/null || true)
INVALID=${INVALID:-0}; INVALID=$(echo "$INVALID" | tr -d '\n' | awk '{print $1+0}')
echo "   Failed password attempts: $FAILED"
echo "   Invalid user attempts: $INVALID"
if [ "$FAILED" -gt 100 ] || [ "$INVALID" -gt 100 ]; then
    echo "   ⚠️ High number of failed attempts — review fail2ban config"
    ISSUES=$((ISSUES+1))
else
    echo "   ✅ Within normal range"
fi
echo ""

# 8. System Updates
echo "8️⃣ PENDING UPDATES"
UPDATES=$(apt list --upgradable 2>/dev/null | grep -c "upgradable" || echo "0")
SECURITY=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l || echo "0")
echo "   Pending updates: $UPDATES"
echo "   Security updates: $SECURITY"
if [ "$SECURITY" -gt 0 ]; then
    echo "   ⚠️ Security updates available — consider applying"
    ISSUES=$((ISSUES+1))
else
    echo "   ✅ No pending security updates"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$ISSUES" -eq 0 ]; then
    echo "✅ Security audit passed. No issues found."
else
    echo "⚠️ Security audit found $ISSUES issue(s). Review above."
fi
