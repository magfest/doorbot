#include <unistd.h>

int main() {
    execl("/usr/local/bin/disarm_alarm", NULL);
}

