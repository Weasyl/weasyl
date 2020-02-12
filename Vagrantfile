# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$priv_script = <<'SCRIPT'

apt-get -y update

apt-get -y install apt-transport-https ca-certificates curl \
     dkms linux-headers-amd64 linux-image-amd64

curl -s https://www.postgresql.org/media/keys/ACCC4CF8.asc > \
     /etc/apt/trusted.gpg.d/apt.postgresql.org.asc
curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key > \
     /etc/apt/trusted.gpg.d/deb.nodesource.com.asc

echo >/etc/apt/sources.list.d/postgresql.list \
    'deb https://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main 9.6'
echo >/etc/apt/sources.list.d/nodesource.list \
    'deb https://deb.nodesource.com/node_13.x stretch main'

apt-get -y update
apt-mark hold grub-pc
apt-get -y dist-upgrade

# Provides split-dns for Weasyl VPN users (otherwise unused)
mkdir -p /etc/dnsmasq.d/
echo "server=/i.weasyl.com/10.10.10.103" > /etc/dnsmasq.d/i.weasyl.com
apt-get install -y dnsmasq
if ! grep -Fxq "prepend domain-name-servers 127.0.0.1;" /etc/dhcp/dhclient.conf
then
    echo "prepend domain-name-servers 127.0.0.1;" >> /etc/dhcp/dhclient.conf
fi
dhclient -x
dhclient eth0

apt-get -y install \
    git-core libffi-dev libmagickcore-dev libpam-systemd libssl-dev \
    libxml2-dev libxslt-dev memcached nginx pkg-config liblzma-dev \
    python-dev python-virtualenv sassc

# Assure that nginx attempts restart if it can't immediately use its proxy host at startup.
mkdir -p /etc/systemd/system/nginx.service.d
echo "[Service]
Restart=on-failure
RestartSec=5" > /etc/systemd/system/nginx.service.d/restart.conf
systemctl daemon-reload

apt-get -y --allow-unauthenticated install \
    libpq-dev nodejs postgresql-9.6 postgresql-contrib-9.6

# Required to get Pillow >= 5.0.0 to build from source (since we've disabled using wheels from PyPI)
apt-get -y install build-essential

sudo -u postgres dropdb weasyl
sudo -u postgres dropuser vagrant
sudo -u postgres createuser -drs vagrant
sudo -u postgres createdb -E UTF8 -O vagrant weasyl
sudo -u postgres createdb -E UTF8 -O vagrant weasyl_test

openssl req -subj '/CN=lo.weasyl.com' -nodes -new -newkey rsa:2048 \
    -keyout /etc/ssl/private/weasyl.key.pem -out /tmp/weasyl.req.pem
openssl x509 -req -days 3650 -in /tmp/weasyl.req.pem \
    -signkey /etc/ssl/private/weasyl.key.pem -out /etc/ssl/private/weasyl.crt.pem

cat >/etc/nginx/sites-available/weasyl <<'NGINX'

server {
    listen 8443 ssl http2;

    ssl_certificate /etc/ssl/private/weasyl.crt.pem;
    ssl_certificate_key /etc/ssl/private/weasyl.key.pem;

    server_name lo.weasyl.com;

    root /home/vagrant/weasyl/build;

    location / {
        proxy_pass http://127.0.0.1:8880;
        if ($request_method = HEAD) {
            gzip off;
        }

        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 30m;
        client_body_buffer_size 128k;
        proxy_connect_timeout 10;
        proxy_send_timeout 30;
        proxy_read_timeout 30;
        proxy_buffers 32 4k;
    }

    location /css {}
    location /img {}
    location /js {}

    location = /fonts/museo500.css {
        return 307 https://cdn.weasyl.com/static/fonts/museo500.css;
    }

    location /static/media {
        root /home/vagrant/weasyl;
        try_files $uri @missing;
    }

    location /static/character {
        rewrite "^(/static/character/../../../../../../)(.+)-(.+)$" $1$3 break;
        root /home/vagrant/weasyl;
        try_files $uri @missing;
    }

    location @missing {
        return 307 https://cdn.weasyl.com$uri;
    }
}

NGINX
ln -fs /etc/nginx/sites-available/weasyl /etc/nginx/sites-enabled
/etc/init.d/nginx restart

SCRIPT


$unpriv_script = <<'SCRIPT'

psql weasyl -c 'CREATE EXTENSION hstore;'
curl https://deploy.weasyldev.com/weasyl-latest-staff.sql.xz \
    | unxz | psql weasyl

# Install libweasyl into the weasyl directory and upgrade this VM's DB.
ln -s /vagrant ~/weasyl
cd ~/weasyl
make install-libweasyl upgrade-db

SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "debian/stretch64"
  config.vm.synced_folder '.', '/vagrant', type: "virtualbox"
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
