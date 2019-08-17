/* Server model */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/socket.h>


void error_message(const char *msg)
{
	perror(msg);
	exit(1);
}

void usage()
{
	printf("Run the server with port\n"
	       "Usage: [Compiled_file] [port]\n");
	printf("\n");
	printf("if you want to run with default port, assign value to portnumber\n"
			">>> portnumber = 8080\n");
}

int main(int argc, char *argv[])
{
	int sock, newsock, portnumber, client;

	char buffer[256];
   	struct sockaddr_in serv_addr, cli_addr;
	int n;
	if (argc < 2) {
		usage();
		exit(1);
	}
	sock =  socket(AF_INET, SOCK_STREAM, 0);
	if (sock < 0) 
		error_message("Can't create socket");

	bzero((char *) &serv_addr, sizeof(serv_addr));
	portnumber = atoi(argv[1]);
	serv_addr.sin_family = AF_INET; 
	serv_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
	serv_addr.sin_port = htons(portnumber);
	
	if (bind(sock, (struct sockaddr *) &serv_addr,
				sizeof(serv_addr)) < 0) 
		error_message("Server could not able to bind to host and port");
	
	listen(sock, 5);
	
	client = sizeof(cli_addr);

	newsock = accept(sock, (struct sockaddr *) &cli_addr, &client);
	
	if (newsock < 0)
		error_message("Can't initiate connection");
	
	printf("New connection: host %s port %d\n",
			            inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port));
	bzero(buffer,256);

	// server runs forever
	// receive message in bytes.
	while (buffer) {
	n = read(newsock,buffer,255);
	if (n < 0) 
		error_message("ERROR");
	printf("Message from the Client: %s\n",buffer);
	}
	n = write(newsock, "Test", 18);
	if (n > 0)
		error_message("Cant send to socket");
	return 0; 
}

