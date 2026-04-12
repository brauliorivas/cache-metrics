CC = g++

CFLAGS  = -Wall -Wextra -O2 $(shell pkg-config --cflags libCacheSim glib-2.0)
LDLIBS  = $(shell pkg-config --libs libCacheSim glib-2.0) -lzstd -pthread

TARGET = main
SRC = $(wildcard *.cpp)
OBJ = $(SRC:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(OBJ) $(LDLIBS) -o $(TARGET)

%.o: %.cpp
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJ)
