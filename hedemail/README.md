# hedemail

hedemail package implements a webhook to send an email when there is an update to
any of the .mediawiki files on a specified repository.

### What is HED?
HED (Hierarchical Event Descriptors) is a semi-structured vocabulary and
framework for annotating events in a machine-friendly and uniform way. The HED
framework is being developed and maintained by the
[hed-standard organization](https://github.com/hed-standard).  

For more information on HED visit: <https://github.com/hed-standard/hed-specification> or
[hedtags.org](http://hedtags.org) for an html schema viewer.

### Dependencies

* [Python 3](https://www.python.org/downloads/)
* SMTP server
* [hedconverter]

### Screenshots

![Email example](screenshots/hedemailer-email.png)

### Notes
* The webhook has been implemented to ONLY accept JSON content type push events. 
* Emails may potentially be blocked without a fully-qualified domain name.  
