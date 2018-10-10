#include <stdio.h>
#include <sys/types.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

/* Server and client side code: get from RPI
   different implementations for TCP and UDP */

void server(sockfd,hostnm,port,is_udp){
	char buffer[256];
	struct sockaddr_in serv_addr, cli_addr;
	bzero((char*) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	
}

int main(int argc, char*argv[]){
	int is_serv = 0; //0 if client 1 if server	
	int is_udp = 0; //0 if tcp 1 if udp
	int port = 0; //if still 0 after reading argv then invalid, port 0 is not usable for messages
	char hostnm[50] = "none";
	for (int i=1;i<argc;i++){
		if (strcmp(argv[i],"-l") == 0)
			is_serv = 1;
		else if (strcmp(argv[i],"-u") == 0)
			is_udp = 1;	
		else{
			if (i<argc-1)
				strcpy(hostnm, argv[i]);
			else
				port = atoi(argv[i]);
		}
	}
	if (argc<2 || (!is_serv&&!strcmp(hostnm,"none")) || port==0){
		fprintf(stderr,"invalid or missing options\n");
		fprintf(stderr,"usage: snc [-l] [-u] [hostname] port\n");
		exit(1)
	}
	//opening socket
	if (is_udp)
		sockfd = socket(AF_INET, SOCK_DGRAM, 0);
	else
		sockfd = socket(AF_INET, SOCK_STREAM, 0);
    	if (sockfd < 0) 
        	error("ERROR opening socket");	
	
	if is_serv
		server(sockfd,hostnm,port,is_udp);
	else
		client(sockfd,hostnm,port,is_udp);
	return 0;
}
