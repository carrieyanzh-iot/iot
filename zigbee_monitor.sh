#!/bin/bash
#
# zigbee_monitor.sh
# 监控 zigbee2mqtt 设备:离线检测 / 低电量 / 弱信号
#
# 依赖: mosquitto_sub, jq
#   sudo apt install -y mosquitto-clients jq
#
# 用法:
#   ./zigbee_monitor.sh
#   (Ctrl+C 停止)

set -uo pipefail

# ========== 配置区 ==========
BROKER="192.168.1.122"
PORT="1883"
BASE_TOPIC="zigbee2mqtt"

OFFLINE_THRESHOLD_SEC=3600   # 超过这么久没消息 = 判定离线 (默认1小时)
BATTERY_LOW_THRESHOLD=20     # 电量低于这个百分比就告警
LINKQUALITY_LOW_THRESHOLD=30 # 信号质量低于这个值就告警
CHECK_INTERVAL_SEC=60        # 每隔多久检查一次"是否离线"

LOG_FILE="/home/carrieyanzh/zigbee-monitor/monitor.log"

# ========== 告警函数(按需替换成 Telegram / 邮件 / webhook)==========
send_alert() {
    local msg="$1"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] ALERT: $msg" | tee -a "$LOG_FILE"

    # 示例:发送到 Telegram(取消注释并填入你的 token/chat_id)
    # curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
    #      -d chat_id=<CHAT_ID> -d text="$msg" > /dev/null

    # 示例:发送到本地 ntfy 服务
    # curl -s -d "$msg" ntfy.sh/your-topic > /dev/null
}

log_info() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] $1" | tee -a "$LOG_FILE"
}

# ========== 状态存储 ==========
# 用普通文件存每个设备的"最后一次收到消息的时间戳" (关联数组在子进程/后台任务间不共享,用文件更稳)
STATE_DIR="/home/carrieyanzh/zigbee-monitor/state"
mkdir -p "$STATE_DIR"

update_last_seen() {
    local device="$1"
    date +%s > "${STATE_DIR}/${device}.lastseen"
}

get_last_seen() {
    local device="$1"
    local f="${STATE_DIR}/${device}.lastseen"
    if [[ -f "$f" ]]; then
        cat "$f"
    else
        echo "0"
    fi
}

# ========== 处理一条 MQTT 消息 ==========
handle_message() {
    local topic="$1"
    local payload="$2"

    # 跳过 bridge 内部话题(定义表、健康检查等噪音)
    if [[ "$topic" == "${BASE_TOPIC}/bridge/"* ]]; then
        return
    fi

    # 只处理形如 zigbee2mqtt/<device> 的顶层设备话题(不含 /set /get /availability 等子话题)
    local device="${topic#${BASE_TOPIC}/}"
    if [[ "$device" == *"/"* ]]; then
        return
    fi

    # payload 必须是合法 JSON,否则跳过
    if ! echo "$payload" | jq -e . >/dev/null 2>&1; then
        return
    fi

    update_last_seen "$device"
    rm -f "${STATE_DIR}/${device}.alerted"  # 恢复上线,清除离线告警标记

    # 检查电量
    local battery
    battery=$(echo "$payload" | jq -r '.battery // empty')
    if [[ -n "$battery" ]] && (( battery < BATTERY_LOW_THRESHOLD )); then
        send_alert "设备 [$device] 电量低: ${battery}%"
    fi

    # 检查信号质量
    local linkquality
    linkquality=$(echo "$payload" | jq -r '.linkquality // empty')
    if [[ -n "$linkquality" ]] && (( linkquality < LINKQUALITY_LOW_THRESHOLD )); then
        send_alert "设备 [$device] 信号弱: linkquality=${linkquality}"
    fi

    # 检查 battery_low 标志位(部分设备直接上报这个字段)
    local battery_low
    battery_low=$(echo "$payload" | jq -r '.battery_low // empty')
    if [[ "$battery_low" == "true" ]]; then
        send_alert "设备 [$device] 上报电量过低标志 (battery_low=true)"
    fi

    log_info "收到消息 [$device]: $payload"
}

# ========== 后台任务:定期检查离线设备 ==========
check_offline_devices() {
    while true; do
        sleep "$CHECK_INTERVAL_SEC"
        local now
        now=$(date +%s)

        for f in "${STATE_DIR}"/*.lastseen; do
            [[ -e "$f" ]] || continue
            local device
            device=$(basename "$f" .lastseen)
            local last_seen
            last_seen=$(cat "$f")
            local diff=$(( now - last_seen ))

            local alerted_flag="${STATE_DIR}/${device}.alerted"
            if (( diff > OFFLINE_THRESHOLD_SEC )); then
                if [[ ! -f "$alerted_flag" ]]; then
                    send_alert "设备 [$device] 已 $((diff / 60)) 分钟无消息,疑似离线"
                    touch "$alerted_flag"
                fi
            fi
        done
    done
}

# ========== 主流程 ==========
log_info "启动 zigbee2mqtt 监控脚本,连接 ${BROKER}:${PORT} ..."

# 启动后台离线检测(与主循环共享同一个 shell 进程,共享关联数组)
check_offline_devices &
OFFLINE_CHECKER_PID=$!

cleanup() {
    log_info "停止监控脚本..."
    kill "$OFFLINE_CHECKER_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# 主循环:订阅所有 topic,逐行处理
mosquitto_sub -h "$BROKER" -p "$PORT" -t "${BASE_TOPIC}/#" -v | while IFS=' ' read -r topic payload; do
    handle_message "$topic" "$payload"
done
