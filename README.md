**AWS Security Audit Tool**

Python tool which will audit an AWS account and highlight areas in which security could be improved. 

This uses AWS Config to check for monitored resources in every region. 

Checks include:
* EC2 instances and report on EBS volume encryption status.
* S3 buckets without default encryption (this does not check individual objects due to cost implications and speed). 
* All load balancers for insecure ciphers. Currently checking:
	* TLS-1.0
	* TLS-1.1
* RDS for unencrypted instances. 

This is only advisory as there can always be reasons for each of the above to be configured the way they are. 

Currently WIP. 
