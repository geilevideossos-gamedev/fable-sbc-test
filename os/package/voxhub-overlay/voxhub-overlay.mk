################################################################################
#
# voxhub-overlay - device tree overlay for the VoxHub CM4 carrier
#
################################################################################

VOXHUB_OVERLAY_VERSION = 1.0
VOXHUB_OVERLAY_SITE = $(BR2_EXTERNAL_HAOS_PATH)/package/voxhub-overlay/src
VOXHUB_OVERLAY_SITE_METHOD = local
VOXHUB_OVERLAY_LICENSE = GPL-2.0
VOXHUB_OVERLAY_DEPENDENCIES = host-dtc
VOXHUB_OVERLAY_INSTALL_IMAGES = YES
VOXHUB_OVERLAY_INSTALL_TARGET = NO

define VOXHUB_OVERLAY_BUILD_CMDS
	$(HOST_DIR)/bin/dtc -@ -I dts -O dtb -W no-unit_address_vs_reg \
		-o $(@D)/voxhub.dtbo $(@D)/voxhub-overlay.dts
endef

# haos-hook.sh (board/raspberrypi) copies $(BINARIES_DIR)/*.dtbo to /overlays on the boot partition
define VOXHUB_OVERLAY_INSTALL_IMAGES_CMDS
	$(INSTALL) -D -m 0644 $(@D)/voxhub.dtbo $(BINARIES_DIR)/voxhub.dtbo
endef

$(eval $(generic-package))
