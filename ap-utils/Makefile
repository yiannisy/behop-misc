#STAGING_DIR=/home/yiannis/of/attitude/staging_dir/toolchain-mips_r2_gcc-4.6-linaro_uClibc-0.9.33.2/bin/
CCPREFIX=/home/yiannis/of/attitude/staging_dir/toolchain-mips_r2_gcc-4.6-linaro_uClibc-0.9.33.2/bin/mips-openwrt-linux-uclibc-
HPREFIX=/home/yiannis/of/attitude/staging_dir/target-mips_r2_uClibc-0.9.33.2
#CC=${CCPREFIX}gcc
#LD=${CCPREFIX}ld
#CFLAGS=-c -Wall -I/usr/include/libnl3
#LDFLAGS= -L/lib/ -lnl-3 -l:libnl-genl-3.so.200 -ljansson
CFLAGS=-c -Wall -I${HPREFIX}/usr/include/ -I${HPREFIX}/usr/include/libnl/ -I${HPREFIX}/usr/include/libnl-tiny/
LDFLAGS= -L${HPREFIX}/lib -L${HPREFIX}/usr/lib/ -lnl-tiny -ljansson

SOURCES=sta_manager.c
OBJECTS=$(SOURCES:.c=.o)
EXECUTABLE=sta_manager

all: sta_manager mon_to_tap

$(sta_manager): $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@

$(mon_to_tap): $(OBJECTS)
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@

.c.o:
	$(CC) $(CFLAGS) $< -o $@

sta_manager.o: sta_manager.c
	$(CC) $(CFLAGS) sta_manager.c

mon_to_tap.o: mon_to_tap.c
	$(CC) $(CFLAGS) mon_to_tap.c

clean: 
	rm -rf *.o sta_manager mon_to_tap
