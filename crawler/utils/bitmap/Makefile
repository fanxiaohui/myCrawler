CC= g++
SHELL= /bin/sh
RANLIB=ranlib

LIB= libbitmap.a
LIBOBJ= bitmap.o membitmap.o

LDFLAGS= -L ./lib/ -lbitmap \
		 -L ../mylog/lib/ -lmylog\
		 -L ../MyException/lib/ -lMyException \

INCS= -I ../mylog/include/ -I ../MyException/include/ -I ./include/
CPPFLAGS= $(INCS) -g -pipe -fPIC -W -Wall -Wshadow -Wreturn-type \
		  -Wtrigraphs -Wformat -Wparentheses -Wpointer-arith \
		  -Wwrite-strings -Wswitch -Wconversion -Wsign-promo -Wredundant-decls -Wreorder \
		  #			-Weffc++ \-Werror \

# 用来控制是否执行代码覆盖率检查
# 若想执行，在命令行中执行 export COVER=xxoo即可
# 若不想执行，则在命令行中执行 unset COVER即可
ifneq ($(origin COVER), undefined)
LDFLAGS+= -L ../unittest/lib/ -lgcover
CPPFLAGS+= -fprofile-arcs -ftest-coverage
endif


all: clean $(LIB) test bitmapReader
#all: clean $(LIB)
	rm *.o -f

$(LIB): $(LIBOBJ)
	ar cr $(LIB) $(LIBOBJ)
	$(RANLIB) $(LIB)
	rm -rf lib include
	mkdir lib/
	mkdir include/
	mv $(LIB) lib/
	cp bitmap.h include
	cp membitmap.h include

%.o: %.cpp %.h
	$(CC) $(CPPFLAGS) $< -c -o $@

clean:
	rm $(LIB) -f
	rm *.o -f
	rm test bitmapReader -f
	rm -rf lib/ include/

test:
	$(CC) test.cpp -o test $(CPPFLAGS) $(LDFLAGS)

bitmapReader:
	$(CC) bitmapReader.cpp -o bitmapReader $(CPPFLAGS) $(LDFLAGS)

test_mem:
	$(CC) test_membitmap.cpp -o test_mem $(CPPFLAGS) $(LDFLAGS)
