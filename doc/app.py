from flask import Flask, render_template, request, jsonify
import paramiko

app = Flask(__name__)

# Dicionário das bases disponíveis
bases = {
    'debug': "debuglnx",
    'homol': "homollnx",
    'amb1': "amb1lnx",
    'amb2': "amb2lnx",
    'amb3': "amb3lnx",
    'amb4': "amb4lnx",
    'devbf': "devbflnx",
    'devbf2': "devbf2lnx"
}

@app.route('/')
def index():
    return render_template('index.html', bases=bases)

@app.route('/get_services', methods=['POST'])
def get_services():
    base = request.json.get('base')
    if not base or base not in bases:
        return jsonify({'error': 'Base inválida'}), 400

    # Conexão SSH para obter os serviços disponíveis
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=bases[base],
            username='opc',
            key_filename=fr"C:\keys\{bases[base]}.pem"
        )

        command_ls = "ls /totvs/protheus/bin/"
        stdin, stdout, stderr = ssh.exec_command(command_ls)
        resposta = stdout.read().decode('utf-8').strip().split('\n')
        ssh.close()

        return jsonify({'services': resposta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/service/<base>/<service>')
def service_info(base, service):
    if base not in bases:
        return f"Base '{base}' inválida", 400

    try:
        # Conexão SSH e SFTP para acessar o appserver.ini
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=bases[base],
            username='opc',
            key_filename=fr"C:\keys\{bases[base]}.pem"
        )
        command_ip = "ifconfig | grep 'inet ' | awk '{print $2}'"
        stdin, stdout, stderr = ssh.exec_command(command_ip)
        resposta_ip = stdout.read().decode('utf-8')

        command_status = f"/etc/init.d/totvs{service} status"
        stdin, stdout, stderr = ssh.exec_command(command_status)
        resposta_status = stdout.read().decode('utf-8')
        for line in resposta_status.splitlines():
            if "[ running ]" in line:
                status_ok = line.strip()  
                #print(f"Status encontrado: {status}")
                #status = status_ok[-20:]
                status = f"{service} running"
            elif "not running" in line:
                #status = line.strip()
                status = f"{service} not running"

        sftp = ssh.open_sftp()
        file_path = f'/totvs/protheus/bin/{service}/appserver.ini'

        try:
            with sftp.open(file_path, 'r') as remote_file:
                content = remote_file.readlines()
        except FileNotFoundError:
            content = []

        ssh.close()

        # Processar as linhas do arquivo appserver.ini
        response_data = {
            "first_line": content[0].strip() if content else "Arquivo vazio ou não encontrado",
            "ip_base": resposta_ip[:11], 
            "status_servico": status,
            "details": []
        }

        for line in content:
            if "sourcepath" in line.lower():
                response_data["details"].append(f"RPO em uso: {line.strip()}")
            if line.strip().lower().startswith("port="):
                response_data["details"].append(f"Porta em uso: {line.strip()}")
            if "alias" in line.lower():
                response_data["details"].append(f"Alias do banco: {line.strip()}")

        return render_template('services.html', base=base, service=service, data=response_data)

    except Exception as e:
        return f"Erro ao acessar o serviço '{service}' na base '{base}': {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
