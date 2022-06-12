FROM python:3.7-alpine

# Install Packages and Upgrade
RUN apk add --no-cache --update \
    python3 python3-dev gcc g++ \
    gfortran musl-dev \
    libffi-dev openssl-dev libpq-dev \
    docker
RUN pip install --upgrade pip
RUN apk --update add gcc make cmake g++ zlib-dev

# Working Directory 
RUN mkdir /workspace/
WORKDIR /workspace/

# Install python requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy and requirements install
COPY MinaNodeQuery.py .

# Run 
CMD ["python3", "MinaNodeQuery.py"]