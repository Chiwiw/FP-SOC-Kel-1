#!/bin/bash
# Actions for SOAR Playbooks to be run on Target VMs (e.g. VM-2)
# These commands are referenced by Shuffle SOAR nodes via SSH/agents.

ACTION=$1
IP_OR_USER=$2

if [ -z "$ACTION" ]; then
    echo "Usage: ./playbook_actions.sh [ddos_block|malware_isolate|lock_user] [TARGET_IP or TARGET_USER]"
    exit 1
fi

case "$ACTION" in
    "ddos_block")
        if [ -z "$IP_OR_USER" ]; then
            echo "Missing TARGET_IP for ddos_block"
            exit 1
        fi
        echo "Blocking IP $IP_OR_USER for DDoS mitigation..."
        sudo iptables -A INPUT -s "$IP_OR_USER" -j DROP
        echo "IP Blocked."
        ;;
        
    "malware_isolate")
        echo "Isolating Host for Malware containment..."
        # Note: Be careful, this will drop all connections, including SSH unless an exception is added
        # Recommendation: add SSH exception before dropping all
        sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        sudo iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT
        sudo iptables -P INPUT DROP
        sudo iptables -P OUTPUT DROP
        echo "Host Isolated."
        ;;
        
    "lock_user")
        if [ -z "$IP_OR_USER" ]; then
            echo "Missing TARGET_USER for lock_user"
            exit 1
        fi
        echo "Locking user $IP_OR_USER for Credential Abuse..."
        sudo passwd -l "$IP_OR_USER"
        echo "User Locked."
        ;;
        
    *)
        echo "Unknown action: $ACTION"
        echo "Valid actions: ddos_block, malware_isolate, lock_user"
        exit 1
        ;;
esac
