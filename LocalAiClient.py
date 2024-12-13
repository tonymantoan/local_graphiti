import json
import logging
import typing
import requests
import re

from graphiti_core.prompts import Message
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.errors import RateLimitError

logger = logging.getLogger(__name__)


def extract_json_from_string( input_string ):
    # Find the first occurrence of '{' and the last occurrence of '}'
    print( f"extract json from input string: {input_string}" )
    start_index = input_string.find('{')
    end_index = input_string.rfind('}')
    
    # Check if both indices are valid
    if start_index == -1 or end_index == -1 or start_index > end_index:
        return "{}"  # Return None if no valid JSON is found
    
    # Extract the substring that is expected to be JSON
    json_str = input_string[start_index:end_index + 1]
    print( f"extraacted json string: {json_str}" )
    return json_str

class LocalAiClient(LLMClient):
    """
    LocalAiClient is a client class for interacting with self hosted language models.

    This class extends the LLMClient and provides methods to initialize the client,
    get an embedder, and generate responses from the language model.

    Attributes:
        baseUrl (str): Self hosted LLM Url to connect to for inference
        grammar_content (str): grammar to pass to Llamma.cpp to constrain the LLM output if None, no grammar will be used.
        temperature (float): The temperature to use for generating responses.
        max_tokens (int): The maximum number of tokens to generate in a response.

    Methods:
        __init__(config: LLMConfig | None = None, cache: bool = False, client: typing.Any = None):
            Initializes the LocalAIClient with the provided configuration, cache setting, and client.
            Note - This should probably accept param to format promts in chatML vs Mistral style, but for now
            you have to edit the code manually to do so.

        _generate_response(messages: list[Message]) -> dict[str, typing.Any]:
            Generates a response from the language model based on the provided messages.
    """

    def __init__(
        self, config: LLMConfig | None = None, grammar_file: str | None = None
    ):
        """
        Initialize the OpenAIClient with the provided configuration, cache setting, and client.

        Args:
            config (LLMConfig | None): The configuration for the LLM client, including API key, model, base URL, temperature, and max tokens.
            grammar_file (str | None): The path to the grammar file. If provided it will be read in, and used in the body of the POST to the inference endpoint.

        """
        if config is None:
            config = LLMConfig()

        super().__init__(config)
        self.base_url = config.base_url

        if grammar_file is not None:
            self.read_grammar_file( grammar_file )

    def read_grammar_file( self, grammar_file_path ):
        grammar_file = open( grammar_file_path, "r")
        self.grammar_content = grammar_file.read()
        grammar_file.close()

    async def _generate_response(self, messages: list[Message]) -> dict[str, typing.Any]:
        response_json_str = self.execute_llm_query(  messages )
        print( f'response json string:\n{response_json_str}' )
        llm_response_json = {}

        try:
            llm_response_json = json.loads(response_json_str)
        except json.JSONDecodeError:
            print( "Error parsing json string trying again..." )
            # re-raise the error, graphiti already has retry logic built in if _generate_response fails
            raise json.JSONDecodeError
            # try_again_content = f"Your previous response was not valid json. Here is your incorrect response: {response_json_str}\n Please try again to produce a response with correct JSON syntax."
            # try_again_msg = Message( role = "user", content = try_again_content )
            # messages.append( try_again_msg )
            # response_json_str = self.execute_llm_query(  messages )
            # try:
            #     llm_response_json = json.loads(response_json_str)
            # except json.JSONDecodeError:
            #     print( "Second attempt to get valid json failed" )

        print( f'Final llm respons is {json.dumps(llm_response_json)}' )

        return llm_response_json

    def execute_llm_query(self, messages: list[Message]) -> dict[str, typing.Any]:
        print( f'Generate Local llm response for prompts:' )
        full_prompt = self.format_prompt_for_mistral( messages )
        # full_prompt = self.format_prompt_for_chatml( messages )
        print( f'Full prompt is: {full_prompt}' )

        request_body = {
            "prompt": full_prompt,
            "n_predict": self.max_tokens,
            "temperature": self.temperature,
            "grammar": self.grammar_content,
        }

        response = requests.post( self.base_url, json=request_body )
        response_message = response.json()['content']
        extracted_json_str = extract_json_from_string( response_message )
        return extracted_json_str

    def format_prompt_for_mistral(self, messages: list[Message]) -> str:
        system_prompt = """
        <s>
        [INST]

        """
        instructions = "Follow the instructions. Only produce the required JSON response, do not include any explanation or other text.\n"
        for m in messages:
            if m.role == 'system':
                system_prompt = system_prompt + m.content + "\n"
            else:
                instructions = instructions + m.content + "\n"

        system_prompt = system_prompt + "[/INST]"
        return f"{system_prompt}\n[INST]\n{instructions}\n[/INST]"

    def format_prompt_for_chatml(self, messages: list[Message]) -> str:
        system_prompt = ""
        instructions = "Follow the instructions. Only produce the required JSON response, do not include any explanation or other text.\n"
        for m in messages:
            if m.role == 'system':
                system_prompt = system_prompt + m.content + "\n"
            else:
                instructions = instructions + m.content + "\n"

        extra_inst = ""
        return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{instructions}\n{extra_inst}\n<|im_end|>"
