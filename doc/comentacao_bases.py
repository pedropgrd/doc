#import subprocess
import paramiko

username = 'opc'
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

bases = {'debug':"debuglnx",'homol':"homollnx",'amb1':"amb1lnx",
        'amb2':"amb2lnx",'amb3':"amb3lnx",'amb4':"amb4lnx",
        'devbf':"devbflnx",'devbf2':"devbf2lnx"}

print('BASES DISPONIVEIS PARA ACESSAR:')
print(bases.keys())
base = input("QUAL BASE VAI ACESSAR: ")

command_ls = "ls /totvs/protheus/bin/"
ssh.connect(hostname=f'{bases[base]}', username=username, key_filename=fr"C:\keys\{bases[base]}.pem")

stdin, stdout, stderr = ssh.exec_command(command_ls)
resposta = stdout.read().decode('utf-8')
#ssh.close()
#shell_ls = subprocess.run(command_ls,shell=True)
print("Esses sao os repositorios disponiveis na homologacao : ")
print('tss')
print(resposta)
ambiente = input(f"qual quer saber: ")

command_ip = "ifconfig | grep 'inet ' | awk '{print $2}'"
stdin, stdout, stderr = ssh.exec_command(command_ip)
resposta_ip = stdout.read().decode('utf-8')

print(f'ip da base {base}: {resposta_ip[:11]} \n')

command_ls = f"/etc/init.d/totvs{ambiente} status"
ssh.connect(hostname=f'{bases[base]}', username=username, key_filename=fr"C:\keys\{bases[base]}.pem")

stdin, stdout, stderr = ssh.exec_command(command_ls)
resposta_status = stdout.read().decode('utf-8')
for line in resposta_status.splitlines():
    if "[ running ]" in line:
        status_ok = line.strip()  # Remover espaços extras
        #print(f"Status encontrado: {status}")
        status = status_ok[-20:]
    elif "not running" in line:
        status = line.strip()

sftp = ssh.open_sftp()

if ambiente == 'tss':
    with sftp.open(f'/totvs/tss/bin/appserver/appserver.ini', 'r') as remote_file:

        for line in remote_file:
            if '.bomfuturo.local' in line or '10.19' in line:
                print(f'portas webs no tss: {line}')
            if line.strip() == 'port=5557' or line.strip() == 'port=7890':
                continue

            if  'alias' in line:
                print(f'alias do banco do tss: {line}')

            if line.startswith('port=') or line.startswith('Port=') or line.startswith('PORT='):
                print(f"a porta em uso: {line}")
else:
    with sftp.open(f'/totvs/protheus/bin/{ambiente}/appserver.ini', 'r') as remote_file:
        first_line = remote_file.readline().strip()  
        print(f"ambiente desse serviço é: {first_line} \n")
        print(f"status: {status} \n")

        for line in remote_file:
            if 'sourcepath' in line:
                print(f'o rpo em uso: {line}')
            if line.strip() == 'port=5557' or line.strip() == 'port=7890' or line.strip() == 'port=5000':
                continue

            if line.startswith('port=') or line.startswith('Port=')or line.startswith('PORT='):
                print(f"a porta em uso: {line}")
            if 'alias' in line:
                print(f'alias do banco: {line}')
            #print(line.strip()) 