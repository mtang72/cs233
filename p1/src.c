#include <stdio.h>

/* Server and client side code: get from RPI
   different implementations for TCP and UDP */

int main(int argc, char*argv[]){
	if (argc < 2)
		fprintf(stderr,"invalid or missing options\n");
	for (int i=0;i<argc;i++)
		printf("%s\n",argv[i]);
	return 0;
}
