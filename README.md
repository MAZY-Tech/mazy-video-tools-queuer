# MAZY Video Tools Queuer

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=MAZY-Tech_mazy-video-tools-queuer&metric=coverage)](https://sonarcloud.io/summary/new_code?id=MAZY-Tech_mazy-video-tools-queuer)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=MAZY-Tech_mazy-video-tools-queuer&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=MAZY-Tech_mazy-video-tools-queuer)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=MAZY-Tech_mazy-video-tools-queuer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=MAZY-Tech_mazy-video-tools-queuer)

## Visão Geral
**Mazy Video Tools Queuer** é uma aplicação serverless que realiza:
1. Recepção de eventos de upload de vídeo em um bucket S3 existente.
2. Enfileiramento de jobs de processamento de vídeo em uma fila SQS dedicada.
3. Processamento de atualizações de progresso, sucesso e falha em outra fila SQS.
4. Atualização de um banco de dados MongoDB com status de processamento e, em caso de sucesso, registro da localização do arquivo ZIP gerado com os frames extraídos.

## Arquitetura
- **Amazon S3**: Dispara a função de ingestão ao criar um novo objeto de vídeo.
- **Funções Lambda**:
  - **video-s3-handler**: Escuta eventos S3, lê metadata do vídeo e envia mensagem para a fila **InboundQueueUrl**.
  - **video-progress-updates**: Disparada por mensagens na fila **ProgressUpdatesQueue**; atualiza o MongoDB com porcentagem de progresso, status e localização do ZIP em caso de sucesso.
- **Amazon SQS**:
  - **ProgressUpdatesQueue**: Atualizações de progresso.
  - **ProgressUpdatesDeadLetterQueue**: Captura mensagens falhadas de ambas as filas.
- **MongoDB**: Armazena registros na coleção `video_events`.

## Funções

### video-s3-handler
- **Caminho**: `functions/video-s3-handler/`
- **Dependências**: `boto3`, `pymongo`
- **Variáveis de Ambiente**:
  - `S3_BUCKET`
  - `INBOUND_QUEUE_URL`
  - `DATABASE_HOST`
  - `DATABASE_USER`
  - `DATABASE_PASSWORD`
  - `DATABASE_NAME`
- **Permissões (LabRole)**:
  - `s3:GetObject`
  - `sqs:SendMessage`

### video-progress-updates
- **Caminho**: `functions/video-progress-updates/`
- **Dependências**: `boto3`, `pymongo`
- **Variáveis de Ambiente**:
  - `DATABASE_HOST`
  - `DATABASE_USER`
  - `DATABASE_PASSWORD`
  - `DATABASE_NAME`
- **Permissões (LabRole)**:
  - `sqs:ReceiveMessage`
  - `sqs:DeleteMessage`
  - `sqs:GetQueueAttributes`

## Implantação
Todos os recursos estão definidos no template SAM (`template.yaml`). Pontos principais:
- **Globals**: `Timeout`, `Runtime`, `MemorySize` e `EphemeralStorage`.
- **Parameters**: Bucket S3, filas SQS, conexão com MongoDB e configuração VPC.
- **Resources**:
  - `ProgressUpdatesQueue` (com `RedrivePolicy`), `ProgressUpdatesDeadLetterQueue`.
  - `VideoS3HandlerFunction` e `VideoProgressUpdatesFunction`.

### Deploy com SAM CLI
```bash
sam build
sam deploy --guided
```

## Monitoramento e Logs
- Ambas as Lambdas usam logs estruturados via `logger` compartilhado.
- Mensagens incorretas são encaminhadas para a DLQ.

## Licença
Este projeto está licenciado sob a **Apache License 2.0**.  
Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Participantes

- **Alison Israel - RM358367**  
  *Discord*: @taykarus | E-mail: taykarus@gmail.com

- **José Matheus de Oliveira - RM358854**  
  *Discord*: @jsmatheus | E-mail: matheusoliveira.info@gmail.com

- **Victor Zaniquelli - RM358533**  
  *Discord*: @zaniquelli | E-mail: zaniquelli@outlook.com.br

- **Yan Gianini - RM358368**  
  *Discord*: @.gianini | E-mail: yangianini@gmail.com
