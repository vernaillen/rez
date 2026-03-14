#!/bin/bash
# Market Monitor - Checks key indicators and outputs alert if thresholds breached
# Usage: ./market-monitor.sh [--force]

set -e

# Thresholds
SP_THRESHOLD=2.0      # S&P futures ±2%
VIX_HIGH=25           # VIX above this = alert
VIX_SPIKE=20          # VIX % change above this = alert
GOLD_LOW=4700         # Gold below this = alert
GOLD_HIGH=5000        # Gold above this = alert (recovery)
BTC_LOW=58000         # BTC below this = alert
BTC_DCA_55=55000      # DCA tranche alert
BTC_DCA_50=50000      # DCA tranche alert - aggressive buy zone
BTC_HIGH=65000        # BTC above this = alert
SILVER_MOVE=10        # Silver ±10% = alert
# PHAG (WisdomTree Physical Silver) alerts - Wouter volgt zilver via PHAG
PHAG_TARGET=90        # PHAG €90 = take profit signal
PHAG_ALERT_60=60      # First warning
PHAG_ALERT_55=55      # Significant dip
PHAG_ALERT_50=50      # Critical level
PHAG_RECOVER_65=65    # Recovery signal
PHAG_RECOVER_70=70    # Strong recovery

# EMIM (iShares EM) alerts - IE00BKM4GZ66
EMIM_ALERT_38=38      # ~8% dip - eerste signaal
EMIM_ALERT_36=36      # ~13% dip - koopzone
EMIM_ALERT_34=34      # ~18% dip - agressief bijkopen

# IMIE (SPDR MSCI ACWI) alerts - IE00B3YLTY66 (post-split feb 2026, ~25:1)
IMIE_ALERT_950=9.50   # ~6% dip - eerste signaal
IMIE_ALERT_900=9.00   # ~11% dip - koopzone
IMIE_ALERT_850=8.50   # ~16% dip - agressief bijkopen

# Force flag for testing
FORCE_OUTPUT=${1:-""}

# Fetch data
fetch_quote() {
    yf quote "$1" 2>/dev/null | jq -r "$2" 2>/dev/null || echo "N/A"
}

# Get quotes
echo "Fetching market data..." >&2

ES_PRICE=$(fetch_quote "ES=F" '.regularMarketPrice')
ES_CHANGE=$(fetch_quote "ES=F" '.regularMarketChangePercent')
VIX_PRICE=$(fetch_quote "^VIX" '.regularMarketPrice')
VIX_CHANGE=$(fetch_quote "^VIX" '.regularMarketChangePercent')
GOLD_PRICE=$(fetch_quote "GC=F" '.regularMarketPrice')
GOLD_CHANGE=$(fetch_quote "GC=F" '.regularMarketChangePercent')
SILVER_PRICE=$(fetch_quote "SI=F" '.regularMarketPrice')
SILVER_CHANGE=$(fetch_quote "SI=F" '.regularMarketChangePercent')
BTC_PRICE=$(fetch_quote "BTC-USD" '.regularMarketPrice')
BTC_CHANGE=$(fetch_quote "BTC-USD" '.regularMarketChangePercent')
KAS_PRICE=$(fetch_quote "KAS-USD" '.regularMarketPrice')
KAS_CHANGE=$(fetch_quote "KAS-USD" '.regularMarketChangePercent')
PHAG_PRICE=$(fetch_quote "PHAG.AS" '.regularMarketPrice')
PHAG_CHANGE=$(fetch_quote "PHAG.AS" '.regularMarketChangePercent')

# Fetch EUR ETFs via etf_realtime.py
ETF_DATA=$(cd ~/clawd && python3 scripts/etf_realtime.py IE00BKM4GZ66 IE00B3YLTY66 2>/dev/null || echo "[]")
EMIM_PRICE=$(echo "$ETF_DATA" | jq -r '.[0].mid // "N/A"')
EMIM_CHANGE=$(echo "$ETF_DATA" | jq -r '.[0].change_pct // "N/A"')
SPYI_PRICE=$(echo "$ETF_DATA" | jq -r '.[1].mid // "N/A"')
SPYI_CHANGE=$(echo "$ETF_DATA" | jq -r '.[1].change_pct // "N/A"')

