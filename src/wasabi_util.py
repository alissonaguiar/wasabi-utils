import boto3
import argparse
from jproperties import Properties
import os
import sys

print("Wasabi Utils by Alisson Aguiar and Douglas Gomes")

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

def upload(local_path, s3_path, creds):
    s3 = get_s3_client(creds)
    bucket = creds['WASABI_BUCKET']
    
    if os.path.isfile(local_path):
        # Upload de arquivo único
        try:
            s3.upload_file(local_path, bucket, s3_path)
            print(f"Upload de arquivo: {local_path} -> {s3_path}")
        except Exception as e:
            print(f"Erro no upload de arquivo: {e}")
    
    elif os.path.isdir(local_path):
        # Upload recursivo de pasta
        try:
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_path)
                    s3_key = os.path.join(s3_path, relative_path).replace("\\", "/")
                    
                    s3.upload_file(local_file, bucket, s3_key)
                    print(f"Upload: {local_file} -> {s3_key}")
            print("Upload de pasta concluído!")
        except Exception as e:
            print(f"Erro no upload de pasta: {e}")
    else:
        print(f"Erro: Caminho local inválido - {local_path}")

def download(s3_path, local_path, creds):
    s3 = get_s3_client(creds)
    bucket = creds['WASABI_BUCKET']
    
    try:
        # Verifica se é um arquivo (trata nomes com espaços)
        if not s3_path.endswith('/'):
            try:
                # Verifica se o objeto existe
                s3.head_object(Bucket=bucket, Key=s3_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                s3.download_file(bucket, s3_path, local_path)
                print(f"Download de arquivo: {s3_path} -> {local_path}")
                return
            except:
                pass  # Não é um arquivo, tratar como pasta
        
        # Trata como pasta
        # Normaliza o caminho S3 garantindo que termine com '/'
        s3_path = s3_path.rstrip('/') + '/'
        
        # Cria o diretório local se necessário
        os.makedirs(local_path, exist_ok=True)
        
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=s3_path):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Ignora pastas virtuais
                    if key.endswith('/') or key == s3_path:
                        continue
                    
                    # Calcula caminho relativo
                    rel_path = os.path.relpath(key, s3_path)
                    local_file = os.path.join(local_path, rel_path)
                    os.makedirs(os.path.dirname(local_file), exist_ok=True)
                    
                    # Download do arquivo
                    s3.download_file(bucket, key, local_file)
                    print(f"Download: {key} -> {local_file}")
        print("Download de pasta concluído!")
    except Exception as e:
        print(f"Erro no download: {e}")

def list_files(prefix, creds):
    s3 = get_s3_client(creds)
    bucket = creds['WASABI_BUCKET']
    
    try:
        # Normaliza o prefixo para a raiz
        if prefix in ['', '.', '/', './']:
            prefix = ''
            print("Listando conteúdo da raiz do bucket:")
        else:
            prefix = prefix.rstrip('/') + '/'
            print(f"Conteúdo de '{prefix}':")
        
        paginator = s3.get_paginator('list_objects_v2')
        operation_parameters = {
            'Bucket': bucket,
            'Prefix': prefix,
            'Delimiter': '/'
        }
        
        for page in paginator.paginate(**operation_parameters):
            # Pastas
            if 'CommonPrefixes' in page:
                for folder in page['CommonPrefixes']:
                    folder_name = folder.get('Prefix')
                    display_name = folder_name[len(prefix):] if prefix else folder_name
                    print(f"[Pasta] {display_name.rstrip('/')}")
            
            # Arquivos
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key == prefix or key.endswith('/'):
                        continue
                    display_name = key[len(prefix):] if prefix else key
                    size_bytes = obj.get('Size', 0)
                    print(f"[Arquivo] {display_name} ({size_bytes} bytes)")
    except Exception as e:
        print(f"Erro ao listar arquivos: {e}")

