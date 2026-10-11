#!/usr/bin/env bash
# ==============================================================================
# DRM Virtual Layer Setup Script (Linux Kernel Level)
# Replaces Hyprland-specific headless monitors with a genuine DRM/KMS device.
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}       Configuring Kernel DRM Virtual Display Layer    ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 1. Configure VKMS (Virtual Kernel Mode Setting)
echo -e "\n${YELLOW}[1/3] Enabling VKMS kernel module for virtual DRM connector...${NC}"
sudo bash -c 'cat << "EOF" > /etc/modules-load.d/vkms.conf
vkms
EOF'

sudo bash -c 'cat << "EOF" > /etc/modprobe.d/vkms.conf
options vkms enable_cursor=1 enable_overlay=1 enable_writeback=1
EOF'

echo -e "${GREEN}✓ VKMS configured to auto-load on system boot.${NC}"

# 2. Configure DRM EDID Firmware for NVIDIA Hardware DRM connector forcing
echo -e "\n${YELLOW}[2/3] Setting up DRM EDID injection firmware...${NC}"
sudo mkdir -p /usr/lib/firmware/edid

if [ -f "${HOME}/edid_1080p.bin" ]; then
    sudo cp "${HOME}/edid_1080p.bin" /usr/lib/firmware/edid/1080p.bin
    echo -e "${GREEN}✓ Saved 1080p EDID block to /usr/lib/firmware/edid/1080p.bin${NC}"
fi

# 3. Instruction for Kernel boot parameters (GRUB)
echo -e "\n${YELLOW}[3/3] DRM Layer Summary & Next Steps:${NC}"
echo -e "1. ${GREEN}VKMS Module${NC}: Loads a software-emulated DRM/KMS card (/dev/dri/cardX) with Virtual-1 connector."
echo -e "2. ${GREEN}EDID Forcing on NVIDIA GPU${NC}: To force the physical HDMI-A-1 connector on the GTX 1050 Ti to stay active when headless, add to /etc/default/grub:"
echo -e "   ${YELLOW}GRUB_CMDLINE_LINUX_DEFAULT=\"... drm.edid_firmware=HDMI-A-1:edid/1080p.bin video=HDMI-A-1:1920x1080@60e\"${NC}"
echo -e "   and run: ${GREEN}sudo grub-mkconfig -o /boot/grub/grub.cfg${NC}"
echo -e "\n${BLUE}======================================================${NC}"
