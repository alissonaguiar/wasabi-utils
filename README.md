## Instalação

Clone o repositório e instale as dependências

git clone https://github.com/seuusuario/wasabi-utils.git
cd wasabi-utils
pip install -r requirements.txt

## VENV
source .venv/bin/activate && pip install boto3


## Configuração

1. Copie `wasabi_credentials.properties.example` para `wasabi_credentials.properties`.
2. Preencha com suas credenciais Wasabi.

## Uso

python src/wasabi_utils/wasabi_util.py upload arquivo_local.txt destino_no_bucket.txt
python src/wasabi_utils/wasabi_util.py download destino_no_bucket.txt arquivo_baixado.txt
python src/wasabi_utils/wasabi_util.py link destino_no_bucket.txt --expires 600
python src/wasabi_utils/wasabi_util.py list --prefix pasta/


## Segurança
**Nunca suba suas credenciais reais para o GitHub!**

## Estrutura do Projeto

wasabi-utils/
├── src/
│ └── wasabi_utils/
│ └── wasabi_util.py
├── tests/
│ └── test_wasabi_util.py
├── examples/
│ └── exemplo_upload.py
├── .gitignore
├── README.md
├── LICENSE
├── requirements.txt
├── wasabi_credentials.properties.example

## Testes
Coloque seus testes na pasta `tests/` e rode com [pytest](https://pytest.org).

## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.




# BUCKET ALISSON (TESTE)

name= mralisson
region= us-central-1
public_access= default