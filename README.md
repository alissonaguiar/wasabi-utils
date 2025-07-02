# 📁 Wasabi Utils

Utilitário de linha de comando para operações com Wasabi (armazenamento compatível com S3).

---

## ⚙️ Funcionalidades

- 📤 **Upload** de arquivos/pastas (recursivo)  
- 📥 **Download** de arquivos/pastas (recursivo)  
- 📋 **Listagem** de conteúdo de pastas  
- 🗑️ **Deleção** de arquivos/pastas (recursivo)  

---

## 🧾 Pré-requisitos

- Python 3.6+
- Credenciais Wasabi configuradas

---

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/wasabi-utils.git
cd wasabi-utils
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

> 💡 Em sistemas Linux, use `pip3` caso necessário:
```bash
pip3 install -r requirements.txt
```

### 3. Configuração das credenciais

Crie um arquivo chamado `wasabi_credentials.properties` no mesmo diretório do script com o seguinte conteúdo:

```properties
WASABI_ENDPOINT=https://s3.wasabisys.com
WASABI_REGION=us-east-1
WASABI_ACCESS_KEY=SUA_ACCESS_KEY_AQUI
WASABI_SECRET_KEY=SUA_SECRET_KEY_AQUI
WASABI_BUCKET=SEU_BUCKET_AQUI
```

Proteja o arquivo de credenciais:

```bash
chmod 600 wasabi_credentials.properties
```

---

## 🚀 Uso

O utilitário é executado via linha de comando:

```bash
python wasabi_util.py [COMANDO] [ARGUMENTOS]
```

---

### 📚 Comandos Disponíveis

| Comando   | Descrição                                    | Sintaxe                                               |
|-----------|----------------------------------------------|--------------------------------------------------------|
| `upload`  | Envia arquivos/pastas para o Wasabi          | `upload <local> <destino-s3>`                         |
| `download`| Baixa arquivos/pastas do Wasabi              | `download <origem-s3> <local>`                        |
| `list`    | Lista conteúdo de um bucket/pasta            | `list [prefixo]`                                      |
| `delete`  | Remove arquivos/pastas do Wasabi             | `delete <caminho-s3>`                                 |
| `link`    | Gera link temporário para download de arquivo| `link <arquivo-s3> [--expires SEGUNDOS]`              |

---

### 📤 4.1 Upload

```bash
# Enviar arquivo único
python wasabi_util.py upload relatorio.pdf documentos/relatorios/relatorio_final.pdf

# Enviar pasta recursivamente (note a barra no final)
python wasabi_util.py upload ~/fotos/ albums/ferias2023/
```

---

### 📥 4.2 Download

```bash
# Baixar arquivo único (use aspas para nomes com espaços)
python wasabi_util.py download "musicas/rock/ACDC - Back In Black.mp3" "downloads/acdc.mp3"

# Baixar pasta recursivamente
python wasabi_util.py download backups/clientes/ ~/backups_local/
```

---

### 📋 4.3 Listagem

```bash
# Listar raiz do bucket
python wasabi_util.py list

# Listar pasta específica
python wasabi_util.py list documentos/

# Listar com prefixo parcial
python wasabi_util.py list doc
```

---

### 🗑️ 4.4 Deleção

```bash
# Deletar arquivo
python wasabi_util.py delete temporarios/arquivo_antigo.txt

# Deletar pasta recursivamente
python wasabi_util.py delete backups/2022/
```

---

### 🔗 4.5 Links Temporários

```bash
# Gerar link com validade padrão (1 hora)
python wasabi_util.py link relatorios/analise_final.pdf

# Gerar link com validade personalizada
python wasabi_util.py link imagens/logo.png --expires 600      # 10 minutos
python wasabi_util.py link documentos/contrato.docx -e 86400   # 1 dia
```

> ⚠️ **Nota:** Links temporários só funcionam para arquivos individuais, não para pastas.

---

## 🔒 Segurança e Boas Práticas

### 5.1 Proteção de Credenciais

- Nunca compartilhe o arquivo `wasabi_credentials.properties`
- Use permissões restritas:  
  ```bash
  chmod 600 wasabi_credentials.properties
  ```
- Adicione o arquivo ao seu `.gitignore` para evitar commits acidentais

### 5.2 Operações de Deleção

- **Todas as deleções são permanentes e irreversíveis**
- Considere habilitar o versionamento no bucket para maior segurança

### 5.3 Gerenciamento de Links

