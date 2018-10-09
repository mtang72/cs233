#include <stdio.h>
#include <string.h>
#include <sys/socket.h>

/* Server and client side code: get from RPI
   different implementations for TCP and UDP */

int main(int argc, char*argv[]){
	int cliserv = 0; //0 if client 1 if server	
	int tcpudp = 0; //0 if tcp 1 if udp
	int port;
	char hostnm[50];
	for (int i=1;i<argc;i++){
		if (strcmp(argv[i],"-l"))
			cliserv = 1;
		else if (strcmp(argv[i],"-u"))
			tcpudp = 1;	
		else{
			if (i<argc-1){
				for (int j=0;j<strlen(argv[i]);j++)
					hostnm[j] = argv[i][j];
			}
			else
				port = atoi(argv[i]);
		}
	}
	printf("cliserv: %d\ntcpudp: %d\nport: %s\nhostnm: %s\n",
		cliserv, tcpudp, port, hostnm);

	if (argc<2 || cliserv){
		fprintf(stderr,"invalid or missing options\n");
		fprintf(stderr,"usage: snc [-l] [-u] [hostname] port\n");
	}
	return 0;
}
