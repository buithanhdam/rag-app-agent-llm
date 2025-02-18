import json
import logging
from typing import List,Any, Optional
from colorama import Fore
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import ChatMessage
from src.agents.llm import BaseLLM
from src.agents.utils import PlanStep, ExecutionPlan, clean_json_response
from src.agents.base import BaseAgent, AgentOptions
logger = logging.getLogger(__name__)


class ReActAgent(BaseAgent):
    """Agent that creates and executes plans using available tools"""
    
    def __init__(self, llm: BaseLLM, options: AgentOptions, tools: List[FunctionTool] = []):
        super().__init__(llm, options)
        self.tools = tools
        self.tools_dict = {tool.metadata.name: tool for tool in tools}
        
    def _create_system_message(self, prompt: str) -> ChatMessage:
        return ChatMessage(role="system", content=prompt)
        
    def _format_tool_signatures(self) -> str:
        """Format all tool signatures into a string format LLM can understand"""
        if not self.tools:
            return "No tools are available. Respond based on your general knowledge only."
            
        tool_descriptions = []
        for tool in self.tools:
            metadata = tool.metadata
            parameters = metadata.get_parameters_dict()
            
            tool_descriptions.append(
                f"""
                Function: {metadata.name}
                Description: {metadata.description}
                Parameters: {json.dumps(parameters, indent=2)}
                """
            )
        
        return "\n".join(tool_descriptions)

    async def _get_initial_plan(self, task: str, chat_history: List[ChatMessage] = []) -> ExecutionPlan:
        """Generate initial execution plan with focus on available tools"""
        prompt = f"""
        You are a planning assistant with access to specific tools. Create a focused plan using ONLY the tools listed below.
        
        Task to accomplish: {task}
        
        Chat history: {str(chat_history)}
        
        Available tools and specifications:
        {self._format_tool_signatures()}
        
        Important rules:
        1. ONLY use the tools listed above - do not assume any other tools exist
        2. If a tool doesn't exist for a specific need, use your general knowledge to provide information
        3. For information retrieval tasks, immediately use the RAG search tool if available
        4. Keep the plan simple and focused - avoid unnecessary steps
        5. Never include web searches or external tool usage in the plan
        
        Format your response as JSON:
        {{
            "steps": [
                {{
                    "description": "step description",
                    "requires_tool": true/false,
                    "tool_name": "tool_name or null",
                    "is_required": true/false
                }},
                ...
            ]
        }}
        """
        
        try:
            response = await self.llm.achat(query=prompt)
            response = clean_json_response(response)
            plan_data = json.loads(response)
            
            plan = ExecutionPlan()
            for step_data in plan_data['steps']:
                # Validate tool name if step requires tool
                if step_data['requires_tool']:
                    tool_name = step_data.get('tool_name')
                    if tool_name not in self.tools_dict:
                        # Skip invalid tool steps
                        continue
                
                plan.add_step(PlanStep(
                    description=step_data['description'],
                    tool_name=step_data.get('tool_name'),
                    requires_tool=step_data.get('is_required', True)
                ))
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating initial plan: {str(e)}")
            raise

    async def _execute_tool(self, step: PlanStep) -> Optional[Any]:
        """Execute a tool with better error handling"""
        if not step.requires_tool or not step.tool_name:
            return None
            
        tool = self.tools_dict.get(step.tool_name)
        if not tool:
            return None
            
        prompt = f"""
        Generate parameters to call this tool:
        Step: {step.description}
        Tool: {step.tool_name}
        
        Tool specification:
        {json.dumps(tool.metadata.get_parameters_dict(), indent=2)}
        
        Response format:
        {{
            "arguments": {{
                // parameter names and values matching the specification exactly
            }}
        }}
        """
        
        try:
            response = await self.llm.achat(query=prompt)
            response = clean_json_response(response)
            params = json.loads(response)
            
            result = await tool.acall(**params['arguments'])
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {step.tool_name}: {str(e)}")
            if step.is_required:
                raise
            return None

    async def _generate_summary(self, task: str, results: List[Any], chat_history: List[ChatMessage] = []) -> str:
        """Generate a coherent summary of the results"""
        prompt = f"""
        Create a clear and concise summary based on the following:
        
        Original task: {task}
        Chat history: {str(chat_history)}
        Results from execution: {results}
        
        Rules:
        1. If no relevant information was found, clearly state that
        2. Don't mention the internal steps or tools used
        3. Focus on providing a direct, informative answer
        4. If the information seems insufficient, acknowledge that
        """
        
        try:
            return await self.llm.achat(query=prompt)
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise

    async def run(
        self,
        query: str,
        max_steps: int = 3,
        chat_history: List[ChatMessage] = [],
        verbose: bool = False
    ) -> str:
        """Execute the plan and generate response"""
        if verbose:
            print(Fore.BLUE + f"\nProcessing query: {query}")
        
        try:
            # Generate plan
            plan = await self._get_initial_plan(query,chat_history)
            
            if verbose:
                print(Fore.GREEN + "\nExecuting plan:")
            
            # Execute all steps and collect results
            results = []
            for step_num, step in enumerate(plan.steps, 1):
                if step_num > max_steps:
                    break
                    
                if verbose:
                    print(Fore.YELLOW + f"\nStep {step_num}: {step.description}")
                
                try:
                    if step.requires_tool:
                        result = await self._execute_tool(step)
                        if result is not None:
                            results.append(result)
                    else:
                        # Non-tool step - use LLM directly
                        result = await self.llm.achat(query=step.description)
                        results.append(result)
                        
                except Exception as e:
                    logger.error(f"Error in step {step_num}: {str(e)}")
                    if step.is_required:
                        raise
                        
            # Generate final summary
            return await self._generate_summary(query, results, chat_history)
            
        except Exception as e:
            logger.error(f"Error in run: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    async def _reflect_and_adjust(self, plan: ExecutionPlan, last_result: Any) -> bool:
        reflection_prompt = f"""
        Reflect on the current execution state and determine if the plan needs adjustment.
        Only respond with a valid JSON object containing your analysis and decisions.
        
        Current progress: {plan.get_progress()}
        Last result: {last_result}
        Remaining steps: {[step.description for step in plan.steps[plan.current_step + 1:]]}
        
        Available tools: {list(self.tools_dict.keys())}
        
        Respond with a JSON object in this exact format:
        {{
            "decision": "continue",
            "reasoning": "brief explanation",
            "modifications": []
        }}
        
        OR if modifications are needed:
        {{
            "decision": "modify",
            "reasoning": "brief explanation",
            "modifications": [
                {{
                    "type": "add|modify|remove",
                    "step_index": null,
                    "new_description": "step description",
                    "requires_tool": false,
                    "tool_name": null
                }}
            ]
        }}
        Remove the ```json and ```
        """
        
        try:
            response = await self.llm.achat(query=reflection_prompt)
            cleaned_response = clean_json_response(response)
            
            try:
                reflection_data = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}\nResponse: {cleaned_response}")
                return False
                
            if reflection_data.get("decision") == "continue":
                return False
                
            if reflection_data.get("decision") == "modify":
                modifications = reflection_data.get("modifications", [])
                plan_modified = False
                
                for mod in modifications:
                    try:
                        if mod["type"] == "add":
                            # Validate tool name if step requires tool
                            if mod.get("requires_tool", False):
                                tool_name = mod.get("tool_name")
                                if not tool_name or tool_name not in self.tools_dict:
                                    logger.warning(f"Skipping step with invalid tool: {tool_name}")
                                    continue
                                    
                            new_step = PlanStep(
                                description=mod["new_description"],
                                requires_tool=mod.get("requires_tool", False),
                                tool_name=mod.get("tool_name")
                            )
                            plan.add_step(new_step)
                            plan_modified = True
                            
                        elif mod["type"] == "modify":
                            step_index = mod.get("step_index")
                            if step_index is not None and 0 <= step_index < len(plan.steps):
                                if mod.get("requires_tool", False):
                                    tool_name = mod.get("tool_name")
                                    if not tool_name or tool_name not in self.tools_dict:
                                        logger.warning(f"Skipping modification with invalid tool: {tool_name}")
                                        continue
                                        
                                plan.steps[step_index] = PlanStep(
                                    description=mod["new_description"],
                                    requires_tool=mod.get("requires_tool", False),
                                    tool_name=mod.get("tool_name")
                                )
                                plan_modified = True
                                
                        elif mod["type"] == "remove":
                            step_index = mod.get("step_index")
                            if step_index is not None and 0 <= step_index < len(plan.steps):
                                plan.steps.pop(step_index)
                                plan_modified = True
                                
                    except KeyError as e:
                        logger.error(f"Missing required field in modification: {str(e)}")
                        continue
                        
                return plan_modified
                
        except Exception as e:
            logger.error(f"Error in reflection and adjustment: {str(e)}")
            return False
            
        return False
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup code if needed
        pass