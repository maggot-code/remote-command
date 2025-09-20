# Ansible跳板机免密

## 环境:
1. Django Server(192.168.199.196)
    * private key: /root/.ssh/id_rsa_ansible
    * public key: /root/.ssh/id_rsa_ansible.pub
2. 堡垒机(192.168.27.131)
    * user: root
    * password: 123
    * private key: /root/.ssh/id_rsa
    * publick key: /root/.ssh/id_rsa.pub
    * authorized_keys: /root/.ssh/authorized_keys
3. 内网节点(192.168.27.132)
    * user: internal-node
    * password: 123
    * authorized_keys: /home/internal-node/.ssh/authorized_keys

## 版本:
1. Python: 3.9.6
2. Django: 4.2.23
3. Ansible: 8.7.0
4. Ansible-runner: 2.4.1
5. OpenSSH:
    5.1 Django Server: OpenSSH_9.9p2, LibreSSL 3.3.6
    5.2 堡垒机: OpenSSH_8.7p1, OpenSSL 3.2.2 4 Jun 2024
    5.3 内网节点: OpenSSH_8.7p1, OpenSSL 3.2.2 4 Jun 2024

## 架构:
1. Django Server与内网节点无法互通
2. Django Server使用/root/.ssh/id_rsa_ansible对堡垒机免密
3. 堡垒机使用/root/.ssh/id_rsa对内部节点免密

## 需求:
1. Django Server提供一个对外可以访问的接口用于接收用户提供的信息:
    1.1 内部节点IP
    1.2 内部节点用户
    1.3 内部节点密码
    1.4 内部节点上执行的命令
    1.5 内部系统类型（linux or windows）
2. Django Server整合用户提供的信息之后组装成为一个ansible上下文，提供给ansible_runner.run函数用于调用ansible执行
3. Django Server中堡垒机的相关信息以配置文件的方式保存
4. ansible首先会经过堡垒机，然后由堡垒机将流量转发到内部节点，最终在内部节点执行用户提供的命令，然后将结果返回到堡垒机，再由堡垒机返回到Django Server最终返回给用户完整整个业务流程