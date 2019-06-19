docker build -t assignment4-image .
for i in {1..8};
do docker kill node$i; 
   docker kill replica$i; done

docker system prune -f
docker network create --subnet=10.10.0.0/16 assignment4-net

for filename in replicascripts/replica*.sh; 
do
   echo $filename
   open -a Terminal.app $filename
   #gnome-terminal -- $filename
done
