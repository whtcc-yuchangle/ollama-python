from ollama import Client

client = Client()

messages = [
  {
    'role': 'user',
    'content': '你好！你有什么能力，你可以做什么呢？',
  },
]

for part in client.chat('modelscope.cn/unsloth/gemma-4-12b-it-GGUF:latest', messages=messages, stream=True):
  print(part.message.content, end='', flush=True)