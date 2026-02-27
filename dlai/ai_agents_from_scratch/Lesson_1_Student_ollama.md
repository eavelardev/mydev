It PAUSE :) and print correctly

* **qwen3-vl:8b-instruct**
* **qwen3-vl:4b-thinking-q8_0**
* **qwen3-vl:4b-instruct-q8_0**
* **qwen3-vl:4b-instruct**
* **nemotron-3-nano:30b**
* **glm-4.7-flash**

It PAUSE, doesn't print like the instructions

* **gpt-oss:120b**
* **qwen3-vl:2b-thinking-q8_0**
* **qwen3-vl:8b-thinking**

Does not PAUSE

* **qwen3-vl:2b-instruct**
* **qwen3-vl:2b-instruct-q8_0**
* **qwen3-vl:4b-thinking**

```
Error code: 500 - {'error': {'message': "error parsing tool call: raw='average_dog_weight: Toy Poodle\n', err=invalid character 'a' looking for beginning of value", 'type': 'api_error', 'param': None, 'code': None}}
```

* **gpt-oss:20b**

Get stuck or it takes to much time
* **qwen3-vl:2b-thinking** > 1m


# model_name = "gpt-oss:120b" # 65 GB
# model_name = "nemotron-3-nano" # 24 GB
# model_name = "glm-4.7-flash" # 19 GB
# model_name = "gpt-oss" # 13 GB
# model_name = "qwen3-vl:8b-thinking" # 6.1 GB
# model_name = "qwen3-vl:8b-instruct" # 6.1 GB
# model_name = "qwen3-vl:4b-thinking-q8_0" # 5.1 GB
# model_name = "qwen3-vl:4b-instruct-q8_0" # 5.1 GB
# model_name = "qwen3-vl:4b-thinking" # 3.3 GB
model_name = "qwen3-vl:4b-instruct" # 3.3 GB
# model_name = "qwen3-vl:2b-thinking-q8_0" # 2.6 GB
# model_name = "qwen3-vl:2b-instruct-q8_0" # 2.6 GB
# model_name = "qwen3-vl:2b-thinking" # 1.9 GB
# model_name = "qwen3-vl:2b-instruct" # 1.9 GB