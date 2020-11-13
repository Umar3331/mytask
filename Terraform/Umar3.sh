#!/bin/bash
  
apt update
apt install apache2 -y
rm /var/www/html/index.html
var=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
ipaddress=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
cat > /var/www/html/index.html <<_EOF
<!DOCTYPE html>
<html>
<head>
    <title>Hello ${var}</title>
</head>
<body>
    <h1>Hello world from ip - ${ipaddress} and hostname - ${var}</h1>
</body>
</html>
_EOF
 
systemctl start apache2
systemctl enable apache2
