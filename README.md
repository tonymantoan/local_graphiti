# What is this?
I thought [Graphiti's](https://github.com/getzep/graphiti) temporal knowledge graph for LLM memory sounded pretty cool, but out of the box it only uses ChatGPT and Claud. (You can setup the config so the OpenAI client points to any inference endpoint you want, but it will still try to use ChatGPT or Claud for tokenizing, and anyway depending the model you are using the prompts might not get formated correctly). I wanted to use for it my own locally running LLM application as well as have more control over the prompts and api requests to the inference endpoint.

After looking over Graphiti's code, it seemed pretty straightforward to extend a few of the core classes to use a local model for inference and emdeddings. Those extended classes are here, along with an adapted version of their sample app to use them. I also have some notes here on getting all the prereqs set up.
# TLDR
Given the complexity of the prompts involved, I am surprised how well the local models actually did.  Ultimately they were either too inconsistent or too slow to be practical, but they're not far off! I have hope that newer, better trained, more compact models will be able to handle the work load on my hardware in the near future. For now I am pursing other options for my home grown AI assistant's long term memory system, but I'll likely return to this before long.

# Results
I don't exactly have the best AI rig. This is all done on my Mac Pro M2 with 32GB of unified ram. I tried a variety models and quant sizes. I'll summarize how each did below.

For context, here are some prompts Graphiti uses to build the graph (slightly modified by my app):
The first prompt (Mistral format):
```
<s>
        [INST]

        You are an AI assistant that extracts entity nodes from conversational text. Your primary task is to identify and extract the speaker and other significant entities mentioned in the conversation.
[/INST]
[INST]
Follow the instructions. Only produce the required JSON response, do not include any explanation or other text.

Given the following conversation, extract entity nodes from the CURRENT MESSAGE that are explicitly or implicitly mentioned:

Conversation:
[]
<CURRENT MESSAGE>
Kamala Harris is the Attorney General of California. She was previously the district attorney for San Francisco.

Guidelines:
2. Extract significant entities, concepts, or actors mentioned in the conversation.
3. Provide concise but informative summaries for each extracted node.
4. Avoid creating nodes for relationships or actions.
5. Avoid creating nodes for temporal information like dates, times or years (these will be added to edges later).
6. Be as explicit as possible in your node names, using full names and avoiding abbreviations.

Respond with a JSON object in the following format:
{
    "extracted_nodes": [
        {
            "name": "Unique identifier for the node (use the speaker's name for speaker nodes)",
            "labels": ["Entity", "OptionalAdditionalLabel"],
            "summary": "Brief summary of the node's role or significance"
        }
    ]
}


[/INST]
```

And another:
```
<s>
        [INST]

        You are a helpful assistant that extracts graph edges from provided context.
[/INST]
[INST]
Follow the instructions. Only produce the required JSON response, do not include any explanation or other text.

        Given the following context, extract edges (relationships) that need to be added to the knowledge graph:
        Nodes:
        [
  {
    "uuid": "38b30f01-f977-4358-9f73-c713848fe9a5",
    "name": "Kamala Harris",
    "summary": "Attorney General of California and former district attorney for San Francisco"
  },
  {
    "uuid": "c8370678-fa44-4c32-ab7e-4954b704ba4b",
    "name": "California",
    "summary": "State where Kamala Harris serves as Attorney General"
  },
  {
    "uuid": "12d44475-858d-46af-8b90-25beb763c59f",
    "name": "San Francisco",
    "summary": "City where Kamala Harris was previously the district attorney"
  }
]



        Episodes:
        []
        Kamala Harris is the Attorney General of California. She was previously the district attorney for San Francisco. <-- New Episode


        Extract entity edges based on the content of the current episode, the given nodes, and context from previous episodes.

        Guidelines:
        1. Create edges only between the provided nodes.
        2. Each edge should represent a clear relationship between two DISTINCT nodes.
        3. The relation_type should be a concise, all-caps description of the relationship (e.g., LOVES, IS_FRIENDS_WITH, WORKS_FOR).
        4. Provide a more detailed fact describing the relationship.
        5. The fact should include any specific relevant information, including numeric information
        6. Consider temporal aspects of relationships when relevant.
        7. Avoid using the same node as the source and target of a relationship

        Respond with a JSON object in the following format:
        {
            "edges": [
                {
                    "relation_type": "RELATION_TYPE_IN_CAPS",
                    "source_node_uuid": "uuid of the source entity node",
                    "target_node_uuid": "uuid of the target entity node",
                    "fact": "brief description of the relationship",
                    "valid_at": "YYYY-MM-DDTHH:MM:SSZ or null if not explicitly mentioned",
                    "invalid_at": "YYYY-MM-DDTHH:MM:SSZ or null if ongoing or not explicitly mentioned"
                }
            ]
        }

        If no edges need to be added, return an empty list for "edges".


[/INST]
```

As I said above, I am surprised the local models did as well as they did with these! Here are the models I tried:
https://huggingface.co/anthracite-org/magnum-v4-22b-gguf

* [Magnum 12b Q8](https://huggingface.co/anthracite-org/magnum-v4-12b-gguf)
* [Mixtral 8x7b q4](https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/tree/main)
* [Mistral 22B instruct q8](https://huggingface.co/mradermacher/Mistral-Small-Instruct-2409-GGUF/tree/main)
* [Magnum 22B Q8](https://huggingface.co/anthracite-org/magnum-v4-22b-gguf)
* [Qwen 2.5 14B](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/tree/main)
* [Nemotron-70B-Instruct-HF-IQ2_M](https://huggingface.co/bartowski/Llama-3.1-Nemotron-70B-Instruct-HF-GGUF/tree/main)

For comparison to the graphs below, [here are the Graphiti docs](https://help.getzep.com/graphiti/graphiti/adding-episodes) which show an ideal version of the graph that should be produced by the sample app.

## Magnum 12B_Q8
Runtime -2 minutes.

This the first one I tried. The graphs are actaully from version 2, but version 4 has pretty similar results. Overall, I felt like it produced the best blanace of accuracy and speed. It could complete the queries in a reasonably short amount of time, and the accuracy was usually pretty good. But Sometimes it would come up with incorrect or partial answers. At it's best it made this graph:
<img width="965" alt="magnum_12b_q8_1" src="https://github.com/user-attachments/assets/5348d8f4-f22f-4ea0-a7cb-106687c1d727" />

But this is also one it came up with:
<img width="928" alt="magnum_12b_q8_2" src="https://github.com/user-attachments/assets/93f24264-56e2-43c1-b576-ac9b4e6b07b6" />

## Qwen 2.5 14B Q8
Runtime -2 minutes.
Initially did better than Magnum, but kept wrongly invalidating edges, or getting false-positives on duplicate nodes, so the final graph didn't have much in it.

## Mixtral 8x7B Q4
Runtime: ~10 minutes.
Before adding the json grammar to the llama.cpp api call, I was surprised that this model generated a lot of invalid json. Even with the grammar, it sometimes didn't follow the requested schema. Overall, too slow and not accurate enough. But I also can't run larger quant size on my machine. It usually came up with a graph similar to this:
<img width="966" alt="mixtral_8x7b_q4_grammar" src="https://github.com/user-attachments/assets/673f7e4d-eedc-4455-a9d6-ddc000a51c3e" />


## Mistral 22B Instruct Q8
Runtime: ~7 minutes.
This model did pretty well overall, aside from being slow on my machine. The main thing it whiffed on was identifying when edges are invalid and including date related facts. So the knowledge graph is decent, but it doesn't really take advantage of Graphiti's temoral capabilities.
<img width="970" alt="mistral-22b-q8" src="https://github.com/user-attachments/assets/b3b4a6bc-7004-4fe5-98da-b2988d3aee8c" />

## Magnum 22B Q8
Runtime: ~7 minutes
Magnum is fine tune of Mistral so, it's not surprising it's results were pretty similar to the base Mistral model above. I didn't run this one  many times, it seemed to do a little better at figuring out when edges should be marked at invalid. An interesting result since the stated purpose of the fine tune is to make it better at prose output. But for a better comparison I would need to run both models more times.
<img width="881" alt="magnum_22b_q8" src="https://github.com/user-attachments/assets/8b042384-156e-4408-8ad9-06d461038516" />

## Nemotron-70B-Instruct-HF-IQ2_M
Total sample app runtime: ~12 minutes.
Even at Q2 this really pushed my machine to it's limits. I didn't expect much out of a 2-bit model, but it showed the most comprehensive and accurate understanding of the prompts. Even this model struggled to dedupe nodes and come up with proper "invalid at" dates for edges.
<img width="557" alt="nemotron_70b_q2" src="https://github.com/user-attachments/assets/6525f125-07ff-4dfc-998e-2ced98417463" />

Interesting side note. Before I added the json grammer, this model took some prompts and reworked them into it's own set of instructions, broken into smaller steps, instead of returning the requested json. It even outputed the Mistral [INST] tags for each of its steps. It's output was pretty accurate in it's reasoning about the prompts, and seemed to identify all the relevant nodes and edges, but it wasn't usable by Graphiti. Also, it was generating so much output for it's reworked "prompts" and related explanitory text it took almost two hours to run!

## What to try next:
Llama.cpp also supports json schemas when using json grammar. I would like to fork the graphiti repo, and modify the calls to the LLM clients to pass in the json schema for each prompt. I'm curious to see how much that would improve the responses. I would also like to try modifying some of the prompts or breaking them into simpler steps to make it easier for smaller models to generate useful answers.

# Project Setup Notes

## Neo4J
Neo4j really pushes their desktop stuff (you need to sign up even for the free version), but you can get the headless community edition [here](https://neo4j.com/deployment-center/?ref=subscription#community). No need to sign up or create an account. Scroll to 'Graph Database Self-Managed' and make sure 'community' is selected.

1. Unzipped to ~/apps/neo4j-community-5.24.1
2. Used sdkman to install java correto 17
3. export NEO4J_HOME=$HOME/apps/neo4j-community-5.24.1
4. To start the server do: `$NEO4J_HOME/bin/neo4j start`
5. First time you login to the webapp (user and pass are `neo4j`) it will have you change the password.
[Installation instructions for macos](https://neo4j.com/docs/operations-manual/current/installation/osx/)

## Python
The docs for Graphiti say python version 3.9+ but I tried it with 3.13 and that didn't work. I had to use 3.11. I created a a virtual env and installed the packages.
1. `python3.11 -m venv kg_venv`
2. `source kg_venv/bin/activate`
3. `pip3 install` (I installed packages one at a time, and only created the requirements.txt later. Hopefully this is easier.)

## Llama.cpp
I ran it as a server with this command (updating the model path as needed):
`./llama-server -m ../ai_workspace/models/Llama-3.1-Nemotron-70B-Instruct-HF-IQ2_M.gguf -c 4096`

## Mac stuff
For larger models I needed to give the GPU more of the unified memory then it gets by default.
I added a file `/etc/sysctl.conf` and added the line
`iogpu.wired_limit_mb=28672`

To do it as a one-off you can just run the command `sudo sysctl iogpu.wired_limit_mb=28672`
