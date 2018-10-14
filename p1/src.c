#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>

void error(char *str){
	fprintf(stderr, "%s\n", str);
	exit(1);
}

void server(int sockfd,char* hostnm,int port,int is_udp){
	//creating buffer and sockaddrs
	char buffer[256];
	struct hostent *spechost;
	struct sockaddr_in serv_addr, cli_addr;
	bzero((char*) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	if (strcmp(hostnm,"none")==0)
		serv_addr.sin_addr.s_addr = INADDR_ANY;
	else{
		spechost = gethostbyname(hostnm);
		if (spechost == NULL)
			error("invalid or missing options\nusage: snc [-l] [-u] [hostname] port");
		bcopy((char *)spechost->h_addr,(char *)&serv_addr.sin_addr.s_addr,spechost->h_length);
	}
	if (bind(sockfd,(struct sockaddr*)&serv_addr,sizeof(serv_addr)) < 0)
		error("invalid or missing options\nusage: snc [-l] [-u] [hostname] port");
	//listening and connecting to client if TCP	
	listen(sockfd, 5);
	socklen_t clilen = sizeof(cli_addr);
	int n, newsockfd;
	if (!is_udp){
		newsockfd = accept(sockfd,(struct sockaddr*)&cli_addr, &clilen);
		if (newsockfd<0)
			error("internal error");
	}
	//receiving messages
	while(1){
		bzero(buffer,256);
     		if (is_udp)
			n = recvfrom(sockfd, buffer, 256,
			MSG_WAITALL, (struct sockaddr*) &cli_addr, &clilen);
		else{
			n = read(newsockfd,buffer,255);
     			if (n==0) return;
		}
     		printf("%s",buffer);
	}
}

void client(int sockfd,char* hostnm,int port,int is_udp){
	//creating buffer,sockaddr, hostent
	struct sockaddr_in serv_addr;
	struct hostent *server;
	char buffer[256];
	server = gethostbyname(hostnm);
	if (server == NULL)
		error("invalid or missing options\nusage: snc [-l] [-u] [hostname] port");
	bzero((char *) &serv_addr, sizeof(serv_addr));
	serv_addr.sin_family = AF_INET;
	bcopy((char *)server->h_addr,(char *)&serv_addr.sin_addr.s_addr,server->h_length);
	serv_addr.sin_port = htons(port);
	//attempting to connect to server
	if (!is_udp){
		if (connect(sockfd,(struct sockaddr *)&serv_addr,sizeof(serv_addr)) < 0) 
			error("internal error");
	}
	int n, can_send = 1;
	//messaging
	while(1){
		bzero(buffer,256);
		//ctrl-d handling
		if (fgets(buffer,255,stdin) == NULL){
			if (is_udp)
				can_send = 0;
			else return;
		}
		if (is_udp && can_send)
			n = sendto(sockfd, buffer, strlen(buffer), 0,
			(const struct sockaddr*) &serv_addr, sizeof(serv_addr));
		else if (!is_udp){
			n = write(sockfd,buffer,strlen(buffer));
			if (n < 0) return; 
		}
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
	if (argc<2 || (!is_serv&&!strcmp(hostnm,"none")) || port<1025
		|| port>65535)
		error("invalid or missing options\nusage: snc [-l] [-u] [hostname] port");
	//opening socket
	int sockfd;
	if (is_udp)
		sockfd = socket(AF_INET, SOCK_DGRAM, 0);
	else
		sockfd = socket(AF_INET, SOCK_STREAM, 0);
    	if (sockfd < 0) 
        	error("internal error");	
	
	if (is_serv)
		server(sockfd,hostnm,port,is_udp);
	else
		client(sockfd,hostnm,port,is_udp);
	if (close(sockfd)<0)
		error("internal error");
	return 0;
}
