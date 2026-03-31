# Fallback for non-Debian build environments where
# /usr/share/dpkg/pkg-info.mk is not available.

DEB_SOURCE := $(shell dpkg-parsechangelog -S Source 2>/dev/null || true)
DEB_VERSION := $(shell dpkg-parsechangelog -S Version 2>/dev/null || true)
DEB_VERSION_UPSTREAM := $(shell echo "$(DEB_VERSION)" | sed 's/-[^-]*$$//')
DEB_VERSION_REVISION := $(shell echo "$(DEB_VERSION)" | sed 's/^.*-//')
