#include "error.h"

void error_message(const char *msg)
{
	perror(msg);
	exit(1)
}
