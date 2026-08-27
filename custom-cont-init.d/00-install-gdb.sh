#!/bin/bash
# Installa gdb per cattura stack Python dal watchdog (il container si ricrea senza apk cache)
apk add --no-cache gdb libunwind >/dev/null 2>&1
# py-spy (attualmente incompatibile con musl+py3.14, tenuto per futuro)
exit 0
