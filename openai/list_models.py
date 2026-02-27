from openai import OpenAI

# Client automatically uses the OPENAI_API_KEY environment variable
client = OpenAI()

# List the models
models_list = sorted(client.models.list(), key=lambda x: x.id)

print("Available models:")
# Iterate and print each model's ID
for model in models_list:
    print(model.id)