- Links podem ser acessados por **qualquer pessoa** com a URL
- Use tempos de expiração curtos para arquivos sensíveis
- Monitore acessos via logs do Wasabi quando possível

### 5.4 Gerenciamento de Buckets

- Utilize **políticas de bucket** para restringir acessos
- Prefira **credenciais temporárias (IAM)** em ambientes de produção
- Ative **logging de acesso** para fins de auditoria

## 🧯 Solução de Problemas

### ❌ Erro: Arquivo de credenciais não encontrado

```bash
Erro: Arquivo wasabi_credentials.properties não encontrado.
```

**Soluções:**

- Verifique se o arquivo está no mesmo diretório do script.
- Confira o nome do arquivo (deve ser exatamente `wasabi_credentials.properties`).
- Garanta que você tem permissão de leitura no arquivo.

---

### 📂 Erro: Pasta não encontrada ao listar

```bash
Nenhum arquivo encontrado.
```

**Soluções:**

- Use **barras no final do caminho**: `documentos/` em vez de `documentos`.
- Verifique se a pasta existe usando o painel Wasabi.
- Confira as permissões do bucket.

---

### 🧱 Erro: Caminhos com espaços

```bash
Erro no download: [Errno 2] No such file or directory...
```

**Solução:**

Sempre use **aspas** em caminhos que contenham espaços:

```bash
python wasabi_util.py download "caminho/com espaços/nome.txt" "destino/com espaços/nome.txt"
```

---

### 🔄 Erro 500 durante deleção

```bash
Erro ao deletar: An error occurred (500)...
```

**Soluções:**

- O script tentará novamente automaticamente.
- Verifique sua conexão com a internet.
- Tente novamente mais tarde se o erro persistir.
- Se o problema continuar, contate o suporte do Wasabi.

---

### ⏱️ Erro: Timeout em operações grandes

**Soluções:**

- Operações com muitos arquivos podem levar tempo.
- Considere **dividir operações grandes em partes menores**.
- Verifique a velocidade da sua conexão com a internet.

---

## 🔐 Segurança e Boas Práticas

### 1. Proteção de Credenciais

- Nunca compartilhe seu arquivo `wasabi_credentials.properties`.
- Use sempre permissões restritas:  
  ```bash
  chmod 600 wasabi_credentials.properties
  ```
- Adicione o arquivo ao seu `.gitignore` para evitar commits acidentais.

### 2. Operações de Deleção

- Todas as deleções são permanentes e irreversíveis.
- Teste comandos de delete em arquivos de teste antes de usar em produção.
- Considere habilitar versionamento no bucket para proteção adicional.

### 3. Gerenciamento de Links

- Links temporários podem ser acessados por qualquer pessoa que possua a URL.
- Use tempos de expiração curtos para dados sensíveis.
- Monitore o acesso através dos logs do Wasabi quando possível.

### 4. Gerenciamento de Buckets

- Use políticas de bucket para restringir acesso.
- Considere usar IAM para credenciais temporárias em ambientes de produção.
- Habilite logging de acesso para auditoria.

---

## ⚠️ Limitações Conhecidas

### 📁 Tamanho de Arquivo

- Limite máximo de 5GB por arquivo.
- Arquivos maiores requerem upload multiparte.

### ⏳ Feedback de Progresso

- Não mostra progresso durante transferências.
- Não estima tempo restante para operações longas.

### 📂 Gerenciamento de Pastas

- Pastas vazias não são representadas no S3.
- Links temporários não funcionam para pastas.

### 🔄 Resiliência

- Não reinicia automaticamente transferências interrompidas.
- Não verifica integridade de arquivos após transferência.

---

## 🚧 Roadmap

### Próximas Versões

- Suporte a transferências com progresso visual.
- Verificação de integridade de arquivos.
- Reinício automático de transferências interrompidas.

### Planejado para Futuro

- Suporte a arquivos maiores que 5GB.
- Configuração de região via linha de comando.
- Interface web para gerenciamento.

### Melhorias Desejadas

- Autocompletar para nomes de arquivos.
- Estimativa de tempo restante para operações.
- Encriptação client-side opcional.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga este processo:

### 🐞 Reporte Problemas

- Verifique se o problema já não foi reportado.
- Forneça detalhes completos.

### 💡 Sugira Melhorias

- Descreva claramente a funcionalidade sugerida.
- Explique por que seria útil.

### 🔧 Envie Pull Requests

- Fork o repositório.
- Crie uma branch descritiva.
- Commit suas mudanças.
- Abra um Pull Request com descrição detalhada.

---

## 📄 Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais informações.