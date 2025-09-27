# Cherry E-commerce

## Descrição
Esse repositório contém o backend e frontend da aplicação cherry e-commerce

## Pré-requisitos
- Docker

## Instalação e Execução

### 1. Clone o repositório:

```bash
git clone https://github.com/paulosergioveras/cherry-ecommerce.git
cd cherry-ecommerce
```

### 2. Primeira execução (construir as imagens Docker):

```bash
docker-compose up --build
```
### 3. Para execuções posteriores:

```bash
docker-compose up -d
```

### 4. Para parar os containers:

```bash
docker-compose down
```

Pronto! Após esses passos o serviço será executado nas portas configuradas no arquivo docker-compose.yml

