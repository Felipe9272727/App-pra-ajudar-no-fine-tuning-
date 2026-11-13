MICROPYTHON_TOP ?= /dev/shm/liquid-android/tools022/micropython-1.26.1
SRC_QSTR += $(MICROPYTHON_TOP)/extmod/modjson.c
include $(MICROPYTHON_TOP)/ports/embed/embed.mk
