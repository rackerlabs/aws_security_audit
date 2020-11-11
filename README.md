**AWS Security Audit Tool**

Python tool which will audit an AWS account and highlight areas in which security could be improved. 

AWS Config is used to check for monitored resources in every region. 

Checks include:
* EBS volume encryption status for all mounted volumed.
* S3 bucket public access and default encryption (this does not check individual objects due to cost implications and speed). 
* Ciphers used on all in use alb and elb. Flags known insecure ciphers:
	* TLS-1.0
	* TLS-1.1
	* (This can be updated in the Config class)
* RDS instance encryption. 

The data is reported back in individual csv files. All data is returned so that it can be filtered / manipulated as required. 

This is only advisory as there can always be reasons for each of the above to be configured the way they are. 
