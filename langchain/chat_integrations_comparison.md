# Chat integrations comparison

## Integration details

| Field         | ChatOllama                                                                                                      | ChatOpenAI                                                                                    |
| :------------ | :-------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------- |
| Class         | [ChatOllama](https://reference.langchain.com/python/integrations/langchain_ollama/#langchain_ollama.ChatOllama) | [ChatOpenAI](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI) |
| Package       | [langchain-ollama](https://reference.langchain.com/python/integrations/langchain_ollama)                        | [langchain-openai](https://reference.langchain.com/python/integrations/langchain_openai)      |
| Serializable  | ❌                                                                                                              | beta                                                                                          |
| JS/TS Support | [JS support](https://js.langchain.com/docs/integrations/chat/ollama)                                            | ✅ ([npm](https://js.langchain.com/docs/integrations/chat/openai))                            |

## Model features

| Feature                                                                                | ChatOllama | ChatOpenAI |
| :------------------------------------------------------------------------------------- | :--------: | :--------: |
| [Tool calling](https://docs.langchain.com/oss/python/langchain/tools)                  | ✅         | ✅         |
| [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output) | ✅         | ✅         |
| Image input                                                                            | ✅         | ✅         |
| Audio input                                                                            | ❌         | ✅         |
| Video input                                                                            | ❌         | ❌         |
| [Token-level streaming](https://docs.langchain.com/oss/python/langchain/streaming)     | ✅         | ✅         |
| Native async                                                                           | ✅         | ✅         |
| [Token usage](https://docs.langchain.com/oss/python/langchain/models#token-usage)      | ❌         | ✅         |
| [Logprobs]https://docs.langchain.com/oss/python/langchain/models#log-probabilities     | ❌         | ✅         |

