
import asyncio
import json
import os
from google import genai
from google.genai import types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
import dotenv
dotenv.load_dotenv()
# The client gets the API key from the environment variable `GEMINI_API_KEY`.

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
previous_context = {"text": "", "tool_results": {}}
def reset_context():
    global previous_context
    previous_context = {"text": "", "tool_results": {}}
    
# Connect to your MCP server
async def use_mcp_with_gemini(prompt:str="Esitä minulle visaan liittyvä kysymys.")-> str:
    logging.info("Starting use_mcp_with_gemini")
    server_params = StdioServerParameters(
        command="c:\\Projects\\visa-mcp-server\\.venv\\Scripts\\python.exe",
        args=["main.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            mcp_tools = await session.list_tools()
            tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                k: v
                                for k, v in tool.inputSchema.items()
                                if k not in ["additionalProperties", "$schema"]
                            },
                        }
                    ]
                )
                for tool in mcp_tools.tools
            ]
            # Call MCP tool
            # result = await session.call_tool("get_random_faq", {})
            original_query=prompt
            role="Olet joviaali teekkarivisan pitäjä."
            full_prompt=f"Use visa-mcp-server-tool. Fetch the next question ONLY if explicitly prompted by the user. {role} {original_query}."
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=full_prompt,
                                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=tools,
                ),
            )
            for parts in response.candidates[0].content.parts:
                if parts.function_call:
                    result = await session.call_tool(
                        parts.function_call.name, arguments=dict(parts.function_call.args)
                    )
                    logging.info(f"Called tool {parts.function_call.name} with arguments {parts.function_call.args}, got result {result}")
                    results = [json.loads(result.text) for result in result.content]
                    tool_call_prompt=f"{role}. Based on the following tool call results, provide a response for: {original_query}. Tool results: {results}.",

                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=tool_call_prompt)                    
                    
                    # previous_context["tool_results"] = results
                    # previous_context["text"] = original_query
                    return final_response.text
            return response.text

if __name__ == "__main__":
    response_text=asyncio.run(use_mcp_with_gemini("Aloita visa 5:llä kysymyksellä ja esitä ensimmäinen niistä."))
    print(response_text)
    response_2=asyncio.run(use_mcp_with_gemini("Tarkista edellisen kysymyksen vastaus. Onko oikeavastaus 32?"))
    print(response_2)
    response_3=asyncio.run(use_mcp_with_gemini("Kysy minulta uusi kysymys."))
    print(response_3)
    response_3_1=asyncio.run(use_mcp_with_gemini("Onko vastaus vene?"))
    print(response_3_1)
    response_4=asyncio.run(use_mcp_with_gemini("Montako kysymystä on vielä jäljellä?"))
    print(response_4)
    response_5=asyncio.run(use_mcp_with_gemini("Lopeta visa."))
    print(response_5)