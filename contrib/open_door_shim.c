#include <unistd.h>

int main() {
    execl("/usr/local/bin/open_door", NULL);
}

