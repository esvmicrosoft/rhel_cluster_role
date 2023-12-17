Role Name
=========

Redhat Pacemaker cluster check tool.

Requirements
------------

- apt-get install ansible #Ansible Package
- Python3
- pip3
- pip3 install lxml #lxml to read cib file


Example Playbook
----------------

***How to use/run Cluster check role :***

- sudo apt-get update
- sudo apt-get install ansible
- pip3 install lxml
- mkdir roles
- cd roles/
- git clone https://github.com/spalnatik/rhel_cluster_role.git .
- cd ..
- wget raw.githubusercontent.com/spalnatik/rhel_cluster_role/main/toolcheck_playbook.yml
- ansible-playbook -e "file_path=sosreport-sapapsbhdb-2023-09-18-ywvudrg" toolcheck_playbook.yml
  
License
-------

BSD

Author Information
------------------

Name : Sai Kumar Palnati
