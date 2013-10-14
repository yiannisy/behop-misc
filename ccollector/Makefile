#STAGING_DIR=/home/yiannis/of/attitude/staging_dir/toolchain-mips_r2_gcc-4.6-linaro_uClibc-0.9.33.2/bin/
CCPREFIX=/home/yiannis/of/attitude/staging_dir/toolchain-mips_r2_gcc-4.6-linaro_uClibc-0.9.33.2/bin/mips-openwrt-linux-uclibc-
HPREFIX=/home/yiannis/of/attitude/staging_dir/target-mips_r2_uClibc-0.9.33.2
#CC=${CCPREFIX}gcc
#LD=${CCPREFIX}ld
#CFLAGS=-c -Wall -I/usr/include/libnl3
#LDFLAGS= -L/lib/ -lnl-3 -l:libnl-genl-3.so.200 -ljansson
CFLAGS=-c -Wall -I${HPREFIX}/usr/include/ -I${HPREFIX}/usr/include/libnl/ -I${HPREFIX}/usr/include/libnl-tiny/
LDFLAGS= -L${HPREFIX}/lib -L${HPREFIX}/usr/lib/ -lnl-tiny -ljansson

CC=mips-openwrt-linux-uclibc-gcc 
LD=mips-openwrt-linux-uclibc-ld

SOURCES=ccol.c
OBJECTS=$(SOURCES:.c=.o)
EXECUTABLE=ccol

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS) 
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@

.c.o:
	$(CC) $(CFLAGS) $< -o $@

ccol.o: ccol.c conf.h util.h
	$(CC) $(CFLAGS) ccol.c

clean: 
	rm -rf *.o ccol
	rm -rf ccollector

test: force_look
	$(MAKE) -C test

force_look:
	true
