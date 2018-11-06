# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/stretch64"

  config.vm.provision "shell", inline: <<-SHELL
     apt-get update
     apt-get install wget gnupg2
     wget -qO- http://pike.esi.uclm.es/add-pike-repo.sh | sh
     apt-get update
     apt-get install -y make zeroc-ice36 python3-nose python3-doublex python3-prego
   SHELL
end
