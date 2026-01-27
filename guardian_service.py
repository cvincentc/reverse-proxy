from vllm import LLM, SamplingParams

# Initialize the model
llm = LLM(
    model="ibm-granite/granite-guardian-3.0-2b",  # HuggingFace model name
    trust_remote_code=True
)

# Set sampling parameters
sampling_params = SamplingParams(
    temperature=0.1,
    top_p=0.95,
    max_tokens=512
)

# Generate response
prompts = ["Analyze this content for safety: 'Hello, how are you?'"]
outputs = llm.generate(prompts, sampling_params)

# Print response
for output in outputs:
    print(output.outputs[0].text)