# Build status report
STATUS="📊 **Markt Update**\n\n"
STATUS+="**S&P 500 Futures (ES):** \$${ES_PRICE} (${ES_CHANGE}%)\n"
STATUS+="**VIX:** ${VIX_PRICE} (${VIX_CHANGE}%)\n"
STATUS+="**Gold (GC):** \$${GOLD_PRICE} (${GOLD_CHANGE}%)\n"
STATUS+="**Silver (SI):** \$${SILVER_PRICE} (${SILVER_CHANGE}%)\n"
STATUS+="**Bitcoin:** \$${BTC_PRICE} (${BTC_CHANGE}%)\n"
STATUS+="**Kaspa:** \$${KAS_PRICE} (${KAS_CHANGE}%)\n"
STATUS+="**PHAG (Silver ETC):** €${PHAG_PRICE} (${PHAG_CHANGE}%)\n"
STATUS+="**EMIM (Emerging Markets):** €${EMIM_PRICE} (${EMIM_CHANGE}%)\n"
STATUS+="**IMIE (World ACWI):** €${SPYI_PRICE} (${SPYI_CHANGE}%)\n"

# Check alerts
ALERTS=""

# Helper for numeric comparison
is_breached() {
    local val=$1
    local threshold=$2
    local op=$3
    [[ "$val" == "N/A" ]] && return 1
    case $op in
        "gt") awk "BEGIN {exit !($val > $threshold)}" ;;
        "lt") awk "BEGIN {exit !($val < $threshold)}" ;;
        "abs_gt") awk "BEGIN {exit !(sqrt($val * $val) > $threshold)}" ;;
    esac
}

# S&P check
if is_breached "$ES_CHANGE" "$SP_THRESHOLD" "abs_gt"; then
    ALERTS+="⚠️ S&P Futures move >±${SP_THRESHOLD}%: ${ES_CHANGE}%\n"
fi

# VIX check
if is_breached "$VIX_PRICE" "$VIX_HIGH" "gt"; then
    ALERTS+="🔴 VIX boven ${VIX_HIGH}: ${VIX_PRICE}\n"
fi
if is_breached "$VIX_CHANGE" "$VIX_SPIKE" "abs_gt"; then
    ALERTS+="🔴 VIX spike >±${VIX_SPIKE}%: ${VIX_CHANGE}%\n"
fi

# Gold check
if is_breached "$GOLD_PRICE" "$GOLD_LOW" "lt"; then
    ALERTS+="🟡 Gold onder \$${GOLD_LOW}: \$${GOLD_PRICE}\n"
fi
if is_breached "$GOLD_PRICE" "$GOLD_HIGH" "gt"; then
    ALERTS+="🟢 Gold boven \$${GOLD_HIGH}: \$${GOLD_PRICE}\n"
fi

# Silver check
if is_breached "$SILVER_CHANGE" "$SILVER_MOVE" "abs_gt"; then
    ALERTS+="⚠️ Silver move >±${SILVER_MOVE}%: ${SILVER_CHANGE}%\n"
fi
# Silver spot target removed — monitoring PHAG €90 instead

# BTC check
if is_breached "$BTC_PRICE" "$BTC_DCA_50" "lt"; then
    ALERTS+="🟢🟢 BTC DCA ZONE \$50k! Onder \$${BTC_DCA_50}: \$${BTC_PRICE} — sterke koopzone!\n"
elif is_breached "$BTC_PRICE" "$BTC_DCA_55" "lt"; then
    ALERTS+="🟢 BTC DCA alert! Onder \$${BTC_DCA_55}: \$${BTC_PRICE} — overweeg volgende tranche\n"