def delete(s3_path, creds):
    s3 = get_s3_client(creds)
    bucket = creds['WASABI_BUCKET']
    
    try:
        # Primeiro tenta deletar como arquivo único
        if not s3_path.endswith('/'):
            try:
                s3.head_object(Bucket=bucket, Key=s3_path)
                s3.delete_object(Bucket=bucket, Key=s3_path)
                print(f"Arquivo deletado: {s3_path}")
                return
            except:
                # Não é um arquivo, tratar como pasta
                pass
        
        # Trata como pasta (deleção recursiva)
        s3_path = s3_path.rstrip('/') + '/'
        
        # Lista todos os objetos no prefixo
        objects_to_delete = []
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=s3_path):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    # Ignora pastas virtuais
                    if key != s3_path and not key.endswith('/'):
                        objects_to_delete.append({'Key': key})
        
        if not objects_to_delete:
            print("Nenhum arquivo encontrado para deletar.")
            return
        
        # Deleta em lotes (máximo de 1000 objetos por solicitação)
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i+1000]
            try:
                s3.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': batch, 'Quiet': True}
                )
            except Exception as e:
                print(f"Erro ao deletar lote: {e}")
                # Tenta deletar individualmente os objetos restantes
                for obj in batch:
                    try:
                        s3.delete_object(Bucket=bucket, Key=obj['Key'])
                    except Exception as single_error:
                        print(f"Erro ao deletar {obj['Key']}: {single_error}")
        
        print(f"Pasta deletada: {len(objects_to_delete)} arquivos removidos em '{s3_path}'")
        
    except Exception as e:
        print(f"Erro ao deletar: {e}")

def generate_temp_link(s3_path, expires_in, creds):
    s3 = get_s3_client(creds)
    bucket = creds['WASABI_BUCKET']
    
    try:
        # Verifica se é um arquivo (não funciona para pastas)
        if s3_path.endswith('/'):
            print("Erro: Gerar link temporário só é suportado para arquivos, não pastas.")
            return
            
        # Gera o link
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': s3_path},
            ExpiresIn=expires_in
        )
        print(f"\nLink temporário válido por {expires_in} segundos:\n\n{url}")
    except Exception as e:
        print(f"Erro ao gerar link temporário: {e}")

def main():
    parser = argparse.ArgumentParser(description="Utilitário Wasabi S3")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Upload
    up = subparsers.add_parser('upload', help='Enviar arquivo/pasta')
    up.add_argument('local_path', help='Caminho local do arquivo/pasta')
    up.add_argument('s3_path', help='Caminho no S3 (arquivo ou pasta)')

    # Download
    down = subparsers.add_parser('download', help='Baixar arquivo/pasta')
    down.add_argument('s3_path', help='Caminho no S3 (arquivo ou pasta)')
    down.add_argument('local_path', help='Caminho local de destino')

    # Listar
    lista = subparsers.add_parser('list', help='Listar pasta')
    lista.add_argument('prefix', nargs='?', default='', help='Caminho da pasta no S3 (deixe vazio para raiz)')

    # Deletar
    rm = subparsers.add_parser('delete', help='Deletar arquivo/pasta')
    rm.add_argument('s3_path', help='Caminho no S3 (arquivo ou pasta)')

    # Link temporário
    link = subparsers.add_parser('link', help='Gerar link temporário para download de arquivo')
    link.add_argument('s3_path', help='Caminho do arquivo no S3')
    link.add_argument('--expires', '-e', type=int, default=3600, help='Tempo de validade em segundos (padrão: 3600)')

    args = parser.parse_args()
    creds = load_credentials()

    if args.command == 'upload':
        upload(args.local_path, args.s3_path, creds)
    elif args.command == 'download':
        download(args.s3_path, args.local_path, creds)
    elif args.command == 'list':
        list_files(args.prefix, creds)
    elif args.command == 'delete':
        delete(args.s3_path, creds)
    elif args.command == 'link':
        generate_temp_link(args.s3_path, args.expires, creds)

if __name__ == '__main__':
    main()