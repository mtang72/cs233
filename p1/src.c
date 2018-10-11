#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

/* Server and client side code: get from RPI
   different implementations for TCP and UDP */

void error(char *str){
	fprintf(stderr, "%s\n", str);
	exit(1);
}

void server(int sockfd,char* hostnm,int port,int is_udp){
	char buffer[256];
	struct sockaddr_in serv_addr, cli_addr;
	bzero((char*) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	serv_addr.sin_addr.s_addr = INADDR_ANY;
	if (bind(sockfd,(struct sockaddr*)&serv_addr,sizeof(serv_addr)) < 0)
		error("binding error");	
	listen(sockfd, 5);
	socklen_t clilen = sizeof(cli_addr);
	int newsockfd;
	if (!is_udp){
		newsockfd = accept(sockfd,(struct sockaddr*)&cli_addr, &clilen);
		if (newsockfd<0)
			error("accept error");
	}
	while(1){
		bzero(buffer,256);
		int n;
     		if (is_udp)
			n = recvfrom(sockfd, buffer, 256,
			MSG_WAITALL, (struct sockaddr*) &cli_addr, &clilen);
		else{
			n = read(newsockfd,buffer,255);
     			if (n<0) return;
		}
     		printf("%s",buffer);
	}
}

void client(int sockfd,char* hostnm,int port,int is_udp){
	struct sockaddr_in serv_addr;
	struct hostent *server;
	char buffer[256];
	server = gethostbyname(hostnm);
	if (server == NULL)
	error("No such host");
	bzero((char *) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	bcopy((char *)server->h_addr,(char *)&serv_addr.sin_addr.s_addr,server->h_length);
	serv_addr.sin_port = htons(port);
	if (!is_udp){
		if (connect(sockfd,(struct sockaddr *)&serv_addr,sizeof(serv_addr)) < 0) 
			error("ERROR connecting");
	}
	while(1){
		printf("Enter message: ");
		bzero(buffer,256);
		if (fgets(buffer,255,stdin) == NULL){
			if (close(sockfd)<0)
				error("ERROR closing socket");
			return;
		}
		int n;
		if (is_udp)
			n = sendto(sockfd, buffer, strlen(buffer), 0,
			(const struct sockaddr*) &serv_addr, sizeof(serv_addr));
		else{
			n = write(sockfd,buffer,strlen(buffer));
			if (n < 0) return; 
		}
		/*bzero(buffer,256);
		n = read(sockfd,buffer,255);
		if (n < 0) 
			error("ERROR reading from socket");
		printf("%s\n",buffer);*/
	}
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
	if (argc<2 || (!is_serv&&!strcmp(hostnm,"none")) || port==0)
		error("invalid or missing options\nusage: snc [-l] [-u] [hostname] port");
	//opening socket
	int sockfd;
	if (is_udp)
		sockfd = socket(AF_INET, SOCK_DGRAM, 0);
	else
		sockfd = socket(AF_INET, SOCK_STREAM, 0);
    	if (sockfd < 0) 
        	error("ERROR opening socket");	
	
	if (is_serv)
		server(sockfd,hostnm,port,is_udp);
	else
		client(sockfd,hostnm,port,is_udp);
	return 0;
}
