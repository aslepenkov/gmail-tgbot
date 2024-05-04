# gmail tgbot

Fetch gmail api and send emails as tg bot


```
docker build -t a4mail . && sudo docker run -d --name a4mail a4mail
docker rm -f a4mail && sudo docker rmi-f a4mail
sudo docker run -d -v /home/ec2-user/dev/gmail-tgbot:/app --name a4mail a4mail
docker -it a4mail /bin/bash

```