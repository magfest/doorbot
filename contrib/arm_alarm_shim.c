#include <unistd.h>

int main() {
    execl("/usr/local/bin/arm_alarm", NULL);
}

