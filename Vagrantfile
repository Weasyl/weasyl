# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$priv_script = <<SCRIPT

apt-get update
apt-get install -y ca-certificates apt-transport-https

echo >/etc/apt/sources.list.d/weasyl.list \
    'deb http://apt.weasyldev.com/repos/apt/debian jessie main'

curl https://deploy.weasyldev.com/weykent-key.asc | apt-key add -

echo >/etc/apt/sources.list.d/nodesource.list \
    'deb https://deb.nodesource.com/node_6.x jessie main'

curl https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -

apt-get update
apt-mark hold grub-pc
apt-get -y dist-upgrade

# Provides split-dns for Weasyl VPN users (otherwise unused)
mkdir -p /etc/dnsmasq.d/
echo "server=/i.weasyl.com/10.10.10.103" > /etc/dnsmasq.d/i.weasyl.com
apt-get install -y dnsmasq
echo "prepend domain-name-servers 127.0.0.1;" >> /etc/dhcp/dhclient.conf
dhclient -x
dhclient eth0

apt-get -y install \
    git-core libffi-dev libmagickcore-dev libpam-systemd libpq-dev \
    libxml2-dev libxslt-dev memcached nginx pkg-config \
    postgresql-9.4 postgresql-contrib-9.4 \
    liblzma-dev python-dev python-virtualenv \
    ruby-sass nodejs

npm install -g gulp-cli

sudo -u postgres dropdb weasyl
sudo -u postgres dropuser vagrant
sudo -u postgres createuser -drs vagrant
sudo -u postgres createdb -E UTF8 -O vagrant weasyl
sudo -u postgres createdb -E UTF8 -O vagrant weasyl_test
sudo -u vagrant psql weasyl -c 'CREATE EXTENSION hstore;'
curl https://deploy.weasyldev.com/weasyl-latest-staff.sql.gz \
    | gunzip | sudo -u vagrant psql weasyl

openssl req -subj '/CN=lo.weasyl.com' -nodes -new -newkey rsa:2048 \
    -keyout /etc/ssl/private/weasyl.key.pem -out /tmp/weasyl.req.pem
openssl x509 -req -days 3650 -in /tmp/weasyl.req.pem \
    -signkey /etc/ssl/private/weasyl.key.pem -out /etc/ssl/private/weasyl.crt.pem

cat >/etc/nginx/sites-available/weasyl <<NGINX

server {
    listen 8443 ssl;

    ssl_certificate /etc/ssl/private/weasyl.crt.pem;
    ssl_certificate_key /etc/ssl/private/weasyl.key.pem;

    server_name lo.weasyl.com;

    rewrite "^(/static/(submission|character)/../../../../../../)(.+)-(.+)\$" \\$1\\$4 break;
    # Allows trailing slash after a profile name
    rewrite ^/(.*)/$ /\\$1 permanent;

    location /static {
        root /home/vagrant/weasyl;
        try_files \\$uri @proxy;
    }

    location /css {
        root /home/vagrant/weasyl/build;
    }

    location / {
        proxy_pass http://127.0.0.1:8880;
        if (\\$request_method = HEAD) {
            gzip off;
        }

        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto \\$scheme;
        proxy_set_header Host \\$http_host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        client_max_body_size 30m;
        client_body_buffer_size 128k;
        proxy_connect_timeout 10;
        proxy_send_timeout 30;
        proxy_read_timeout 30;
        proxy_buffers 32 4k;
    }

    location @proxy {
        proxy_pass https://www.weasyl.com;
    }
}

NGINX
ln -fs /etc/nginx/sites-available/weasyl /etc/nginx/sites-enabled
/etc/init.d/nginx restart

SCRIPT


$unpriv_script = <<SCRIPT

# Install libweasyl into the weasyl directory and upgrade this VM's DB.
ln -s /vagrant ~/weasyl
cd ~/weasyl
make install-libweasyl upgrade-db

SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "weasyl-debian81.box"
  config.vm.box_url = "http://deploy.weasyldev.com/weasyl-debian81.box"
  config.vm.box_download_checksum = "34592e65ebd4753d6f74a54b019e36d1ce006010cb4f03ed8ec131824f45ff9b"
  config.vm.box_download_checksum_type = "sha256"
  config.vm.hostname = "vagrant-weasyl"
  config.vm.provision :shell, :privileged => true, :inline => $priv_script
  config.vm.provision :shell, :privileged => false, :inline => $unpriv_script
  config.vm.network :forwarded_port, host: 8443, guest: 8443
  # Increase memory.
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end
  config.vm.provider "vmware_fusion" do |v|
    v.vmx["memsize"] = "1024"
  end
end