elif is_breached "$BTC_PRICE" "$BTC_LOW" "lt"; then
    ALERTS+="🔴 Bitcoin onder \$${BTC_LOW}: \$${BTC_PRICE}\n"
fi
if is_breached "$BTC_PRICE" "$BTC_HIGH" "gt"; then
    ALERTS+="🟢 Bitcoin boven \$${BTC_HIGH}: \$${BTC_PRICE}\n"
fi

# PHAG check (zilver tracking)
if is_breached "$PHAG_PRICE" "$PHAG_ALERT_50" "lt"; then
    ALERTS+="🔴 PHAG KRITIEK onder €${PHAG_ALERT_50}: €${PHAG_PRICE}\n"
elif is_breached "$PHAG_PRICE" "$PHAG_ALERT_55" "lt"; then
    ALERTS+="🟠 PHAG onder €${PHAG_ALERT_55}: €${PHAG_PRICE}\n"
elif is_breached "$PHAG_PRICE" "$PHAG_ALERT_60" "lt"; then
    ALERTS+="🟡 PHAG onder €${PHAG_ALERT_60}: €${PHAG_PRICE}\n"
elif is_breached "$PHAG_PRICE" "$PHAG_TARGET" "gt"; then
    ALERTS+="🎯🎯 PHAG TARGET €${PHAG_TARGET} BEREIKT: €${PHAG_PRICE} — overweeg deels winst nemen!\n"
elif is_breached "$PHAG_PRICE" "$PHAG_RECOVER_70" "gt"; then
    ALERTS+="🚀 PHAG boven €${PHAG_RECOVER_70}: €${PHAG_PRICE}\n"
elif is_breached "$PHAG_PRICE" "$PHAG_RECOVER_65" "gt"; then
    ALERTS+="🟢 PHAG herstelt boven €${PHAG_RECOVER_65}: €${PHAG_PRICE}\n"
fi

# EMIM check (Emerging Markets dip alerts)
if is_breached "$EMIM_PRICE" "$EMIM_ALERT_34" "lt"; then
    ALERTS+="🔴 EMIM agressief bijkopen! Onder €${EMIM_ALERT_34}: €${EMIM_PRICE}\n"
elif is_breached "$EMIM_PRICE" "$EMIM_ALERT_36" "lt"; then
    ALERTS+="🟢 EMIM koopzone! Onder €${EMIM_ALERT_36}: €${EMIM_PRICE}\n"
elif is_breached "$EMIM_PRICE" "$EMIM_ALERT_38" "lt"; then
    ALERTS+="🟡 EMIM eerste signaal, onder €${EMIM_ALERT_38}: €${EMIM_PRICE}\n"
fi

# SPYI check (World ACWI dip alerts)
if is_breached "$SPYI_PRICE" "$IMIE_ALERT_850" "lt"; then
    ALERTS+="🔴 IMIE agressief bijkopen! Onder €${IMIE_ALERT_850}: €${SPYI_PRICE}\n"
elif is_breached "$SPYI_PRICE" "$IMIE_ALERT_900" "lt"; then
    ALERTS+="🟢 IMIE koopzone! Onder €${IMIE_ALERT_900}: €${SPYI_PRICE}\n"
elif is_breached "$SPYI_PRICE" "$IMIE_ALERT_950" "lt"; then
    ALERTS+="🟡 IMIE eerste signaal, onder €${IMIE_ALERT_950}: €${SPYI_PRICE}\n"
fi

# Output
if [[ -n "$ALERTS" ]]; then
    echo -e "${STATUS}\n---\n🚨 **ALERTS:**\n${ALERTS}"
elif [[ "$FORCE_OUTPUT" == "--force" ]]; then
    echo -e "${STATUS}\n✅ Geen alerts - alle indicatoren binnen thresholds."
else
    # No alerts, no output (silent)
    exit 0
fi
