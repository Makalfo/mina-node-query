
# build image
docker build -t mina-node-query .

# tag image
docker tag mina-node-query makalfe/mina-node-query

# push image
docker push makalfe/mina-node-query:latest
