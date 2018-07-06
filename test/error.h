/* Handles error */

void error_message(const char *msg)
{
	perror(msg);
	// exit now
	exit(1)
}
