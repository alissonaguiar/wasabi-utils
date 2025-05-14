import boto3
import argparse
from jproperties import Properties

print("Wasabi Utils by Alisson Aguiar")  # Debug

def load_credentials():
    try:
        configs = Properties()
        with open('wasabi_credentials.properties', 'rb') as config_file:
            configs.load(config_file)

        required_keys = [
            'WASABI_ENDPOINT',
            'WASABI_REGION',
            'WASABI_ACCESS_KEY',
            'WASABI_SECRET_KEY',
            'WASABI_BUCKET'
        ]
        creds = {}
        for key in required_keys:
            value = configs.get(key)
            if not value:
                raise ValueError(f"Chave {key} não encontrada no arquivo de configurações")
            creds[key] = value.data
        return creds

    except FileNotFoundError:
        raise SystemExit("Erro: Arquivo wasabi_credentials.properties não encontrado.")
    except Exception as e:
        raise SystemExit(f"Erro ao ler configurações: {str(e)}")

def get_s3_client(creds):
    return boto3.client(
        's3',
        endpoint_url=creds['WASABI_ENDPOINT'],
        aws_access_key_id=creds['WASABI_ACCESS_KEY'],
        aws_secret_access_key=creds['WASABI_SECRET_KEY'],
        region_name=creds['WASABI_REGION']
    )

def upload_file(local_path, key, creds):
    s3 = get_s3_client(creds)
    try:
        with open(local_path, 'rb') as data:
            s3.upload_fileobj(data, creds['WASABI_BUCKET'], key)
        print(f"Upload de '{local_path}' para '{key}' realizado com sucesso!")
    except Exception as e:
        print(f"Erro no upload: {e}")

def download_file(key, local_path, creds):
    s3 = get_s3_client(creds)
    try:
        s3.download_file(creds['WASABI_BUCKET'], key, local_path)
        print(f"Download de '{key}' para '{local_path}' realizado com sucesso!")
    except Exception as e:
        print(f"Erro no download: {e}")

def generate_temp_link(key, expires_in, creds):
    s3 = get_s3_client(creds)
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': creds['WASABI_BUCKET'], 'Key': key},
            ExpiresIn=expires_in
        )
        print(f"Link temporário ({expires_in}s):\n{url}")
    except Exception as e:
        print(f"Erro ao gerar link temporário: {e}")

def list_files(prefix, creds):
    s3 = get_s3_client(creds)
    try:
        response = s3.list_objects_v2(Bucket=creds['WASABI_BUCKET'], Prefix=prefix)
        print(f"Arquivos encontrados com prefixo '{prefix}':")
        if 'Contents' in response:
            for obj in response['Contents']:
                print(obj['Key'])
        else:
            print("Nenhum arquivo encontrado.")
    except Exception as e:
        print(f"Erro ao listar arquivos: {e}")

def main():
    parser = argparse.ArgumentParser(description="Utilitário Wasabi S3")
    subparsers = parser.add_subparsers(dest='command', required=True)

    up = subparsers.add_parser('upload', help='Enviar arquivo')
    up.add_argument('local_path')
    up.add_argument('key')

    down = subparsers.add_parser('download', help='Baixar arquivo')
    down.add_argument('key')
    down.add_argument('local_path')

    link = subparsers.add_parser('link', help='Gerar link temporário')
    link.add_argument('key')
    link.add_argument('--expires', type=int, default=3600, help='Tempo de validade em segundos (padrão: 3600)')

    lista = subparsers.add_parser('list', help='Listar arquivos')
    lista.add_argument('--prefix', default='', help='Prefixo do diretório (pasta/)')

    args = parser.parse_args()
    creds = load_credentials()

    if args.command == 'upload':
        upload_file(args.local_path, args.key, creds)
    elif args.command == 'download':
        download_file(args.key, args.local_path, creds)
    elif args.command == 'link':
        generate_temp_link(args.key, args.expires, creds)
    elif args.command == 'list':
        list_files(args.prefix, creds)

if __name__ == '__main__':
    main()
