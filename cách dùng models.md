````
---
language:
- en
- vi
license: apache-2.0
tags:
- text-generation-inference
- transformers
- mistral
- gguf
- vistral
- unsloth
base_model: Viet-Mistral/Vistral-7B-Chat
datasets:
- chillies/vn-legal-conversation
library_name: transformers
---

# Vistral-legal-chat

[![Model Card](https://img.shields.io/badge/Hugging%20Face-Model%20Card-blue)](https://huggingface.co/username/Vistral-legal-chat)

## Description

**Vistral-legal-chat** is a fine-tuned version of Vistral, enhanced using QLoRA on 31,000 question-answer pairs about Vietnamese law. This model serves as an expert legal advisor, capable of providing detailed answers and legal consultations for questions related to Vietnamese law.

## Installation

To use this model, you will need to install the following dependencies:

```bash
pip install transformers
pip install torch  # or tensorflow depending on your preference
````

## Usage

Here is how you can load and use the model in your code:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("username/Vistral-legal-chat")
model = AutoModelForCausalLM.from_pretrained("username/Vistral-legal-chat")

# Example usage
chat_template = """
<<SYS>>
Bạn là một chuyên viên tư vấn pháp luật Việt Nam. Bạn có nhiều năm kinh nghiệm và kiến thức chuyên sâu. Bạn sẽ cung cấp câu trả lời về pháp luật, tư vấn luật pháp cho các câu hỏi của User.
<</SYS>>
## user:
Tạm trú là gì?

## assistant:
"""

inputs = tokenizer(chat_template, return_tensors="pt")
outputs = model.generate(**inputs)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)
```

### Inference

Provide example code for performing inference with your model:

```python
# Example inference
user_question = "Tạm trú là gì?"
chat_template = f"""
<<SYS>>
Bạn là một chuyên viên tư vấn pháp luật Việt Nam. Bạn có nhiều năm kinh nghiệm và kiến thức chuyên sâu. Bạn sẽ cung cấp câu trả lời về pháp luật, tư vấn luật pháp cho các câu hỏi của User.
<</SYS>>
## user:
{user_question}

## assistant:
"""

inputs = tokenizer(chat_template, return_tensors="pt")
outputs = model.generate(**inputs)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)
```

### Training

If your model can be trained further, provide instructions for training:

```python
# Example training code
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()
```

## Training Details

### Training Data

The model was fine-tuned on a dataset of 31,000 question-answer pairs related to Vietnamese law. This dataset encompasses a wide range of legal topics to ensure comprehensive legal advice.

### Training Procedure

The model was fine-tuned using the QLoRA technique, optimizing for legal language understanding and response accuracy. Training was conducted on [describe hardware, e.g., GPUs, TPUs] over [number of epochs] epochs with [any relevant hyperparameters].

## Evaluation

### Metrics

The model was evaluated using the following metrics:

- **Accuracy**: X%
- **F1 Score**: Y%
- **Precision**: Z%
- **Recall**: W%

### Comparison

The performance of Vistral-legal-chat was benchmarked against other legal advice models, demonstrating superior accuracy and comprehensiveness in the Vietnamese legal domain.

## Limitations and Biases

While Vistral-legal-chat is highly accurate, it may have limitations in the following areas:

- It may not be up-to-date with the latest legal changes.
- There may be biases present in the training data that could affect responses.

## How to Contribute

We welcome contributions! Please see our [contributing guidelines](link_to_contributing_guidelines) for more information on how to contribute to this project.

## License

This model is licensed under the [MIT License](LICENSE).

## Acknowledgements

We would like to thank the contributors and the creators of the datasets used for training this model.

```

### Tips for Completing the Template

1. **Replace placeholders** (like `username`, `training data`, `evaluation metrics`) with your actual data.
2. **Include any additional information** specific to your model or training process.
3. **Keep the document updated** as the model evolves or more information becomes available.
```
