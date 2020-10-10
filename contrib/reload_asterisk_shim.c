#include <unistd.h>

int main() {
    execl("/usr/bin/systemctl", "reload", "asterisk", NULL);
}

