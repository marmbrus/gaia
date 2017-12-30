sudo apt-get -y install net-tools vim git nodejs build-essential python-pip librdkafka-dev openjdk-8-jdk

pip install flask flask-socketio confluent_kafka requests httplib2 oauth2client google-api-python-client apscheduler sht-sensor

if [ ! -d $HOME/core ]
then
    git clone git@github.com:c9/core.git
fi

if [ ! -d $HOME/.c9 ]
then
    cd $HOME/core
    scripts/install-sdk.sh
fi

if [ ! -d $HOME/confluent-4.0.0 ]
then
    cd $HOME
    wget http://packages.confluent.io/archive/4.0/confluent-oss-4.0.0-2.11.tar.gz
    tar zxvf confluent-oss-4.0.0-2.11.tar.gz
fi

if [ ! -d $HOME/Adafruit_Python_DHT ]
then
    echo Installing DHT Driver
    cd $HOME
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install --force-pi
fi

if [ ! -d $HOME/spark-2.2.1-bin-hadoop2.7 ]
then
    echo Installing Spark
    cd $HOME
    wget http://mirrors.gigenet.com/apache/spark/spark-2.2.1/spark-2.2.1-bin-hadoop2.7.tgz
    tar zxvf spark-2.2.1-bin-hadoop2.7.tgz
fi

