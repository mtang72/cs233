#include <stdio.h>
#include <sys/types.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>

/* Server and client side code: get from RPI
   different implementations for TCP and UDP */

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
	if is_serv
		server(hostnm,port,is_udp);
	else
		client(hostnm,port,is_udp);
	return 0;
}
