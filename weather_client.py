import asyncio
import json
import os
import ssl
import certifi
import httpx
import signal
from contextlib import AsyncExitStack
from typing import Optional

from click import prompt
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI
from openai.types import Completion
import google.generativeai as genai

load_dotenv() # load environment variables from .env

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Setup OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_available = openai_key and openai_key.startswith('sk-')
        print(f"OpenAI API Key loaded: {'Yes' if self.openai_available else 'No'}")

        if self.openai_available:
            # TEMPORARY FIX: Disable SSL verification due to certificate issues
            print("⚠️  WARNING: SSL verification disabled - not secure for production!")
            http_client = httpx.Client(verify=False)
            self.openai = OpenAI(api_key=openai_key, http_client=http_client)
        else:
            self.openai = None

        # Setup Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_available = bool(gemini_key)
        print(f"Gemini API Key loaded: {'Yes' if self.gemini_available else 'No'}")
        
        if self.gemini_available:
            genai.configure(api_key=gemini_key)
            # Choose your preferred Gemini model:
            # 🔥 RECOMMENDED: gemini-2.5-flash (newest, fastest, best balance)
            # 🧠 POWERFUL: gemini-2.5-pro (most capable)
            # 💰 BUDGET: gemini-1.5-flash-8b (cheapest)
            # ⚡ FAST: gemini-2.0-flash
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            print(f"Using Gemini model: {gemini_model}")
            self.gemini = genai.GenerativeModel(gemini_model)
        else:
            self.gemini = None
        
        # Check if at least one AI provider is available
        if not self.openai_available and not self.gemini_available:
            raise ValueError("No AI provider available! Please set OPENAI_API_KEY or GEMINI_API_KEY")
        
        self.available_tools = []
        self.messages = []
        pass


    async def connect_to_sse_server(self, server_url: str):
        print("Connecting to MCP SSE server...")
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()
        print("Streams:", streams)

        self._session_contex = ClientSession(*streams)
        self.session: ClientSession = await self._session_contex.__aenter__()

        # initialize
        print("Initializing SSE client...")
        await self.session.initialize()
        print("Initialized SSE client")

        await self.get_available_tools();
        await self.get_initial_prompts();
        pass


    async def cleanup(self):
        """Gracefully cleanup all resources"""
        print("\n🔄 Shutting down gracefully...")
        
        # Close session context
        if hasattr(self, '_session_contex') and self._session_contex:
            try:
                await asyncio.wait_for(
                    self._session_contex.__aexit__(None, None, None), 
                    timeout=2.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                print(f"⚠️  Session cleanup timeout/error: {type(e).__name__}")
            finally:
                self._session_contex = None

        # Close streams context  
        if hasattr(self, '_streams_context') and self._streams_context:
            try:
                await asyncio.wait_for(
                    self._streams_context.__aexit__(None, None, None),
                    timeout=2.0
                )
            except (asyncio.TimeoutError, Exception) as e:
                print(f"⚠️  Streams cleanup timeout/error: {type(e).__name__}")
            finally:
                self._streams_context = None
                
        print("✅ Cleanup completed!")


    async def get_initial_prompts(self):
        prompt = await self.session.get_prompt("get_initial_prompts")

        messages = []

        for message in prompt.messages:
            messages.append({
                "role": message.role,
                "content": message.content.text
            })
            pass

        self.messages = messages
        pass


    async def get_available_tools(self):
        """Get available tools from the server"""
        print("Fetching available server tools...")
        response = await self.session.list_tools()
        print("Connected to MCP server with tools:", [tool.name for tool in response.tools])

        # Format tools for AI
        available_tools = [
            {
                "type": 'function',
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
                "strict": True,
            }
            for tool in response.tools
        ]

        self.available_tools = available_tools


    async def call_ai(self):
        """Call AI provider with fallback (Gemini -> OpenAI)"""
        
        # Try Gemini first if available (DEFAULT)
        if self.gemini_available:
            try:
                print("🤖 Trying Gemini...")
                # Convert messages to Gemini format
                gemini_messages = self._convert_messages_for_gemini()
                
                # Add tool information to the prompt
                tools_info = self._format_tools_for_gemini()
                full_prompt = f"{tools_info}\n\nUser: {gemini_messages}"
                
                response = self.gemini.generate_content(full_prompt)
                print("✅ Gemini succeeded")
                return {"provider": "gemini", "response": response}
            except Exception as e:
                print(f"❌ Gemini failed: {e}")
                if not self.openai_available:
                    raise

        # Fallback to OpenAI
        if self.openai_available:
            try:
                print("🤖 Trying OpenAI...")
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=1000,
                    messages=self.messages,
                    tools=self.available_tools
                )
                print("✅ OpenAI succeeded")
                return {"provider": "openai", "response": response}
            except Exception as e:
                print(f"❌ OpenAI failed: {e}")
                raise

        raise Exception("No AI provider available")


    def _convert_messages_for_gemini(self) -> str:
        """Convert chat messages to a single prompt for Gemini"""
        conversation = []
        for msg in self.messages:
            if msg["role"] == "user":
                conversation.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                conversation.append(f"Assistant: {msg['content']}")
            elif msg["role"] == "system":
                conversation.append(f"System: {msg['content']}")
        
        return "\n".join(conversation)


    def _format_tools_for_gemini(self) -> str:
        """Format available tools for Gemini prompt"""
        if not self.available_tools:
            return ""
        
        tools_desc = ["Available tools:"]
        for tool in self.available_tools:
            func = tool["function"]
            tools_desc.append(f"- {func['name']}: {func['description']}")
            if "parameters" in func and "properties" in func["parameters"]:
                params = []
                for param, details in func["parameters"]["properties"].items():
                    params.append(f"{param} ({details.get('type', 'unknown')})")
                tools_desc.append(f"  Parameters: {', '.join(params)}")
        
        tools_desc.append("\nTo use a tool, respond with JSON in this format:")
        tools_desc.append('{"tool_name": "function_name", "parameters": {"param1": "value1", "param2": "value2"}}')
        
        return "\n".join(tools_desc)


    async def process_ai_response(self, ai_result) -> str:
        """Process response from either OpenAI or Gemini"""
        provider = ai_result["provider"]
        response = ai_result["response"]
        
        if provider == "openai":
            return await self._process_openai_response(response)
        elif provider == "gemini":
            return await self._process_gemini_response(response)
        else:
            raise ValueError(f"Unknown provider: {provider}")


    async def _process_openai_response(self, response: Completion) -> str:
        """Process the response from OpenAI"""
        for choice in response.choices:
            if choice.finish_reason == "tool_calls":
                # We need to include the original message and assistant response
                self.messages.append(choice.message)

                for tool_call in choice.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(f"\n[Calling tool {tool_name} with args {tool_args}]...")
                    result = await self.session.call_tool(tool_name, tool_args)
                    print(f"\nTool response: {result}")
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result.content,
                        }
                    )

                response = await self.call_ai()
                return await self.process_ai_response(response)

            elif choice.finish_reason == "stop":
                print("\nAssistant: " + choice.message.content)
                return choice.message.content
            pass

        return ""


    async def _process_gemini_response(self, response) -> str:
        """Process response from Gemini"""
        response_text = response.text
        
        # Check if the response contains a tool call (JSON format)
        try:
            # Look for JSON in the response (handle markdown code blocks)
            import re
            # First try to find JSON in markdown code blocks (multiline)
            json_match = re.search(r'```json\s*(\{.*?"tool_name".*?\})\s*```', response_text, re.DOTALL)
            if not json_match:
                # Fallback to plain JSON (multiline)
                json_match = re.search(r'\{.*?"tool_name".*?\}', response_text, re.DOTALL)
            
            if json_match:
                # Extract JSON - use group(1) for markdown blocks, group() for plain JSON
                tool_call_json = json_match.group(1) if json_match.lastindex else json_match.group()
                tool_call = json.loads(tool_call_json)
                
                tool_name = tool_call["tool_name"]
                tool_args = tool_call["parameters"]
                
                print(f"\n[Calling tool {tool_name} with args {tool_args}]...")
                result = await self.session.call_tool(tool_name, tool_args)
                print(f"\nTool response: {result}")
                
                # Add the tool result to conversation context
                self.messages.append({
                    "role": "assistant", 
                    "content": f"I'll use the {tool_name} tool to get that information."
                })
                self.messages.append({
                    "role": "user",
                    "content": f"Tool {tool_name} returned: {result.content}"
                })
                
                # Call AI again to process the tool result
                response = await self.call_ai()
                return await self.process_ai_response(response)
            else:
                # Regular text response
                print(f"\nAssistant: {response_text}")
                return response_text
                
        except Exception as e:
            print(f"Error processing Gemini response: {e}")
            print(f"\nAssistant: {response_text}")
            return response_text


    async def process_query(self, query: str) -> str:
        """Process a query using AI providers with tool support"""
        self.messages.append({
            "role": "user",
            "content": query
        })

        response = await self.call_ai()
        return await self.process_ai_response(response)


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("Press Ctrl+C to exit gracefully.")

        while True:
            try:
                print("\n" + "-" * 100)
                
                # Get user input (handles Ctrl+C gracefully)
                try:
                    loop = asyncio.get_event_loop()
                    query = await loop.run_in_executor(None, input, "\nQuery: ")
                    query = query.strip()
                except (KeyboardInterrupt, EOFError):
                    print("\n👋 Goodbye!")
                    break

                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if query:
                    try:
                        await self.process_query(query)
                    except Exception as e:
                        print(f"\nDetailed Error: {type(e).__name__}: {str(e)}")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\nGeneral Error: {str(e)}")
                # Don't break on general errors, continue the loop


async def main():
    """Main function with proper signal handling"""
    client = None
    try:
        client = MCPClient()
        await client.connect_to_sse_server(server_url=os.getenv("MCP_SSE_URL"))
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\n⚠️  Received interrupt signal...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {str(e)}")
    finally:
        if client:
            await client.cleanup()


def setup_signal_handler():
    """Setup signal handlers for graceful shutdown"""
    shutdown_initiated = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_initiated
        if shutdown_initiated:
            # If shutdown already initiated, just exit
            print(f"\n🚪 Force exit...")
            os._exit(0)
        
        shutdown_initiated = True
        print(f"\n⚠️  Received signal {signum}")
        # Don't do anything here, let KeyboardInterrupt propagate
        raise KeyboardInterrupt()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    setup_signal_handler()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Final goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {type(e).__name__}: {str(e)}")
    
    print("🏁 Weather client stopped.")
